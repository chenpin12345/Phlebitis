from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from src.common import ROOT, inside, read_json, write_json
from src.inference.engine import InvalidImage, Predictor
from src.line_bot.messages import command, results, text_message
from src.lock import OperationLock


@dataclass
class Settings:
    secret: str
    token: str
    public_url: str
    weights: Path
    device: str = "0"
    allow_demo: bool = False
    runtime: Path = ROOT / "runtime"
    queue_size: int = 4
    ttl: int = 3600
    timeout: int = 120

    @classmethod
    def load(cls):
        from dotenv import load_dotenv
        load_dotenv(ROOT/".env",override=False)
        cfg=read_json(ROOT/"configs/service.json")
        s=cls(os.getenv("LINE_CHANNEL_SECRET",""),os.getenv("LINE_CHANNEL_ACCESS_TOKEN",""),os.getenv("PUBLIC_BASE_URL","").rstrip("/"),inside(os.getenv("MODEL_PATH","models/selected/best.pt")),os.getenv("INFERENCE_DEVICE","0"),os.getenv("DEMO_MODEL_ALLOWED","false").lower()=="true",queue_size=int(os.getenv("LINE_QUEUE_SIZE",str(cfg["queue_size"]))),ttl=int(os.getenv("RESULT_TTL_SECONDS",str(cfg["result_ttl_seconds"]))),timeout=cfg["job_timeout_seconds"])
        if not s.secret or not s.token:
            raise ValueError("Set LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN in .env")
        parsed=urlparse(s.public_url)
        if parsed.scheme!="https" or not parsed.hostname or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("PUBLIC_BASE_URL must be a public HTTPS base address")
        if not 1<=s.queue_size<=20 or not 60<=s.ttl<=3600:
            raise ValueError("Queue size must be 1..20 and result TTL 60..3600 seconds")
        return s


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    expected=base64.b64encode(hmac.new(secret.encode(),body,hashlib.sha256).digest()).decode()
    try:
        return hmac.compare_digest(expected.encode("ascii"),signature.encode("ascii"))
    except UnicodeEncodeError:
        return False


class LineClient:
    def __init__(self,token):
        self.http=httpx.AsyncClient(headers={"Authorization":f"Bearer {token}"},timeout=20,follow_redirects=False)
    async def close(self): await self.http.aclose()
    async def image(self,message_id,max_bytes):
        parts=[];total=0
        async with self.http.stream("GET",f"https://api-data.line.me/v2/bot/message/{message_id}/content") as res:
            res.raise_for_status()
            async for block in res.aiter_bytes():
                total+=len(block)
                if total>max_bytes: raise InvalidImage("圖片超過 10 MB，請縮小後再傳。")
                parts.append(block)
        return b"".join(parts)
    async def loading(self,user):
        res=await self.http.post("https://api.line.me/v2/bot/chat/loading/start",json={"chatId":user,"loadingSeconds":60})
        res.raise_for_status()
    async def send(self,user,reply_token,messages,received_at):
        if reply_token and time.time()-received_at<45:
            res=await self.http.post("https://api.line.me/v2/bot/message/reply",json={"replyToken":reply_token,"messages":messages})
            res.raise_for_status()
        else:
            # This key identifies this one push request; no automatic retry is performed.
            import uuid
            res=await self.http.post("https://api.line.me/v2/bot/message/push",headers={"X-Line-Retry-Key":str(uuid.uuid4())},json={"to":user,"messages":messages})
            res.raise_for_status()


class Store:
    def __init__(self,path, *, clock=time.time, reconcile=True):
        self.clock=clock
        path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS jobs(event_id TEXT PRIMARY KEY,message_id TEXT,user_key TEXT,status TEXT,token TEXT,expires REAL,updated REAL,error TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS unsent(message_id TEXT PRIMARY KEY,expires REAL)")
        if reconcile: self.db.execute("UPDATE jobs SET status='interrupted',updated=? WHERE status IN ('queued','running')",(self.clock(),))
        self.db.commit()
    def reserve(self,event,message,user_key,status="queued"):
        # LINE redelivery may arrive out of order, including after an unsend.
        if self.db.execute("SELECT 1 FROM unsent WHERE message_id=? AND expires>?",(message,self.clock())).fetchone():
            return "cancelled"
        if self.db.execute("SELECT 1 FROM jobs WHERE event_id=?",(event,)).fetchone(): return "duplicate"
        if status=="queued" and self.db.execute("SELECT 1 FROM jobs WHERE user_key=? AND status IN ('queued','running')",(user_key,)).fetchone(): return "busy"
        self.db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?)",(event,message,user_key,status,None,None,self.clock(),None));self.db.commit();return "accepted"
    def update(self,event,status,token=None,expires=None,error=None):
        self.db.execute("UPDATE jobs SET status=?,token=COALESCE(?,token),expires=COALESCE(?,expires),updated=?,error=? WHERE event_id=?",(status,token,expires,self.clock(),error,event));self.db.commit()
    def cancelled(self,event):
        row=self.db.execute("SELECT status FROM jobs WHERE event_id=?",(event,)).fetchone()
        return not row or row[0]=="cancelled"
    def unsend(self,message):
        self.db.execute("INSERT OR REPLACE INTO unsent VALUES(?,?)",(message,self.clock()+86400))
        tokens=[r[0] for r in self.db.execute("SELECT token FROM jobs WHERE message_id=?",(message,)) if r[0]]
        self.db.execute("UPDATE jobs SET status='cancelled',updated=? WHERE message_id=?",(self.clock(),message));self.db.commit();return tokens
    def expiry(self,token):
        r=self.db.execute("SELECT expires,status FROM jobs WHERE token=?",(token,)).fetchone()
        return r[0] if r and r[1]=="completed" else None
    def cleanup(self):
        self.db.execute("DELETE FROM unsent WHERE expires<=?",(self.clock(),))
        self.db.execute("DELETE FROM jobs WHERE updated<? AND status NOT IN ('queued','running')",(self.clock()-86400,));self.db.commit()
    def close(self): self.db.close()


def create_app(settings=None,*,predictor=None,client=None):
    supplied=predictor is not None

    @asynccontextmanager
    async def lifespan(app):
        s=settings or Settings.load()
        app.state.settings=s
        s.runtime.mkdir(parents=True,exist_ok=True)
        (s.runtime/"results").mkdir(exist_ok=True)
        lock=None
        if not supplied:
            lock=OperationLock();lock.__enter__()
        try:
            app.state.predictor=predictor or Predictor(s.weights,device=s.device,allow_demo=s.allow_demo)
        except BaseException:
            if lock:lock.__exit__(None,None,None)
            raise
        app.state.client=client or LineClient(s.token)
        app.state.store=Store(s.runtime/"jobs.sqlite3")
        app.state.queue=asyncio.Queue(maxsize=s.queue_size)
        app.state.notifications=set()
        app.state.accepting=True
        if not supplied:(s.runtime/'line-control.json').unlink(missing_ok=True)
        worker=asyncio.create_task(work(app))
        cleaner=asyncio.create_task(clean(app))
        async def control():
            while True:
                path=s.runtime/'line-control.json'
                if path.exists() and read_json(path).get('action')=='drain':
                    app.state.accepting=False
                    write_json(s.runtime/'line-state.json',{'state':'draining','queue':app.state.queue.qsize(),'pid':os.getpid()})
                    await app.state.queue.join()
                    worker.cancel()
                    await asyncio.gather(worker,return_exceptions=True)
                    app.state.predictor=None
                    if not supplied:
                        import torch
                        if torch.cuda.is_available():torch.cuda.empty_cache()
                    if lock and not getattr(app.state,'released',False):
                        lock.__exit__(None,None,None);app.state.released=True
                    write_json(s.runtime/'line-state.json',{'state':'stopped','pid':os.getpid(),'resources_released':True})
                    return
                await asyncio.sleep(1)
        controller=asyncio.create_task(control())
        if not supplied:write_json(s.runtime/'line-state.json',{'state':'accepting','pid':os.getpid()})
        try:
            yield
        finally:
            worker.cancel();cleaner.cancel();controller.cancel()
            await asyncio.gather(worker,cleaner,controller,return_exceptions=True)
            for t in app.state.notifications:t.cancel()
            await asyncio.gather(*app.state.notifications,return_exceptions=True)
            app.state.store.close()
            await app.state.client.close()
            if lock and not getattr(app.state,'released',False):lock.__exit__(None,None,None)

    app=FastAPI(title="Phlebitis LINE research demo",docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)

    def schedule(coro):
        task=asyncio.create_task(coro)
        app.state.notifications.add(task)
        task.add_done_callback(app.state.notifications.discard)

    async def safe_send(user,token,messages,received):
        try:await app.state.client.send(user,token,messages,received)
        except Exception:
            # Do not log access tokens, user IDs or message contents.
            print("LINE notification failed; check network or message quota.")

    @app.get("/health")
    async def health():
        predictor=app.state.predictor
        return {"status":"ready" if app.state.accepting else "draining_or_stopped","model_family":predictor.metadata.get('model','YOLO11n') if predictor else None,"demo_only":bool(predictor.metadata.get("demo_only")) if predictor else None,"queue":app.state.queue.qsize()}

    @app.post("/webhook")
    async def webhook(request:Request):
        chunks=[];length=0
        async for block in request.stream():
            length+=len(block)
            if length>1024*1024:raise HTTPException(413,"Webhook too large")
            chunks.append(block)
        body=b"".join(chunks)
        s=app.state.settings
        if not verify_signature(body,request.headers.get("x-line-signature",""),s.secret):
            raise HTTPException(401,"Invalid signature")
        try:
            payload=json.loads(body)
            events=payload["events"]
            if not isinstance(events,list):raise ValueError()
        except (ValueError,KeyError,TypeError):raise HTTPException(400,"Invalid event payload")
        for event in events:
            if not isinstance(event,dict):continue
            kind=event.get("type")
            if kind=="unsend":
                mid=str(event.get("unsend",{}).get("messageId",""))
                for token in app.state.store.unsend(mid):
                    (s.runtime/"results"/(token+".jpg")).unlink(missing_ok=True)
                continue
            user=event.get("source",{}).get("userId","")
            if event.get("source",{}).get("type")!="user" or not user:
                continue
            received=time.time()
            reply=event.get("replyToken")
            eid=event.get("webhookEventId")
            if not eid or not reply:continue
            msg=event.get("message",{})
            user_key=hmac.new(s.secret.encode(),user.encode(),hashlib.sha256).hexdigest()
            if kind=="follow" or (kind=="message" and msg.get("type")=="text"):
                state=app.state.store.reserve(eid,str(msg.get("id","")),user_key,"completed")
                if state=="accepted":schedule(safe_send(user,reply,[text_message(command(msg.get("text","專題介紹")))],received))
            elif kind=="message" and msg.get("type")=="image":
                mid=str(msg.get("id",""))
                if not re.fullmatch(r"[0-9]+",mid):continue
                if not app.state.accepting:
                    state=app.state.store.reserve(eid,mid,user_key,'rejected')
                    if state=='accepted':schedule(safe_send(user,reply,[text_message('本地模型目前進行維護，暫停照片分析。請稍後再試。')],received))
                    continue
                state=app.state.store.reserve(eid,mid,user_key)
                if state in {"duplicate","cancelled"}:continue
                if state=="busy":
                    # Record rejected events too, so redelivery cannot produce another message.
                    app.state.store.reserve(eid,mid,user_key,"rejected")
                    schedule(safe_send(user,reply,[text_message("上一張照片仍在處理，請等待結果後再傳送。")],received))
                    continue
                try:app.state.queue.put_nowait((eid,mid,user,reply,received))
                except asyncio.QueueFull:
                    app.state.store.update(eid,"rejected")
                    schedule(safe_send(user,reply,[text_message("目前分析工作已滿，請稍後重新傳送。")],received))
            elif kind=="message":
                state=app.state.store.reserve(eid,str(msg.get("id","")),user_key,"completed")
                if state=="accepted":schedule(safe_send(user,reply,[text_message("目前只接受照片，請傳送一張 JPEG、PNG 或 WEBP 圖片。")],received))
        return {"ok":True}

    @app.get("/results/{token}.jpg")
    async def result_image(token:str):
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}",token):raise HTTPException(404)
        expires=app.state.store.expiry(token)
        path=app.state.settings.runtime/"results"/(token+".jpg")
        if not expires or expires<=time.time() or not path.exists():
            raise HTTPException(410,"Result expired")
        return FileResponse(path,media_type="image/jpeg",headers={"Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"})

    return app


async def work(app):
    s=app.state.settings
    store=app.state.store
    while True:
        job=await app.state.queue.get()
        eid,mid,user,reply,received=job
        inference=None
        try:
            if store.cancelled(eid):continue
            store.update(eid,"running")
            try:await app.state.client.loading(user)
            except Exception:pass
            raw=await app.state.client.image(mid,app.state.predictor.config["max_image_bytes"])
            if store.cancelled(eid):continue
            inference=asyncio.create_task(asyncio.to_thread(app.state.predictor.predict,raw))
            try:
                record,jpeg=await asyncio.wait_for(asyncio.shield(inference),s.timeout)
            except asyncio.TimeoutError:
                if not store.cancelled(eid):
                    await app.state.client.send(user,reply,[text_message("分析逾時，請稍後重新傳送。")],received)
                # A timed-out GPU thread cannot be force-killed. Keep the worker slot until it exits.
                await asyncio.gather(inference,return_exceptions=True)
                if not store.cancelled(eid):store.update(eid,"failed",error="inference_timeout")
                continue
            if store.cancelled(eid):continue
            token=secrets.token_urlsafe(32)
            path=s.runtime/"results"/(token+".jpg")
            path.write_bytes(jpeg)
            store.update(eid,"completed",token=token,expires=time.time()+s.ttl)
            try:
                await app.state.client.send(user,reply,results(record,s.public_url+"/results/"+token+".jpg"),received)
            except Exception:
                # Delivery may have succeeded despite a network timeout. Keep its URL valid.
                store.update(eid,"completed",error="delivery_unconfirmed")
                print("LINE result delivery unconfirmed; inspect connectivity and account quota.")
        except asyncio.CancelledError:
            if inference:await asyncio.gather(inference,return_exceptions=True)
            if not store.cancelled(eid):store.update(eid,"interrupted",error="service_shutdown")
            raise
        except Exception as exc:
            if not store.cancelled(eid):
                store.update(eid,"failed",error=type(exc).__name__)
                message=str(exc) if isinstance(exc,InvalidImage) else "分析暫時失敗，請稍後重新傳送照片。"
                try:await app.state.client.send(user,reply,[text_message(message)],received)
                except Exception:pass
        finally:
            # A notification failure must never release the compute slot early.
            if inference is not None and not inference.done():
                await asyncio.gather(inference, return_exceptions=True)
            raw = record = jpeg = inference = None
            app.state.queue.task_done()


async def clean(app):
    while True:
        s=app.state.settings
        for p in (s.runtime/"results").glob("*.jpg"):
            expires=app.state.store.expiry(p.stem)
            if not expires or expires<=time.time():p.unlink(missing_ok=True)
        app.state.store.cleanup()
        await asyncio.sleep(30)

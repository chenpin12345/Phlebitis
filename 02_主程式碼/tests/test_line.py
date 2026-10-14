import base64
import hashlib
import hmac
import io
import json
import secrets
import threading
import time
from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from src.line_bot.service import Settings,Store,create_app,verify_signature
from src.inference.engine import InvalidImage


class FakePredictor:
    metadata={"demo_only":True}
    config={"max_image_bytes":100000}
    calls=0
    def predict(self,raw):
        self.calls+=1
        if raw==b"broken":raise InvalidImage("無法讀取圖片")
        return {"status":"suspected","boxes":[{"confidence":0.8}],"model_version":"test","elapsed_ms":1,"demo_only":True},jpeg()


def jpeg():
    buf=io.BytesIO();Image.new("RGB",(100,100)).save(buf,format="JPEG");return buf.getvalue()


class FakeLine:
    def __init__(self):self.sent=[];self.raw=jpeg()
    async def image(self,mid,maxbytes):return self.raw
    async def send(self,user,reply,messages,received):self.sent.append(messages)
    async def loading(self,user):pass
    async def close(self):pass


def settings(tmp_path):
    return Settings("test-secret","fake-token","https://demo.example",Path("unused"),runtime=tmp_path)

def post(client,events):
    body=json.dumps({"events":events}).encode()
    signature=base64.b64encode(hmac.new(b"test-secret",body,hashlib.sha256).digest()).decode()
    return client.post("/webhook",content=body,headers={"x-line-signature":signature,"content-type":"application/json"})

def event(eid="e1",mid="123"):
    return {"type":"message","webhookEventId":eid,"replyToken":"reply","source":{"type":"user","userId":"U-test"},"message":{"type":"image","id":mid}}

def until(predicate):
    deadline=time.time()+3
    while not predicate():
        if time.time()>deadline:raise AssertionError("worker did not finish")
        time.sleep(0.02)

def test_signature_and_empty_verification(tmp_path):
    app=create_app(settings(tmp_path),predictor=FakePredictor(),client=FakeLine())
    with TestClient(app) as c:
        assert c.post("/webhook",content=b"{}").status_code==401
        assert post(c,[]).status_code==200
        assert c.get("/health").json()["demo_only"] is True

def test_image_reply_dedup_and_expiry(tmp_path):
    line=FakeLine();pred=FakePredictor();app=create_app(settings(tmp_path),predictor=pred,client=line)
    with TestClient(app) as c:
        assert post(c,[event()]).status_code==200
        until(lambda:bool(line.sent))
        assert pred.calls==1
        post(c,[event()]);time.sleep(.05);assert pred.calls==1
        url=line.sent[0][1]["originalContentUrl"]
        path=url.removeprefix("https://demo.example")
        assert c.get(path).status_code==200
        assert c.get("/results/../../.env.jpg").status_code!=200
        assert post(c,[{"type":"unsend","unsend":{"messageId":"123"}}]).status_code==200
        assert c.get(path).status_code==410

def test_invalid_image_receives_error(tmp_path):
    line=FakeLine();line.raw=b"broken"
    app=create_app(settings(tmp_path),predictor=FakePredictor(),client=line)
    with TestClient(app) as c:
        post(c,[event()]);until(lambda:bool(line.sent))
        assert "無法讀取" in line.sent[0][0]["text"]

def test_restart_marks_unfinished_jobs_interrupted(tmp_path):
    store=Store(tmp_path/"jobs.sqlite3")
    store.reserve("e","1","u");store.close()
    store=Store(tmp_path/"jobs.sqlite3")
    assert store.db.execute("SELECT status FROM jobs").fetchone()[0]=="interrupted"
    assert store.reserve("e","1","u")=="duplicate"
    store.close()

def test_busy_user_does_not_start_second_inference(tmp_path):
    gate=threading.Event()
    class Slow(FakePredictor):
        def predict(self,raw):
            gate.wait(2)
            return super().predict(raw)
    pred=Slow();line=FakeLine()
    app=create_app(settings(tmp_path),predictor=pred,client=line)
    with TestClient(app) as c:
        try:
            post(c,[event()])
            post(c,[event("e2","124")])
            until(lambda:bool(line.sent))
            assert "上一張" in line.sent[0][0]["text"]
        finally:gate.set()
        until(lambda:pred.calls==1)

def test_timeout_does_not_run_gpu_threads_concurrently(tmp_path):
    class Slow(FakePredictor):
        def predict(self,raw):
            time.sleep(.1)
            return super().predict(raw)
    s=settings(tmp_path);s.timeout=.02
    line=FakeLine();app=create_app(s,predictor=Slow(),client=line)
    with TestClient(app) as c:
        post(c,[event()]);until(lambda:bool(line.sent))
        assert "逾時" in line.sent[0][0]["text"]
        time.sleep(.15)
        assert len(line.sent)==1

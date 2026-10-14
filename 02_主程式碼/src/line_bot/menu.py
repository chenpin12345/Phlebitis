from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.common import ROOT, write_json
from src.paths import LINE_MENU_DIR


LABELS=[("開始分析","傳送一張清楚照片"),("拍照說明","取景・對焦・光線"),("結果說明","了解方框與模型分數"),("專題介紹","研究用途與資料處理")]


def definition():
    """Rich-menu payload (the same structure published to LINE and rendered by the simulator)."""
    areas=[]
    for i,(label,desc) in enumerate(LABELS):
        x=(i%2)*1250;y=(i//2)*843
        areas.append({"bounds":{"x":x,"y":y,"width":1250,"height":843},"action":{"type":"message","text":label},"description":desc})
    payload={"size":{"width":2500,"height":1686},"selected":True,"name":"Phlebitis research demo","chatBarText":"分析與說明","areas":[{k:v for k,v in a.items() if k!='description'} for a in areas]}
    return payload,areas


def prepare():
    out=LINE_MENU_DIR
    out.mkdir(parents=True,exist_ok=True)
    fontpath=next((p for p in [Path("C:/Windows/Fonts/msjh.ttc"),Path("C:/Windows/Fonts/msyh.ttc")] if p.exists()),None)
    if not fontpath:raise ValueError("Install Microsoft JhengHei font to generate the Chinese menu")
    big=ImageFont.truetype(str(fontpath),78)
    small=ImageFont.truetype(str(fontpath),40)
    img=Image.new("RGB",(2500,1686),"#F3F6F8")
    d=ImageDraw.Draw(img)
    payload,areas=definition()
    for i,area in enumerate(areas):
        b=area["bounds"];x,y=b["x"],b["y"]
        fill="#174E5A" if i==0 else "#FFFFFF"
        ink="#FFFFFF" if i==0 else "#173B45"
        d.rounded_rectangle((x+28,y+28,x+1222,y+815),radius=40,fill=fill,outline="#D7E2E6",width=3)
        d.text((x+625,y+340),area["action"]["text"],font=big,fill=ink,anchor="mm")
        d.text((x+625,y+470),area["description"],font=small,fill=ink,anchor="mm")
    img.save(out/"rich-menu.png")
    write_json(out/"rich-menu.json",payload)
    return {"image":str((out/"rich-menu.png").relative_to(ROOT)),"configuration":str((out/"rich-menu.json").relative_to(ROOT)),"published":False}


def publish():
    import httpx
    from src.line_bot.service import Settings
    from src.common import read_json
    s=Settings.load();prepare()
    with httpx.Client(headers={"Authorization":f"Bearer {s.token}"},timeout=30) as client:
        config=read_json(LINE_MENU_DIR/"rich-menu.json")
        validation=client.post("https://api.line.me/v2/bot/richmenu/validate",json=config);validation.raise_for_status()
        response=client.post("https://api.line.me/v2/bot/richmenu",json=config);response.raise_for_status()
        rid=response.json()["richMenuId"]
        response=client.post(f"https://api-data.line.me/v2/bot/richmenu/{rid}/content",content=(LINE_MENU_DIR/"rich-menu.png").read_bytes(),headers={"Content-Type":"image/png"});response.raise_for_status()
        response=client.post(f"https://api.line.me/v2/bot/user/all/richmenu/{rid}");response.raise_for_status()
    return {"published":True,"rich_menu_id":rid}

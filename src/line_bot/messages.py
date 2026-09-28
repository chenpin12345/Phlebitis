GUIDE = "請傳送一張對焦清楚、光線均勻、完整包含觀察部位的照片，避免反光與無關的姓名或證件資訊。支援 JPEG、PNG、WEBP，檔案上限 10 MB。"
EXPLANATION = "方框代表模型偵測到的疑似區域。信心分數不是嚴重程度或罹病機率；未偵測到也不代表排除疾病。本專題第一版沒有嚴重度分級功能。"
INTRO = "這是靜脈炎影像研究展示：LINE 傳圖後由本地模型分析。照片會經過 LINE 平台；本機原圖不永久保存，結果圖暫存一小時。不會自動將照片用於訓練。"


def text_message(text):
    return {"type":"text","text":text,"quickReply":{"items":[{"type":"action","action":{"type":"message","label":label,"text":label}} for label in ["開始分析","拍照說明","結果說明","專題介紹"]]}}


def command(text):
    return {"開始分析":GUIDE,"拍照說明":GUIDE,"結果說明":EXPLANATION,"專題介紹":INTRO}.get(text.strip(),"請傳送一張照片，或選擇「拍照說明」。一次處理一張照片。")


def results(record,url):
    detected=record["status"]=="suspected"
    classification=record.get('task_type')=='classification'
    statuses={'suspected':'整圖分類：疑似陽性' if classification else '偵測到疑似區域','not_detected':'整圖分類：未達陽性門檻' if classification else '未偵測到疑似區域','quality_rejected':'照片品質不足，請重新拍攝','needs_review':'結果不確定，需要人工確認'}
    if record['status'] not in statuses:
        raise ValueError('Unknown analysis status; never map it to a normal result')
    status=statuses[record['status']]
    lines=[{"type":"text","text":"影像分析完成","weight":"bold","size":"lg"},{"type":"text","text":status,"wrap":True}]
    if not classification:
        lines.append({"type":"text","text":f"疑似區域：{len(record.get('boxes') or [])} 處","wrap":True})
    if record.get("demo_only"):
        lines.append({"type":"text","text":"研究展示模型，尚未完成正式泛化評估。","wrap":True,"size":"sm","color":"#805400"})
    lines.append({"type":"text","text":"信心分數不是嚴重度；未偵測到不代表排除疾病。","wrap":True,"size":"sm"})
    details=f"模型：{record['model_version']}\n分析耗時：{record['elapsed_ms']:.0f} ms"
    if record.get("boxes"):
        details+="\n模型信心分數："+", ".join(f"{b['confidence']:.2f}" for b in record["boxes"])
    elif classification:
        details+=f"\n陽性類別分數：{record['prediction_score']:.3f}（未校準，非疾病機率）"
    return [{"type":"flex","altText":f"分析完成：{status}","contents":{"type":"bubble","body":{"type":"box","layout":"vertical","spacing":"md","contents":lines}}},{"type":"image","originalContentUrl":url,"previewImageUrl":url},{"type":"text","text":details}]

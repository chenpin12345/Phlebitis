"""LINE message definitions shared by the real webhook and the offline simulator.

Every message the project sends is built here, so the simulator renders exactly the
structures that would be sent to LINE (text + quickReply, image, Flex bubble/box/text).
"""
from urllib.parse import parse_qs, urlencode

GUIDE = "請傳送一張對焦清楚、光線均勻、完整包含觀察部位的照片，避免反光與無關的姓名或證件資訊。支援 JPEG、PNG、WEBP，檔案上限 10 MB。"
EXPLANATION = "方框代表模型偵測到的疑似區域。信心分數不是嚴重程度或罹病機率；未偵測到也不代表排除疾病。本專題第一版沒有嚴重度分級功能。"
INTRO = ("這是靜脈炎影像研究展示：LINE 傳圖後由本地模型分析。照片會經過 LINE 平台；分析用的原圖與結果圖只暫存一小時，"
         "未同意研究使用的照片會在到期後刪除。只有在您明確同意後，照片才會成為研究資料，且仍需人工確認才可能用於訓練；您可隨時傳送「撤回研究同意」。")
WITHDRAW = "撤回研究同意"
CONSENT_INFO = "研究同意說明"
QUICK_LABELS = ["開始分析", "拍照說明", "結果說明", "專題介紹"]
COMMANDS = {"開始分析": GUIDE, "拍照說明": GUIDE, "結果說明": EXPLANATION, "專題介紹": INTRO}
FALLBACK = "請傳送一張照片，或選擇「拍照說明」。一次處理一張照片。"


def quick_reply(items=None):
    return {"items": [{"type": "action", "action": {"type": "message", "label": label, "text": label}} for label in (items or QUICK_LABELS)]}


def text_message(text, quick=True):
    message = {"type": "text", "text": text}
    if quick:
        message["quickReply"] = quick_reply()
    return message


def command(text, consent=None):
    text = text.strip()
    if text == CONSENT_INFO:
        return consent_text(consent)
    return COMMANDS.get(text, FALLBACK)


def consent_text(consent):
    if not consent:
        return "目前沒有開放研究使用同意。照片分析功能不受影響。"
    return f"{consent['title']}\n\n{consent['text']}\n\n保存：{consent.get('retention') or '依研究規範'}\n版本：{consent['version']}"


STATUS_TEXT = {
    'detection': {'suspected': '偵測到疑似區域', 'not_detected': '未偵測到疑似區域'},
    'classification': {'suspected': '整圖分類：疑似陽性', 'not_detected': '整圖分類：未達陽性門檻'},
}
COMMON_STATUS = {'quality_rejected': '照片品質不足，請重新拍攝', 'needs_review': '結果不確定，需要人工確認'}


def results(record, url, *, patient_view=True):
    """Result messages. With patient_view (always used on LINE), stage models only expose
    the binary view (suspected / below threshold); stage and per-class scores stay internal."""
    classification = record.get('task_type') == 'classification'
    statuses = {**STATUS_TEXT['classification' if classification else 'detection'], **COMMON_STATUS}
    if record['status'] not in statuses:
        raise ValueError('Unknown analysis status; never map it to a normal result')
    status = statuses[record['status']]
    if record['status'] == 'suspected':
        status += '，建議聯絡醫護人員確認'
    lines = [{"type": "text", "text": "影像分析完成", "weight": "bold", "size": "lg"}, {"type": "text", "text": status, "wrap": True}]
    if not classification:
        lines.append({"type": "text", "text": f"疑似區域：{len(record.get('boxes') or [])} 處", "wrap": True})
    if not patient_view and record.get('predicted_class') and record.get('label_scheme') == 'stage_v1':
        lines.append({"type": "text", "text": f"工程檢視：模型類別 {record['predicted_class']}（未校準，非臨床分期）", "wrap": True, "size": "sm", "color": "#805400"})
    if record.get("demo_only"):
        lines.append({"type": "text", "text": "研究展示模型，尚未完成正式泛化評估。", "wrap": True, "size": "sm", "color": "#805400"})
    lines.append({"type": "text", "text": "結果僅供參考，不是診斷；信心分數不是嚴重度；未偵測到不代表排除疾病。", "wrap": True, "size": "sm"})
    details = f"模型：{record['model_version']}\n分析耗時：{record['elapsed_ms']:.0f} ms"
    if record.get("boxes"):
        details += "\n模型信心分數：" + ", ".join(f"{b['confidence']:.2f}" for b in record["boxes"])
    elif classification and record.get('prediction_score') is not None:
        details += f"\n陽性類別分數：{record['prediction_score']:.3f}（未校準，非疾病機率）"
    return [{"type": "flex", "altText": f"分析完成：{status}", "contents": {"type": "bubble", "body": {"type": "box", "layout": "vertical", "spacing": "md", "contents": lines}}},
            {"type": "image", "originalContentUrl": url, "previewImageUrl": url}, {"type": "text", "text": details}]


def consent_message(consent, ref):
    """Separate research-use question; declining never affects analysis."""
    def data(decision):
        return urlencode({'action': 'consent', 'decision': decision, 'v': consent['version'], 'ref': ref})
    return {"type": "text", "text": "是否同意將這張照片用於研究？（選擇不同意不影響分析）\n" + consent['text'] + "\n\n輸入「研究同意說明」可查看完整說明。",
            "quickReply": {"items": [
                {"type": "action", "action": {"type": "postback", "label": "同意研究使用", "data": data('accept'), "displayText": "同意研究使用"}},
                {"type": "action", "action": {"type": "postback", "label": "不同意", "data": data('decline'), "displayText": "不同意研究使用"}},
                {"type": "action", "action": {"type": "message", "label": CONSENT_INFO, "text": CONSENT_INFO}}]}}


def parse_postback(value):
    if not isinstance(value, str) or len(value) > 300:
        return {}
    return {k: v[0] for k, v in parse_qs(value, strict_parsing=False).items() if v}


CONSENT_REPLIES = {
    'recorded_accept': '已記錄您的研究使用同意。照片仍需研究人員人工確認後才可能使用；您可隨時傳送「撤回研究同意」。',
    'recorded_decline': '已記錄：不同意研究使用。此照片只用於本次分析，將於到期後刪除。',
    'already': '這張照片已記錄同意，不會重複建立。',
    'expired': '此照片已過期或已刪除，無法再同意研究使用；如願意提供，請重新傳送照片後再選擇同意。',
    'disabled': '目前沒有開放研究使用同意。',
    'version_mismatch': '同意說明已更新，請重新傳送照片後依最新說明選擇。',
    'not_owner': '只能由傳送照片的使用者決定是否同意。',
    'duplicate': None,
}


def supported_types():
    """Message structures this project actually produces (used by the simulator)."""
    return {'messages': ['text', 'image', 'flex'], 'flex': {'bubble': ['body'], 'box': ['layout', 'spacing', 'contents'], 'text': ['text', 'weight', 'size', 'color', 'wrap']},
            'quick_reply_actions': ['message', 'postback'], 'rich_menu_actions': ['message']}

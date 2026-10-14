"""Transport-independent LINE conversation rules.

The real webhook (signed LINE events, LINE Messaging API transport) and the offline
simulator (synthetic events, local transport that never contacts LINE) both call this
service, so deduplication, busy/queue rules, unsend, consent and withdrawal behave the
same way.  Inference and delivery remain in the transport-specific callers.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.line_bot import messages as M

TOKEN = re.compile(r'[A-Za-z0-9_-]{43}')


@dataclass
class Incoming:
    kind: str
    event_id: str | None
    message_id: str
    user: str
    reply_token: str | None = None
    text: str | None = None
    data: str | None = None
    redelivery: bool = False


@dataclass
class Reply:
    messages: list
    user: str
    reply_token: str | None
    event_id: str | None = None


@dataclass
class Enqueue:
    event_id: str
    message_id: str
    user: str
    reply_token: str | None


@dataclass
class Unsent:
    message_id: str
    tokens: list = field(default_factory=list)


def parse(event: dict) -> Incoming | None:
    """LINE webhook event -> normalized event. Events the project does not act on return None."""
    if not isinstance(event, dict):
        return None
    kind = event.get('type')
    source = event.get('source') or {}
    redelivery = bool((event.get('deliveryContext') or {}).get('isRedelivery'))
    if kind == 'unsend':
        return Incoming('unsend', event.get('webhookEventId'), str((event.get('unsend') or {}).get('messageId', '')), source.get('userId', ''))
    user = source.get('userId', '')
    if source.get('type') != 'user' or not user:
        return None
    eid, reply = event.get('webhookEventId'), event.get('replyToken')
    if not eid or not reply:
        return None
    message = event.get('message') or {}
    if kind == 'follow':
        return Incoming('follow', eid, '', user, reply, text='專題介紹', redelivery=redelivery)
    if kind == 'postback':
        return Incoming('postback', eid, 'postback:' + eid, user, reply, data=(event.get('postback') or {}).get('data'), redelivery=redelivery)
    if kind == 'message':
        mtype, mid = message.get('type'), str(message.get('id', ''))
        if mtype == 'text':
            return Incoming('text', eid, mid, user, reply, text=str(message.get('text', '')), redelivery=redelivery)
        if mtype == 'image':
            return Incoming('image', eid, mid, user, reply, redelivery=redelivery)
        return Incoming('other', eid, mid, user, reply, redelivery=redelivery)
    return None


class Research:
    """Port to the research-consent store (workbench database)."""
    def __init__(self, home=None, root=None):
        self.home, self.root = home, root

    def _kw(self):
        from src.workbench import intake
        return {'home': self.home or intake.HOME, 'root': self.root or intake.ROOT}

    def offer(self, source):
        from src.workbench import intake
        return intake.offer(source, self._kw()['root'])

    def decide(self, **kwargs):
        from src.workbench import intake
        return intake.decide(**kwargs, **self._kw())

    def withdraw_user(self, **kwargs):
        from src.workbench import intake
        return intake.withdraw_user(**kwargs, home=self._kw()['home'])


class Conversation:
    def __init__(self, store, *, source, user_key, pending_dir: Path, research: Research | None = None,
                 message_id_pattern=r'[0-9]+', clock=time.time, session=None):
        self.store, self.source, self.user_key = store, source, user_key
        self.pending_dir, self.research = Path(pending_dir), research or Research()
        self.pattern, self.clock, self.session = re.compile(message_id_pattern), clock, session

    def consent_offer(self):
        try:
            return self.research.offer(self.source)
        except Exception:
            return None  # Consent is optional; analysis keeps working.

    def handle(self, incoming: Incoming, *, accepting=True) -> list:
        if incoming.kind == 'unsend':
            tokens = self.store.unsend(incoming.message_id)
            for token in tokens:
                (self.pending_dir / (token + '.jpg')).unlink(missing_ok=True)
            return [Unsent(incoming.message_id, tokens)]
        key = self.user_key(incoming.user)
        reply = lambda *msgs: [Reply(list(msgs), incoming.user, incoming.reply_token, incoming.event_id)]
        if incoming.kind in ('follow', 'text'):
            if self.store.reserve(incoming.event_id, incoming.message_id, key, 'completed') != 'accepted':
                return []
            text = (incoming.text or '').strip()
            if text == M.WITHDRAW:
                count = self.research.withdraw_user(source=self.source, user_key=key, event_id=incoming.event_id)['withdrawn']
                message = f'已撤回 {count} 張照片的研究使用同意，並立即停止研究使用；研究副本會由系統刪除。已訓練模型無法移除既有影響，研究人員會重新評估。' if count else '目前沒有生效中的研究使用同意。照片分析功能不受影響。'
                return reply(M.text_message(message))
            return reply(M.text_message(M.command(text, self.consent_offer())))
        if incoming.kind == 'postback':
            if self.store.reserve(incoming.event_id, incoming.message_id, key, 'completed') != 'accepted':
                return []
            data = M.parse_postback(incoming.data)
            if data.get('action') != 'consent' or data.get('decision') not in ('accept', 'decline'):
                return reply(M.text_message('不支援的操作。'))
            status = self._consent(key, incoming, data)
            text = M.CONSENT_REPLIES['recorded_' + data['decision'] if status == 'recorded' else status]
            return reply(M.text_message(text)) if text else []
        if incoming.kind == 'image':
            if not self.pattern.fullmatch(incoming.message_id):
                return []
            if not accepting:
                if self.store.reserve(incoming.event_id, incoming.message_id, key, 'rejected') == 'accepted':
                    return reply(M.text_message('本地模型目前進行維護，暫停照片分析。請稍後再試。'))
                return []
            state = self.store.reserve(incoming.event_id, incoming.message_id, key)
            if state in ('duplicate', 'cancelled'):
                return []
            if state == 'busy':
                # Record rejected events too, so redelivery cannot produce another message.
                self.store.reserve(incoming.event_id, incoming.message_id, key, 'rejected')
                return reply(M.text_message('上一張照片仍在處理，請等待結果後再傳送。'))
            return [Enqueue(incoming.event_id, incoming.message_id, incoming.user, incoming.reply_token)]
        if self.store.reserve(incoming.event_id, incoming.message_id, key, 'completed') == 'accepted':
            return reply(M.text_message('目前只接受照片，請傳送一張 JPEG、PNG 或 WEBP 圖片。'))
        return []

    def _consent(self, key, incoming, data):
        ref = data.get('ref', '')
        job = self.store.result(ref) if TOKEN.fullmatch(ref) else None
        if not job or job['status'] != 'completed' or not job['expires'] or job['expires'] <= self.clock():
            return 'expired'
        if job['user_key'] != key:
            return 'not_owner'
        pending = self.pending_dir / (ref + '.jpg')
        return self.research.decide(source=self.source, simulated=self.source != 'line', user_key=key, session=self.session,
                                    event_id=incoming.event_id, message_id=job['message_id'], result_token=ref, version=data.get('v'),
                                    decision=data['decision'], pending=pending if pending.is_file() else None,
                                    prediction=job.get('record'), clock=self.clock)['status']

    def queue_full(self, event_id):
        self.store.update(event_id, 'rejected')
        return M.text_message('目前分析工作已滿，請稍後重新傳送。')

    def finish(self, *, event_id, token, record, raw, ttl, service_config):
        """Mark a completed analysis and keep a clean original only if consent can be asked."""
        offer = self.consent_offer()
        if offer and record.get('status') in ('suspected', 'not_detected', 'needs_review'):
            from src.workbench.intake import save_pending
            save_pending(raw, self.pending_dir / (token + '.jpg'), service_config)
        else:
            offer = None
        expires = self.clock() + ttl
        summary = {k: record.get(k) for k in ('status', 'task', 'task_type', 'label_scheme', 'model_version', 'prediction_score', 'predicted_class', 'class_scores', 'binary_prediction', 'demo_only')}
        summary['note'] = '模型預測僅供參考，不是人工標籤'
        self.store.update(event_id, 'completed', token=token, expires=expires)
        self.store.save_result(token, summary, expires)
        return offer

    def result_messages(self, record, url, token, offer):
        messages = M.results(record, url, patient_view=True)
        if offer:
            messages.append(M.consent_message(offer, token))
        return messages

    def cleanup_pending(self):
        """Delete clean originals whose result lifetime ended without consent."""
        for path in self.pending_dir.glob('*.jpg'):
            expires = self.store.expiry(path.stem)
            if not expires or expires <= self.clock():
                path.unlink(missing_ok=True)

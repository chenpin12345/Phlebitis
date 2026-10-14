"""Management-only routes for LINE research intake and the offline LINE simulator.
Mounted on the local workbench (127.0.0.1, CSRF, origin checks); never on the public LINE app."""
from typing import Literal
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from src.workbench import intake, simulation
from src.workbench.storage import operator


class IntakeReview(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int
    state: Literal['reviewed', 'needs_changes', 'rejected']
    binary_label: Literal['positive', 'negative', 'unknown']
    stage_label: Literal['normal', 'stage1', 'stage2', 'positive_unstaged', 'unknown'] = 'unknown'
    quality: Literal['', 'acceptable', 'limited', 'unusable'] = ''
    subject_alias: str = Field('', max_length=40)
    subject_confirmed: bool = False
    note: str = Field('', max_length=1000)


class Promote(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int


class Withdraw(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reason: str = Field(min_length=1, max_length=500)


def mount(app):
    router = APIRouter(prefix='/api/v1')

    @router.get('/intake')
    def intake_query(source: str = '', state: str = '', usage: str = '', label: str = '', start: str = '', end: str = '', page: int = 1, size: int = 30):
        return intake.query(source=source, state=state, usage=usage, label=label, start=start, end=end, page=page, size=size)

    @router.get('/intake/consent-config')
    def consent_config():
        cfg = intake.consent_config()
        return {'line_enabled': cfg['line_enabled'], 'simulator_enabled': cfg['simulator_enabled'], 'current_version': cfg['current_version'],
                'versions': cfg['versions'], 'line_offer': intake.offer('line'), 'simulator_offer': intake.offer('simulator')}

    @router.get('/intake/{ident}/image')
    def intake_image(ident: str):
        return FileResponse(intake.image_path(ident), media_type='image/jpeg', headers={'Cache-Control': 'no-store'})

    @router.put('/intake/{ident}')
    def intake_review(ident: str, body: IntakeReview):
        return intake.review(ident, actor=operator.get(), **body.model_dump())

    @router.post('/intake/{ident}/promote')
    def intake_promote(ident: str, body: Promote):
        return intake.promote(ident, revision=body.revision, actor=operator.get())

    @router.post('/intake/{ident}/withdraw')
    def intake_withdraw(ident: str, body: Withdraw):
        return intake.withdraw_intake(ident, reason=body.reason, actor=operator.get())

    @router.post('/intake/cleanup/run')
    def intake_cleanup():
        return {'results': intake.run_cleanup()}

    @router.get('/simulation/rich-menu')
    def rich_menu():
        from src.line_bot.menu import definition
        from src.line_bot.messages import QUICK_LABELS, supported_types, quick_reply
        payload, areas = definition()
        return {'menu': payload, 'areas': areas, 'quick_reply': quick_reply(), 'quick_labels': QUICK_LABELS, 'supported': supported_types(),
                'consent_offer': intake.offer('simulator'), 'scenarios': sorted(simulation.SCENARIOS - {''}),
                'reference': {'checked_on': '2026-10-13', 'sources': ['LINE Developers Messaging API reference（訊息類型、quick reply、postback、rich menu 尺寸與區域）', 'Flex Message 元件規格（bubble/box/text 屬性）'],
                              'limits': '外觀為近似樣式，未取得逐版本官方畫面，不宣稱逐像素一致；色彩與尺寸集中於 CSS 變數可調整。'}}

    @router.get('/simulation/{session}/messages')
    def transcript(session: str, before: int | None = None, limit: int = 30):
        return simulation.transcript(session, before, limit)

    app.include_router(router)

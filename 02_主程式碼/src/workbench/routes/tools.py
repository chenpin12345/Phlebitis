"""Workbench-wide tools: next steps, notifications, search, disk usage, settings, daily and full backups."""

from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from fastapi.responses import PlainTextResponse
from src.data import photo_trash, prospective
from src.workbench import (
    cards,
    backup,
    disk,
    flags,
    full_backup,
    next_steps,
    notifications,
    search,
    settings,
    source_audit,
    spot_check,
    source_watch,
)


class ReadRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ids: list[int] | None = Field(None, max_length=500)


class PairDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    a: str = Field(min_length=1, max_length=128)
    b: str = Field(min_length=1, max_length=128)
    decision: str = Field(pattern='^(not_duplicate|duplicate)$')
    keep: str | None = Field(None, max_length=128)
    reviewer: str = Field(min_length=1, max_length=100)


class Reviewer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reviewer: str = Field(min_length=1, max_length=100)


class SpotAnswer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    correct: bool
    reviewer: str = Field(min_length=1, max_length=100)
    revision: str | None = None


class ProspectiveRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=60)
    codes: list[str] = Field(min_length=1, max_length=1000)
    role: str
    reviewer: str = Field(min_length=1, max_length=100)


class PhotoIds(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ids: list[str] = Field(min_length=1, max_length=1000)
    reviewer: str = ''


class RestoreRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    include_database: bool = False


class FullRestoreRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    output: str = Field(min_length=3, max_length=400)


def mount(app, root: Path):
    router = APIRouter(prefix='/api/v1')

    @router.get('/next-steps')
    def steps():
        return {'items': next_steps.collect(root)}

    @router.get('/notifications')
    def notices(limit: int = 30):
        return notifications.listing(limit)

    @router.post('/notifications/read')
    def read(body: ReadRequest):
        return notifications.mark_read(body.ids)

    @router.get('/search')
    def find(q: str = ''):
        return search.search(root, q)

    @router.get('/disk-usage')
    def usage(refresh: bool = False):
        return disk.usage(root, refresh)

    @router.get('/settings/workbench')
    def get_settings():
        return settings.load().model_dump()

    @router.put('/settings/workbench')
    def put_settings(body: dict):
        return settings.save(body).model_dump()

    @router.get('/backups')
    def backups():
        return backup.listing(root)

    @router.post('/backups')
    def create_backup():
        return backup.create('manual', root)

    @router.post('/backups/{name}/restore')
    def restore_backup(name: str, body: RestoreRequest):
        result = backup.restore(name, include_database=body.include_database, root=root)
        notifications.add(
            'backup',
            '已從備份還原',
            f"還原 {result['restored']} 個檔案；還原前狀態另存為 {result['safety_backup']}",
            '#settings?section=backup',
            'success',
        )
        return result

    @router.get('/full-backups')
    def full_backups():
        return full_backup.overview(root)

    @router.post('/full-backups')
    def start_full_backup():
        return full_backup.start('backup', root)

    @router.post('/full-backups/verify')
    def verify_full_backup():
        return full_backup.start('verify', root)

    @router.post('/full-backups/{run}/restore-to')
    def restore_full_backup(run: str, body: FullRestoreRequest):
        return full_backup.start('restore', root, run=run, output=body.output)

    @router.get('/source-watch/new')
    def source_new(refresh: bool = False):
        return source_watch.check(root) if refresh else source_watch.cached(root)

    @router.get('/flags/summary')
    def flag_summary():
        return flags.summary(root)

    @router.get('/data/{ident}/flags')
    def image_flags(ident: str):
        return flags.for_image(root, ident)

    @router.post('/duplicates/decision')
    def duplicate_decision(body: PairDecision):
        return flags.decide_pair(root, body.a, body.b, body.decision, keep=body.keep, reviewer=body.reviewer)

    @router.post('/data/{ident}/quality-ack')
    def quality_ack(ident: str, body: Reviewer):
        return flags.acknowledge_quality(root, ident, body.reviewer)

    @router.get('/data-trust')
    def trust_view():
        return source_audit.view(root)

    @router.post('/data-trust/source-check')
    def trust_check():
        return source_audit.run(root)

    @router.get('/prospective')
    def prospective_view():
        return {'items': prospective.listing(root)}

    @router.post('/prospective')
    def prospective_register(body: ProspectiveRequest):
        return prospective.register(body.name, body.codes, body.role, body.reviewer, root)

    @router.post('/prospective/{ident}/unlock')
    def prospective_unlock(ident: str, body: Reviewer):
        return prospective.unlock(ident, body.reviewer, root)

    @router.get('/data-card.md', response_class=PlainTextResponse)
    def data_card():
        return PlainTextResponse(cards.data_markdown(root), media_type='text/markdown; charset=utf-8')

    @router.get('/artifacts/{ident}/card.md', response_class=PlainTextResponse)
    def model_card(ident: str):
        return PlainTextResponse(cards.model_markdown(root, ident), media_type='text/markdown; charset=utf-8')

    @router.get('/photo-trash')
    def photo_trash_view():
        return photo_trash.listing(root)

    @router.post('/photo-trash/preview')
    def photo_trash_preview(body: PhotoIds):
        return photo_trash.preview(body.ids, root)

    @router.post('/photo-trash/move')
    def photo_trash_move(body: PhotoIds):
        return photo_trash.move(body.ids, body.reviewer, root)

    @router.post('/photo-trash/restore')
    def photo_trash_restore(body: PhotoIds):
        return photo_trash.restore(body.ids, body.reviewer, root)

    @router.post('/photo-trash/purge')
    def photo_trash_purge(body: PhotoIds):
        return photo_trash.purge(body.ids, body.reviewer, root)

    @router.get('/spot-check')
    def spot_view():
        return {**spot_check.view(root), 'enabled': settings.load().spot_check.enabled}

    @router.post('/spot-check/start')
    def spot_start():
        return spot_check.start(root, settings.load().spot_check.ratio)

    @router.post('/spot-check/{ident}')
    def spot_answer(ident: str, body: SpotAnswer):
        return spot_check.answer(root, ident, correct=body.correct, reviewer=body.reviewer, revision=body.revision)

    app.include_router(router)

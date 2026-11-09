"""Model and data cards to hand to other people (#23), laid out after TRIPOD+AI.

Exports never hold filenames or patient codes: everything is counts, and the text is scanned
before it leaves the workbench.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from src.common import read_manifest

FILENAME = re.compile(r'\d{8,11}[ _]\S+_[A-Z]{2}_\d|_(?:LH|RH|LL|RL)_\d|candidate:', re.I)
LABELS = '照片的分類標籤由兩位醫師核准；系統內沒有第二次確認。'
NAMES = {'binary_classification': '二分類（正常／陽性）', 'stage_classification': '分期（正常／第一期／第二期）'}


def _safe(text: str) -> str:
    if FILENAME.search(text):
        raise ValueError('匯出內容含有檔名樣式，已停止匯出')
    return text


def _pct(value) -> str:
    return '—' if value is None else f'{value * 100:.1f}%'


def _metric_rows(summary: dict | None) -> list[str]:
    if not summary:
        return ['尚無評估結果。']
    rows = ['| 指標 | 數值 | 95% 區間 |', '|---|---|---|']
    for m in summary['metrics']:
        ci = m.get('ci')
        interval = f'{_pct(ci[0])}–{_pct(ci[1])}' if ci else '—'
        rows.append(f"| {m['name']} | {_pct(m.get('value'))} | {interval} |")
    return rows


def model_markdown(root: Path, ident: str) -> str:
    from src.workbench.evaluation_views import model_card

    card = model_card(root, ident)
    data = card.get('data') or {}
    summary = (card.get('evaluation') or {}).get('summary')
    lines = [
        f"# 模型卡：{card['model_name']}",
        '',
        '依 TRIPOD+AI 的項目整理。這是研究原型，不是醫療器材。',
        '',
        '## 目的',
        '',
        f"- 任務：{NAMES.get(card.get('task'), card.get('task'))}",
        f"- 用途：{card.get('intended_use') or '—'}",
        '- 不用於：診斷、治療決策或對病人的個別建議。',
        '',
        '## 資料',
        '',
        f"- 快照：{data.get('snapshot', '—')}",
        f"- 訓練／驗證張數：{(data.get('counts') or {}).get('train', '—')}／{(data.get('counts') or {}).get('val', '—')}",
        f'- {LABELS}',
        '- 分組：同一位病人的照片不跨訓練與驗證。',
        '',
        '## 模型開發',
        '',
        f"- 模型：{card['model']}",
        f"- 訓練設定：{card.get('training') or '—'}",
        '- 輪數固定，驗證資料不用來挑模型；門檻只用訓練折決定。',
        '',
        '## 效能',
        '',
        *_metric_rows(summary),
        '',
        '## 限制',
        '',
        *[f'- {text}' for text in card['limitations']],
        *[f'- {text}' for text in (summary or {}).get('cautions', [])],
        '',
    ]
    return _safe('\n'.join(lines))


def data_markdown(root: Path) -> str:
    from src.workbench import source_audit

    rows = read_manifest(root)
    state = Counter(r['status'] for r in rows)
    stock = source_audit.inventory(root)
    view = source_audit.view(root)
    audit = view['audit'] or {}
    lines = [
        '# 資料卡',
        '',
        '依 TRIPOD+AI 的項目整理。只有統計數字，沒有檔名或病歷號。',
        '',
        '## 來源',
        '',
        '- 岡山高醫的靜脈注射部位照片。',
        '- 只保留檔名符合「日期_病歷號_部位_幾期_第幾張」的照片。',
        f'- {LABELS}',
        '',
        '## 數量',
        '',
        f"- 全部 {len(rows)} 張：可用 {state['approved']}、排除 {state['excluded']}、待處理 {state['pending_review']}",
        f"- 病人 {stock['patients']} 位；正常照片 {stock['normal_photos']} 張，來自 {stock['normal_patients']} 位",
        '',
        '| 病人 | 照片 | 正常 | 第一期 | 第二期 |',
        '|---|---|---|---|---|',
        *[f"| {p['label']} | {p['photos']} | {p['normal']} | {p['stage1']} | {p['stage2']} |" for p in stock['rows']],
        '',
        '## 已知問題',
        '',
        *[f'- {text}' for text in stock['warnings'] + audit.get('findings', [])],
        '- 只來自單一醫院，換拍攝條件時表現可能不同。',
        '',
    ]
    return _safe('\n'.join(lines))

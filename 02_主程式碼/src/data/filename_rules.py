"""Versioned filename label rules. Applied only to aliases of an explicitly configured
source whose rule is named here; never to arbitrary future uploads.

yida_filename_v1 (confirmed by the user for the 合作醫院 folder):
  <date>[ _]<bed/record code>_<side>_<stage>[_<sequence>].<ext>
  side LH / RH = left / right hand; recorded as source information only.
  stage 0 = normal, 1 = stage1 (第一期), 2 = stage2 (第二期).
  The trailing sequence number is a photo counter and never a stage.
  The bed/record code is NOT a verified patient identity and is never used for grouping.
Anything not matching (other site codes, other stage digits, extra tokens) is 'unknown'.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath

RULES = {'yida_filename_v1', 'yida_filename_v2'}
# v2 (project owner, 2026-10-14): LL is also a site code (stage read from the digit after it).
SIDES_BY_RULE = {'yida_filename_v1': ('LH', 'RH'), 'yida_filename_v2': ('LH', 'RH', 'LL')}
_PATTERN = re.compile(r'^(?P<date>\d{8,10})[ _](?P<code>.+?)_(?P<side>[A-Z]{2})_(?P<stage>\d+)(?:_(?P<seq>\d+))?$')
_STAGES = {'0': 'normal', '1': 'stage1', '2': 'stage2'}
_SIDES = {'LH': '左手', 'RH': '右手'}


def record_code(relative_path: str) -> str | None:
    """Bed/record code from a 合作醫院-style filename, used only as a conservative candidate
    group (never as a verified patient identity). Hyphens are dropped so that
    'BED-03' and 'BED03' fall into the same group (merging is the safe direction)."""
    match = _PATTERN.match(PurePosixPath(relative_path).stem)
    return match['code'].replace('-', '').upper() if match else None


def parse(rule: str, relative_path: str) -> dict:
    if rule not in RULES:
        raise ValueError('Unknown filename rule')
    path = PurePosixPath(relative_path)
    result = {'rule': rule, 'value': 'unknown', 'side': None, 'sequence': None, 'reasons': []}
    if path.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
        result['reasons'].append('不是影像檔')
        return result
    match = _PATTERN.match(path.stem)
    if not match:
        result['reasons'].append('檔名不符合「日期_代碼_LH/RH_分期_序號」格式')
        return result
    side, stage = match['side'], match['stage']
    result.update(side=side, sequence=int(match['seq']) if match['seq'] else None, date=match['date'])
    if side not in SIDES_BY_RULE[rule]:
        result['reasons'].append(f'部位代碼 {side} 不在已確認規則（僅 {"／".join(SIDES_BY_RULE[rule])}）')
    if stage not in _STAGES:
        result['reasons'].append(f'分期數字 {stage} 不在已確認規則（僅 0／1／2）')
    folder_says_normal = any('正常' in part for part in path.parts[:-1])
    if folder_says_normal and stage != '0':
        result['reasons'].append('資料夾標示正常，但檔名分期不是 0')
    if not result['reasons']:
        result['value'] = _STAGES[stage]
    return result

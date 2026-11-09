"""Block commits that would put patient data, model weights or secrets into git.

Run by the pre-commit hook (scripts/githooks/pre-commit).  Only the Python standard library
is used, so the check also works before the project environment is complete.

Real record codes are never stored in git: they are read at commit time from this
computer's own source records and import folder.  Tests use made-up codes starting with ZZ.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tif', '.tiff', '.heic'}
BLOCKED_SUFFIXES = {
    '.pt',
    '.pth',
    '.ckpt',
    '.onnx',
    '.safetensors',
    '.npz',
    '.npy',
    '.sqlite',
    '.sqlite3',
    '.db',
    '.bundle',
    '.docx',
}
ALLOWED_IMAGES = Path(__file__).with_name('githooks') / 'allowed-images.txt'
# <date>_<record code>_<site>_<stage>; made-up test codes start with ZZ.
NAME_SHAPE = re.compile(r'\d{8,11}[ _](?!ZZ)[0-9A-Za-z-]+_(?:LH|RH|LL|RL)_\d')
SOURCE_NAME = re.compile(r'(?:^|/)\d{8,11}[ _]([^_/]+?)_[A-Z]{2}_\d+')
# The source was renamed; these words stay only in the research reports, notes and slides.
RETIRED_NAMES = re.compile('yi' + 'da|義' + '大|E-' + 'Da', re.I)
RETIRED_NAME_KEPT_IN = ('01_文件與紀錄/研究決策/', '01_文件與紀錄/研究筆記/', '01_文件與紀錄/簡報/')
SECRETS = (
    ('LINE 金鑰', re.compile(r'LINE_CHANNEL_(?:SECRET|ACCESS_TOKEN)\s*=\s*\S{8,}')),
    ('私鑰', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('API 金鑰', re.compile(r'\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b')),
)


def allowed_images(path: Path = ALLOWED_IMAGES) -> set[str]:
    if not path.is_file():
        return set()
    lines = (line.strip() for line in path.read_text(encoding='utf-8').splitlines())
    return {line for line in lines if line and not line.startswith('#')}


def path_problems(paths: list[str], allowed: set[str]) -> list[str]:
    problems = []
    for name in paths:
        path = Path(name)
        suffix = path.suffix.lower()
        if suffix in IMAGE_SUFFIXES and name not in allowed:
            problems.append(f'{name}：照片或截圖不進 git（確定是合成畫面才加入 allowed-images.txt）')
        elif suffix in BLOCKED_SUFFIXES:
            problems.append(f'{name}：模型權重、資料庫或可能含病人影像的文件不進 git')
        elif path.name == '.env' or path.name.startswith('.env.') and path.name != '.env.example':
            problems.append(f'{name}：環境設定檔可能含金鑰')
    return problems


def code_pattern(codes: set[str]) -> re.Pattern | None:
    if not codes:
        return None
    joined = '|'.join(re.escape(code) for code in sorted(codes, key=len, reverse=True))
    return re.compile(rf'(?<![0-9A-Za-z])(?:{joined})(?![0-9A-Za-z])')


def text_problems(added: dict[str, list[str]], codes: set[str]) -> list[str]:
    """Findings never quote the matched text, so the message itself cannot leak it."""
    real = code_pattern(codes)
    problems = []
    for name, lines in added.items():
        for line in lines:
            if real and real.search(line) or NAME_SHAPE.search(line):
                problems.append(f'{name}：新增內容含病歷號或真實檔名，請改用 ZZ 開頭的合成代碼')
                break
        if not name.startswith(RETIRED_NAME_KEPT_IN) and any(RETIRED_NAMES.search(line) for line in lines):
            problems.append(f'{name}：新增內容含舊來源名稱，請改用岡山高醫或 gangshan')
        for label, pattern in SECRETS:
            if any(pattern.search(line) for line in lines):
                problems.append(f'{name}：新增內容疑似含{label}')
    return problems


def local_codes(workspace: Path) -> set[str]:
    """Record codes known to this computer, in the forms the source records use."""
    layout = json.loads((workspace / 'workspace-layout.json').read_text(encoding='utf-8'))
    names: list[str] = []
    sources = workspace / layout.get('storage', '') / 'data' / 'image_sources.json'
    if sources.is_file():
        for entry in json.loads(sources.read_text(encoding='utf-8')).get('images', {}).values():
            names += [str(a.get('relative_path') or '') for a in entry.get('aliases', [])]
    inbox = workspace / layout.get('inbox', '05_匯入區')
    for folder, _, files in os.walk(inbox):
        names += files
    codes = set()
    for name in names:
        match = SOURCE_NAME.search(name.replace('\\', '/'))
        if match:
            codes |= {match[1], match[1].replace('-', '')}
    return codes


def staged_paths() -> list[str]:
    command = ['git', '-c', 'core.quotePath=false', 'diff', '--cached', '--name-only', '--diff-filter=ACMR']
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
    return [line for line in result.stdout.splitlines() if line]


def staged_added_lines() -> dict[str, list[str]]:
    command = ['git', '-c', 'core.quotePath=false', 'diff', '--cached', '--unified=0', '--no-color']
    data = subprocess.run(command, capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    added: dict[str, list[str]] = {}
    current = None
    for line in data.splitlines():
        if line.startswith('+++ '):
            target = line[4:].strip().strip('"')
            current = None if target == '/dev/null' else target.removeprefix('b/')
        elif line.startswith('+') and current:
            added.setdefault(current, []).append(line[1:])
    return added


def main() -> int:
    top = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, encoding='utf-8', check=True
    ).stdout.strip()
    problems = path_problems(staged_paths(), allowed_images())
    problems += text_problems(staged_added_lines(), local_codes(Path(top)))
    if problems:
        print('提交已擋下，請先處理：', file=sys.stderr)
        for problem in problems:
            print('  - ' + problem, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())

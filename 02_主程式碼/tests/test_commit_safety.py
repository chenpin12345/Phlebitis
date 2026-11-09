"""The pre-commit check must stop patient data, weights and secrets, and let normal work through."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check_commit_safety.py'
spec = importlib.util.spec_from_file_location('check_commit_safety', SCRIPT)
safety = importlib.util.module_from_spec(spec)
spec.loader.exec_module(safety)

# Built from parts so this test file itself passes the check it is testing.
REAL_CODE = 'Q7' + '77'
REAL_NAME = '20260101_' + REAL_CODE + '_LH_1_1.jpg'


def test_new_image_is_blocked_unless_listed():
    assert safety.path_problems(['docs/new.png'], set())
    assert safety.path_problems(['docs/new.JPG'], set())
    assert not safety.path_problems(['docs/new.png'], {'docs/new.png'})


@pytest.mark.parametrize('name', ['best.pt', 'a/model.safetensors', 'x/feature.npy', 'w.sqlite3', 'report.docx'])
def test_weights_databases_and_word_files_are_blocked(name):
    assert safety.path_problems([name], set())


@pytest.mark.parametrize('name', ['.env', 'sub/.env', '.env.local'])
def test_env_files_are_blocked(name):
    assert safety.path_problems([name], set())


def test_normal_files_pass():
    assert not safety.path_problems(['.env.example', 'src/a.py', 'docs/a.md', 'configs/a.json'], set())


def test_real_code_is_blocked_in_any_text():
    found = safety.text_problems({'a.md': ['病人 ' + REAL_CODE + ' 的照片']}, {REAL_CODE})
    assert found and REAL_CODE not in found[0]


def test_code_needs_a_word_boundary():
    assert not safety.text_problems({'a.md': ['abc' + REAL_CODE + 'def']}, {REAL_CODE})


def test_filename_shape_is_blocked_even_for_unknown_patients():
    assert safety.text_problems({'a.py': [REAL_NAME]}, set())


def test_made_up_zz_codes_pass():
    assert not safety.text_problems({'a.py': ['20260101_ZZ0101_LH_1_1.jpg', '2026010101 ZZ01-01_RL_2.png']}, set())


@pytest.mark.parametrize(
    'line',
    [
        'LINE_CHANNEL_SECRET=' + 'abcdef123456',
        'LINE_CHANNEL_ACCESS_TOKEN = ' + 'abcdef123456',
        '-----BEGIN ' + 'PRIVATE KEY-----',
        'token: gh' + 'p_' + 'a' * 30,
    ],
)
def test_secrets_are_blocked(line):
    assert safety.text_problems({'a.txt': [line]}, set())


def test_empty_example_settings_pass():
    assert not safety.text_problems({'.env.example': ['LINE_CHANNEL_SECRET=', 'LINE_CHANNEL_ACCESS_TOKEN=']}, set())


def test_local_codes_come_from_source_records_and_inbox(tmp_path):
    (tmp_path / 'workspace-layout.json').write_text(json.dumps({'storage': 'store', 'inbox': 'in'}), encoding='utf-8')
    (tmp_path / 'store/data').mkdir(parents=True)
    aliases = [{'relative_path': '06/20260101_' + 'Q7-77_LH_1_1.jpg'}, {'relative_path': 'IMG_1.jpg'}]
    (tmp_path / 'store/data/image_sources.json').write_text(
        json.dumps({'images': {'a': {'aliases': aliases}}}), encoding='utf-8'
    )
    (tmp_path / 'in/hospital').mkdir(parents=True)
    (tmp_path / 'in/hospital' / ('2026010101 ' + 'R12_RL_0.csv')).write_text('', encoding='utf-8')
    assert safety.local_codes(tmp_path) == {'Q7-77', 'Q777', 'R12'}


def test_hook_blocks_a_real_commit_attempt(tmp_path):
    def git(*args):
        return subprocess.run(['git', '-C', str(tmp_path), *args], capture_output=True, text=True, encoding='utf-8')

    git('init', '-q')
    git('config', 'user.name', 'test')
    git('config', 'user.email', 'test@example.invalid')
    (tmp_path / 'workspace-layout.json').write_text('{}', encoding='utf-8')
    (tmp_path / 'note.md').write_text(REAL_NAME + '\n', encoding='utf-8')
    git('add', '.')
    result = subprocess.run(
        [sys.executable, '-X', 'utf8', str(SCRIPT)], cwd=tmp_path, capture_output=True, text=True, encoding='utf-8'
    )
    assert result.returncode == 1
    assert '病歷號' in result.stderr and REAL_CODE not in result.stderr


def test_retired_source_names_are_blocked_outside_the_kept_documents():
    for word in ('Yi' + 'da', '義' + '大', 'E-' + 'Da'):
        assert safety.text_problems({'a.md': [word]}, set())
        assert not safety.text_problems({'01_文件與紀錄/研究決策/a.md': [word]}, set())

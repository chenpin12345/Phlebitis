"""Every third-party import must be declared; nothing may arrive only through another package."""

import ast
import re
import sys

from src import paths

CODE = paths.CODE_ROOT
# Import name -> requirement name, where they differ. torch and torchvision are installed by
# scripts/setup.ps1 because they need the CUDA wheel index.
NAMES = {
    'PIL': 'pillow',
    'yaml': 'pyyaml',
    'sklearn': 'scikit-learn',
    'cv2': 'opencv-python-headless',
    'dotenv': 'python-dotenv',
    'multipart': 'python-multipart',
}
INSTALLED_BY_SETUP = {'torch', 'torchvision'}
# Installed together with a declared package and part of its public interface.
BUNDLED = {'starlette': 'fastapi', 'pydantic': 'fastapi', 'huggingface_hub': 'transformers'}
# scripts/benchmark_queries.py runs with the test tools.
DEVELOPMENT = {'pytest', 'workbench_fixture'}


def declared() -> set[str]:
    text = (CODE / 'requirements.txt').read_text(encoding='utf-8')
    return {
        re.split(r'[<>=!~\[ ]', line.strip())[0].lower()
        for line in text.splitlines()
        if line.strip() and line[0] != '#'
    }


def imported() -> set[str]:
    found = set()
    for folder in ('src', 'scripts'):
        for path in (CODE / folder).rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(node, ast.Import):
                    found |= {a.name.split('.')[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    found.add(node.module.split('.')[0])
    return found - set(sys.stdlib_module_names) - {'src'}


def test_every_third_party_import_is_declared():
    packages = declared()
    missing = []
    for name in sorted(imported() - INSTALLED_BY_SETUP - DEVELOPMENT):
        if BUNDLED.get(name, '') in packages:
            continue
        if NAMES.get(name, name).lower() not in packages:
            missing.append(name)
    assert missing == []

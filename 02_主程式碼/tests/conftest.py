import pytest


@pytest.fixture(autouse=True)
def doctors_approved(request, monkeypatch):
    """Only test_data_trust exercises the rules a formal snapshot must pass."""
    if request.path.name != 'test_data_trust.py':
        from src.data import dataset

        # Other tests draw plain placeholder pictures, which all look alike to the near-duplicate check.
        monkeypatch.setattr(dataset, 'leakage', lambda rows, groups, splits, root: [])

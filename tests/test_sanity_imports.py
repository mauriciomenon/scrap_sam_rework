import importlib
import pytest


@pytest.mark.parametrize(
    "mod",
    [
        "pandas",
        "selenium",
        "dash",
        "plotly",
        "requests",
        "bs4",
        "yaml",
    ],
)
def test_can_import(mod):
    importlib.import_module(mod)

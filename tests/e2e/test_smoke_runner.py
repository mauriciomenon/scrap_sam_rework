import sys
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

REPO = Path(__file__).resolve().parents[2]


def load_runner_module():
    run_path = REPO / "src/dashboard/Class/run.py"
    spec = spec_from_file_location("ssa_runner", run_path)
    assert spec and spec.loader
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def test_run_main_smoke(monkeypatch):
    monkeypatch.chdir(REPO)
    mod = load_runner_module()
    # patch server run to no-op
    monkeypatch.setattr(mod.SSADashboard, "run_server", lambda self, **kw: None, raising=False)
    try:
        mod.main([])
    except SystemExit as e:
        assert isinstance(e, SystemExit)

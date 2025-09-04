import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Ensure repo root on path
REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.dashboard.Class.src.data.data_loader import DataLoader
from src.dashboard.Class.src.data.ssa_columns import SSAColumns as C


def test_header_detection_and_canonicalization(tmp_path):
    # Create a minimal excel with a header on row 3 (0-based index 2)
    data = {
        "foo": ["x", "y"],
        "Número da SSA": ["SSA-1", "SSA-2"],
        "Emitida Em": ["01/09/2025 00:00:00", "02/09/2025 00:00:00"],
        "Setor Executor": ["SX1", "SX2"],
        "Grau de Prioridade Emissão": ["S3.7", "S2"],
    }
    # introduce two junk rows before header
    junk = pd.DataFrame([{"a": 1}, {"a": 2}])
    proper = pd.DataFrame(data)
    df = pd.concat([junk, proper], ignore_index=True)
    excel = tmp_path / "min.xlsx"
    with pd.ExcelWriter(excel) as xw:
        df.to_excel(xw, header=False, index=False)

    loader = DataLoader(str(excel))
    out = loader.load_data()

    # After canonicalization, columns should be index-ordered [0..max]
    assert out.shape[1] >= max(getattr(C, a) for a in dir(C) if a.isupper() and isinstance(getattr(C, a), int)) + 1
    # Access by positional indices should not fail
    _ = out.iloc[:, C.NUMERO_SSA]
    _ = out.iloc[:, C.EMITIDA_EM]
    _ = out.iloc[:, C.SETOR_EXECUTOR]


def test_date_conversion_dtype(tmp_path):
    df = pd.DataFrame(
        {
            "Número da SSA": ["SSA-1"],
            "Emitida Em": ["01/09/2025 00:00:00"],
            "Setor Executor": ["SX1"],
            "Grau de Prioridade Emissão": ["S3.7"],
            "Situação": ["AAD"],
        }
    )
    excel = tmp_path / "dates.xlsx"
    with pd.ExcelWriter(excel) as xw:
        df.to_excel(xw, index=False)

    loader = DataLoader(str(excel))
    out = loader.load_data()
    # EMITIDA_EM should be datetime64[ns]
    assert str(out.iloc[:, C.EMITIDA_EM].dtype) == "datetime64[ns]"


def test_dashboard_instantiation_with_synthetic_df():
    max_idx = max(getattr(C, a) for a in dir(C) if a.isupper() and isinstance(getattr(C, a), int))
    arr = np.empty((1, max_idx + 1), dtype=object)
    arr[:] = None
    arr[:, C.NUMERO_SSA] = ["SSA-1"]
    arr[:, C.SITUACAO] = ["AAD"]
    arr[:, C.SETOR_EXECUTOR] = ["SX1"]
    arr[:, C.GRAU_PRIORIDADE_EMISSAO] = ["S3.7"]
    arr[:, C.EMITIDA_EM] = [datetime(2025, 9, 1)]

    df = pd.DataFrame(arr)
    # Import here to avoid heavy dash import in earlier tests
    from src.dashboard.Class.src.dashboard.ssa_dashboard import SSADashboard

    app = SSADashboard(df)
    assert app is not None

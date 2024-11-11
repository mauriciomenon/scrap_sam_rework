# src/data/__init__.py
"""
Módulo de dados do Dashboard SSA.
"""

from .ssa_data import SSAData
from .ssa_columns import SSAColumns
from .data_loader import DataLoader

__all__ = ["SSAData", "SSAColumns", "DataLoader"]

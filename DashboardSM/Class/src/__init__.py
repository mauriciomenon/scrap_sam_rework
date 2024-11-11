# src/__init__.py
"""
Módulo principal do Dashboard SSA.
"""
from .dashboard.ssa_dashboard import SSADashboard
from .data.data_loader import DataLoader
from .data.ssa_data import SSAData
from .data.ssa_columns import SSAColumns
from .utils.log_manager import LogManager
from .utils.date_utils import diagnose_dates


__all__ = [
    "SSADashboard",
    "DataLoader",
    "SSAData",
    "SSAColumns",
    "LogManager",
    "diagnose_dates",
]

__version__ = "3.0.0"
__author__ = "Maurício Menon"

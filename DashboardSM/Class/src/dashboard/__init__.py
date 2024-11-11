# src/dashboard/__init__.py
"""
Módulo do dashboard do SSA.
"""
from .ssa_dashboard import SSADashboard
from .ssa_visualizer import SSAVisualizer
from .kpi_calculator import KPICalculator

__all__ = ["SSADashboard", "SSAVisualizer", "KPICalculator"]

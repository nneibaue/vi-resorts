"""
VI Resorts Concierge - Vacation Internationale Management System

A data-model-first system for managing VI ownership with embedded accounting.
"""

from .accountant import Accountant, CostAnalysis
from .concierge import Concierge, PointOptimizer
from .models import (
    Booking,
    Cost,
    CostCategory,
    LedgerEntry,
    OwnershipRules,
    PointBalance,
    PointType,
    Resort,
    Season,
    Trip,
    UnitType,
)

__version__ = "0.1.0"

__all__ = [
    "Accountant",
    "CostAnalysis",
    "Concierge",
    "PointOptimizer",
    "Booking",
    "Cost",
    "CostCategory",
    "LedgerEntry",
    "OwnershipRules",
    "PointBalance",
    "PointType",
    "Resort",
    "Season",
    "Trip",
    "UnitType",
]

"""Tab modules for the Embedded Tracker application.

Each tab is a separate module for maintainability.
All tabs extend BaseCrudTab from the base module.
"""

from .phases import PhasesTab
from .weeks import WeeksTab
from .days import DaysTab
from .hours import HoursTab
from .resources import ResourcesTab
from .projects import ProjectsTab
from .certifications import CertificationsTab
from .applications import ApplicationsTab
from .metrics import MetricsTab
from .hardware import HardwareTab

__all__ = [
    "PhasesTab",
    "WeeksTab",
    "DaysTab",
    "HoursTab",
    "ResourcesTab",
    "ProjectsTab",
    "CertificationsTab",
    "ApplicationsTab",
    "MetricsTab",
    "HardwareTab",
]

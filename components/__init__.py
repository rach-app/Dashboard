"""
Component modules for the Clinical Trial Dashboard application.

This package contains tab components for:
- Enrollment progress (enrollment_tab.py)
- Site activation (site_activation_tab.py)
- COSL performance (cosl_performance_tab.py)
- Screen failure analysis (screening_tab.py)
"""

from components.enrollment_tab import render_enrollment_tab
from components.site_activation_tab import render_site_activation_tab
from components.cosl_performance_tab import render_cosl_performance_tab
from components.screening_tab import render_screening_tab
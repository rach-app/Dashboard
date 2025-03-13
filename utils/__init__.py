"""
Utility modules for the Clinical Trial Dashboard application.

This package contains utility functions for:
- Data processing (data_processing.py)
- Visualization (visualization.py)
- Download functionality (download.py)
"""

from utils.data_processing import (
    process_enrollment_data,
    process_monthly_data,
    process_site_data,
    generate_cosl_data,
    calculate_screen_failure_rate,
    generate_enrollment_projections
)

from utils.visualization import (
    create_line_chart,
    create_bar_chart,
    create_pie_chart,
    create_histogram,
    create_scatter_chart,
    create_combined_chart
)

from utils.download import get_table_download_link
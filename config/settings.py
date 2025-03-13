"""
Configuration settings for the Clinical Trial Dashboard.

This module contains application constants and configuration settings.
"""

from datetime import datetime

# Default dashboard values
DEFAULT_TARGET_ENROLLMENT = 10
DEFAULT_PROJECTION_END_DATE = datetime(2025, 9, 30)
DEFAULT_SCREEN_FAILURE_RATE = 50.0  # Default if calculation not possible

# Chart colors
CHART_COLORS = {
    'primary': '#0066b2',
    'secondary': '#FF7F0E',
    'tertiary': '#2CA02C',
    'quaternary': '#d62728',
    'quinary': '#9467bd'
}

# COSL names (fallback if not in data)
DEFAULT_COSL_NAMES = [
    'Evelina Pogoriler',
    'Jayden Cho',
    'Janice Graboso',
    'Farah Ridore',
    'Malini Shankar'
]

# Column mappings (for column name standardization)
COLUMN_MAPPINGS = {
    'Site ID': ['SiteID', 'Site Number', 'Site'],
    'Site Name': ['Site', 'Center Name', 'Center'],
    'Country': ['Region', 'Nation', 'Location'],
    'Screened': ['Total Screened', 'Screening', 'Screenings'],
    'Screen Failed': ['Screen Fails', 'Failed', 'Failed Screening'],
    'Randomized': ['Enrolled', 'Randomizations', 'Total Randomized'],
    'Status': ['Site Status', 'Active Status', 'Status'],
    'Investigator': ['PI', 'PI Name', 'Principal Investigator']
}

# Date formats to try when parsing strings
DATE_FORMATS = [
    '%d-%b-%Y',
    '%Y-%m-%d',
    '%m/%d/%Y',
    '%d/%m/%Y',
    '%B %d, %Y'
]

# Month formats to try when identifying date columns
MONTH_FORMATS = [
    '%b-%Y',
    '%B-%Y',
    '%m-%Y'
]
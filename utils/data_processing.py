"""
Data processing utilities for Clinical Trial Dashboard.

This module contains functions for processing and transforming data
from Excel/CSV files into the format needed for the dashboard.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import calendar

def process_enrollment_data(enrollment_df):
    """
    Process enrollment summary data for use in the dashboard.
    
    Args:
        enrollment_df (pandas.DataFrame): Raw enrollment data
        
    Returns:
        pandas.DataFrame: Processed enrollment data
    """
    # Clean up column names if needed
    enrollment_df.columns = [col.strip() for col in enrollment_df.columns]
    
    # Ensure required columns exist
    req_cols = ['Site ID', 'Site Name', 'Country', 'Screened', 'Screen Failed', 'Randomized']
    missing_cols = [col for col in req_cols if col not in enrollment_df.columns]
    
    if missing_cols:
        alt_cols = {
            'Site ID': ['SiteID', 'Site Number', 'Site'],
            'Site Name': ['Site', 'Center Name', 'Center'],
            'Country': ['Region', 'Nation', 'Location'],
            'Screened': ['Total Screened', 'Screening', 'Screenings'],
            'Screen Failed': ['Screen Fails', 'Failed', 'Failed Screening'],
            'Randomized': ['Enrolled', 'Randomizations', 'Total Randomized']
        }
        
        # Try to find alternative column names
        for missing in missing_cols:
            for alt in alt_cols.get(missing, []):
                if alt in enrollment_df.columns:
                    enrollment_df[missing] = enrollment_df[alt]
                    break
    
    # Fill NA values with 0 for numeric columns
    numeric_cols = ['Screened', 'Screen Failed', 'Randomized']
    for col in numeric_cols:
        if col in enrollment_df.columns:
            enrollment_df[col] = pd.to_numeric(enrollment_df[col], errors='coerce').fillna(0)
    
    return enrollment_df

def process_monthly_data(monthly_df):
    """
    Process monthly summary data for use in the dashboard.
    
    Args:
        monthly_df (pandas.DataFrame): Raw monthly data
        
    Returns:
        pandas.DataFrame: Processed monthly data
    """
    # Clean up column names
    monthly_df.columns = [col.strip() for col in monthly_df.columns]
    
    # Ensure required columns exist
    req_cols = ['Site ID', 'Site Name', 'Status', 'Country', 'Subject Status']
    missing_cols = [col for col in req_cols if col not in monthly_df.columns]
    
    if missing_cols:
        alt_cols = {
            'Site ID': ['SiteID', 'Site Number', 'Site'],
            'Site Name': ['Site', 'Center Name', 'Center'],
            'Status': ['Site Status', 'Active Status', 'Status'],
            'Country': ['Region', 'Nation', 'Location'],
            'Subject Status': ['Status', 'Participant Status', 'Patient Status']
        }
        
        # Try to find alternative column names
        for missing in missing_cols:
            for alt in alt_cols.get(missing, []):
                if alt in monthly_df.columns:
                    monthly_df[missing] = monthly_df[alt]
                    break
    
    # Convert date columns to datetime if they exist
    date_cols = ['1st Screening', '1st Enrollment']
    for col in date_cols:
        if col in monthly_df.columns:
            monthly_df[col] = pd.to_datetime(monthly_df[col], errors='coerce')
    
    return monthly_df

def process_site_data(site_df):
    """
    Process site data for use in the dashboard.
    
    Args:
        site_df (pandas.DataFrame): Raw site data
        
    Returns:
        pandas.DataFrame: Processed site data
    """
    # Clean up column names
    site_df.columns = [col.strip() for col in site_df.columns]
    
    # Ensure required columns exist
    req_cols = ['Site Number', 'Country', 'Site Activated Date']
    missing_cols = [col for col in req_cols if col not in site_df.columns]
    
    if missing_cols:
        alt_cols = {
            'Site Number': ['Site ID', 'SiteID', 'Site'],
            'Country': ['Region', 'Nation', 'Location'],
            'Site Activated Date': ['Activation Date', 'Activated On', 'Date Activated']
        }
        
        # Try to find alternative column names
        for missing in missing_cols:
            for alt in alt_cols.get(missing, []):
                if alt in site_df.columns:
                    site_df[missing] = site_df[alt]
                    break
    
    # Convert date columns to datetime
    date_cols = ['Site Activated Date', 'First Subject Screened Date', 'First Subject Enrolled Date']
    for col in date_cols:
        if col in site_df.columns:
            site_df[col] = pd.to_datetime(site_df[col], errors='coerce')
    
    return site_df

def generate_cosl_data(df):
    """
    Generate COSL assignment data from site data.
    If no COSL column exists, tries to use PI name or creates dummy assignments.
    
    Args:
        df (pandas.DataFrame): Site data
        
    Returns:
        pandas.DataFrame: COSL assignments
    """
    # Look for COSL column
    cosl_col = next((col for col in df.columns if 'cosl' in col.lower()), None)
    
    if cosl_col:
        # Use existing COSL column
        return df[['Site Number', cosl_col]].rename(columns={cosl_col: 'Assigned COSL'})
    else:
        # No COSL column found, check if we can use PI Name as substitute
        pi_col = next((col for col in df.columns if 'pi' in col.lower() or 'investigator' in col.lower()), None)
        
        if pi_col:
            return df[['Site Number', pi_col]].rename(columns={pi_col: 'Assigned COSL'})
        
        # If no PI column either, create dummy COSL data
        unique_sites = df['Site Number'].unique()
        
        # Create 5 fictional COSLs
        cosl_names = ['Evelina Pogoriler', 'Jayden Cho', 'Janice Graboso', 'Farah Ridore', 'Malini Shankar']
        
        # Assign sites to COSLs
        cosl_assignments = []
        for i, site in enumerate(unique_sites):
            cosl_assignments.append({
                'Site Number': site,
                'Assigned COSL': cosl_names[i % len(cosl_names)]
            })
            
        return pd.DataFrame(cosl_assignments)

def calculate_screen_failure_rate(enrollment_data, monthly_data, sf_rate_override=0):
    """
    Calculate the screen failure rate from enrollment data.
    
    Args:
        enrollment_data (pandas.DataFrame): Enrollment data
        monthly_data (pandas.DataFrame): Monthly data
        sf_rate_override (float): Override value for screen failure rate (0 means no override)
        
    Returns:
        float: Screen failure rate (percentage)
    """
    # Use override if provided
    if sf_rate_override > 0:
        return sf_rate_override
    
    # Calculate from enrollment data
    if 'Screen Failed' in enrollment_data.columns and 'Screened' in enrollment_data.columns:
        total_screened = enrollment_data['Screened'].sum()
        total_failed = enrollment_data['Screen Failed'].sum()
        
        if total_screened > 0:
            return (total_failed / total_screened) * 100
    
    # Alternative calculation from monthly data
    statuses = monthly_data['Subject Status'].unique()
    
    if 'Screen Failed' in statuses and 'Screened' in statuses:
        screened_data = monthly_data[monthly_data['Subject Status'] == 'Screened']
        failed_data = monthly_data[monthly_data['Subject Status'] == 'Screen Failed']
        
        if 'Total' in screened_data.columns and 'Total' in failed_data.columns:
            total_screened = screened_data['Total'].sum()
            total_failed = failed_data['Total'].sum()
            
            if total_screened > 0:
                return (total_failed / total_screened) * 100
    
    # Default if calculation not possible
    return 50.0

def generate_enrollment_projections(enrollment_data, target_enrollment, projection_end, screen_failure_rate):
    """
    Generate enrollment projections through the specified end date.
    
    Args:
        enrollment_data (pandas.DataFrame): Enrollment data
        target_enrollment (int): Monthly enrollment target
        projection_end (datetime): End date for projections
        screen_failure_rate (float): Screen failure rate percentage
        
    Returns:
        pandas.DataFrame: Enrollment projections
    """
    # Find current cumulative randomizations
    if 'Randomized' in enrollment_data.columns:
        current_cumulative = enrollment_data['Randomized'].sum()
    else:
        current_cumulative = 0
    
    # Calculate screenings needed for target
    screenings_needed = round(target_enrollment / (1 - screen_failure_rate/100)) if screen_failure_rate < 100 else target_enrollment * 5
    
    # Generate monthly projections
    current_date = datetime.now()
    start_date = datetime(current_date.year, current_date.month, 1)
    end_date = datetime(projection_end.year, projection_end.month, calendar.monthrange(projection_end.year, projection_end.month)[1])
    
    months = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    projections = []
    
    for i, month in enumerate(months):
        month_name = month.strftime('%b-%Y')
        month_cumulative = current_cumulative + ((i + 1) * target_enrollment)
        
        projections.append({
            'Month': month_name,
            'Target Randomizations': target_enrollment,
            'Cumulative Target': month_cumulative,
            'Screenings Needed': screenings_needed
        })
    
    return pd.DataFrame(projections)

def extract_monthly_enrollment(monthly_data):
    """
    Extract monthly enrollment figures from monthly data.
    
    Args:
        monthly_data (pandas.DataFrame): Monthly data
        
    Returns:
        pandas.DataFrame: Monthly enrollment data
    """
    # Find date columns (format: 'Mar-2025', 'Feb-2025', etc.)
    date_cols = []
    date_mapping = {}
    
    for col in monthly_data.columns:
        if col not in ['Site ID', 'Site Name', 'PI First Name', 'PI Last Name', 
                      'Status', 'Country', '1st Screening', '1st Enrollment', 
                      'Subject Status', 'Total']:
            try:
                # Try different date formats
                for fmt in ['%b-%Y', '%B-%Y', '%m-%Y']:
                    try:
                        date_obj = datetime.strptime(col, fmt)
                        date_cols.append(col)
                        date_mapping[col] = date_obj
                        break
                    except:
                        continue
            except:
                pass
    
    if not date_cols:
        return None
    
    # Sort date columns by actual date
    sorted_date_cols = sorted(date_cols, key=lambda x: date_mapping[x])
    
    # Filter to only randomized subjects
    randomized_data = monthly_data[monthly_data['Subject Status'] == 'Randomized']
    
    # Calculate monthly totals
    monthly_totals = []
    cumulative_total = 0
    
    for col in sorted_date_cols:
        month_total = randomized_data[col].sum()
        cumulative_total += month_total
        
        monthly_totals.append({
            'Month': col,
            'Monthly Randomized': month_total,
            'Cumulative Randomized': cumulative_total,
            'Month_dt': date_mapping[col]
        })
    
    return pd.DataFrame(monthly_totals)

def calculate_site_metrics(activation_data):
    """
    Calculate metrics about site activation and performance.
    
    Args:
        activation_data (pandas.DataFrame): Site activation data
        
    Returns:
        dict: Site metrics including counts and averages
    """
    # Make a copy to avoid modifying the original
    site_data = activation_data.copy()
    
    # Convert date columns to datetime
    date_cols = ['Date of Activation', 'Date of First Screening', 'Date of First Randomization']
    for col in date_cols:
        if col in site_data.columns:
            site_data[col] = pd.to_datetime(site_data[col], errors='coerce')
    
    # Calculate days between activation and first enrolled
    if 'Date of Activation' in site_data.columns and 'Date of First Screening' in site_data.columns:
        # Calculate days between activation and first screening
        site_data['Days to First Screening'] = np.nan
        mask = ~site_data['Date of Activation'].isna() & ~site_data['Date of First Screening'].isna()
        site_data.loc[mask, 'Days to First Screening'] = (
            site_data.loc[mask, 'Date of First Screening'] - site_data.loc[mask, 'Date of Activation']
        ).dt.days
        
        # Sites with no screening yet
        mask_no_screening = ~site_data['Date of Activation'].isna() & site_data['Date of First Screening'].isna()
        site_data.loc[mask_no_screening, 'Days to First Screening'] = (
            pd.Timestamp.today() - site_data.loc[mask_no_screening, 'Date of Activation']
        ).dt.days
    
    # Calculate site metrics
    metrics = {
        'total_sites': len(site_data),
        'active_sites': site_data[site_data['Site Status'] == 'Active'].shape[0],
        'inactive_sites': site_data[site_data['Site Status'] != 'Active'].shape[0],
        'avg_days_to_first_screening': site_data['Days to First Screening'].mean() if 'Days to First Screening' in site_data.columns else None,
        'median_days_to_first_screening': site_data['Days to First Screening'].median() if 'Days to First Screening' in site_data.columns else None,
        'sites_not_screening': site_data['Date of First Screening'].isna().sum(),
        'sites_not_randomizing': site_data['Date of First Randomization'].isna().sum()
    }
    
    # Calculate percentages
    if metrics['total_sites'] > 0:
        metrics['pct_active'] = (metrics['active_sites'] / metrics['total_sites']) * 100
        metrics['pct_not_screening'] = (metrics['sites_not_screening'] / metrics['total_sites']) * 100
        metrics['pct_not_randomizing'] = (metrics['sites_not_randomizing'] / metrics['total_sites']) * 100
    
    return metrics, site_data
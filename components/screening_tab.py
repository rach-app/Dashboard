"""
Screen Failure Analysis Tab for the Clinical Trial Dashboard.

This module renders the Screen Failure Analysis tab which displays:
- Screen failure rates by country
- Screen failure rates by site
- Screen failure details
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from plotly.subplots import make_subplots as plotly_make_subplots

from utils.visualization import create_bar_chart
from utils.download import get_table_download_link

def render_screening_tab(enrollment_data, monthly_data):
    """
    Render the Screen Failure Analysis tab.
    
    Args:
        enrollment_data (pandas.DataFrame): Enrollment data
        monthly_data (pandas.DataFrame): Monthly data
    """
    st.markdown('<h3 class="sub-header">Screen Failure Analysis</h3>', unsafe_allow_html=True)
    
    if enrollment_data is not None:
        # Make sure we have the necessary columns
        if all(col in enrollment_data.columns for col in ['Country', 'Screened', 'Screen Failed']):
            # Group by country
            country_sf = enrollment_data.groupby('Country').agg({
                'Screened': 'sum',
                'Screen Failed': 'sum',
                'Randomized': 'sum' if 'Randomized' in enrollment_data.columns else lambda x: 0
            }).reset_index()
            
            # Calculate screen failure rate
            country_sf['Screen Failure Rate'] = (country_sf['Screen Failed'] / country_sf['Screened'] * 100).round(1)
            country_sf['Randomization Rate'] = (country_sf['Randomized'] / country_sf['Screened'] * 100).round(1) if 'Randomized' in country_sf.columns else 0
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Screen failure rate by country
                fig = px.bar(
                    country_sf.sort_values('Screen Failure Rate'),
                    x='Country',
                    y='Screen Failure Rate',
                    title='Screen Failure Rate by Country',
                    color='Screen Failure Rate',
                    color_continuous_scale='RdYlGn_r',  # Red for high values, green for low
                    text_auto='.1f'
                )
                
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Screening volume by country
                fig = px.bar(
                    country_sf.sort_values('Screened', ascending=False),
                    x='Country',
                    y=['Screened', 'Screen Failed', 'Randomized'] if 'Randomized' in country_sf.columns else ['Screened', 'Screen Failed'],
                    title='Screening Volume by Country',
                    barmode='group'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Screen Failure Analysis Table
            st.markdown('<h4>Screen Failure Metrics by Country</h4>', unsafe_allow_html=True)
            
            # Prepare the data for display
            display_df = country_sf.copy()
            display_df = display_df.sort_values('Screened', ascending=False)
            
            # Calculate the randomization rate if not already present
            if 'Randomization Rate' not in display_df.columns and 'Randomized' in display_df.columns:
                display_df['Randomization Rate'] = (display_df['Randomized'] / display_df['Screened'] * 100).round(1)
            
            st.dataframe(display_df)
            
            # Add download link
            st.markdown(get_table_download_link(
                display_df,
                'screen_failure_by_country',
                '📥 Download Country Metrics'
            ), unsafe_allow_html=True)
            
            # Site-level screen failure analysis
            st.markdown('<h4>Screen Failure Rate by Site</h4>', unsafe_allow_html=True)
            
            # Group by site
            if 'Site ID' in enrollment_data.columns or 'Site Number' in enrollment_data.columns:
                site_col = 'Site ID' if 'Site ID' in enrollment_data.columns else 'Site Number'
                
                site_sf = enrollment_data.groupby([site_col, 'Country']).agg({
                    'Screened': 'sum',
                    'Screen Failed': 'sum',
                    'Randomized': 'sum' if 'Randomized' in enrollment_data.columns else lambda x: 0
                }).reset_index()
                
                # Calculate screen failure rate
                site_sf['Screen Failure Rate'] = (site_sf['Screen Failed'] / site_sf['Screened'] * 100).round(1)
                
                # Only include sites with at least 5 screened subjects for meaningful rates
                site_sf_meaningful = site_sf[site_sf['Screened'] >= 5].copy()
                
                if len(site_sf_meaningful) > 0:
                    # Create scatter plot of screen failure rate vs screening volume
                    fig = px.scatter(
                        site_sf_meaningful,
                        x='Screened',
                        y='Screen Failure Rate',
                        color='Country',
                        size='Screened',
                        hover_name=site_col,
                        title='Screen Failure Rate vs Screening Volume by Site',
                        labels={'Screened': 'Number of Screened Subjects', 'Screen Failure Rate': 'Screen Failure Rate (%)'}
                    )
                    
                    # Add a horizontal line for the average screen failure rate
                    avg_sf_rate = (site_sf['Screen Failed'].sum() / site_sf['Screened'].sum() * 100)
                    fig.add_hline(y=avg_sf_rate, line_dash="dash", line_color="red",
                                  annotation_text=f"Avg: {avg_sf_rate:.1f}%")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Table of sites with highest screen failure rates
                    st.markdown('<h4>Sites with Highest Screen Failure Rates</h4>', unsafe_allow_html=True)
                    
                    # Filter for sites with at least 5 screened subjects
                    top_sf_sites = site_sf[site_sf['Screened'] >= 5].sort_values('Screen Failure Rate', ascending=False).head(10)
                    
                    st.dataframe(top_sf_sites)
                    
                    # Add download link for all site data
                    st.markdown(get_table_download_link(
                        site_sf,
                        'screen_failure_by_site',
                        '📥 Download All Site Screen Failure Data'
                    ), unsafe_allow_html=True)
                else:
                    st.info("Not enough sites with sufficient screening volume (≥5 subjects) for meaningful analysis")
            else:
                st.warning("Site ID/Number information not available for site-level analysis")
            
            # Screen Failure Analysis by Month (if monthly data is available)
            if monthly_data is not None:
                st.markdown('<h4>Screen Failure Trends Over Time</h4>', unsafe_allow_html=True)
                
                try:
                    # Attempt to extract monthly screening and failure data
                    monthly_sf_data = extract_monthly_screening_data(monthly_data)
                    
                    if monthly_sf_data is not None and len(monthly_sf_data) > 0:
                        # Using the correct plotly subplots function
                        fig = plotly_make_subplots(specs=[[{"secondary_y": True}]])
                        
                        # Add bar chart for number of screenings
                        fig.add_trace(
                            go.Bar(
                                x=monthly_sf_data['Month'],
                                y=monthly_sf_data['Screened'],
                                name='Subjects Screened',
                                marker_color='#1f77b4'
                            ),
                            secondary_y=False
                        )
                        
                        # Add line chart for screen failure rate
                        fig.add_trace(
                            go.Scatter(
                                x=monthly_sf_data['Month'],
                                y=monthly_sf_data['Screen Failure Rate'],
                                mode='lines+markers',
                                name='Screen Failure Rate (%)',
                                marker=dict(size=8),
                                line=dict(width=3, color='#d62728')
                            ),
                            secondary_y=True
                        )
                        
                        # Update layout
                        fig.update_layout(
                            title='Screening Volume and Screen Failure Rate by Month',
                            xaxis=dict(title='Month'),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        # Update y-axes titles
                        fig.update_yaxes(title_text="Subjects Screened", secondary_y=False)
                        fig.update_yaxes(title_text="Screen Failure Rate (%)", secondary_y=True)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display monthly data table
                        st.dataframe(monthly_sf_data)
                        
                        # Add download link
                        st.markdown(get_table_download_link(
                            monthly_sf_data,
                            'monthly_screen_failure_data',
                            '📥 Download Monthly Data'
                        ), unsafe_allow_html=True)
                    else:
                        st.info("Unable to extract monthly screening failure data from the provided monthly data")
                except Exception as e:
                    st.info(f"Unable to extract monthly screening failure data: {str(e)}")
                    st.exception(e)  # Show the full exception for debugging
        else:
            st.warning("Screening and screen failure data required for analysis")
    else:
        st.warning("Enrollment data not available")

def extract_monthly_screening_data(monthly_data):
    """
    Extract monthly screening and screen failure data from monthly data.
    
    Args:
        monthly_data (pandas.DataFrame): Monthly data
        
    Returns:
        pandas.DataFrame: Monthly screening data with screen failure rates
    """
    try:
        # Check if we have the necessary columns
        if 'Subject Status' not in monthly_data.columns:
            return None
        
        # Find date columns (format: 'Mar-2025', 'Feb-2025', etc.)
        date_cols = []
        date_mapping = {}
        
        # Get all potential month columns
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
            # Check if we might have month columns with different formats
            potential_month_cols = []
            for col in monthly_data.columns:
                # Look for columns that might be numeric months
                if col not in ['Site ID', 'Site Name', 'PI First Name', 'PI Last Name', 
                              'Status', 'Country', '1st Screening', '1st Enrollment', 
                              'Subject Status', 'Total'] and pd.api.types.is_numeric_dtype(monthly_data[col].dtype):
                    potential_month_cols.append(col)
            
            if potential_month_cols:
                # Assuming these are month columns but with different format
                date_cols = potential_month_cols
                # Create a simple mapping
                for i, col in enumerate(date_cols):
                    # Create a dummy date just for sorting
                    date_mapping[col] = pd.Timestamp(year=2020, month=(i % 12) + 1, day=1)
            else:
                return None
        
        # Sort date columns by actual date if available
        sorted_date_cols = sorted(date_cols, key=lambda x: date_mapping.get(x, pd.Timestamp.now()))
        
        # Extract data for each month
        monthly_totals = []
        
        # Check if we have the correct subject status values
        expected_statuses = ['Screened', 'Screen Failed', 'Randomized']
        actual_statuses = monthly_data['Subject Status'].unique()
        
        # If we don't have the expected statuses, try to map what we have
        status_mapping = {}
        for expected in expected_statuses:
            for actual in actual_statuses:
                if expected.lower() in str(actual).lower():
                    status_mapping[expected] = actual
                    break
        
        # If we couldn't map all expected statuses, try to use what we have
        if len(status_mapping) < 2:  # Need at least screened and failed
            # Try to find any statuses that might be related to screening or failure
            for status in actual_statuses:
                status_str = str(status).lower()
                if 'screen' in status_str and 'fail' not in status_str:
                    status_mapping['Screened'] = status
                elif 'fail' in status_str or 'screen fail' in status_str:
                    status_mapping['Screen Failed'] = status
                elif 'random' in status_str or 'enroll' in status_str:
                    status_mapping['Randomized'] = status
        
        # If we still don't have the needed statuses, we can't extract the data
        if 'Screened' not in status_mapping or 'Screen Failed' not in status_mapping:
            return None
        
        for col in sorted_date_cols:
            # Skip if the column isn't numeric
            if not pd.api.types.is_numeric_dtype(monthly_data[col].dtype):
                continue
                
            # Get screening and screen failure data
            screened_data = monthly_data[monthly_data['Subject Status'] == status_mapping.get('Screened', 'Screened')]
            failed_data = monthly_data[monthly_data['Subject Status'] == status_mapping.get('Screen Failed', 'Screen Failed')]
            randomized_data = monthly_data[monthly_data['Subject Status'] == status_mapping.get('Randomized', 'Randomized')] if 'Randomized' in status_mapping else None
            
            # Sum values for this month
            screened = screened_data[col].sum() if col in screened_data.columns else 0
            failed = failed_data[col].sum() if col in failed_data.columns else 0
            randomized = randomized_data[col].sum() if randomized_data is not None and col in randomized_data.columns else 0
            
            # Only include months with at least some screening activity
            if screened > 0 or failed > 0:
                # Calculate screen failure rate
                sf_rate = (failed / screened * 100) if screened > 0 else 0
                
                monthly_totals.append({
                    'Month': col,
                    'Screened': screened,
                    'Screen Failed': failed,
                    'Randomized': randomized,
                    'Screen Failure Rate': round(sf_rate, 1),
                    'Month_dt': date_mapping.get(col, pd.Timestamp.now())
                })
        
        # Convert to dataframe and sort by date
        if monthly_totals:
            df = pd.DataFrame(monthly_totals)
            if 'Month_dt' in df.columns:
                df = df.sort_values('Month_dt')
            return df
        else:
            return None
        
    except Exception as e:
        print(f"Error extracting monthly data: {str(e)}")
        return None
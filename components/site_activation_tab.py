"""
Site Activation Tab for the Clinical Trial Dashboard.

This module renders the Site Activation tab which displays:
- Site status overview (pie chart)
- Sites by country chart
- Site activation metrics
- Site activation timeline histogram
- Site activation details table
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_processing import calculate_site_metrics
from utils.visualization import create_pie_chart, create_bar_chart, create_histogram
from utils.download import get_table_download_link

def render_site_activation_tab(activation_data):
    """
    Render the Site Activation tab.
    
    Args:
        activation_data (pandas.DataFrame): Site activation data
    """
    st.markdown('<h3 class="sub-header">Site Activation Status</h3>', unsafe_allow_html=True)
    
    if activation_data is not None:
        # Calculate site metrics
        metrics, site_data = calculate_site_metrics(activation_data)
        
        # Create activation visualization
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Count sites by status
            status_counts = site_data['Site Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            # Create pie chart
            fig = create_pie_chart(
                status_counts,
                'Status',
                'Count',
                'Sites by Status',
                hole=0.4
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Create activation timeline chart
            # Group by country
            country_activation = site_data.groupby('Country').agg({
                'Site Number': 'count'
            }).reset_index()
            country_activation.columns = ['Country', 'Sites']
            
            # Sort by number of sites
            country_activation = country_activation.sort_values('Sites', ascending=False)
            
            fig = create_bar_chart(
                country_activation,
                'Country',
                'Sites',
                'Sites by Country',
                color='Sites'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Site activation metrics
        if 'Days to First Screening' in site_data.columns:
            st.markdown('<h4>Site Activation Metrics</h4>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Average days to first screening
                avg_days = metrics['avg_days_to_first_screening']
                median_days = metrics['median_days_to_first_screening']
                
                st.metric("Average Days to First Screening", f"{avg_days:.1f}" if avg_days is not None else "N/A")
                st.metric("Median Days to First Screening", f"{median_days:.1f}" if median_days is not None else "N/A")
            
            with col2:
                # Sites not yet screening
                not_screening = metrics['sites_not_screening']
                pct_not_screening = metrics['pct_not_screening'] if 'pct_not_screening' in metrics else 0
                
                st.metric("Sites Not Yet Screening", not_screening)
                st.metric("% of Sites Not Screening", f"{pct_not_screening:.1f}%" if pct_not_screening is not None else "N/A")
            
            with col3:
                # Sites not yet randomizing
                not_randomizing = metrics['sites_not_randomizing']
                pct_not_randomizing = metrics['pct_not_randomizing'] if 'pct_not_randomizing' in metrics else 0
                
                st.metric("Sites Not Yet Randomizing", not_randomizing)
                st.metric("% of Sites Not Randomizing", f"{pct_not_randomizing:.1f}%" if pct_not_randomizing is not None else "N/A")
        
        # Site activation histogram
        if 'Days to First Screening' in site_data.columns:
            # Filter data for sites with screening data
            site_data_with_screening = site_data.dropna(subset=['Days to First Screening'])
            
            if len(site_data_with_screening) > 0:
                # Create histogram of days to first screening
                fig = create_histogram(
                    site_data_with_screening,
                    'Days to First Screening',
                    'Distribution of Days from Activation to First Screening',
                    nbins=20
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No sites with both activation and first screening dates available for histogram")
        
        # Site activation table
        st.markdown('<h4>Site Activation Details</h4>', unsafe_allow_html=True)
        
        # Country filter
        countries = ['All'] + sorted(site_data['Country'].unique().tolist())
        selected_country = st.selectbox('Filter by Country', countries)
        
        # Status filter
        statuses = ['All'] + sorted(site_data['Site Status'].unique().tolist())
        selected_status = st.selectbox('Filter by Status', statuses)
        
        # Apply filters
        filtered_data = site_data.copy()
        if selected_country != 'All':
            filtered_data = filtered_data[filtered_data['Country'] == selected_country]
        if selected_status != 'All':
            filtered_data = filtered_data[filtered_data['Site Status'] == selected_status]
        
        # Format dates for display
        display_cols = [
            'Country', 'Site Number', 'Investigator', 'Site Status', 
            'Date of Activation', 'Date of First Screening', 'Date of First Randomization'
        ]
        
        if 'Days to First Screening' in filtered_data.columns:
            display_cols.append('Days to First Screening')
        
        # Display filtered columns
        cols_to_display = [col for col in display_cols if col in filtered_data.columns]
        
        display_df = filtered_data[cols_to_display].copy()
        
        # Format date columns
        for col in ['Date of Activation', 'Date of First Screening', 'Date of First Randomization']:
            if col in display_df.columns:
                display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%d-%b-%Y')
        
        # Format days column
        if 'Days to First Screening' in display_df.columns:
            display_df['Days to First Screening'] = display_df['Days to First Screening'].round(0).astype('Int64')
        
        if len(display_df) > 0:
            st.dataframe(display_df)
            
            # Add download link
            st.markdown(get_table_download_link(
                display_df, 
                'site_activation_details', 
                '📥 Download Site Activation Details'
            ), unsafe_allow_html=True)
        else:
            st.info("No sites match the selected filters")
    else:
        st.warning("No site activation data available")
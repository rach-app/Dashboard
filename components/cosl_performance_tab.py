"""
COSL Performance Tab for the Clinical Trial Dashboard.

This module renders the COSL Performance tab which displays:
- COSL metrics overview
- COSL performance visualizations
- Sites by COSL table
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.visualization import create_bar_chart
from utils.download import get_table_download_link

def render_cosl_performance_tab(cosl_data, activation_data, enrollment_data):
    """
    Render the COSL Performance tab.
    
    Args:
        cosl_data (pandas.DataFrame): COSL assignment data
        activation_data (pandas.DataFrame): Site activation data
        enrollment_data (pandas.DataFrame): Enrollment data
    """
    st.markdown('<h3 class="sub-header">COSL Performance</h3>', unsafe_allow_html=True)
    
    if cosl_data is not None and activation_data is not None:
        try:
            # Make sure Site Number columns are of the same type
            activation_data['Site Number'] = activation_data['Site Number'].astype(str)
            cosl_data['Site Number'] = cosl_data['Site Number'].astype(str)
            
            # Merge COSL assignments with site data
            cosl_site_data = activation_data.merge(
                cosl_data,
                on='Site Number',
                how='left'
            )
            
            # Calculate metrics by COSL
            cosl_metrics = calculate_cosl_metrics(cosl_site_data)
            
            # Calculate screen failure rates by COSL if possible
            if 'Screen Failed' in enrollment_data.columns and 'Site ID' in enrollment_data.columns:
                cosl_metrics = calculate_cosl_screen_failure_rates(cosl_metrics, cosl_data, enrollment_data)
            
            # Visualization of COSL performance
            if not cosl_metrics.empty:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Compare sites assigned vs. screened
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=cosl_metrics['COSL'],
                        y=cosl_metrics['Sites Assigned'],
                        name='Sites Assigned',
                        marker_color='#1f77b4'
                    ))
                    
                    fig.add_trace(go.Bar(
                        x=cosl_metrics['COSL'],
                        y=cosl_metrics['Sites Screened'],
                        name='Sites Screened',
                        marker_color='#2ca02c'
                    ))
                    
                    fig.update_layout(
                        title='COSL: Sites Assigned vs. Screened',
                        xaxis_title='COSL',
                        yaxis_title='Sites',
                        barmode='group',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Average days to first screening
                    if 'Avg Days to First Screening' in cosl_metrics.columns:
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=cosl_metrics['COSL'],
                            y=cosl_metrics['Avg Days to First Screening'],
                            marker_color='#ff7f0e'
                        ))
                        
                        fig.update_layout(
                            title='Average Days from Activation to First Screening',
                            xaxis_title='COSL',
                            yaxis_title='Days'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No activation date data available for time-to-screening analysis")
                
                # Additional charts if screen failure rate data is available
                if 'Screen Failure Rate' in cosl_metrics.columns:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Screen failure rate by COSL
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=cosl_metrics['COSL'],
                            y=cosl_metrics['Screen Failure Rate'],
                            marker_color='#d62728'
                        ))
                        
                        fig.update_layout(
                            title='Average Screen Failure Rate by COSL',
                            xaxis_title='COSL',
                            yaxis_title='Screen Failure Rate (%)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Sites randomized by COSL
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=cosl_metrics['COSL'],
                            y=cosl_metrics['Sites Randomized'],
                            marker_color='#9467bd'
                        ))
                        
                        fig.update_layout(
                            title='Sites with Randomized Subjects by COSL',
                            xaxis_title='COSL',
                            yaxis_title='Number of Sites'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # COSL metrics table
                st.markdown('<h4>COSL Performance Metrics</h4>', unsafe_allow_html=True)
                
                # Format days and rates for display
                display_df = cosl_metrics.copy()
                if 'Avg Days to First Screening' in display_df.columns:
                    display_df['Avg Days to First Screening'] = display_df['Avg Days to First Screening'].round(1)
                if 'Screen Failure Rate' in display_df.columns:
                    display_df['Screen Failure Rate'] = display_df['Screen Failure Rate'].round(1)
                
                st.dataframe(display_df)
                
                # Add download link
                st.markdown(get_table_download_link(
                    display_df, 
                    'cosl_performance_metrics', 
                    '📥 Download COSL Metrics'
                ), unsafe_allow_html=True)
                
            # Show site details by COSL
            st.markdown('<h4>Sites by COSL</h4>', unsafe_allow_html=True)
            
            # Filter by COSL
            cosls = cosl_site_data['Assigned COSL'].dropna().unique()
            selected_cosl = st.selectbox("Select COSL to view details", ['All'] + list(cosls))
            
            if selected_cosl != 'All':
                filtered_sites = cosl_site_data[cosl_site_data['Assigned COSL'] == selected_cosl]
            else:
                filtered_sites = cosl_site_data
            
            # Display site details
            display_cols = [
                'Country', 'Site Number', 'Investigator', 'Site Status', 
                'Date of Activation', 'Date of First Screening', 'Date of First Randomization',
                'Assigned COSL'
            ]
            
            if 'Days to First Screening' in filtered_sites.columns:
                display_cols.append('Days to First Screening')
            
            # Display filtered columns
            cols_to_display = [col for col in display_cols if col in filtered_sites.columns]
            
            # Format date columns
            display_df = filtered_sites[cols_to_display].copy()
            for col in ['Date of Activation', 'Date of First Screening', 'Date of First Randomization']:
                if col in display_df.columns:
                    display_df[col] = pd.to_datetime(display_df[col], errors='coerce').dt.strftime('%d-%b-%Y')
            
            # Format days column
            if 'Days to First Screening' in display_df.columns:
                display_df['Days to First Screening'] = display_df['Days to First Screening'].round(0).astype('Int64')
            
            st.dataframe(display_df)
            
            # Add download link
            st.markdown(get_table_download_link(
                display_df, 
                f'sites_by_cosl_{selected_cosl.replace(" ", "_").lower()}', 
                '📥 Download Sites List'
            ), unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error rendering COSL performance tab: {str(e)}")
            st.exception(e)
    else:
        st.info("COSL assignment data or site activation data not available")

def calculate_cosl_metrics(cosl_site_data):
    """
    Calculate metrics for each COSL based on site data.
    
    Args:
        cosl_site_data (pandas.DataFrame): Site data with COSL assignments
        
    Returns:
        pandas.DataFrame: Metrics for each COSL
    """
    cosl_metrics = []
    
    for cosl, group in cosl_site_data.groupby('Assigned COSL'):
        if pd.isna(cosl):
            continue
            
        total_sites = group.shape[0]
        sites_screened = group['Date of First Screening'].notna().sum()
        sites_not_screened = total_sites - sites_screened
        sites_randomized = group['Date of First Randomization'].notna().sum()
        sites_not_randomized = total_sites - sites_randomized
        
        # Calculate average days to first screening
        if 'Days to First Screening' in group.columns:
            avg_days = group.loc[group['Days to First Screening'].notna(), 'Days to First Screening'].mean()
        else:
            avg_days = None
        
        cosl_metrics.append({
            'COSL': cosl,
            'Sites Assigned': total_sites,
            'Sites Screened': sites_screened,
            'Sites Not Screened': sites_not_screened,
            'Sites Randomized': sites_randomized,
            'Sites Not Randomized': sites_not_randomized,
            'Avg Days to First Screening': avg_days if not pd.isna(avg_days) else 0
        })
    
    return pd.DataFrame(cosl_metrics)

def calculate_cosl_screen_failure_rates(cosl_metrics, cosl_data, enrollment_data):
    """
    Calculate screen failure rates by COSL and add to metrics.
    
    Args:
        cosl_metrics (pandas.DataFrame): COSL metrics dataframe
        cosl_data (pandas.DataFrame): COSL assignment data
        enrollment_data (pandas.DataFrame): Enrollment data
        
    Returns:
        pandas.DataFrame: Updated COSL metrics with screen failure rates
    """
    # Make sure we have the right columns
    if not all(col in enrollment_data.columns for col in ['Site ID', 'Screened', 'Screen Failed']):
        return cosl_metrics
    
    try:
        # Group enrollment data by site
        site_metrics = enrollment_data.groupby('Site ID').agg({
            'Screened': 'sum',
            'Screen Failed': 'sum',
            'Randomized': 'sum' if 'Randomized' in enrollment_data.columns else lambda x: 0
        }).reset_index()
        
        # Calculate screen failure rate
        site_metrics['Screen Failure Rate'] = (site_metrics['Screen Failed'] / site_metrics['Screened'] * 100).fillna(0)
        
        # Convert Site ID to string for merging
        site_metrics['Site ID'] = site_metrics['Site ID'].astype(str)
        
        # Rename column to match
        site_metrics = site_metrics.rename(columns={'Site ID': 'Site Number'})
        
        # Ensure COSL data Site Number column is string type
        cosl_data_copy = cosl_data.copy()
        cosl_data_copy['Site Number'] = cosl_data_copy['Site Number'].astype(str)
        
        # Merge with COSL data
        cosl_site_metrics = site_metrics.merge(
            cosl_data_copy,
            on='Site Number',
            how='left'
        )
        
        # Calculate average screen failure rate by COSL
        cosl_sf_rates = cosl_site_metrics.groupby('Assigned COSL').agg({
            'Screen Failure Rate': 'mean',
            'Screened': 'sum',
            'Randomized': 'sum'
        }).reset_index()
        
        # Safe merge with COSL metrics - ensuring string comparison for 'COSL' column
        cosl_metrics_copy = cosl_metrics.copy()
        cosl_metrics_copy['COSL'] = cosl_metrics_copy['COSL'].astype(str)
        
        cosl_sf_rates['Assigned COSL'] = cosl_sf_rates['Assigned COSL'].astype(str)
        
        merged_metrics = cosl_metrics_copy.merge(
            cosl_sf_rates[['Assigned COSL', 'Screen Failure Rate']],
            left_on='COSL',
            right_on='Assigned COSL',
            how='left'
        )
        
        if 'Assigned COSL' in merged_metrics.columns:
            merged_metrics = merged_metrics.drop('Assigned COSL', axis=1)
        
        return merged_metrics
        
    except Exception as e:
        st.warning(f"Error calculating screen failure rates: {str(e)}")
        return cosl_metrics
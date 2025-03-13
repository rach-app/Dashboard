"""
Enrollment Progress Tab for the Clinical Trial Dashboard.

This module renders the Enrollment Progress tab which displays:
- Enrollment progress chart (actual vs projected)
- Enrollment projections table
- Enrollment statistics and projections
- Screenings needed calculator
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_processing import extract_monthly_enrollment
from utils.visualization import create_combined_chart
from utils.download import get_table_download_link

def render_enrollment_tab(monthly_data, enrollment_data, enrollment_projections, target_enrollment, screen_failure_rate):
    """
    Render the Enrollment Progress tab.
    
    Args:
        monthly_data (pandas.DataFrame): Monthly enrollment data
        enrollment_data (pandas.DataFrame): Summary enrollment data
        enrollment_projections (pandas.DataFrame): Enrollment projections
        target_enrollment (int): Monthly enrollment target
        screen_failure_rate (float): Screen failure rate percentage
    """
    st.markdown('<h3 class="sub-header">Enrollment Progress</h3>', unsafe_allow_html=True)
    
    # Create dataframe for actual enrollment
    if monthly_data is not None:
        # Extract monthly enrollment data
        actual_enrollment = extract_monthly_enrollment(monthly_data)
        
        if actual_enrollment is None or len(actual_enrollment) == 0:
            # Use enrollment data to create a simple visualization
            render_simple_enrollment_chart(enrollment_data, target_enrollment)
        else:
            # Merge with projections
            if enrollment_projections is not None:
                # Add datetime column to projections
                projections = enrollment_projections.copy()
                projections['Month_dt'] = projections['Month'].apply(lambda x: datetime.strptime(x, '%b-%Y'))
                
                # Create combined chart
                fig = create_combined_chart(actual_enrollment, projections, 'Enrollment Progress and Projections')
                st.plotly_chart(fig, use_container_width=True)
                
                # Show the projection data table
                st.markdown('<h4>Enrollment Projections</h4>', unsafe_allow_html=True)
                
                # Display the projections table with download link
                st.dataframe(projections[['Month', 'Target Randomizations', 'Cumulative Target', 'Screenings Needed']])
                st.markdown(get_table_download_link(
                    projections[['Month', 'Target Randomizations', 'Cumulative Target', 'Screenings Needed']], 
                    'enrollment_projections', 
                    '📥 Download Projections'
                ), unsafe_allow_html=True)
    
    # Enrollment Futures Content - Show current enrollment rate and projection
    st.markdown('<h4>Enrollment Futures</h4>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Current stats
        st.markdown("<b>Current Enrollment Statistics</b>", unsafe_allow_html=True)
        
        # Calculate the current enrollment rate (last 3 months)
        if 'actual_enrollment' in locals() and len(actual_enrollment) > 0:
            recent_months = min(3, len(actual_enrollment))
            recent_data = actual_enrollment.tail(recent_months)
            avg_monthly_rate = recent_data['Monthly Randomized'].mean()
            
            st.metric("Current Monthly Enrollment Rate", f"{avg_monthly_rate:.1f} subjects/month")
            st.metric("Target Monthly Enrollment Rate", f"{target_enrollment} subjects/month")
            st.metric("Screen Failure Rate", f"{screen_failure_rate:.1f}%")
        else:
            # Use summary data if actual monthly data not available
            if 'Randomized' in enrollment_data.columns:
                total_randomized = enrollment_data['Randomized'].sum()
                # Estimate over 12 months
                avg_monthly_rate = total_randomized / 12
                
                st.metric("Estimated Monthly Enrollment Rate", f"{avg_monthly_rate:.1f} subjects/month")
                st.metric("Target Monthly Enrollment Rate", f"{target_enrollment} subjects/month")
                st.metric("Screen Failure Rate", f"{screen_failure_rate:.1f}%")
            else:
                st.info("No monthly enrollment data available for statistics")
    
    with col2:
        # Projection to completion
        st.markdown("<b>Enrollment Completion Projection</b>", unsafe_allow_html=True)
        
        # Calculate completion date based on current rate vs target
        if enrollment_projections is not None and len(enrollment_projections) > 0:
            total_target = enrollment_projections['Cumulative Target'].max()
            
            if 'actual_enrollment' in locals() and len(actual_enrollment) > 0:
                current_enrolled = actual_enrollment['Cumulative Randomized'].max()
                recent_months = min(3, len(actual_enrollment))
                recent_data = actual_enrollment.tail(recent_months)
                avg_monthly_rate = recent_data['Monthly Randomized'].mean()
            else:
                current_enrolled = enrollment_data['Randomized'].sum() if 'Randomized' in enrollment_data.columns else 0
                avg_monthly_rate = current_enrolled / 12  # Estimate based on 1 year
            
            # Calculate months to completion
            remaining = total_target - current_enrolled
            
            if avg_monthly_rate > 0:
                months_at_current = np.ceil(remaining / avg_monthly_rate)
            else:
                months_at_current = np.nan
            
            months_at_target = np.ceil(remaining / target_enrollment)
            
            # Calculate completion dates
            current_date = datetime.now()
            
            if not np.isnan(months_at_current):
                completion_at_current = current_date + pd.DateOffset(months=int(months_at_current))
                st.metric("Completion Date (Current Rate)", completion_at_current.strftime('%b %Y'))
            else:
                st.metric("Completion Date (Current Rate)", "N/A")
            
            completion_at_target = current_date + pd.DateOffset(months=int(months_at_target))
            st.metric("Completion Date (Target Rate)", completion_at_target.strftime('%b %Y'))
            st.metric("Remaining Subjects", f"{int(remaining)}")
        else:
            st.info("No projection data available")
    
    # Screenings needed calculation
    st.markdown('<h4>Required Screenings Calculation</h4>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    # Calculate screenings needed for target
    screenings_needed = round(target_enrollment / (1 - screen_failure_rate/100)) if screen_failure_rate < 100 else target_enrollment * 5
    
    with col1:
        # Formula explanation
        st.markdown(f"""
        <p>Based on the current screen failure rate of <b>{screen_failure_rate:.1f}%</b>, 
        to achieve the target of <b>{target_enrollment}</b> randomizations per month, 
        approximately <b>{screenings_needed}</b> subjects need to be screened monthly.</p>
        
        <p><b>Formula:</b> Screenings Needed = Target Enrollment / (1 - Screen Failure Rate)</p>
        <p><b>Calculation:</b> {target_enrollment} / (1 - {screen_failure_rate:.1f}%) = {screenings_needed}</p>
        """, unsafe_allow_html=True)
    
    with col2:
        # Screen failure rate slider for what-if analysis
        st.markdown("<b>What-If Analysis</b>", unsafe_allow_html=True)
        what_if_sf_rate = st.slider("Adjust Screen Failure Rate", 0.0, 100.0, float(screen_failure_rate), 0.5, format="%.1f%%")
    
    with col3:
        # Calculate what-if scenario
        what_if_screenings = round(target_enrollment / (1 - what_if_sf_rate/100)) if what_if_sf_rate < 100 else target_enrollment * 5
        
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        st.metric("Screenings Needed", what_if_screenings)

def render_simple_enrollment_chart(enrollment_data, target_enrollment):
    """
    Render a simple enrollment chart when no monthly data is available.
    
    Args:
        enrollment_data (pandas.DataFrame): Summary enrollment data
        target_enrollment (int): Monthly enrollment target
    """
    if 'Randomized' in enrollment_data.columns:
        total_randomized = enrollment_data['Randomized'].sum()
        
        # Create a simple chart showing total randomized vs target
        current_date = datetime.now()
        months_elapsed = 12  # Assume 1 year
        
        # Create a basic enrollment chart
        fig = go.Figure()
        
        # Current enrollment
        fig.add_trace(go.Bar(
            x=['Current Enrollment'],
            y=[total_randomized],
            name='Current Enrollment',
            marker_color='#0066b2'
        ))
        
        # Target based on monthly rate
        target_total = target_enrollment * months_elapsed
        fig.add_trace(go.Bar(
            x=['Target Enrollment'],
            y=[target_total],
            name=f'Target ({target_enrollment}/month for {months_elapsed} months)',
            marker_color='#FF7F0E'
        ))
        
        fig.update_layout(
            title='Current Enrollment vs Target',
            xaxis_title='',
            yaxis_title='Number of Subjects',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No enrollment data available for visualization")
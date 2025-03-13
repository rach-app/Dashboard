import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import component modules
from components.enrollment_tab import render_enrollment_tab
from components.site_activation_tab import render_site_activation_tab
from components.cosl_performance_tab import render_cosl_performance_tab
from components.screening_tab import render_screening_tab

# Import utility functions
from utils.data_processing import (
    process_enrollment_data,
    process_monthly_data,
    process_site_data,
    generate_cosl_data,
    calculate_screen_failure_rate,
    generate_enrollment_projections
)

# Set page configuration
st.set_page_config(
    page_title="Clinical Trial Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #0066b2;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0066b2;
        margin-top: 30px;
        margin-bottom: 15px;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #0066b2;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
    }
    .status-active {
        color: green;
        font-weight: bold;
    }
    .status-inactive {
        color: red;
        font-weight: bold;
    }
    .dashboard-container {
        padding: 20px;
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .table-container {
        max-height: 400px;
        overflow-y: auto;
    }
    .download-button {
        display: inline-block;
        background-color: #0066b2;
        color: white;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        border-radius: 4px;
        margin: 10px 0;
        cursor: pointer;
    }
    .download-button:hover {
        background-color: #004c8c;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for storing data
def init_session_state():
    if 'enrollment_data' not in st.session_state:
        st.session_state.enrollment_data = None
    if 'activation_data' not in st.session_state:
        st.session_state.activation_data = None
    if 'monthly_data' not in st.session_state:
        st.session_state.monthly_data = None
    if 'site_data' not in st.session_state:
        st.session_state.site_data = None
    if 'cosl_data' not in st.session_state:
        st.session_state.cosl_data = None
    if 'enrollment_projections' not in st.session_state:
        st.session_state.enrollment_projections = None
    if 'screen_failure_rate' not in st.session_state:
        st.session_state.screen_failure_rate = None
    if 'dashboard_date' not in st.session_state:
        st.session_state.dashboard_date = datetime.now().strftime('%d-%b-%Y')
    if 'dashboard_generated' not in st.session_state:
        st.session_state.dashboard_generated = False

# Main dashboard header
def render_header():
    st.markdown('<h1 class="main-header">Clinical Trial Dashboard</h1>', unsafe_allow_html=True)

# Sidebar for data upload and configuration
def render_sidebar():
    with st.sidebar:
        st.header("Data Upload")
        
        # File upload section
        enrollment_file = st.file_uploader("Upload Enrollment Summary File", type=['xlsx', 'xls', 'csv'], 
                                         help="Upload VX21147301_BLINDED_EnrollmentSummary_*.xlsx")
        
        monthly_file = st.file_uploader("Upload Site Monthly Summary File", type=['xlsx', 'xls', 'csv'],
                                       help="Upload VX21147301_BLINDED_SiteMonthlySummary_*.xlsx")
        
        site_file = st.file_uploader("Upload Site Data File", type=['xlsx', 'xls', 'csv'],
                                   help="Upload data_*.xlsx")
        
        st.write("---")
        
        # Dashboard configuration
        st.header("Configuration")
        target_enrollment = st.number_input("Monthly Enrollment Target", min_value=1, value=10)
        projection_end = st.date_input("Projection End Date", datetime(2025, 9, 30))
        sf_rate_override = st.number_input("Override Screen Failure Rate (%)", min_value=0.0, max_value=100.0, value=0.0, 
                                          help="Enter a value to override the calculated screen failure rate, or leave at 0 to use calculated rate")
        
        generate_button = st.button("Generate Dashboard", key="generate_button")
        
        return enrollment_file, monthly_file, site_file, target_enrollment, projection_end, sf_rate_override, generate_button

# Process uploaded data
def process_data(enrollment_file, monthly_file, site_file, target_enrollment, projection_end, sf_rate_override):
    with st.spinner("Processing data and building dashboard..."):
        try:
            # Load enrollment summary data
            if enrollment_file:
                if enrollment_file.name.endswith('.csv'):
                    enrollment_df = pd.read_csv(enrollment_file)
                else:
                    enrollment_df = pd.read_excel(enrollment_file)
                
                st.session_state.enrollment_data = process_enrollment_data(enrollment_df)
            else:
                st.warning("Enrollment Summary file required")
                return False
            
            # Load monthly site data
            if monthly_file:
                if monthly_file.name.endswith('.csv'):
                    monthly_df = pd.read_csv(monthly_file)
                else:
                    monthly_df = pd.read_excel(monthly_file)
                
                st.session_state.monthly_data = process_monthly_data(monthly_df)
                
                # Extract activation data
                st.session_state.activation_data = extract_activation_data(st.session_state.monthly_data)
            else:
                st.warning("Site Monthly Summary file required")
                return False
            
            # Load site data
            if site_file:
                if site_file.name.endswith('.csv'):
                    site_df = pd.read_csv(site_file)
                else:
                    site_df = pd.read_excel(site_file)
                
                st.session_state.site_data = process_site_data(site_df)
                
                # Update activation dates if available
                update_activation_dates(st.session_state.activation_data, st.session_state.site_data)
            else:
                st.warning("Site Data file required")
                return False
            
            # Generate COSL data
            st.session_state.cosl_data = generate_cosl_data(st.session_state.site_data)
            
            # Calculate screen failure rate
            st.session_state.screen_failure_rate = calculate_screen_failure_rate(
                st.session_state.enrollment_data,
                st.session_state.monthly_data,
                sf_rate_override
            )
            
            # Generate enrollment projections
            st.session_state.enrollment_projections = generate_enrollment_projections(
                st.session_state.enrollment_data,
                target_enrollment,
                projection_end,
                st.session_state.screen_failure_rate
            )
            
            st.session_state.dashboard_generated = True
            st.session_state.dashboard_date = datetime.now().strftime('%d-%b-%Y')
            st.success("Dashboard generated successfully!")
            return True
            
        except Exception as e:
            st.error(f"Error generating dashboard: {str(e)}")
            st.exception(e)
            return False

# Extract activation data from monthly data
def extract_activation_data(monthly_data):
    activation_data = []
    
    # Get unique sites
    sites = monthly_data[['Site ID', 'Site Name', 'Status', 'Country', '1st Screening', '1st Enrollment']].drop_duplicates()
    
    for _, row in sites.iterrows():
        site_id = str(row['Site ID'])
        activation_data.append({
            'Country': row['Country'],
            'Site Number': site_id,
            'Investigator': f"{row.get('PI First Name', '')} {row.get('PI Last Name', '')}".strip(),
            'Site Status': row['Status'],
            'Date of First Screening': row.get('1st Screening'),
            'Date of First Randomization': row.get('1st Enrollment')
        })
    
    return pd.DataFrame(activation_data)

# Update activation dates from site data
def update_activation_dates(activation_data, site_data):
    if activation_data is not None and site_data is not None:
        for _, row in site_data.iterrows():
            site_id = str(row['Site Number'])
            mask = activation_data['Site Number'] == site_id
            
            if any(mask) and pd.notnull(row.get('Site Activated Date')):
                activation_data.loc[mask, 'Date of Activation'] = row['Site Activated Date']

# Render overview metrics at the top of the dashboard
def render_overview_metrics(target_enrollment):
    st.markdown('<h2 class="sub-header">Study Overview</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sites = len(st.session_state.activation_data['Site Number'].unique()) if st.session_state.activation_data is not None else 0
        active_sites = st.session_state.activation_data[st.session_state.activation_data['Site Status'] == 'Active'].shape[0] if st.session_state.activation_data is not None else 0
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_sites}</div>
            <div class="metric-label">Total Sites</div>
            <div class="metric-value">{active_sites}</div>
            <div class="metric-label">Active Sites</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_screened = st.session_state.enrollment_data['Screened'].sum() if 'Screened' in st.session_state.enrollment_data.columns else 0
        total_enrolled = st.session_state.enrollment_data['Randomized'].sum() if 'Randomized' in st.session_state.enrollment_data.columns else 0
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{int(total_screened)}</div>
            <div class="metric-label">Total Screened</div>
            <div class="metric-value">{int(total_enrolled)}</div>
            <div class="metric-label">Total Randomized</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        screen_fail_rate = round(st.session_state.screen_failure_rate, 1) if st.session_state.screen_failure_rate is not None else 0
        screenings_needed = round(target_enrollment / (1 - screen_fail_rate/100)) if screen_fail_rate < 100 else target_enrollment * 5
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{screen_fail_rate}%</div>
            <div class="metric-label">Screen Failure Rate</div>
            <div class="metric-value">{screenings_needed}</div>
            <div class="metric-label">Monthly Screenings Needed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{target_enrollment}</div>
            <div class="metric-label">Target Monthly Enrollment</div>
            <div class="metric-label">Dashboard Last Updated</div>
            <div class="metric-label">{st.session_state.dashboard_date}</div>
        </div>
        """, unsafe_allow_html=True)

# Render instructions when no data is loaded
def render_instructions():
    st.info("Please upload your data files using the sidebar to generate the dashboard.")
    
    st.markdown("""
    ## Getting Started
    
    1. Upload your source files using the sidebar:
       - Enrollment Summary file (VX21147301_BLINDED_EnrollmentSummary_*.xlsx)
       - Site Monthly Summary file (VX21147301_BLINDED_SiteMonthlySummary_*.xlsx)
       - Site Data file (data_*.xlsx)
       
    2. Configure your dashboard settings:
       - Set the monthly enrollment target (default: 10)
       - Set the projection end date (default: September 30, 2025)
       - Optionally override the screen failure rate
       
    3. Click "Generate Dashboard" to process the data and build the visualizations
    
    4. Explore the interactive dashboard and download any tables as needed
    """)

# Main application function
def main():
    # Initialize session state variables
    init_session_state()
    
    # Render header
    render_header()
    
    # Render sidebar and get inputs
    enrollment_file, monthly_file, site_file, target_enrollment, projection_end, sf_rate_override, generate_button = render_sidebar()
    
    # Process data if generate button is clicked
    if generate_button:
        process_data(enrollment_file, monthly_file, site_file, target_enrollment, projection_end, sf_rate_override)
    
    # Main dashboard content
    if st.session_state.dashboard_generated:
        # Render overview metrics
        render_overview_metrics(target_enrollment)
        
        # Create tabs for different dashboard sections
        tabs = st.tabs(["Enrollment Progress", "Site Activation", "COSL Performance", "Screen Failure Analysis"])
        
        # Render individual tabs
        with tabs[0]:
            render_enrollment_tab(
                st.session_state.monthly_data,
                st.session_state.enrollment_data,
                st.session_state.enrollment_projections,
                target_enrollment,
                st.session_state.screen_failure_rate
            )
        
        with tabs[1]:
            render_site_activation_tab(st.session_state.activation_data)
        
        with tabs[2]:
            render_cosl_performance_tab(
                st.session_state.cosl_data,
                st.session_state.activation_data,
                st.session_state.enrollment_data
            )
        
        with tabs[3]:
            render_screening_tab(
                st.session_state.enrollment_data,
                st.session_state.monthly_data
            )
    else:
        # Show instructions if no data loaded yet
        render_instructions()
    
    # Footer
    st.markdown(f"""
    ---
    Dashboard generated on {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}
    """)

if __name__ == "__main__":
    main()
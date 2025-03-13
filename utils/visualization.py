"""
Visualization utilities for the Clinical Trial Dashboard.

This module contains functions for creating charts and plots
using Plotly for the dashboard visualizations.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_line_chart(df, x_col, y_col, title, x_title=None, y_title=None, color=None, color_discrete_map=None):
    """
    Create a line chart using Plotly Express.
    
    Args:
        df (pandas.DataFrame): Data to plot
        x_col (str): Column name for x-axis
        y_col (str or list): Column name(s) for y-axis
        title (str): Chart title
        x_title (str, optional): X-axis title
        y_title (str, optional): Y-axis title
        color (str, optional): Column name for color differentiation
        color_discrete_map (dict, optional): Mapping of categories to colors
        
    Returns:
        plotly.graph_objects.Figure: The created figure
    """
    fig = px.line(
        df, 
        x=x_col, 
        y=y_col, 
        title=title,
        color=color,
        color_discrete_map=color_discrete_map
    )
    
    fig.update_layout(
        xaxis_title=x_title or x_col,
        yaxis_title=y_title or y_col
    )
    
    return fig

def create_bar_chart(df, x_col, y_col, title, x_title=None, y_title=None, color=None, barmode='group'):
    """
    Create a bar chart using Plotly Express.
    
    Args:
        df (pandas.DataFrame): Data to plot
        x_col (str): Column name for x-axis
        y_col (str or list): Column name(s) for y-axis
        title (str): Chart title
        x_title (str, optional): X-axis title
        y_title (str, optional): Y-axis title
        color (str, optional): Column name for color differentiation
        barmode (str, optional): Mode for bars ('group', 'stack', 'relative')
        
    Returns:
        plotly.graph_objects.Figure: The created figure
    """
    fig = px.bar(
        df, 
        x=x_col, 
        y=y_col, 
        title=title,
        color=color,
        barmode=barmode
    )
    
    fig.update_layout(
        xaxis_title=x_title or x_col,
        yaxis_title=y_title or y_col
    )
    
    return fig

def create_pie_chart(df, names_col, values_col, title, color=None, hole=0.4):
    """
    Create a pie chart using Plotly Express.
    
    Args:
        df (pandas.DataFrame): Data to plot
        names_col (str): Column name for segment names
        values_col (str): Column name for values
        title (str): Chart title
        color (str, optional): Column name for color differentiation
        hole (float, optional): Size of center hole (0-1, 0 for pie, >0 for donut)
        
    Returns:
        plotly.graph_objects.Figure: The created figure
    """
    fig = px.pie(
        df, 
        names=names_col, 
        values=values_col, 
        title=title,
        color=color,
        hole=hole
    )
    
    # Adjust text position and info
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_histogram(df, x_col, title, nbins=20, color=None):
    """
    Create a histogram using Plotly Express.
    
    Args:
        df (pandas.DataFrame): Data to plot
        x_col (str): Column name for x-axis
        title (str): Chart title
        nbins (int, optional): Number of bins
        color (str, optional): Column name for color differentiation
        
    Returns:
        plotly.graph_objects.Figure: The created figure
    """
    fig = px.histogram(
        df, 
        x=x_col, 
        title=title,
        nbins=nbins,
        color=color
    )
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title='Count'
    )
    
    return fig

def create_scatter_chart(df, x_col, y_col, title, color=None, size=None, hover_name=None):
    """
    Create a scatter plot using Plotly Express.
    
    Args:
        df (pandas.DataFrame): Data to plot
        x_col (str): Column name for x-axis
        y_col (str): Column name for y-axis
        title (str): Chart title
        color (str, optional): Column name for color differentiation
        size (str, optional): Column name for point size
        hover_name (str, optional): Column name for hover labels
        
    Returns:
        plotly.graph_objects.Figure: The created figure
    """
    fig = px.scatter(
        df, 
        x=x_col, 
        y=y_col, 
        title=title,
        color=color,
        size=size,
        hover_name=hover_name
    )
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col
    )
    
    return fig

def create_combined_chart(df_actual, df_projected, title):
    """
    Create a combined line and bar chart for enrollment data.
    Shows actual vs. projected enrollment with bars for monthly values.
    
    Args:
        df_actual (pandas.DataFrame): Actual enrollment data
        df_projected (pandas.DataFrame): Projected enrollment data
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: The created figure
    """
    # Create subplot with shared x-axis and secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add actual enrollment line
    fig.add_trace(
        go.Scatter(
            x=df_actual['Month'],
            y=df_actual['Cumulative Randomized'],
            mode='lines+markers',
            name='Actual Cumulative',
            line=dict(color='#0066b2', width=3)
        ),
        secondary_y=False
    )
    
    # Add enrollment projection line
    fig.add_trace(
        go.Scatter(
            x=df_projected['Month'],
            y=df_projected['Cumulative Target'],
            mode='lines+markers',
            name='Target Cumulative',
            line=dict(color='#FF7F0E', width=3, dash='dash')
        ),
        secondary_y=False
    )
    
    # Add monthly bars on secondary axis
    fig.add_trace(
        go.Bar(
            x=df_actual['Month'],
            y=df_actual['Monthly Randomized'],
            name='Monthly Randomized',
            marker_color='#2CA02C'
        ),
        secondary_y=True
    )
    
    # Add projection bars
    fig.add_trace(
        go.Bar(
            x=df_projected['Month'],
            y=df_projected['Target Randomizations'],
            name='Monthly Target',
            marker_color='rgba(255, 127, 14, 0.5)'
        ),
        secondary_y=True
    )
    
    # Layout
    fig.update_layout(
        title=title,
        xaxis=dict(title='Month'),
        yaxis=dict(title='Cumulative Enrollment'),
        yaxis2=dict(title='Monthly Enrollment', showgrid=False),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=500
    )
    
    return fig
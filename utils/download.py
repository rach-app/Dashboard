"""
Download utilities for the Clinical Trial Dashboard.

This module contains functions for generating download links
for data tables and visualizations.
"""

import base64
import pandas as pd
import io

def get_table_download_link(df, filename, button_text):
    """
    Generate a download link for a DataFrame.
    
    Args:
        df (pandas.DataFrame): Data to be downloaded
        filename (str): Name of the file without extension
        button_text (str): Text to display on the download button
        
    Returns:
        str: HTML for download link
    """
    # Convert DataFrame to CSV
    csv = df.to_csv(index=False)
    
    # Base64 encode
    b64 = base64.b64encode(csv.encode()).decode()
    
    # Generate HTML link
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv" class="download-button">{button_text}</a>'
    
    return href

def get_excel_download_link(df_dict, filename, button_text):
    """
    Generate a download link for multiple DataFrames as Excel file with multiple sheets.
    
    Args:
        df_dict (dict): Dictionary mapping sheet names to DataFrames
        filename (str): Name of the file without extension
        button_text (str): Text to display on the download button
        
    Returns:
        str: HTML for download link
    """
    # Create a BytesIO object
    output = io.BytesIO()
    
    # Use pandas ExcelWriter to write multiple sheets
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Get binary data
    excel_data = output.getvalue()
    
    # Base64 encode
    b64 = base64.b64encode(excel_data).decode()
    
    # Generate HTML link
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx" class="download-button">{button_text}</a>'
    
    return href

def get_pdf_download_link(fig, filename, button_text):
    """
    Generate a download link for a Plotly figure as PDF.
    Note: This requires kaleido package to be installed.
    
    Args:
        fig (plotly.graph_objects.Figure): Plotly figure to be downloaded
        filename (str): Name of the file without extension
        button_text (str): Text to display on the download button
        
    Returns:
        str: HTML for download link
    """
    try:
        # Generate PDF bytes
        img_bytes = fig.to_image(format="pdf")
        
        # Base64 encode
        b64 = base64.b64encode(img_bytes).decode()
        
        # Generate HTML link
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}.pdf" class="download-button">{button_text}</a>'
        
        return href
    except Exception as e:
        # Fallback if kaleido is not installed
        return f'<div class="download-button" style="opacity: 0.5; cursor: not-allowed;">{button_text} (PDF export requires kaleido)</div>'

def get_image_download_link(fig, filename, button_text, format="png"):
    """
    Generate a download link for a Plotly figure as an image.
    Note: This requires kaleido package to be installed.
    
    Args:
        fig (plotly.graph_objects.Figure): Plotly figure to be downloaded
        filename (str): Name of the file without extension
        button_text (str): Text to display on the download button
        format (str): Image format (png, jpg, svg)
        
    Returns:
        str: HTML for download link
    """
    try:
        # Generate image bytes
        img_bytes = fig.to_image(format=format)
        
        # Base64 encode
        b64 = base64.b64encode(img_bytes).decode()
        
        # Set correct MIME type
        mime_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "svg": "image/svg+xml"
        }
        mime_type = mime_types.get(format.lower(), "image/png")
        
        # Generate HTML link
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}.{format}" class="download-button">{button_text}</a>'
        
        return href
    except Exception as e:
        # Fallback if kaleido is not installed
        return f'<div class="download-button" style="opacity: 0.5; cursor: not-allowed;">{button_text} (Image export requires kaleido)</div>'
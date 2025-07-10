import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Define main service centers
main_centers = ['MM-1.Care-MSC-Yangon-Hledan', 'MM-1.Care-MSC-Mandalay-35street', 'MM-1.Care-MSC-MawLaMyine']

# Function to analyze duration distribution for a center
def get_center_duration_analysis(data):
    duration_bins = [0, 3, 5, 10, 15, 30, 50, float('inf')]
    duration_labels = ['0-3', '3-5', '5-10', '10-15', '15-30', '30-50', '50+']
    
    data['Duration_Bracket'] = pd.cut(data['pending_duration'], 
                                  bins=duration_bins, 
                                  labels=duration_labels, 
                                  right=False)
    
    analysis = data['Duration_Bracket'].value_counts().reset_index()
    analysis.columns = ['Duration (Days)', 'Count']
    analysis['Percentage'] = (analysis['Count'] / len(data) * 100).round(1)
    analysis['Percentage'] = analysis['Percentage'].apply(lambda x: f'{x}%')
    return analysis

def main():
    # Set full width for the page
    st.set_page_config(layout="wide")
    st.title("📊 Xiaomi Job Analysis Dashboard")

    # File uploader for Excel files
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        # --- 1) Read Excel & Show Data ---
        df = pd.read_excel(uploaded_file)

        # Calculate pending duration using today's date for open orders
        today = datetime.now()
        df['pending_duration'] = (today - pd.to_datetime(df['Creation Time'])).dt.days

        with st.expander("Preview of the uploaded data", expanded=False):
            st.dataframe(df)
            
        # Create pending duration brackets
        duration_bins = [0, 3, 5, 10, 15, 30, 50, float('inf')]
        duration_labels = ['0-3', '3-5', '5-10', '10-15', '15-30', '30-50', '50+']
        
        df['Duration_Bracket'] = pd.cut(df['pending_duration'], 
                                      bins=duration_bins, 
                                      labels=duration_labels, 
                                      right=False)
        
        # Calculate counts and percentages
        duration_counts = df['Duration_Bracket'].value_counts().reset_index()
        duration_counts.columns = ['Duration_Bracket', 'Count']
        duration_counts['Percentage'] = (duration_counts['Count'] / len(df) * 100).round(1)
        
        # Display overall data in a table format
        st.subheader('Repairs by Pending Duration')
        
        # Create three columns with equal width for better layout
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            with st.expander('Overall Distribution', expanded=True):
                duration_counts['Percentage'] = duration_counts['Percentage'].apply(lambda x: f'{x}%')
                duration_counts.columns = ['Duration (Days)', 'Count', 'Percentage']
                st.table(duration_counts)

        # Analyze main centers in columns
        for i, center in enumerate(main_centers):
            center_data = df[df['服务网点'] == center]
            if len(center_data) > 0:
                with [col2, col3, col1][i % 3]:
                    # st.write(f"### {center}")
                    with st.expander(f"{center}", expanded=True):
                        center_analysis = get_center_duration_analysis(center_data)
                        st.table(center_analysis)

        # Analyze other centers
        other_centers_data = df[~df['服务网点'].isin(main_centers)]
        if len(other_centers_data) > 0:
            with col2:
                with st.expander('Other Centers', expanded=True):
                    other_centers_analysis = get_center_duration_analysis(other_centers_data)
                    st.table(other_centers_analysis)



if __name__ == "__main__":
    main()

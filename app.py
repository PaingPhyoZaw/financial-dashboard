import streamlit as st
import pandas as pd
from datetime import datetime

# Define main service centers
main_centers = ['MM-1.Care-MSC-Yangon-Hledan', 'MM-1.Care-MSC-Mandalay-35street', 'MM-1.Care-MSC-MawLaMyine']

def get_center_duration_analysis(data):
    duration_bins = [0, 3, 5, 10, 15, 30, 50, float('inf')]
    duration_labels = ['0-3', '3-5', '5-10', '10-15', '15-30', '30-50', '50+']
    
    data['Duration_Bracket'] = pd.cut(data['pending_duration'], 
                                   bins=duration_bins, 
                                   labels=duration_labels, 
                                   right=False)
    
    analysis = pd.DataFrame({'Duration (Days)': duration_labels})
    counts = data['Duration_Bracket'].value_counts().reset_index()
    counts.columns = ['Duration (Days)', 'Count']
    
    analysis = analysis.merge(counts, how='left', left_on='Duration (Days)', right_on='Duration (Days)')
    analysis['Count'] = analysis['Count'].fillna(0).astype(int)
    analysis['Percentage'] = (analysis['Count'] / len(data) * 100).round(1)
    analysis['Percentage'] = analysis['Percentage'].apply(lambda x: f'{x}%')
    
    return analysis

def main():
    st.set_page_config(layout="wide")
    st.title("📊 Xiaomi Job Analysis Dashboard")

    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        today = datetime.now()
        df['pending_duration'] = (today - pd.to_datetime(df['Creation Time'])).dt.days

        with st.expander("Preview of the uploaded data", expanded=False):
            st.dataframe(df)

        # Add Service Center Summary Section
        st.subheader("📋 Service Center Summary")
        
        # Get all service centers and their job counts
        center_counts = df['服务网点'].value_counts().reset_index()
        center_counts.columns = ['Service Center', 'Total Jobs']
        total_jobs = len(df)
        
        # Separate main centers and other centers
        main_centers_data = center_counts[center_counts['Service Center'].isin(main_centers)]
        other_centers_data = center_counts[~center_counts['Service Center'].isin(main_centers)]
        other_centers_total = other_centers_data['Total Jobs'].sum()
        
        # Create columns for the summary cards
        cols = st.columns(5)
        
        # Total Jobs card
        with cols[0]:
            st.metric(label="📦 Total Jobs", value=total_jobs)
        
        # Main centers cards
        for i in range(min(3, len(main_centers_data))):
            with cols[i+1]:
                center_name = main_centers_data.iloc[i]['Service Center']
                count = main_centers_data.iloc[i]['Total Jobs']
                percentage = (count / total_jobs * 100)
                st.metric(
                    label=f"🏢 {center_name}{'...' if len(center_name)>15 else ''}",
                    value=count,
                    delta=f"{percentage:.1f}% of total"
                )
        
        # Other centers card
        with cols[4]:
            percentage = (other_centers_total / total_jobs * 100)
            st.metric(
                label="🏢 Other Centers",
                value=other_centers_total,
                delta=f"{percentage:.1f}% of total"
            )
        
        # Show full center distribution in an expander
        with st.expander("View All Service Centers", expanded=False):
            # Combine all centers with type indicator
            main_centers_data['Type'] = 'Main Center'
            other_centers_data['Type'] = 'Other Center'
            all_centers = pd.concat([main_centers_data, other_centers_data])
            
            # Add percentage column
            all_centers['Percentage'] = (all_centers['Total Jobs'] / total_jobs * 100).round(1)
            all_centers['Percentage'] = all_centers['Percentage'].astype(str) + '%'
            
            # Sort by job count
            all_centers = all_centers.sort_values('Total Jobs', ascending=False)
            
            # Display with nice formatting
            st.dataframe(
                all_centers,
                column_config={
                    "Service Center": st.column_config.TextColumn("Service Center"),
                    "Total Jobs": st.column_config.NumberColumn("Total Jobs"),
                    "Percentage": st.column_config.TextColumn("Percentage"),
                    "Type": st.column_config.TextColumn("Center Type")
                },
                use_container_width=True
            )

        # Rest of your existing code...
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.subheader('⏳ Repairs by Pending Duration')

        with col2:    
            # Add warranty status filter
            warranty_options = ['All', 'IW', 'OOW']
            selected_warranty = st.selectbox("Warranty Filter", warranty_options)
            
        with col3:
            # Add service type filter with dynamic options
            if selected_warranty == 'OOW':
                service_options = ['All', 'Repair']
            else:
                service_options = ['All', 'Repair', 'Inspection']
            
            selected_service = st.selectbox("Service Type Filter", service_options)
            
        # Filter data based on selections
        filtered_df = df.copy()
        
        if selected_warranty != 'All':
            filtered_df = filtered_df[filtered_df['保内/保外'] == selected_warranty]
            
        if selected_service != 'All':
            filtered_df = filtered_df[filtered_df['Service Type'] == selected_service]
                
        duration_bins = [0, 3, 5, 10, 15, 30, 50, float('inf')]
        duration_labels = ['0-3', '3-5', '5-10', '10-15', '15-30', '30-50', '50+']
        
        filtered_df['Duration_Bracket'] = pd.cut(filtered_df['pending_duration'], 
                                            bins=duration_bins, 
                                            labels=duration_labels, 
                                            right=False)
            
        # Calculate counts with the filtered data
        duration_counts = pd.DataFrame({'Duration (Days)': duration_labels})
        counts = filtered_df['Duration_Bracket'].value_counts().reset_index()
        counts.columns = ['Duration (Days)', 'Count']
        
        duration_counts = duration_counts.merge(counts, how='left', on='Duration (Days)')
        duration_counts['Count'] = duration_counts['Count'].fillna(0).astype(int)
        duration_counts['Percentage'] = (duration_counts['Count'] / len(filtered_df) * 100).round(1)
        duration_counts['Percentage'] = duration_counts['Percentage'].apply(lambda x: f'{x}%')
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            with st.expander('Overall Distribution', expanded=True):
                st.table(duration_counts)
                
                # Add clickable counts for Overall Distribution
                selected_duration = st.selectbox(
                    "View jobs for duration:",
                    options=duration_labels,
                    key="overall_duration_select"
                )
                
                if selected_duration:
                    duration_jobs = filtered_df[filtered_df['Duration_Bracket'] == selected_duration]
                    st.dataframe(duration_jobs[['Service Order Number', 'Creation Time', 'Service Order Status', 'Engineer', '保内/保外', 'Picking Parts Status', 'Service Type']])
        
        # Analyze main centers with filtered data
        for i, center in enumerate(main_centers):
            center_data = filtered_df[filtered_df['服务网点'] == center]
            if len(center_data) > 0:
                with [col2, col3, col1][i % 3]:
                    with st.expander(f"{center}", expanded=True):
                        center_analysis = get_center_duration_analysis(center_data)
                        st.table(center_analysis)
                        
                        # Add clickable counts for each center
                        center_selected_duration = st.selectbox(
                            f"View {center} jobs for duration:",
                            options=duration_labels,
                            key=f"{center}_duration_select"
                        )
                        
                        if center_selected_duration:
                            center_duration_jobs = center_data[center_data['Duration_Bracket'] == center_selected_duration]
                            st.dataframe(center_duration_jobs[['Service Order Number', 'Creation Time', 'Service Order Status', 'Engineer', '保内/保外', 'Picking Parts Status', 'Service Type']])

        # Analyze other centers with filtered data
        other_centers_data = filtered_df[~filtered_df['服务网点'].isin(main_centers)]
        if len(other_centers_data) > 0:
            with col2:
                with st.expander('Other Centers', expanded=False):
                    other_centers_analysis = get_center_duration_analysis(other_centers_data)
                    st.table(other_centers_analysis)
                    
                    # Add clickable counts for Other Centers
                    other_selected_duration = st.selectbox(
                        "View Other Centers jobs for duration:",
                        options=duration_labels,
                        key="other_duration_select"
                    )
                    
                    if other_selected_duration:
                        other_duration_jobs = other_centers_data[other_centers_data['Duration_Bracket'] == other_selected_duration]
                        st.dataframe(other_duration_jobs[['Service Order Number', 'Creation Time','服务网点', 'Service Order Status', 'Engineer', '保内/保外', 'Picking Parts Status', 'Service Type']])

if __name__ == "__main__":
    main()
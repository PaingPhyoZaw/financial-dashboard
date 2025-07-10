import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO

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

def get_status_analysis(data):
    status_counts = data['Service Order Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    status_counts['Percentage'] = (status_counts['Count'] / len(data) * 100).round(1)
    status_counts['Percentage'] = status_counts['Percentage'].apply(lambda x: f'{x}%')
    return status_counts

def main():
    st.set_page_config(layout="wide")
    st.title("📊 Xiaomi Service Center Dashboard")

    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        today = datetime.now()
        df['pending_duration'] = (today - pd.to_datetime(df['Creation Time'])).dt.days
        df['Duration (Days)'] = df['pending_duration'].astype(str) + " days"

        with st.expander("📂 Preview of the uploaded data", expanded=False):
            st.dataframe(df)

        # ========== SERVICE CENTER SUMMARY SECTION ==========
        st.subheader("📋 Service Center Overview")
        
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
        
        # Show full center distribution
        with st.expander("🔍 View All Service Centers", expanded=False):
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

        # ========== FILTER SECTION ==========
        st.subheader("🔧 Filters")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:    
            # Add warranty status filter
            warranty_options = ['All', 'IW', 'OOW']
            selected_warranty = st.selectbox("Warranty Status", warranty_options)
            
        with col2:
            # Add service type filter with dynamic options
            if selected_warranty == 'OOW':
                service_options = ['All', 'Repair']
            else:
                service_options = ['All', 'Repair', 'Inspection']
            
            selected_service = st.selectbox("Service Type", service_options)
            
        with col3:
            # Add center filter
            center_options = ['All'] + sorted(df['服务网点'].unique().tolist())
            selected_center = st.selectbox("Service Center", center_options)

        with col4:
            # Add Picking Parts Status filter
            parts_status_options = ['All'] + sorted(df['Picking Parts Status'].dropna().unique().tolist())
            selected_parts_status = st.selectbox("Picking Parts Status", parts_status_options)
            
        # Filter data based on selections
        filtered_df = df.copy()
        
        if selected_warranty != 'All':
            filtered_df = filtered_df[filtered_df['保内/保外'] == selected_warranty]
            
        if selected_service != 'All':
            filtered_df = filtered_df[filtered_df['Service Type'] == selected_service]
            
        if selected_center != 'All':
            filtered_df = filtered_df[filtered_df['服务网点'] == selected_center]

        if selected_parts_status != 'All':
            filtered_df = filtered_df[filtered_df['Picking Parts Status'] == selected_parts_status]

        # ========== DURATION ANALYSIS SECTION ==========
        st.subheader("⏳ Pending Duration Analysis")
        
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
        
        # Visualizations
        tab1, tab2 = st.tabs(["📊 Data Table", "📈 Visualization"])
        
        with tab1:
            # Overall distribution
            with st.expander('Overall Distribution', expanded=True):
                st.table(duration_counts)
                
                selected_duration = st.selectbox(
                    "View jobs for duration:",
                    options=duration_labels,
                    key="overall_duration_select"
                )
                
                if selected_duration:
                    duration_jobs = filtered_df[filtered_df['Duration_Bracket'] == selected_duration]
                    st.dataframe(duration_jobs[['Service Order Number', 'Creation Time', 'Service Order Status', 
                                              'Engineer', '保内/保外', 'Picking Parts Status', 'Service Type', 
                                              'Engineer Comments On Completion', 'Duration (Days)']])
            
            # Center-specific analysis in separate columns
            st.write("### Center-Specific Analysis")
            cols = st.columns(len(main_centers) + 1)
            
            # Main centers analysis
            for i, center in enumerate(main_centers):
                with cols[i]:
                    center_data = filtered_df[filtered_df['服务网点'] == center]
                    if len(center_data) > 0:
                        with st.expander(f"{center}", expanded=False):
                            center_analysis = get_center_duration_analysis(center_data)
                            st.table(center_analysis)
                            
                            center_selected_duration = st.selectbox(
                                f"View {center} jobs:",
                                options=duration_labels,
                                key=f"{center}_duration_select"
                            )
                            
                            if center_selected_duration:
                                center_duration_jobs = center_data[center_data['Duration_Bracket'] == center_selected_duration]
                                st.dataframe(center_duration_jobs[['Service Order Number', 'Creation Time', 'Service Order Status', 
                                                                 'Engineer', '保内/保外', 'Picking Parts Status', 'Service Type', 
                                                                 'Engineer Comments On Completion', 'Duration (Days)']])
            
            # Other centers analysis
            with cols[-1]:
                other_centers_data = filtered_df[~filtered_df['服务网点'].isin(main_centers)]
                if len(other_centers_data) > 0:
                    with st.expander('Other Centers', expanded=False):
                        other_centers_analysis = get_center_duration_analysis(other_centers_data)
                        st.table(other_centers_analysis)
                        
                        other_selected_duration = st.selectbox(
                            "View Other Centers jobs:",
                            options=duration_labels,
                            key="other_duration_select"
                        )
                        
                        if other_selected_duration:
                            other_duration_jobs = other_centers_data[other_centers_data['Duration_Bracket'] == other_selected_duration]
                            st.dataframe(other_duration_jobs[['Service Order Number', 'Creation Time','服务网点', 'Service Order Status', 
                                                            'Engineer', '保内/保外', 'Picking Parts Status', 'Service Type', 
                                                            'Engineer Comments On Completion', 'Duration (Days)']])
        
        with tab2:
            # Duration distribution chart
            fig = px.bar(
                duration_counts,
                x='Duration (Days)',
                y='Count',
                title='Pending Duration Distribution',
                color='Duration (Days)',
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            st.plotly_chart(fig, use_container_width=True)

        # ========== STATUS ANALYSIS SECTION ==========
        st.subheader("📌 Service Order Status Analysis")
        
        status_tab1, status_tab2 = st.tabs(["By Center", "Overall"])
        
        with status_tab1:
            # Status by center analysis
            st.write("### Status Distribution by Service Center")
            
            # Get all centers with data
            centers_with_data = filtered_df['服务网点'].unique()
            
            for center in centers_with_data:
                center_data = filtered_df[filtered_df['服务网点'] == center]
                status_counts = get_status_analysis(center_data)
                
                with st.expander(f"{center} ({len(center_data)} jobs)", expanded=False):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.table(status_counts)
                    
                    with col2:
                        fig = px.pie(
                            status_counts,
                            names='Status',
                            values='Count',
                            title=f'Status Distribution - {center}',
                            hole=0.3
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        with status_tab2:
            # Overall status analysis
            st.write("### Overall Status Distribution")
            overall_status = get_status_analysis(filtered_df)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.table(overall_status)
            
            with col2:
                fig = px.pie(
                    overall_status,
                    names='Status',
                    values='Count',
                    title='Overall Status Distribution',
                    hole=0.3
                )
                st.plotly_chart(fig, use_container_width=True)

        # ========== EXPORT SECTION ==========
        st.subheader("💾 Export Reports")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name=f"service_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
        
        with export_col2:
            # Fix for Excel export error
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False)
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Download Full Report (Excel)",
                data=excel_data,
                file_name=f"full_service_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

if __name__ == "__main__":
    main()
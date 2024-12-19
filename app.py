import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import calendar
import openpyxl
import os

# Function to load data from an Excel file
def load_data(file_path, sheet_name):
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    except ValueError:  # Handle case where the sheet does not exist
        st.warning(f"Sheet '{sheet_name}' not found in {file_path}. Proceeding without it.")
        return pd.DataFrame()  # Return an empty DataFrame

# Sidebar navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose an option", ["Month-wise Summary","Month-wise Analytics", "Compare All Months"])

if app_mode == "Month-wise Summary":
    selected_month = st.selectbox(
        "Select Month:",
        options=calendar.month_name[1:],
        index=4  # Default to 'May'
    )

    # Define file path based on selected month
    file_path = f'{selected_month}.xlsx'

    sheet_name_loop = 'Loop Tasks'
    sheet_name_sprint = 'Sprint Tasks'

    # Load data from sheets
    df_sprint = load_data(file_path, sheet_name_sprint)
    df_loop = load_data(file_path, sheet_name_loop)

    # Ensure there are no leading or trailing spaces in column names
    if not df_loop.empty:
        df_loop.columns = df_loop.columns.str.strip()
    if not df_sprint.empty:
        df_sprint.columns = df_sprint.columns.str.strip()

    # Filter completed tasks
    if not df_sprint.empty:
        completed_tasks_sprint = df_sprint[df_sprint['Status'] == 'Done']
    if not df_loop.empty:
        completed_tasks_loop = df_loop[df_loop['Status'] == 'Done']

    # Combine both Sprint and Loop data for overall task management
    df = pd.concat([df_loop, df_sprint], ignore_index=True)

    # Proceed with the rest of the processing only if df is not empty
    if not df.empty:
        # Summary Metrics Section
        st.write("### Summary Metrics")
        total_tasks = len(df)
        completed_count = len(df[df['Status'] == 'Done'])
        pending_count = len(df[df['Status'] != 'Done'])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", total_tasks)
        col2.metric("Completed Tasks", completed_count)
        col3.metric("Pending Tasks", pending_count)


        # Completed Task Types Section
        st.write("### Completed Task Types")
        task_types = df[df["Status"] == "Done"]["Issue Type"].value_counts().reset_index()
        task_types.columns = ["Task Type", "Count"]

        fig = px.bar(task_types, x="Task Type", y="Count", 
                    title="Completed Task Types", 
                    labels={"Count": "Number of Tasks", "Task Type": "Type"},
                    color="Count",
                    color_continuous_scale="Blues")
        st.plotly_chart(fig)


        # Top Contributors Section
        st.write("### Top Contributors")
        top_contributors = df[df["Status"] == "Done"]["Assignee"].value_counts().reset_index()
        top_contributors.columns = ["Assignee", "Count"]

        fig3 = px.bar(top_contributors, x="Assignee", y="Count", 
                    title="Top Contributors (Completed Tasks)", 
                    labels={"Count": "Number of Tasks", "Assignee": "Contributor"},
                    color="Count",
                    color_continuous_scale="Greens")
        st.plotly_chart(fig3)

        # Filter by Assignee Section
        st.write("### Filter by Assignee")
        assignee = st.selectbox("Select an Assignee", options=df["Assignee"].dropna().unique())

        assignee_tasks = df[df["Assignee"] == assignee]
        assignee_tasks_completed = assignee_tasks[assignee_tasks["Status"] == "Done"]
        assignee_tasks_pending = assignee_tasks[assignee_tasks["Status"] != "Done"]

        # Display task counts for the selected assignee
        completed_count = len(assignee_tasks_completed)
        pending_count = len(assignee_tasks_pending)
        total_count = len(assignee_tasks)

        st.write(f"**Summary for {assignee}:**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", total_count)
        col2.metric("Completed Tasks", completed_count)
        col3.metric("Pending Tasks", pending_count)

        # Task Breakdown by Status for the Selected Assignee
        st.subheader(f"Task Status Breakdown for {assignee}")
        if not assignee_tasks.empty:
            task_status_breakdown = assignee_tasks["Status"].value_counts().reset_index()
            task_status_breakdown.columns = ["Status", "Count"]

            fig = px.bar(task_status_breakdown, x="Status", y="Count",
                        title=f"Task Status Breakdown for {assignee}",
                        labels={"Count": "Number of Tasks", "Status": "Task Status"},
                        color="Count",
                        color_continuous_scale="Reds")
            st.plotly_chart(fig)


        # Pending Task Details Section
        st.write("### Pending Task Details")
        if not assignee_tasks_pending.empty:
            st.write("#### Pending Tasks")
            st.dataframe(assignee_tasks_pending[["Summary", "Issue Type", "Status", "Date"]])
        else:
            st.write(f"No pending tasks for {assignee}.")

        # Completed Task Details Section
        st.write("#### Completed Task Details")
        if not assignee_tasks_completed.empty:
            st.write("### Completed Tasks")
            st.dataframe(assignee_tasks_completed[["Summary", "Issue Type", "Status", "Date"]])
        else:
            st.write(f"No completed tasks for {assignee}.")

# Month-wise Analytics Section
elif app_mode == "Month-wise Analytics":
    selected_month = st.selectbox(
        "Select Month:",
        options=calendar.month_name[1:],
        index=4  # Default to 'May'
    )

    # Define file path based on selected month
    file_path = f'{selected_month}.xlsx'

    sheet_name_loop = 'Loop Tasks'
    sheet_name_sprint = 'Sprint Tasks'

    # Load data from sheets
    df_sprint = load_data(file_path, sheet_name_sprint)
    df_loop = load_data(file_path, sheet_name_loop)

    # Ensure there are no leading or trailing spaces in column names
    if not df_loop.empty:
        df_loop.columns = df_loop.columns.str.strip()
    if not df_sprint.empty:
        df_sprint.columns = df_sprint.columns.str.strip()

    # Filter completed tasks
    if not df_sprint.empty:
        done_tasks_sprint = df_sprint[df_sprint['Status'] == 'Done']

    # Extract first word function
    def extract_first_word(text):
        return text.split()[0] if isinstance(text, str) else None

    # Apply the function to each row in the 'Assignee' column
    if not df_sprint.empty:
        df_sprint['Assignee'] = df_sprint['Assignee'].apply(extract_first_word)

    # Rename columns
    new_column_names = {'Assignee': 'Resource Name', 'Created': 'Date', "Summary": "Tasks List"}
    if not df_sprint.empty:
        df_sprint = df_sprint.rename(columns=new_column_names)

    # Add a column to denote task type
    if not df_loop.empty:
        df_loop['Tasks Type'] = "Loop"
    if not df_sprint.empty:
        df_sprint['Tasks Type'] = "Sprint"

    # Concatenate the DataFrames
    df = pd.concat([df_loop, df_sprint], ignore_index=True)

    # Proceed with the rest of the processing only if df is not empty
    if not df.empty:
        df['Resource Name'] = df['Resource Name'].str.strip()
        replace_dict = {
            'V': 'Thota', 
            'SaradhiMuneendra': 'Saradhi',
            'SaradhiMuneendra Gundabattina': 'Saradhi',
            'Saradhi Muneendra Gundabattina': 'Saradhi',
            "Palaniyappan": "Palan",
            "Achyut Deshpande": "Achyut",
            "Ajay kumar": "Ajay Kumar",
            "Ajay": "Ajay Kumar",
            'Sai': 'Sai Sampath Chinthavatla',
            'Amitabh': 'Amitabh Sharma',
            "Sneha": "Sneha Guthe",
            'MS Manoj Singh': 'Manoj Singh',
            "Somesh": "Somesh Fengade",
            "Gopal": 'Gopalswamy Ramalingam',
            'Naveen Adusumilli': 'Naveen',
            "Manoj Singh Rawat": "Manoj Singh",
            "Manoj": "Manoj Singh",
            "Varad": "Varad Bhalsing",
            "Varad Balasaheb Bhalsing": "Varad Bhalsing",
            "Mahesh Katti": "Mahesh"
        }
        df['Resource Name'] = df['Resource Name'].replace(replace_dict)

        # Sidebar dropdown for selecting resources
        selected_person = st.selectbox(
            'Select a person:',
            options=['All'] + list(df['Resource Name'].unique()),
            index=0  # Default to 'All'
        )

        # Filter DataFrame based on selected person
        if selected_person != 'All':
            df = df[df['Resource Name'] == selected_person]

        # Task Status Distribution for Each Resource
        fig_resource_status = px.bar(
            df.groupby(['Resource Name', 'Status']).size().unstack(fill_value=0),
            barmode='stack',
            title="Task Status Distribution for Each Resource"
        )
        st.plotly_chart(fig_resource_status)

        # Task Type distribution for the selected person
        fig_task_type = px.histogram(
            df, x='Tasks Type', title=f'Task Type Distribution for {selected_person}')
        st.plotly_chart(fig_task_type)

        # Resource Task Load Over Time
        fig_tasks_over_time = px.line(
            df.groupby(['Date', 'Resource Name']).size().reset_index(name='Task Count'),
            x='Date', y='Task Count', color='Resource Name',
            title='Resource Task Load Over Time'
        )
        st.plotly_chart(fig_tasks_over_time)

        # Heatmap of Task Completions by Date
        completion_counts = df[df['Status'] == 'Done'].groupby('Date').size().reset_index(name='Completions')
        completion_counts['Date'] = pd.to_datetime(completion_counts['Date'])
        completion_matrix = completion_counts.pivot_table(
            index=completion_counts['Date'].dt.month,
            columns=completion_counts['Date'].dt.day,
            values='Completions', aggfunc='sum'
        )
        fig_heatmap = px.imshow(
            completion_matrix,
            labels=dict(x="Day of the Month", y="Month", color="Task Completions"),
            title="Heatmap of Task Completions by Date"
        )
        st.plotly_chart(fig_heatmap)

        # Task Assignment and Completion Status
        fig_task_assignment = px.bar(
            df.groupby(['Resource Name', 'Status']).size().unstack(fill_value=0),
            barmode='stack',
            title="Task Assignment and Completion Status"
        )
        st.plotly_chart(fig_task_assignment)

        # Details of Uncompleted Tasks
        uncompleted_tasks = df[df['Status'] != 'Done']

        grouped_incomplete_tasks = uncompleted_tasks.groupby('Resource Name')['Tasks List'].apply(lambda x: ', '.join(x)).reset_index()

        # Split concatenated tasks into individual tasks and convert to set to get unique tasks for each resource
        grouped_incomplete_tasks['Unique Incomplete Tasks'] = grouped_incomplete_tasks['Tasks List'].apply(lambda x: set(task.strip() for task in x.split(',')))

        grouped_incomplete_tasks.drop(columns=['Tasks List'], inplace=True)

        st.write("### Uncompleted Tasks", grouped_incomplete_tasks)

        # Completed Tasks Over Time for Each Resource
        fig_completion_by_resources = px.scatter(df, x='Tasks List', y='Resource Name',
                                                color='Resource Name',
                                                hover_data=['Tasks List', 'Resource Name', 'Date'],
                                                title='Task Completion by Resources')
        st.plotly_chart(fig_completion_by_resources)




else:
    # Get the directory where the code file resides
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Function to load data from an Excel file
    def load_data(file_path, sheet_name):
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
        except ValueError:  # Handle case where the sheet does not exist
            st.warning(f"Sheet '{sheet_name}' not found in {file_path}. Proceeding without it.")
            return pd.DataFrame()  # Return an empty DataFrame

    # List all Excel files in the current directory
    files = [f for f in os.listdir(current_directory) if f.endswith(".xlsx")]
    months_available = [os.path.splitext(f)[0] for f in files]  # Extract month names

    # Streamlit section for month-wise comparison
    st.header("Month-Wise Progress Comparison")

    if months_available:
        # Multi-select for months
        selected_months = st.multiselect(
            "Select Months to Compare:",
            options=months_available,
            default=months_available[1:4]  # Default to first two months for comparison
        )

        if selected_months:
            # Load data for selected months
            monthly_data = {}
            for month in selected_months:
                file_path = os.path.join(current_directory, f"{month}.xlsx")
                sprint_data = load_data(file_path, "Sprint Tasks")
                loop_data = load_data(file_path, "Loop Tasks")

                # Preprocess and combine the data
                if not sprint_data.empty:
                    sprint_data["Tasks Type"] = "Sprint"
                if not loop_data.empty:
                    loop_data["Tasks Type"] = "Loop"

                combined_data = pd.concat([sprint_data, loop_data], ignore_index=True)
                combined_data["Month"] = month
                monthly_data[month] = combined_data

            # Combine data from all selected months
            all_months_data = pd.concat(monthly_data.values(), ignore_index=True)

            # Clean column names
            all_months_data.columns = all_months_data.columns.str.strip()

            # Ensure 'Date' column is properly converted to datetime
            if "Date" in all_months_data.columns:
                all_months_data["Date"] = pd.to_datetime(all_months_data["Date"], errors="coerce")

                # Drop rows with NaT in the Date column
                all_months_data = all_months_data.dropna(subset=["Date"])

                # Create a new column for the period
                all_months_data["Month_Period"] = all_months_data["Date"].dt.to_period("M")
            else:
                st.warning("'Date' column not found in the data.")
                all_months_data["Month_Period"] = "Unknown"

            # Drop rows where 'Status' is missing or not a string
            if "Status" in all_months_data.columns:
                all_months_data = all_months_data.dropna(subset=["Status"])
            else:
                st.warning("'Status' column not found in the data.")
                all_months_data["Status"] = "Unknown"

            

            # Task Status Distribution
            st.subheader("Task Status Distribution Across Months")
            try:
                status_distribution = all_months_data.groupby(["Month", "Status"]).size().unstack(fill_value=0)
                fig_status_dist = px.bar(
                    status_distribution,
                    barmode="stack",
                    title="Task Status Distribution Across Months",
                    labels={"value": "Count", "Month": "Month", "Status": "Task Status"}
                )
                st.plotly_chart(fig_status_dist)
            except ValueError as e:
                st.error(f"Error in grouping data by Status: {e}")

            # Task Type Distribution
            st.subheader("Task Type Distribution Across Months")
            task_types_dist = all_months_data.groupby(["Month", "Tasks Type"]).size().unstack(fill_value=0)
            fig_task_types = px.bar(
                task_types_dist,
                barmode="stack",
                title="Task Type Distribution Across Months",
                labels={"value": "Count", "Month": "Month", "Tasks Type": "Task Type"}
            )
            st.plotly_chart(fig_task_types)

            # Task Completion Trend Analysis
            st.subheader("Task Completion Trend Across Months")
            try:
                task_trend = all_months_data.groupby(["Month_Period", "Status"]).size().reset_index(name="Task Count")
                task_trend["Month_Period"] = task_trend["Month_Period"].astype(str)  # Convert Period to string for plotting

                # Plotting the trend
                fig_task_trend = px.line(
                    task_trend,
                    x="Month_Period",
                    y="Task Count",
                    color="Status",
                    title="Task Completion Trend Across Months",
                    labels={"Task Count": "Number of Tasks", "Month_Period": "Month"}
                )
                st.plotly_chart(fig_task_trend)
            except Exception as e:
                st.error(f"Error in Task Completion Trend Analysis: {e}")
            # Assignee Performance Across Months
            st.subheader("Assignee Performance Comparison Across Months")
            if "Assignee" in all_months_data.columns:
                assignee_performance = all_months_data.groupby(["Month", "Assignee"]).size().unstack(fill_value=0)
                fig_assignee_perf = px.bar(
                    assignee_performance,
                    barmode="stack",
                    title="Assignee Performance Across Months",
                    labels={"value": "Tasks Completed", "Month": "Month", "Assignee": "Resource"}
                )
                st.plotly_chart(fig_assignee_perf)
            else:
                st.warning("Assignee column not found in data. Performance comparison skipped.")

        else:
            st.warning("No months selected for comparison.")
    else:
        st.warning("No valid Excel files found in the current directory.")
    
                

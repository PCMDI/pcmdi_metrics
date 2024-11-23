from bokeh.models import ColumnDataSource, DataTable, TableColumn, MultiChoice, CustomJS
from bokeh.layouts import column
from bokeh.io import curdoc, output_file, save
import pandas as pd

# Sample data
data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'Age': [24, 30, 35, 40, 29],
    'Department': ['HR', 'IT', 'Finance', 'IT', 'HR'],
    'Location': ['New York', 'San Francisco', 'Chicago', 'New York', 'Chicago'],
}

# Create a DataFrame
df = pd.DataFrame(data)

# Function to create the layout
def create_layout():
    # Create a ColumnDataSource
    source = ColumnDataSource(df)

    # Create a filtered ColumnDataSource
    filtered_source = ColumnDataSource(data=dict(df))

    # DataTable setup
    columns = [
        TableColumn(field="Name", title="Name"),
        TableColumn(field="Age", title="Age"),
        TableColumn(field="Department", title="Department"),
        TableColumn(field="Location", title="Location"),
    ]

    data_table = DataTable(source=filtered_source, columns=columns, width=800, height=300)

    # Filter widgets
    department_filter = MultiChoice(
        options=list(df['Department'].unique()),
        title="Filter by Department",
        value=[],
    )

    location_filter = MultiChoice(
        options=list(df['Location'].unique()),
        title="Filter by Location",
        value=[],
    )

    # Callback to filter the data
    filter_callback = CustomJS(
        args=dict(source=source, filtered_source=filtered_source,
                  department_filter=department_filter, location_filter=location_filter),
        code="""
        const original_data = source.data;
        const filtered_data = { Name: [], Age: [], Department: [], Location: [] };

        const selected_departments = department_filter.value;
        const selected_locations = location_filter.value;

        for (let i = 0; i < original_data.Name.length; i++) {
            const in_department = selected_departments.length === 0 || selected_departments.includes(original_data.Department[i]);
            const in_location = selected_locations.length === 0 || selected_locations.includes(original_data.Location[i]);

            if (in_department && in_location) {
                filtered_data.Name.push(original_data.Name[i]);
                filtered_data.Age.push(original_data.Age[i]);
                filtered_data.Department.push(original_data.Department[i]);
                filtered_data.Location.push(original_data.Location[i]);
            }
        }

        filtered_source.data = filtered_data;
        filtered_source.change.emit();
        """
    )

    department_filter.js_on_change("value", filter_callback)
    location_filter.js_on_change("value", filter_callback)

    # Layout
    return column(department_filter, location_filter, data_table)

# Create layout for the HTML file
layout = create_layout()

# Save as HTML file
output_file("interactive_multi_filter_table.html")  # Specify the output HTML file name
save(layout)  # Save the layout to the HTML file

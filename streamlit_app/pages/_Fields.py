from api.neo4j import init_driver
import streamlit as st
from api.dao.field import FieldDAO
from components.navigation_bar import navition_bar
from components.get_pydeck_chart import get_pydeck_chart
import pandas as pd

# Page config and icon
st.set_page_config(layout="wide", page_title="SOCKG Dashboard - Fields", page_icon=":national_park:")

# sidebar for navigation
navition_bar()

# Initialize driver
driver = init_driver()

st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Field Exploration</h1>", unsafe_allow_html=True)
# Get all fields from the database
field_dao = FieldDAO(driver)
ids = field_dao.get_all_ids()

# Error checking
if not ids:
    st.error("No fields found in the database.")

# initialize selected field in session state if not already initialized
if 'selected_field' not in st.session_state:
    st.session_state.selected_field = None

# Field selection
st.subheader("Select a Field:")
option = st.selectbox("Select a field to explore:", ids, index=None, label_visibility="collapsed")
if option is not None:
    st.session_state['selected_field'] = option

# get field extra information
if st.session_state.selected_field is None:
    st.stop()

field_info = field_dao.get_field_info(st.session_state.selected_field)
st.info(f"""
    **Field ID:** {st.session_state['selected_field']}\n
    **Major Land Resource Area:** {field_info['Major_Land_Resource_Area'][0]}\n
    **Postal Code:** {field_info['Postal_Code'][0] if str(field_info['Postal_Code'][0]) != "nan" else "Not available"}\n
    **Established Date:** {field_info['establishedDate'][0]}\n
    **History:** {field_info['History'][0]}\n
    **Description:** {field_info['Description'][0] if field_info['Description'][0] != None else "Not available"}\n
    **Native Vegetation:** {field_info['Native_Vegetation'][0]}\n
    **Spatial Description:** {field_info['Spatial_Description'][0] if str(field_info['Spatial_Description'][0]) != "nan" else "Not available"}\n
    """)

# Column layout
col1, col2 = st.columns(2)

with col1:
    # Get experimental unit data
    exp_units = field_dao.get_all_experimental_unit(st.session_state.selected_field)
    st.subheader("Experimental Units On Field")
    # Print out the total number of experimental units
    st.info(f"Total Experimental Units Found on Field: {exp_units.shape[0]}")

    # Rename columns for better readability
    exp_units.rename(columns={"id": "Experimental Unit ID", "Start_Date": "Start Date", "End_Date": "End Date", "Size": "Size"}, inplace=True)
    # Replace end date to 'Present' if it is empty
    exp_units['End Date'] = exp_units['End Date'].apply(lambda x: 'Present' if pd.isnull(x) else x)
    event = st.dataframe(
        exp_units,
        use_container_width=True,
        hide_index=True,
        height=490,
        on_select='rerun',
        selection_mode='single-row',
        )
    selected_row = event.selection.rows
    if selected_row:
        st.session_state.selected_exp_unit = exp_units.loc[selected_row[0], "Experimental Unit ID"]
        st.switch_page("pages/_ExperimentalUnits.py")

with col2:
    # Get latitude and longitude of the selected field
    df = field_dao.get_lat_long_dataframe(st.session_state.selected_field)
    st.subheader("Field Location")
    # Print out the exact latitude and longitude
    st.info(f"(Latitude, Longitude): ({df['latitude'].values[0]}, {df['longitude'].values[0]})")
    st.pydeck_chart(get_pydeck_chart(df['longitude'].values[0], df['latitude'].values[0]))

# Rainfall data
st.subheader("Precipitation over Time")
rainfall_df = field_dao.get_rainfall_df(st.session_state.selected_field)

# Drop rows with missing values
rainfall_df = rainfall_df.dropna()
if rainfall_df is not None and not rainfall_df.empty:
    tab1, tab2 = st.tabs(["Chart", "Data"])
    
    with tab1:
        st.bar_chart(rainfall_df, x='Period', y='TotalPrecipitation')
    
    with tab2:
        # Calculate average precipitation
        avg_precipitation = rainfall_df['TotalPrecipitation'].mean()
        
        # Display average precipitation
        st.metric("Average Precipitation", f"{avg_precipitation:.2f}")
        
        # Display the data table
        st.dataframe(rainfall_df.style.highlight_max(axis=0), use_container_width=True, hide_index=True)
else:
    st.write("No rainfall data available.")

# get all publicaions in a field
publications_df = field_dao.get_publications(st.session_state.selected_field)
st.subheader("Publications on Field")
st.dataframe(publications_df, use_container_width=True)
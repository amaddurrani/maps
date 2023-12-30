import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import requests
import polyline
from datetime import datetime, timedelta


menu_options = ['Location Details','Route Details']
selected_page = st.sidebar.selectbox("Select Method", menu_options)
google_maps_api_key = 'AIzaSyCg64_rWeCOeAHkRyhPEydjaD09jfME8QE'


if selected_page=='Location Details':
    uploaded_file = st.file_uploader("Choose a file", type='csv')
    if uploaded_file is not None:
        # Load data from CSV
        data = pd.read_csv(uploaded_file)  # Replace 'your_data.csv' with the actual file path

        # Streamlit app
        st.title("Map for Location Data")

        # Initialize variables for total distance and time
        total_distance = 0
        total_duration = timedelta()
        data[['lat', 'lon']] = data['Column1'].str.split(',', expand=True)
        data[['lat', 'lon']] = data[['lat', 'lon']].astype(float)

        # Create a Folium map
        map_center = [(data['lat'][0] + data['lat'].iloc[-1]) / 2, (data['lon'][0] + data['lon'].iloc[-1]) / 2]
        map_obj = folium.Map(location=map_center, zoom_start=9)

        # Iterate over each row in the DataFrame
        for index, row in data.iterrows():
            # Get directions from the Directions API for each leg
            origin = f"{data['lat'][index - 1]},{data['lon'][index - 1]}" if index > 0 else f"{row['lat']},{row['lon']}"
            destination = f"{row['lat']},{row['lon']}"
            api_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={google_maps_api_key}"
            response = requests.get(api_url).json()
            # Extract road distance and duration for each leg
            leg = response.get('routes', [{}])[0].get('legs', [{}])[0]
            distance = leg.get('distance', {}).get('text', '0 m')
            duration = leg.get('duration', {}).get('text', '0 min')
            # Get elevation data for the destination location
            location = f"{row['lat']},{row['lon']}"
            elevation_api_url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={location}&key={google_maps_api_key}"
            elevation_response = requests.get(elevation_api_url).json()
            elevation = elevation_response.get('results', [{}])[0].get('elevation', 0)


            # Update total distance and duration
            total_distance += leg.get('distance', {}).get('value', 0)
            total_duration += timedelta(minutes=leg.get('duration', {}).get('value', 0))
            data['Distance'][index]=distance
            data['Duration'][index]=duration
            data['Height'][index]=str(int(elevation))+' m'
            folium.Marker(location=[data['lat'][index], data['lon'][index]], popup=data['LOCATION_NAME'][index]+'\n User ID:'+str(row['USER_ID'])).add_to(map_obj)
            points = polyline.decode(response.get('routes', [{}])[0].get('overview_polyline', {}).get('points', ''))
            folium.PolyLine(locations=points, color='blue').add_to(map_obj)

        
        # Display the map
        st.subheader("Map")
        folium_static(map_obj)
        # Display the end table
        st.dataframe(data)
        data_as_csv= data.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download data as CSV", 
            data_as_csv, 
            "Location Details.csv",
            "text/csv",
            key="location-csv",
        )

        # Display the total distance and duration
        st.subheader("Total Distance and Duration:")
        st.write(f"Total Distance: {total_distance / 1000:.2f} KM")
        st.write(f"Total Duration: {str(total_duration)}")
else:
    upload_file= st.file_uploader("Choose File", type='csv')
    if upload_file is not None:
        # Replace 'your_data.csv' with the actual file path
        data = pd.read_csv(upload_file)
        st.title("Distance, Elevation, and Duration Calculator App")
        data[['latA', 'lonA']] = data['Location A'].str.split(',', expand=True).astype(float)
        data[['latB', 'lonB']] = data['Location B'].str.split(',', expand=True).astype(float)
        # Create Folium map
        map_center = [(data['latA'][0] + data['latB'].iloc[-1]) / 2, (data['lonA'][0] + data['lonB'].iloc[-1]) / 2]
        map_obj = folium.Map(location=map_center,zoom_start=10)
        # Iterate through each row in the DataFrame
        for index, row in data.iterrows():
            origin = row['Location A']
            destination = row['Location B']

            # Make API request to Google Maps Directions API
            api_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={google_maps_api_key}"
            response = requests.get(api_url).json()

            # Extract road distance and duration for each leg
            leg = response.get('routes', [{}])[0].get('legs', [{}])[0]
            distance = leg.get('distance', {}).get('text', '0 m')
            duration = leg.get('duration', {}).get('text', '0 min')

            # Update DataFrame with distance and duration
            data.at[index, 'Ditance'] = distance
            data.at[index, 'Duration (min)'] = duration
            origin_coords = [float(coord) for coord in origin.split(', ')]
            destination_coords = [float(coord) for coord in destination.split(', ')]
            folium.Marker(location=origin_coords, popup=f"Origin\n{data.at[index, 'Reference ID']}").add_to(map_obj)
            folium.Marker(location=destination_coords, popup=f"Destination\n{data.at[index, 'Reference ID']}").add_to(map_obj)

            # Decode polyline and add route to the map
            points = polyline.decode(response.get('routes', [{}])[0].get('overview_polyline', {}).get('points', ''))
            folium.PolyLine(locations=points, color='blue').add_to(map_obj)
        # Display the map
        
        data= data.drop(['latA','latB','lonA','lonB'],axis=1)
        # Display the DataFrame with updated distance and duration
        st.dataframe(data)
        data_as_csv= data.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download data as CSV", 
            data_as_csv, 
            "Route Details.csv",
            "text/csv",
            key="download-tools-csv",
        )
        folium_static(map_obj)
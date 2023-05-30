from dataclasses import dataclass
from typing import Dict, List, Optional

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from google.cloud import firestore

st.set_page_config(layout="wide")
st.header("🔥 FireBird - Crowdsourcing Wildfire Detection")

@st.cache_resource
def get_data() -> List[Dict]:
    # Authenticate to Firestore with the JSON account key.
    db = firestore.Client.from_service_account_json("firestore-key.json")

    # Create a reference to the Google post.
    docs = db.collection("1").stream()

    geolocations = [geolocation.to_dict() for geolocation in docs]

    for geolocation in geolocations:
        geolocation["_point"] = Point.from_dict(geolocation)

    return geolocations


@dataclass
class Point:
    lat: float
    lon: float

    @classmethod
    def from_dict(cls, data: Dict) -> "Point":
        if "lat" in data:
            return cls(float(data["lat"]), float(data["lng"]))
        elif "latitude" in data:
            return cls(float(data["latitude"]), float(data["longitude"]))
        else:
            raise NotImplementedError(data.keys())

    def is_close_to(self, other: "Point") -> bool:
        close_lat = self.lat - 0.0001 <= other.lat <= self.lat + 0.0001
        close_lon = self.lon - 0.0001 <= other.lon <= self.lon + 0.0001
        return close_lat and close_lon


@dataclass
class Bounds:
    south_west: Point
    north_east: Point

    def contains_point(self, point: Point) -> bool:
        in_lon = self.south_west.lon <= point.lon <= self.north_east.lon
        in_lat = self.south_west.lat <= point.lat <= self.north_east.lat

        return in_lon and in_lat

    @classmethod
    def from_dict(cls, data: Dict) -> "Bounds":
        return cls(
            Point.from_dict(data["_southWest"]), Point.from_dict(data["_northEast"])
        )


#############################
# Streamlit app
#############################

# define layout
c1, c2 = st.columns(2)

# get and cache data from API
geolocations = get_data()

# Sidebar
st.sidebar.header("Map Selection")
starting_location = st.sidebar.selectbox(
    "Choose a starting location",
    (["Daly City", "San Francisco", "San Jose", "Los Angeles", "New York", "Chicago", "Houston"]),
)

# Dictionary mapping location names to their corresponding coordinates
location_dict = {"Daly City": "37.6879, -122.4702",
                 "San Francisco": "37.7749, -122.4194",
                 "San Jose": "37.3382, -121.8863",
                 "Los Angeles": "34.0522, -118.2437",
                 "New York": "40.7128, -74.0060",
                 "Chicago": "41.8781, -87.6298",
                 "Houston": "29.7604, -95.3698"}

selected_location = location_dict[starting_location]

map_type = st.sidebar.selectbox("Select Map Type", ["Open Street Map", "Terrain", "Toner"])
map_dict = {"Open Street Map": "OpenStreetMap", "Terrain": "Stamen Terrain", "Toner": "Stamen Toner"}
selected_map = map_dict[map_type]

# Get latitude and longitude from selected location
location = list(map(float, selected_location.split(',')))

tab1, tab2, tab3 = st.tabs(["__Sightings__", "__Details__", "__Triage Centre__"])

# layout map
with tab1:
    with st.expander("__Map__", expanded=True):
        # get and cache data from API
        geolocations = get_data()

        # layout map
        m = folium.Map(location=location, zoom_start=10)

        for geolocation in geolocations:
            popup = folium.Popup(
                f"""
                                <strong>Coordinates:</strong> {geolocation['latitude']}, {geolocation['longitude']}<br>
                                """,
                max_width=250)
            folium.Marker(
                [geolocation["latitude"], geolocation["longitude"]], popup=popup
            ).add_to(m)

        map_data = st_folium(m, key="fig1", width=1400, height=500)

# get data from map for further processing
map_bounds = Bounds.from_dict(map_data["bounds"])

# when a point is clicked, display additional information about the park
try:
    point_clicked: Optional[Point] = Point.from_dict(map_data["last_object_clicked"])

    if point_clicked is not None:
        with st.spinner(text="Loading fire data..."):
            for geolocation in geolocations:
                if geolocation["_point"].is_close_to(point_clicked):
                    with tab2:
                        st.subheader("Sighting Details")
                        st.json(geolocation)
except TypeError:
    point_clicked = None

# Checkbox widget to show/hide technical details
with tab1:
    if st.checkbox('Show technical details'):
        geolocations_in_view: List[Dict] = []
        for geolocation in geolocations:
            if map_bounds.contains_point(geolocation["_point"]):
                geolocations_in_view.append(geolocation)

        st.markdown("###### Fire Sightings Within View")
        st.code(f"{len(geolocations_in_view)}", language='python')

        st.markdown("###### Map Bounding Box")
        st.code(f"{map_bounds}", language='python')

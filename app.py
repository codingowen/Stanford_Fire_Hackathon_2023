from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import folium
import streamlit as st
from google.cloud import firestore
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from streamlit_folium import st_folium

import algo

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
        return cls(Point.from_dict(data["_southWest"]), Point.from_dict(data["_northEast"]))


def convert_firestore_datetime(dt: DatetimeWithNanoseconds) -> datetime:
    # This will convert a DatetimeWithNanoseconds object to a datetime object,
    # preserving timezone information
    dt = datetime(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        second=dt.second,
        microsecond=dt.microsecond,
        tzinfo=dt.tzinfo,
    )

    dt_truncated = _truncate_microseconds(dt)

    return dt_truncated.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")


def _truncate_microseconds(dt: datetime) -> datetime:
    return dt.replace(microsecond=0)


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
    (
        [
            "Daly City",
            "San Francisco",
            "San Jose",
            "Los Angeles",
            "New York",
            "Chicago",
            "Houston",
        ]
    ),
)

# Dictionary mapping location names to their corresponding coordinates
location_dict = {
    "Daly City": "37.6879, -122.4702",
    "San Francisco": "37.7749, -122.4194",
    "San Jose": "37.3382, -121.8863",
    "Los Angeles": "34.0522, -118.2437",
    "New York": "40.7128, -74.0060",
    "Chicago": "41.8781, -87.6298",
    "Houston": "29.7604, -95.3698",
}
selected_location = location_dict[starting_location]

map_type = st.sidebar.selectbox("Select Map Type", ["Open Street Map", "Terrain", "Toner"])
map_dict = {
    "Open Street Map": "OpenStreetMap",
    "Terrain": "Stamen Terrain",
    "Toner": "Stamen Toner",
}
selected_map = map_dict[map_type]

with st.sidebar:
    if st.button("Refresh"):
        st.cache_resource.clear()
        st.experimental_rerun()

# Get latitude and longitude from selected location
location = list(map(float, selected_location.split(",")))

# Add this in the sidebar
localize_wildfire = st.sidebar.checkbox("Localize Wildfire")

tab1, tab2, tab3 = st.tabs(["__Sightings__", "__Details__", "__Triage Centre__"])

# layout map
with tab1:
    with st.expander("__Map__", expanded=True):
        # get and cache data from API
        geolocations = get_data()

        # layout map
        m = folium.Map(location=location, zoom_start=10, tiles=selected_map)

        points = []  # list to store coordinates for polyline

        for geolocation in geolocations:
            popup = folium.Popup(
                f"""
                <strong>Coordinates:</strong> <code>({round(geolocation['latitude'], 5)}, {round(geolocation['longitude'], 5)})</code><br>
                <strong>Time:</strong> {convert_firestore_datetime(geolocation['datetime'])}<br>
                <strong>Details:</strong> See more in details tab<br>
                                """,
                max_width=250,
            )
            folium.Marker([geolocation["latitude"], geolocation["longitude"]], popup=popup).add_to(m)

            # add coordinates to points list
            points.append((geolocation["latitude"], geolocation["longitude"]))

        map_data = st_folium(m, key="fig1", width=1400, height=500)

        # get data from map for further processing
        map_bounds = Bounds.from_dict(map_data["bounds"])

        # add polyline to the map if checkbox is checked
        if localize_wildfire:
            # Then, inside your tab1, add the following lines after the points loop:
            try:
                fire_coord = algo.get_fire_coordinates(geolocations, map_bounds)
            except TypeError:
                fire_coord = None

            if not fire_coord:
                st.error("🔥 Not enough coordinates or direction vectors on map.")

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
    if st.checkbox("Show technical details"):
        geolocations_in_view: List[Dict] = []
        for geolocation in geolocations:
            if map_bounds.contains_point(geolocation["_point"]):
                geolocations_in_view.append(geolocation)

        st.markdown("###### Fire Sightings Within View")
        st.code(f"{len(geolocations_in_view)}", language="python")

        st.markdown("###### Map Bounding Box")
        st.code(f"{map_bounds}", language="python")

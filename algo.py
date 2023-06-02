import math
from typing import Tuple

import numpy as np
import streamlit as st
from geographiclib.geodesic import Geodesic
from scipy.spatial import distance
from shapely import LineString
from sklearn.cluster import DBSCAN

from app import Point


def _transform_gyroscope_data(geo):
    def __calculate_direction_vector(
        latitude: float, longitude: float, magnetometer_data: Tuple[float, float, float]
    ) -> Tuple[float, float]:
        # calculate azimuth from magnetometer data
        azimuth = __calculate_azimuth_from_magnetometer(magnetometer_data)

        # define a distance (in meters)
        distance = 100000.0  # adjust as needed

        # use geographiclib to calculate a new point at the given distance and direction
        geod = Geodesic.WGS84

        result = geod.Direct(latitude, longitude, azimuth, distance)

        new_latitude, new_longitude = result["lat2"], result["lon2"]

        print("New point: ", new_latitude, new_longitude)

        return new_latitude, new_longitude

    def __calculate_azimuth_from_magnetometer(magnetometer_data: Tuple[float, float, float]) -> float:
        # magnetometer_data is a tuple (x, y, z)
        # for simplicity, let's assume the phone is held flat and the z-component is ignored

        x, y, _ = magnetometer_data

        # calculate the azimuth (angle from the north, in degrees)
        azimuth = math.degrees(math.atan2(y, x))

        # make sure the result is between 0 and 360
        if azimuth < 0:
            azimuth += 360

        return azimuth

    try:
        direction_vectors = __calculate_direction_vector(geo["latitude"], geo["longitude"], geo["gyroscope"])
    except KeyError:
        return None

    return direction_vectors


def calculate_intersections(coordinates, direction_vectors):
    def line_equation(coord1, coord2):
        """Calculate slope and intercept of a line."""
        x1, y1 = coord1
        x2, y2 = coord2

        m = (y2 - y1) / (x2 - x1)  # slope
        c = y1 - m * x1  # y-intercept

        return m, c

    def line_intersection(line1, line2):
        """Calculate intersection point of two lines."""
        m1, c1 = line1
        m2, c2 = line2

        x = (c2 - c1) / (m1 - m2)
        y = m1 * x + c1

        return x, y

    # Store the intersection points and the corresponding coordinate indices
    intersections = []
    coordinate_indices = []

    # Calculate intersection points for all pairs of lines
    for i in range(len(coordinates)):
        for j in range(i + 1, len(coordinates)):
            line1 = line_equation(coordinates[i], direction_vectors[i])
            line2 = line_equation(coordinates[j], direction_vectors[j])

            intersection_point = line_intersection(line1, line2)

            print("Intersection point: ", intersection_point)

            # Add the intersection point to the list and record the coordinate indices
            intersections.append(intersection_point)
            coordinate_indices.append((i, j))

    return intersections, coordinate_indices


# Function to calculate the clustering coefficient of a cluster
def calculate_clustering_coefficient(cluster: np.ndarray) -> float:
    pairwise_distances = distance.pdist(cluster)
    avg_pairwise_distance = pairwise_distances.mean()

    print("Pairwise distances: ", pairwise_distances)

    return avg_pairwise_distance


def find_subset_with_highest_clustering_coefficient(coordinates: np.ndarray) -> np.ndarray:
    # Using DBSCAN to cluster the data
    dbscan = DBSCAN(eps=5, min_samples=3)
    labels = dbscan.fit_predict(coordinates)

    # Calculating clustering coefficients for each cluster
    clustering_coefficients = {
        label: calculate_clustering_coefficient(coordinates[labels == label]) for label in set(labels)
    }

    # Finding the cluster with the highest coefficient
    highest_coefficient_label = min(clustering_coefficients, key=clustering_coefficients.get)
    subset = coordinates[labels == highest_coefficient_label]

    print("Clustering coefficients: ", clustering_coefficients)

    return subset


def get_fire_coordinates(geolocations, map_bounds):
    # Extracting coordinates and directions from the Firebase points
    coordinates = [
        (geo["latitude"], geo["longitude"]) for geo in geolocations if map_bounds.contains_point(Point.from_dict(geo))
    ]

    direction_vectors = [
        _transform_gyroscope_data(geo) for geo in geolocations if map_bounds.contains_point(Point.from_dict(geo))
    ]

    if not direction_vectors:
        return None

    # If there are not enough coordinates or direction vectors, return None
    if len(coordinates) <= 1 or len(direction_vectors) < len(coordinates):
        return None

    # Calculate all intersection points
    intersection_points, intersection_coordinate_indices = calculate_intersections(coordinates, direction_vectors)

    non_shapely_intersection_points = np.array([[x, y] for x, y in intersection_points])

    optimized_intersection_points = find_subset_with_highest_clustering_coefficient(non_shapely_intersection_points)

    # Identify the indices of the user coordinates that contributed to the optimized intersection points
    contributing_coordinate_indices = set()
    for point in optimized_intersection_points:
        index = intersection_points.index(tuple(point))
        contributing_coordinate_indices.update(intersection_coordinate_indices[index])

    # Get the corresponding user coordinates
    contributing_coordinates = [coordinates[i] for i in contributing_coordinate_indices]

    print("Contributing coordinates: ", contributing_coordinates)

    # Calculate the average of the contributing coordinates
    fire_coordinates = tuple(np.mean(contributing_coordinates, axis=0))

    print("Fire coordinates: ", fire_coordinates)

    return fire_coordinates

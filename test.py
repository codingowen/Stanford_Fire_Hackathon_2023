import numpy as np
import pytest
from geographiclib.geodesic import Geodesic
from shapely.geometry import LineString
from sklearn.cluster import DBSCAN

from algo import (
    _transform_gyroscope_data,
    calculate_clustering_coefficient,
    calculate_intersections,
    find_subset_with_highest_clustering_coefficient,
    get_fire_coordinates,
)
from app import Point, map_bounds


# Add your other imports and function definitions here
def test__transform_gyroscope_data():
    geo = {"latitude": 40.7128, "longitude": -74.0060, "gyroscope": (1.0, 2.0, 3.0)}
    result = _transform_gyroscope_data(geo)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_calculate_intersections():
    coordinates = [(40.7128, -74.0060), (34.0522, -118.2437), (51.5074, -0.1278)]
    direction_vectors = [(40.7138, -74.0070), (34.0532, -118.2447), (51.5084, -0.1288)]
    result, _ = calculate_intersections(coordinates, direction_vectors)
    assert isinstance(result, list)
    for point in result:
        assert isinstance(point, tuple)
        assert len(point) == 2


def test_calculate_clustering_coefficient():
    cluster = np.array([(40.7128, -74.0060), (34.0522, -118.2437), (51.5074, -0.1278)])
    result = calculate_clustering_coefficient(cluster)
    assert isinstance(result, float)


def test_find_subset_with_highest_clustering_coefficient():
    coordinates = np.array([(40.7128, -74.0060), (34.0522, -118.2437), (51.5074, -0.1278)])
    result = find_subset_with_highest_clustering_coefficient(coordinates)
    assert isinstance(result, np.ndarray)
    assert result.shape[1] == 2


def test_get_fire_coordinates():
    geolocations = [
        {"latitude": 39.810278, "longitude": -121.7, "gyroscope": (1.0, 2.0, 3.0)},
        {"latitude": 39.89, "longitude": -121.5, "gyroscope": (1.0, 2.0, 3.0)},
        {"latitude": 39.77, "longitude": -121.1, "gyroscope": (1.0, 2.0, 3.0)},
    ]

    map_bounds.south_west = Point(30.7128, -126.0060)
    map_bounds.north_east = Point(51.5074, -0.1278)
    result = get_fire_coordinates(geolocations, map_bounds)
    assert isinstance(result, tuple)
    assert len(result) == 2


if __name__ == "__main__":
    pytest.main()

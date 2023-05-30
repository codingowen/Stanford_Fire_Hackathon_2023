import folium
from math import sin, cos, atan2, radians
from shapely.geometry import Point, LineString
from sklearn.cluster import DBSCAN
from scipy.spatial import distance
from shapely.ops import split

# GPS Datapoints
origin_coordinates = [(34.0522, -118.2437), (37.7749, -122.4194), (32.7157, -117.1611)]

# Direction Vectors
directions = [(0,1), (0,1), (0,1)]

def calculate_intersection(coordinate1, direction1, coordinate2, direction2):
    line1 = LineString([coordinate1, (coordinate1[0] + direction1[0], coordinate1[1] + direction1[1])])
    line2 = LineString([coordinate2, (coordinate2[0] + direction2[0], coordinate2[1] + direction2[1])])

    intersection = line1.intersection(line2)

    if intersection.is_empty:
        return None
    elif intersection.geom_type == 'Point':
        return intersection
    else:
        return None


intersection_points = []

for i in range(len(origin_coordinates)):
    for j in range(i + 1, len(origin_coordinates)):
        intersection = calculate_intersection(origin_coordinates[i], directions[i], origin_coordinates[j], directions[j])
        if intersection:
                intersection_points.append(intersection)


Non_Shapely_intersection_points = []

for i in intersection_points:
    Non_Shapely_intersection_points.append([i.x, i.y])

def calculate_clustering_coefficient(cluster):
    #Calculate average pairwise distance within the cluster
    pairwise_distances = distance.pdist(cluster)
    avg_pairwise_distance = pairwise_distances.mean()
    return avg_pairwise_distance


def find_subset_with_highest_clustering_coefficient(coordinates):
    # Convert the coordinates to a feature matrix
    feature_matrix = coordinates

    # Apply DBSCAN clustering
    dbscan = DBSCAN(eps=5, min_samples=3)  # Set appropriate parameters
    labels = dbscan.fit_predict(feature_matrix)

    # Calculate the clustering coefficient for each cluster
    clustering_coefficients = {}
    for label in set(labels):
        cluster = feature_matrix[labels == label]
        clustering_coefficients[label] = calculate_clustering_coefficient(cluster)

    # Select the subset with the highest clustering coefficient
    highest_coefficient_label = max(clustering_coefficients, key=clustering_coefficients.get)
    subset = feature_matrix[labels == highest_coefficient_label]

    return subset  #IM NOT SURE RIGHT NOW BUT IM ASSUMING THAT THIS SUBSET VARIABLE RETURNS A LIST OF [X,Y] COORDINATES.
############################################################

optimized_intersection_points = find_subset_with_highest_clustering_coefficient(Non_Shapely_intersection_points)

sum_x = 0
sum_y = 0
total_points = 0

for coord in optimized_intersection_points:
    sum_x += coord[0]
    sum_y += coord[1]
    total_points += 1

center_x = sum_x / total_points
center_y = sum_y / total_points

fire_coord = [center_x, center_y]

print(fire_coord)

################################################################
#ALL CODE BELOW IS FOR INTEGRATION WITHIN THE PYTHON SCRIPT TO FOLIUM. IT ALSO HAS LEGACY LOGIC WHICH IS NO LONGER GOOD. IGNORE THAT.
#PLEASE DON'T DELETE THE CODE. I WILL IMPROVE THIS TOMORROW AND MAKE SURE THAT IT WORKS.
'''


# Create a map centered on California
m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

# Plot GPS points with bearings
for i, (lat, lon) in enumerate(gps_data):
    # Convert bearing to radians
    bearing_rad = radians(bearings[i])

    # Calculate destination point using bearing and distance
    distance = 100  # Arbitrary distance for visualization

    # Calculate latitude and longitude of destination point
    lat_dest = lat + (distance / 111.32) * sin(bearing_rad)
    lon_dest = lon + (distance / (111.32 * cos(radians(lat)))) * cos(bearing_rad)

    # Plot GPS point
    folium.CircleMarker(location=[lat, lon], radius=5, color='red', fill=True, fill_color='red').add_to(m)

    # Plot bearing line
    folium.PolyLine(locations=[(lat, lon), (lat_dest, lon_dest)], color='blue').add_to(m)

# Find intersection point
intersection_lat, intersection_lon = gps_data[0]

for i in range(1, len(gps_data)):
    lat1, lon1 = intersection_lat, intersection_lon
    lat2, lon2 = gps_data[i]

    bearing_rad = radians(bearings[i])
    distance = 100  # Arbitrary distance for intersection calculation

    # Calculate destination point using bearing and distance
    lat_dest = lat2 + (distance / 111.32) * sin(bearing_rad)
    lon_dest = lon2 + (distance / (111.32 * cos(radians(lat2)))) * cos(bearing_rad)

    # Calculate intersection point
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    x = lon_dest - lon1
    y = lat_dest - lat1

    cross_product = (dlat * y) - (dlon * x)
    t = ((lat1 - lat2) * x - (lon1 - lon2) * y) / cross_product

    intersection_lat = lat1 + dlat * t
    intersection_lon = lon1 + dlon * t

# Plot intersection point
folium.CircleMarker(location=[intersection_lat, intersection_lon], radius=5, color='green', fill=True,
                    fill_color='green').add_to(m)

# Save the map to an HTML file
m.save('map.html')

'''
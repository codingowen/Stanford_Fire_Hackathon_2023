
from shapely.geometry import LineString, Point
from sklearn.cluster import DBSCAN
from scipy.spatial import distance
import numpy as np



# origin_coordinates refers to the GPS coordinates of the person submitting the photo. It should be a list of (x,y) tuples.
origin_coordinates = [(39.810278, -121.7), (39.89, -121.5), (39.77, -121.1)]

# directions refers to the direction vector for the phone when the photo was taken. It should be a list of (x,y) tuples.
directions = [(0,100), (-100,100), (100,-100)]

# origin_coordinates and directions should have corresponding (x,y) tuples of the same index.


#calculate_intersection takes in the (x,y) origin points and directions of two lines, representing two people.
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
# The above logic only registers a successful intersection if there is only 1 intersection point between the two lines.
# It ignores edge cases, like if two people are facing each other perfectly and their direction vectors are parallel + intersecting.


intersection_points = []
origin_vectors_for_intersection_points = []



# the loop below ensures that all successful intersections are recorded in the intersection_points variable, and the corresponding origin_coordinates are recorded with the same index as well.
for i in range(len(origin_coordinates)):
    for j in range(i + 1, len(origin_coordinates)):
        intersection = calculate_intersection(origin_coordinates[i], directions[i], origin_coordinates[j], directions[j])
        if intersection:
                intersection_points.append(intersection)
                origin_vectors_for_intersection_points.append((origin_coordinates[i],directions[i], origin_coordinates[j], directions[j]))



# Non_Shapely_intersection_points essentially converts the list of (x,y) intersection points
# into a numpy array for compatibility with the sklearn methods
Non_Shapely_intersection_points = []


for i in intersection_points:
    Non_Shapely_intersection_points.append([i.x, i.y])
Non_Shapely_intersection_points = np.array(Non_Shapely_intersection_points)


# Calculate average pairwise distance within the cluster
def calculate_clustering_coefficient(cluster):
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

    # Select the subset with the highest clustering coefficient. GPT wrote max(...) but I changed it to min(...), because logic. I might be wrong.
    highest_coefficient_label = min(clustering_coefficients, key=clustering_coefficients.get)
    subset = feature_matrix[labels == highest_coefficient_label]

    return subset

# optimized_intersection_points will be a list of (x,y) intersection points that provide best clustering coefficient
optimized_intersection_points = find_subset_with_highest_clustering_coefficient(Non_Shapely_intersection_points)

# this is a list of all (x,y) origin vectors that contributed to finding the "optimized intersection points"
optimized_origin_vectors_for_intersection_points = []


# this finds the index j, by finding which index of the total intersection point list, the optimized intersection points correspond to
# by finding j, we can identify the origin vectors that contributed to the final optimized intersection points
for i in optimized_intersection_points:
    for j in range(len(intersection_points)):
        Point_optimized_intersection_points = Point(optimized_intersection_points[j])  # converts to a shapely point
        if Point_optimized_intersection_points == intersection_points[j]:
            optimized_origin_vectors_for_intersection_points.append(origin_vectors_for_intersection_points[j])

sum_x = 0
sum_y = 0
total_points = 0


# the following loop helps find average x and y values of the finalized list of coordinates.
for coord in optimized_intersection_points:
    sum_x += coord[0]
    sum_y += coord[1]
    total_points += 1

center_x = sum_x / total_points
center_y = sum_y / total_points

fire_coord = [center_x, center_y]

# the following two variables are the key outputs. Firstly, the (x,y) coordinate of the fire, as well as the
# the finalized set of origin vectors that contributed to finding the optimized intersection points. For plotting purposes.
print(fire_coord)
print(optimized_origin_vectors_for_intersection_points)




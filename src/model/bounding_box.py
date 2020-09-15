from typing import List

from src.model.point import Point


### MAIN RESPONSIBILITY: BJÖRN WILTING S184214 ###

#Calculates the bounding box of a given list of points
#Input: List of points
# Output: A min point and a max point defining the bounding box
def get_bounding_box(points: List[Point]):
    min_point = Point(-1, -1)
    max_point = Point(-1, -1)
    for i in range(0, len(points)):
        if min_point.x < 0 or points[i].x < min_point.x:
            min_point.x = points[i].x
        elif max_point.x < 0 or points[i].x > max_point.x:
            max_point.x = points[i].x
        if min_point.y < 0 or points[i].y < min_point.y:
            min_point.y = points[i].y
        elif max_point.y < 0 or points[i].y > max_point.y:
            max_point.y = points[i].y
    return min_point, max_point

#Determines if a given point is insde the given bounding box
def is_inside_box(point, box):
    in_x = point.x > box[0].x and point.x < box[1].x
    in_y = point.y > box[0].y and point.y < box[1].y
    return in_x and in_y

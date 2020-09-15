import math
from typing import List, Dict

from src.model.bezier_intersection import Segment
from src.model.path import Path
from src.model.point import Point


### MAIN RESPONSIBILITY: OLAV NØRGAARD OLSEN S184195 ###

# Computes the angle between 2 segments
def segment_angle(seg_a: Segment, seg_b: Segment) -> float:
    # Assume that the start_points of the segments are shared
    delta_a = seg_a.end_point - seg_a.start_point
    delta_b = seg_b.end_point - seg_b.start_point

    angle = math.atan2(delta_a.y, delta_a.x) - math.atan2(delta_b.y, delta_b.x)

    if angle < 0:
        return angle + 2 * math.pi
    return angle


def went_from_start_to_end(path: Path, came_from: Point) -> int:
    if path.start_point == came_from:
        return 1
    else:
        return -1


def find_path_segment(path: Path, point: Point) -> Segment:
    approximation = path.approximate()

    if path.start_point == point:
        return Segment(point, approximation[1])
    else:
        return Segment(point, approximation[-2])


# Finds the cycles bounding the faces of the graph, given the starting point, and the adjacencylist/edgemap
def find_faces(start_point: Point, edge_map: Dict[int, List[Path]]) -> List[List[Path]]:
    path = list((edge_map[start_point.index]))[0]
    cycle_detector = CycleDetection(edge_map)
    # Take first path
    direction = went_from_start_to_end(path, start_point)

    faces_found, last_back_track, directions_used = cycle_detector.faces(start_point, start_point, path,
                                                                         {path: [direction]})
    faces_found.append(last_back_track)

    filtered_faces = []
    for face in faces_found:
        # No path is chosen more than once
        if len(set(face)) == len(face):
            filtered_faces.append(face)

    return filtered_faces


class CycleDetection:
    def __init__(self, edge_map):
        self.edge_map = edge_map

    # Helper function for faces(). Attempts to follow the given path, if it has not already been taken in the
    # direction it is going to be taken.
    def take_path(self, root: Point, taken_path: Path, came_from: Point, directions_taken):
        direction = went_from_start_to_end(taken_path, came_from)
        taken_directions = directions_taken.get(taken_path, [])

        if direction not in taken_directions:
            taken_directions.append(direction)
            directions_taken[taken_path] = taken_directions
            found_faces, constructed_path, directions_taken = self.faces(root, came_from, taken_path, directions_taken)
            if not constructed_path:
                # Hit dead end somewhere
                return found_faces, [], directions_taken
            else:
                return found_faces, constructed_path, directions_taken
        else:
            # Dead end
            return [], [], directions_taken

    # Implementation of the face/cycle finding. It relies on
    # Recursive DFS, which prioritizes the paths coming in a counterclockwise angle. An "edge" (path) may be taken
    # more than once, but only if starting from the other vertex.
    def faces(self, root: Point, came_from: Point, path_to_follow: Path, directions_taken):
        next_point = path_to_follow.get_other_point(came_from)

        # Base case
        if next_point == root:
            return [], [path_to_follow], directions_taken

        # Find paths in next_point to discover
        other_paths = []
        for n_path in self.edge_map.get(next_point.index, []):
            if n_path == path_to_follow:
                continue
            other_paths.append(n_path)

        if not other_paths:
            # Dead end
            return [], [], directions_taken

        elif len(other_paths) == 1:
            # Only one path to take
            first_path = other_paths[0]
            faces_found, constructed_path, directions_taken = self.take_path(root, first_path, next_point,
                                                                             directions_taken)

            if constructed_path:
                # Must only add if currently backtracking
                return faces_found, constructed_path + [path_to_follow], directions_taken
            return [], [], directions_taken
        else:
            # Find segments to find angles between edges
            seg_start = find_path_segment(path_to_follow, next_point)
            seg_0 = find_path_segment(other_paths[0], next_point)
            seg_1 = find_path_segment(other_paths[1], next_point)

            # Assume path 1 has a smaller angle
            first_path = other_paths[1]
            second_path = other_paths[0]

            if segment_angle(seg_start, seg_0) < segment_angle(seg_start, seg_1):
                # Path 0 had a smaller angle
                first_path = other_paths[0]
                second_path = other_paths[1]

            # Take first path
            found_faces, constructed_path_first, directions_taken = self.take_path(root, first_path, next_point,
                                                                                   directions_taken)

            if constructed_path_first:
                # Only start a new face if the first path also contains a face
                found_faces_second, constructed_path_second, directions_taken = self.take_path(next_point, second_path,
                                                                                               next_point,
                                                                                               directions_taken)
                found_faces.extend(found_faces_second)

                if constructed_path_second:
                    found_faces.append(constructed_path_second)

            else:
                # Discard empty path from taking first
                found_faces, constructed_path_first, directions_taken = self.take_path(root, second_path, next_point,
                                                                                       directions_taken)

            if constructed_path_first:
                return found_faces, constructed_path_first + [path_to_follow], directions_taken
            else:
                return found_faces, [], directions_taken

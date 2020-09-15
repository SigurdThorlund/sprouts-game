import unittest

from src.model.face_finder import find_faces
from src.model.path import Path
from src.model.point import Point, GraphicsPoint


def init_points(positions):
    points = [None] * len(positions)

    for vertex, position in positions.items():
        point = GraphicsPoint(*position, False)
        point.index = vertex
        points[vertex] = point

    return points

def init_edge_map(paths):
    edge_map = {}

    for path in paths:
        path.start_point.add_to_path(path)
        path.end_point.add_to_path(path)

        edge_map[path.start_point.index] = edge_map.get(path.start_point.index,[]) + [path]
        edge_map[path.end_point.index] = edge_map.get(path.end_point.index,[]) + [path]

    return edge_map

def init_onion_graph():
    positions = {0: (0, 0), 1: (0, 30), 2: (0, -20), 3: (0, 10), 4: (0, 20), 5: (0, -10)}

    points = init_points(positions)

    paths = [
        Path.from_points([points[0], Point(-10, 5), points[3]]),
        Path.from_points([points[0], Point(10, 5), points[3]]),
        Path.from_points([points[0], points[5]]),
        Path.from_points([points[5], points[2]]),
        Path.from_points([points[1], Point(-30, 0), points[2]]),
        Path.from_points([points[1], Point(30, 0), points[2]]),
        Path.from_points([points[1], points[4]]),
        Path.from_points([points[3], points[4]]),
    ]

    return points, init_edge_map(paths)


def init_dead_ends_0():
    positions = {0: (0, 0), 1: (30, 0), 2: (30, 20), 3: (60, 0)}
    points = init_points(positions)

    paths = [
        Path.from_points([points[0], points[1]]),
        Path.from_points([points[0], Point(30, -10), points[3]]),
        Path.from_points([points[1], points[2]]),
        Path.from_points([points[1], points[3]])
    ]

    return points, init_edge_map(paths)


def init_dead_ends_1():
    positions = {0: (0, 0), 1: (30, 0), 2: (30, 20), 3: (60, 0), 4: (30, 40)}
    points = init_points(positions)

    paths = [
        Path.from_points([points[0], points[1]]),
        Path.from_points([points[0], Point(30, -10), points[3]]),
        Path.from_points([points[1], points[2]]),
        Path.from_points([points[1], points[3]]),
        Path.from_points([points[2], points[4]])
    ]

    return points, init_edge_map(paths)


def init_connected_faces():
    positions = {0: (0, 0), 1: (30, 0), 2: (50, 0), 3: (70, 0), 4: (90, 0)}
    points = init_points(positions)

    paths = [
        Path.from_points([points[0], points[1]]),
        Path.from_points([points[0], Point(15, -10), points[1]]),
        Path.from_points([points[1], points[2]]),
        Path.from_points([points[2], points[3]]),
        Path.from_points([points[3], points[4]]),
        Path.from_points([points[3], Point(15, -10), points[4]])
    ]

    return points, init_edge_map(paths)


def init_connected_faces_added():
    positions = {0: (0, 0), 1: (30, 0), 2: (50, 0), 3: (70, 0), 4: (90, 0), 5: (50, -30)}
    points = init_points(positions)

    paths = [
        Path.from_points([points[0], points[1]]),
        Path.from_points([points[0], Point(15, 10), points[1]]),
        Path.from_points([points[1], points[2]]),
        Path.from_points([points[2], points[3]]),
        Path.from_points([points[3], points[4]]),
        Path.from_points([points[3], Point(15, 10), points[4]]),
        Path.from_points([points[0], points[5]]),
        Path.from_points([points[5], points[4]])
    ]

    return points, init_edge_map(paths)


class TestFaces(unittest.TestCase):
    def test_onion(self):
        points, edge_map = init_onion_graph()
        faces = find_faces(points[0], edge_map)
        self.assertEqual(4, len(faces))

    def test_dead_ends_0(self):
        points, edge_map = init_dead_ends_0()
        faces = find_faces(points[0], edge_map)
        self.assertEqual(1, len(faces))

    def test_dead_ends_1(self):
        points, edge_map = init_dead_ends_1()
        faces = find_faces(points[0], edge_map)
        self.assertEqual(1, len(faces))

    def test_connected_faces(self):
        points, edge_map = init_connected_faces()
        faces = find_faces(points[0], edge_map)
        self.assertEqual(2, len(faces))

    def test_connected_faces_added(self):
        points, edge_map = init_connected_faces_added()
        faces = find_faces(points[0], edge_map)
        self.assertEqual(4, len(faces))


if __name__ == '__main__':
    unittest.main()

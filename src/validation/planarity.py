from typing import Tuple, List, Dict

import networkx as nx

import src.config.game_config as gc
from src.model.cubic_bezier import GraphicsBezier
from src.model.path import Path
from src.model.point import GraphicsPoint


### MAIN RESPONSIBILITY: OLAV NØRGAARD OLSEN S184195 ###

class LoadException(Exception):
    """ Exception raised whenever the input file is invalid"""

    def __init__(self, message):
        self.message = message


def read_graph_file(file_name):
    line_id = 0
    try:
        file = open(file_name, "r")
        initial_vertex_count = int(file.readline())

        actions = []

        # Read all connections drawn in file
        for line in file:
            line_id += 1
            i, j = line.split(' ')
            actions.append((int(i), int(j)))
        file.close()

        return actions_to_graph(initial_vertex_count, actions)

    except ValueError as error:
        error_message = str(error)
        # Handle invalid data
        if "invalid literal for int()" in error_message:
            message = str(error).split("'", 2)
            raise LoadException("Value \"" + message[1] + "\" on line (" + str(line_id) + ") is invalid.")

        elif "too many values to unpack" in error_message or "not enough values to unpack" in error_message:
            raise LoadException("Line (" + str(line_id) + ") is invalid.")
        else:
            raise error

    except FileNotFoundError:
        raise LoadException("File \"" + file_name + "\" does not exist.")

    except PermissionError:
        raise LoadException("Permission denied: " + file_name)


def actions_to_graph(initial_vertices: int, actions: List[Tuple[int, int]]):
    i = 0
    is_planar = True
    embedding = None

    path_grouping = []

    # Initialize graph
    graph = nx.MultiGraph()
    graph.add_nodes_from([i for i in range(0, initial_vertices)])

    while i < len(actions) and is_planar:
        # Find points "clicked on"
        start = actions[i][0]
        end = actions[i][1]

        new_vertex_id = initial_vertices + i
        edge_0 = (start - 1, new_vertex_id)
        edge_1 = (new_vertex_id, end - 1)

        graph.add_edge(*edge_0)
        graph.add_edge(*edge_1)
        path_grouping.append((edge_0, edge_1, new_vertex_id))

        i += 1
        is_planar, embedding = nx.check_planarity(graph)

    if is_planar:
        return graph, embedding, path_grouping
    else:
        raise LoadException(
            "Graph became non-planar at when adding edge (" + str(actions[i - 1][0]) + "," + str(
                actions[i - 1][1]) + ")."
        )


# Find the factors to upscale the positions
def scale_factors(positions: dict):
    min_x = gc.WINDOW_WIDTH
    min_y = gc.WINDOW_HEIGHT
    max_x = 0
    max_y = 0

    for pos in positions.values():
        min_x = min(pos[0], min_x)
        max_x = max(pos[0], max_x)
        min_y = min(pos[1], min_y)
        max_y = max(pos[1], max_y)

    to_add_x = gc.WINDOW_WIDTH * 0.05
    to_add_y = gc.WINDOW_HEIGHT * 0.05

    scale_x = (gc.WINDOW_WIDTH * 0.95 - to_add_x) / (max_x - min_x)
    scale_y = (gc.WINDOW_HEIGHT * 0.95 - to_add_y) / (max_y - min_y)
    return scale_x, to_add_x, scale_y, to_add_y


# Scale a single point
def scale_point(pos, scalings):
    return int(scalings[0] * pos[0] + scalings[1]), int(scalings[2] * pos[1] + scalings[3])


# Scale all points
def scale_positions(unscaled_positions: Dict[int, Tuple[float, float]]) -> Dict[int, Tuple[float, float]]:
    scale_parameters = scale_factors(unscaled_positions)
    for vertex_id, position in unscaled_positions.items():
        unscaled_positions[vertex_id] = scale_point(position, scale_parameters)
    return unscaled_positions


# Raise exception when the point has too many paths
def valid_point(point: GraphicsPoint, start: GraphicsPoint, end: GraphicsPoint):
    if point.num_paths > 3:
        raise LoadException(
            "Point " + str(point.index + 1) + " has more than 3 connections, after adding ("
            + str(start.index + 1) + "," + str(end.index + 1) + ")."
        )


def convert_to_game_structure(graph: nx.Graph, embedding: nx.PlanarEmbedding, path_grouping):
    positions = scale_positions(nx.combinatorial_embedding_to_pos(embedding, True))
    points = [GraphicsPoint] * len(graph.nodes)
    paths = []

    # Initialize points
    for index, position in positions.items():
        point = GraphicsPoint(*position, False)
        point.index = index
        points[index] = point

    # Initialize paths
    for path_start, path_end, mid_point in path_grouping:
        start_point = points[path_start[0]]
        end_point = points[path_end[1]]

        # The path was created from the same point to itself
        if start_point == end_point:
            end_point = points[path_start[1]]

            # Make small difference to width of the paths
            delta_pos = end_point - start_point
            mid_point = start_point + delta_pos.scalar(0.5)
            shift = delta_pos.rotate_anticlock().normalized().scalar(5)

            pos_control = mid_point + shift
            neg_control = mid_point - shift

            path_0 = Path([GraphicsBezier(start_point, end_point, gc.LINE_COLOR, pos_control, pos_control)], start_point, end_point)
            path_1 = Path([GraphicsBezier(start_point, end_point, gc.LINE_COLOR, neg_control, neg_control)], start_point, end_point)

            # Update paths of points
            start_point.add_to_path(path_0)
            start_point.add_to_path(path_1)
            end_point.add_to_path(path_0)
            end_point.add_to_path(path_1)

            paths.append((path_0, path_1, points[path_start[1]]))
        # Normal path
        else:
            middle_point = points[path_start[1]]

            path_0 = Path([GraphicsBezier(start_point, middle_point)], start_point, middle_point)
            path_1 = Path([GraphicsBezier(middle_point, end_point)], middle_point, end_point)

            # Update paths of points
            start_point.add_to_path(path_0)
            middle_point.add_to_path(path_0)
            middle_point.add_to_path(path_1)
            end_point.add_to_path(path_1)

            paths.append((path_0, path_1, middle_point))

        # Test whether the points are still valid
        valid_point(start_point, start_point, end_point)
        valid_point(end_point, start_point, end_point)
    return points, paths


# Give filename as a string, to have it validated
def validate_file(file_name):
    graph, embedding, path_grouping = read_graph_file(file_name)
    points, paths = convert_to_game_structure(graph, embedding, path_grouping)
    return points, paths


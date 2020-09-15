from typing import Dict, Set

import pygame

import src.config.game_config as gc
from src.model.bezier_intersection import *
from src.model.bounding_box import *
from src.model.face_finder import find_faces
from src.model.path import Path
from src.model.point import GraphicsPoint
from src.model.point_in_polygon import PointInPolygon


### MAIN RESPONSIBILITY: BJÖRN WILTING S184214 ###

# Sort two points by their x-coordinate in ascending order
# Input: The two points (p1, p2)
# Output: The two points sorted
def get_min_max_x(p1, p2):
    if p1.x > p2.x:
       return p2.x, p1.x
    else:
       return p1.x, p2.x

def is_in_range(value, min, max):
    return value >= min and value <= max

# The Region class is used to create, store and maintain the game state of a Sprouts game
class Region:

    @staticmethod
    # Returns whether a region can be added without exeeding the limit of the points state
    # (Limit: 2 regions for an open point, 3 for a closed point)
    def full(point) -> bool:
        return point.available() and len(point.regions) > 1 or \
               (not point.available() and len(point.regions) > 2)

    #Removes the duplicate start/end point in given cycle border
    #Input: A list of points representing the cycle
    #Output: The optimized list
    @staticmethod
    def optimized_border_points(points):
        if points[0].equals(points[-1]):
            points.pop(-1)
        return points

    @staticmethod
    # Updates the number of line end points in all the regions the given points are contained in
    # Input: A set of game points
    # Output: None 
    def update_all_connections(points: Set[GraphicsPoint]):
        regions = set()
        for point in points:
            regions = regions.union(point.regions)
        for region in regions:
            region.open_connections = region.compute_connections()

    @staticmethod
    # Adds a given region to a given point or replaces a region of the given point with the given region
    #Input: A game point and a region
    #Output: None, the region and the game point were updated
    def add_replace_region(game_point, region):
        if not Region.full(game_point):  # A region can be added
            game_point.regions.add(region)
        else: # A region need to be replaced, (it always has to be the parent)
            Region.remove_region(game_point, region.parent)
            game_point.regions.add(region)

    # Removes a region from  a game points set of regions
    #Input: The game point and the region
    #Output: None, the game point now no longer has the given region in its set of regions
    @staticmethod
    def remove_region(game_point, region):
        if len(game_point.regions) > 0:
            game_point.regions.discard(region)
        if game_point in region.game_points:
            region.game_points.discard(game_point)

    ################################################
    # Non-Static Methods                           #
    ################################################

    # The constructor
    def __init__(self, game_points: Set[GraphicsPoint], border_points: List[Point], edge_map: Dict[int, Set[Path]],
                 exclusions: Set['Region'], parent: 'Region' = None, surf=None, cycle: List[Path] = []):
        self.surf = surf                        # Pygame surface used by draw functions
        self.game_points = game_points          # The visible points used in a game of Sprouts
        # Working with base region
        if not parent:
            for point in game_points:
                point.regions.add(self)
        self.border_points = Region.optimized_border_points(border_points) # A list of points forming the approximate border of the region
        self.cycle = cycle                                                 # A list of Paths forming the cycle that defines the region
        self.bounding_box = get_bounding_box(self.border_points)           # The minimum bounding box of the regions approximation
        self.edge_map = edge_map                                           # An adjancency map of all Paths in region, mapping Point-Index -> Set(Path)
        self.exclusions = exclusions                                       # A set of exclusions
        self.parent = parent                                               # The regions parent (the region it is excluded in)
        self.open_connections = self.compute_connections()                 # The amount of line end points that can be added inside the region

    # Adds point to region and adds region reference to the point
    # Input: Point and region
    # Output: None, the point and the region were updated
    def add_point(self, new_point):
        self.game_points.add(new_point)
        new_point.regions.add(self)

    # Removes the point from given region, and removes the region reference from the point
    # Input: Point and region
    # Output: None, the point and the region were updated
    def remove_point(self, point):
        if point in self.game_points:
            self.game_points.remove(point)
        point.regions.discard(self)
        self.edge_map.pop(point, None)

    # Generate an adjancency map for given region from a list of paths
    # Input: List of Paths, Region instance
    # Output: The edge map of given region instace was updated
    def compute_edge_map(self, paths: List[Path]):
        for path in paths:
            self.update_edge_map(path)

    # Computes the amount of line end points that can be added in given region instance
    # Input, Region instance
    # Output: The amount of line end points
    def compute_connections(self):
        connections = 0
        for point in self.game_points:
            connections += 3 - point.num_paths
        return connections

    # Adds the new paths to given region instance½
    # Input: region instance, list of paths, point
    # Output: The region instance is updated
    def update(self, paths, mid_point):
        for path in paths:
            self.update_edge_map(path)
        self.add_point(mid_point)

    # Reduces given region to an empty container region (split region)
    # A container region only provides structure in the region tree, but contains no relevant game information
    #Input: Region instance
    #Output: The given region is cleared
    def clear(self):
        points = self.game_points
        self.game_points = {}
        for point in points:
            self.remove_point(point)
        self.edge_map = {}
        self.open_connections = 0

    # Get the game points that are part of the border of the given region
    #Input: Region instance
    #Output: Set of game points
    def get_outer_set(self):
        outer_set = set()
        if self.cycle:
            for path in self.cycle:
                outer_set.add(path.start_point)
                outer_set.add(path.end_point)
        else:
            for point in self.border_points:
                if isinstance(point, GraphicsPoint):
                    outer_set.add(point)
        return outer_set

    # Manager for cycle detection
    # Manages search and validates that the found cycles are unique
    # Input: A region instance, the starting point of the search
    # Output: A list of all new and unique cycles
    def detect_cycles(self, p: GraphicsPoint):
        cycles = find_faces(p, self.edge_map)
        existing_cycles = [self.cycle]
        for exclusion in self.exclusions:
            existing_cycles.append(exclusion.cycle)
        new_cycles = []
        for cycle in cycles:
            new_cycle = True
            if not cycle:
                continue
            for existing_cycle in existing_cycles:
                if not set(cycle).symmetric_difference(set(existing_cycle)):
                    new_cycle = False
            if new_cycle:
                new_cycles.append(cycle)
        return new_cycles

    # Recursively searches for a region that still is able to add another path
    #Input: Starting region (root node)
    #Output: The first encountered open region or None
    def find_open_region(self):
        if self.compute_connections() > 1:
            return self
        else:
            for exclusion in self.exclusions:
                open = exclusion.find_open_region()
                if open:
                    return open
            return None

    # updates visibility level of game points, by transfering them to the new region
    # Input: A region instance and its new parent
    # Output: None, the regions transeferred all necessary points
    def transfer_game_points(self, parent):
        if parent:
            self.add_game_points(parent)
        for point in self.game_points:
            Region.add_replace_region(point, self)

    # Adds edges from given set of exclusions (regions) to given region (self)
    #Input: A region instance, a set of exclusions
    # Ouput: None, the region instance's edge map was updated
    def add_edges(self, regions):
        for region in regions:
            if region.game_points:
                outer_set = region.get_outer_set()
            else:
                outer_set = set()
            for point in outer_set:
                paths = region.edge_map[point.index]
                for path in paths:
                    if path.get_other_point(point) in outer_set:
                        self.update_edge_map(path)

    # Remove edges for given regions from current region (self)
    # Input: A region, a set of regions
    # Output: None, the given region's (self) edge map was updated
    def remove_edges(self, regions):
        for region in regions:
            if region.parent:
                border = set(region.parent.cycle)
                for path in region.cycle:
                    if not (path in border):
                        self.remove_from_edge_map(path)

    # Add a single path to a regions adjancency map
    #Input: A region, the new path
    #Output: None, the path was added to the regions edge map
    def update_edge_map(self, new_path):
        for point in [new_path.start_point.index, new_path.end_point.index]:
            if point in self.edge_map:
                path_set = self.edge_map[point]
                path_set.add(new_path)
            else:
                path_set = set([new_path])
            self.edge_map.update({point: path_set})

    # remove a path from given regions adjacency map
    #Input: A region instance, the path to be removed
    #Output: None, the path is removed from the regions edge map
    def remove_from_edge_map(self, path):
        for point in [path.start_point.index, path.end_point.index]:
            if point in self.edge_map:
                path_set = self.edge_map[point]
                if path_set and path in path_set:
                    path_set.remove(path)
                    if path_set:
                        self.edge_map.update({point: path_set})
                    else:
                        self.edge_map.pop(point, None)

    # Retrieves all game points in subtree of given region
    # Input: A region, root node
    # Output: A set of game points
    def points_in_subtree(self):
        points = set(self.game_points)
        for exclusion in self.exclusions:
            points = points.union(exclusion.points_in_subtree())
        return points

    # Determines whether a given region was split by the newly created cycle
    #Input: A region, the cycle that might split the region, the starting point for iterating the cycle
    #Output: Boolean value that stats whether the region is split or not
    def region_is_splitted(self, cycle, start_point):
        points_on_border = 0
        game_points_on_border = self.get_outer_set()
        #for point in self.border_points:
            #if isinstance(point, GraphicsPoint):
                #game_points_on_border.add(point)
        next_point = start_point
        for path in cycle:
            next_point = path.get_other_point(next_point)
            if next_point in game_points_on_border:
                points_on_border += 1
        return points_on_border >= 2

    # Find first non-container parent (non-split region)
    # Input: Starting region
    # Output: Closest parent region that is no container region
    def find_proper_parent(self):
        parent_region = self.parent
        while not parent_region.game_points:
            parent_region = parent_region.parent
        return parent_region

    # Transfers mssing game points and paths from parent to child
    # Input: a region and it parent region
    # Output: None, the transfer is completed
    def add_game_points(self, parent: 'Region'):
        points = parent.game_points.difference(self.game_points)
        missing_game_points = set()
        # Game point must know the regions they are contained in
        for point in points:
            if self.is_point_in_region(point) and not (point in self.game_points):
                missing_game_points.add(point)
        self.game_points = self.game_points.union(missing_game_points)

        paths_to_remove = set()
        for point in missing_game_points:
            Region.remove_region(point, parent)

            for path in parent.edge_map.get(point.index, []):
                # Add path if it is contained
                if path.start_point in self.game_points and path.end_point in self.game_points:
                    self.update_edge_map(path)

                if not (path.start_point in parent.game_points and path.end_point in parent.game_points):
                    paths_to_remove.add(path)

        for path in paths_to_remove:
            parent.remove_from_edge_map(path)

    # insert child region into region tree
    #Input: the region in which to insert (parent), the new region to be inserted
    #Output: Returns if the new region was splitted, also the region tree structure is updated
    def insert_rotation(self, new_region: 'Region'):
        # Find all exclusions in self, that need to be moved to new region
        rotation_regions = set()
        new_region_splitted = False
        clear_region = False
        for exclusion in self.exclusions:
            all_points_in_region = True # All game point of current exclusion are located within the new region
            all_on_border = True # All of the current exclusion's game point are located on the border of the new region
            border_set = new_region.get_outer_set() # All game points on the border of the new region
            on_border = 0 # amount of the exclusion's game points that are located on the border of the new region

            #Get the game point of the current exclusion
            if exclusion.game_points:
                points_inside_exclusion = exclusion.game_points
            else:
                points_inside_exclusion = exclusion.get_outer_set()

            #Iterate the current exclusion's game points
            for game_point in points_inside_exclusion:
                if game_point in border_set: # Is the point part of the new regions border?
                    on_border += 1
                if not (new_region.is_point_in_polygon(game_point) or game_point in new_region.game_points): #Is the point inside the new region?
                    all_points_in_region = False
                    break

            # The exclusion lies inside new_region (sharply)
            if all_points_in_region and on_border < 1:
                rotation_regions.add(exclusion)
            elif all_points_in_region and on_border > 1:
                # The exclusion either split the new_region in two
                # Or is a neighbouring region
                exclusion_cycle = set(exclusion.cycle)
                all_paths_in_region = True
                # Validate whether all paths in exclusion are contained within new_region
                for path in exclusion_cycle:
                    if not path in new_region.cycle:
                        # Find if path is inside the region
                        path_mid_point = Path.calculate_mid_point(path)
                        if not new_region.is_point_in_region(path_mid_point):
                            all_paths_in_region = False
                            break
                # The exclusion is contained within new_region (and new_region is split in two)
                if all_paths_in_region:
                    if new_region_splitted:
                        clear_region = True
                    else:
                        new_region_splitted = True
                    rotation_regions.add(exclusion)

        # Update the parent regions exclusions
        parent_regions = self.exclusions.difference(rotation_regions)
        parent_regions.add(new_region)
        self.exclusions = parent_regions

        #Add exclusions to the new region
        new_region.exclusions = rotation_regions
        #Update the parent of the new region's exclusions
        for region in rotation_regions:
            region.parent = new_region
        #Update the new region's edge map and the parent region's (self)
        new_region.add_edges(rotation_regions)
        self.remove_edges(rotation_regions)
        # Is the new region a container region? If so, clear it
        if clear_region:
            new_region.clear()
        return new_region_splitted

    # Updates the region tree and modifies the regions accordingly
    # Paths list may NOT be longer than 2 elements
    # Manager for the updating of the region tree
    # Input: the region to be updated, the new paths (a list), the new game point
    # Output: None, the region tree is updated
    def update_region_tree(self, paths, mid_point):
        if len(paths) > 2 or not paths: #Validates the given path list input
            #Should never be reached, unless the game already broke earlier
            raise Exception("the list of paths was empty or longer than 2 elements")
        #Update the current region (self)
        self.update(paths, mid_point)
        start_path, end_path = paths[0], paths[1]
        # Get the two points, where a new line was drawn in between
        start_point = start_path.get_other_point(mid_point)
        end_point = end_path.get_other_point(mid_point)
        # Check to see if any cycles are made
        cycles = self.detect_cycles(mid_point)

        last_cycle_split, container_region, split_region = False, None, False
        child_regions = set()
        # Set of points that will change the amount of open connections for some regions
        points_connections_update = set([start_point, mid_point, end_point])

        if cycles: #If cycles were found
            for cycle in cycles:
                if last_cycle_split and container_region:
                    #The current cycle is cycle defines a region, which is a child of the most recent added region of the tree
                    child_region = container_region.create_region_from_cycle(cycle)
                    last_cycle_split = container_region.insert_rotation(child_region)
                else:
                    # The new region is a normal addition to the tree
                    child_region = self.create_region_from_cycle(cycle)
                    last_cycle_split = self.insert_rotation(child_region)
                child_region.compute_edge_map(cycle)

                if last_cycle_split and not container_region:
                    # Cycle has been split and is an empty container
                    container_region = child_region
                    split_region = True
                else:
                    child_regions.add(child_region)

            if not container_region and len(cycles) == 2:
                # The region that was inserted into, was split and has to be updated
                for child_region in child_regions:
                    parent_region = child_region.parent
                    while not parent_region.game_points:
                        parent_region = parent_region.parent

                    child_region.transfer_game_points(parent_region)

                self.clear()
            elif split_region:
                container_region.clear()

                # For all outer points in exclusions, if they are not outer points in the container region, they
                # can't be visible for other regions

                # Compute points to move further down in the subtree
                points_to_move = container_region.points_in_subtree().difference(container_region.get_outer_set())
                proper_parent = container_region.find_proper_parent()
                #Transfer points to child, from non-empty parent
                for point in points_to_move:
                    proper_parent.remove_point(point)

                for child_region in child_regions:
                    # Find non-empty parent for current child
                    parent_region = child_region.parent
                    while not parent_region.game_points:
                        parent_region = parent_region.parent

                    #Transfer game points to child regions
                    child_region.transfer_game_points(parent_region)

                #Add points that changed state
                points_connections_update = points_connections_update.union(points_to_move)
            else:
                #Transfer game point from actual parent to child
                child_region.transfer_game_points(child_region.find_proper_parent())
        #Update all affected regions open connections
        Region.update_all_connections(points_connections_update)

    # Create a new region instance from given cycle
    #Input: Current region, a cycle to create a new exclusions
    #Output: The new region
    def create_region_from_cycle(self, cycle: List[Path]):
        #Initialize the new regions fields as variables
        border_points = []
        game_points = set()
        edge_map = {}
        start_path = cycle[0]


        start_point = start_path.start_point
        end_point = start_path.end_point

        # Case if we rotate the wrong way through the cycle
        if not cycle[1].get_other_point(end_point):
            start_point = end_point

        #iterate the cycle to create the border_points approximation of the region
        border_points.append(start_point)
        game_points.add(start_point)

        for path in cycle:
            path_approximation = path.approximate()
            if path_approximation[0].equals(start_point):
                border_points.extend(path_approximation[1:])
                print(path.to_string(False))
            elif path_approximation[-1].equals(start_point):
                #The path was added inverse, the list has to be flipped
                path_approximation.reverse()
                border_points.extend(path_approximation[1:])
                print(path.to_string(True))
            else:
                raise Exception("path did not match path_approximation")
            next_point = path.get_other_point(start_point)
            start_point = next_point
            game_points.add(next_point)
        print("-----------------------")
        return Region(game_points, border_points, {}, set(), self, self.surf, cycle=cycle)

    #Pygame draw function
    # Draw the border approximation of a region
    # Input: Region, Surface to be drawn upon
    # Output: None, the region is being drawn
    def draw(self, SCREEN):
        border_points = [p.pos() for p in self.border_points]
        pygame.draw.polygon(SCREEN, gc.REGION_COLOR, border_points, 5)

        for p in self.game_points:
            p.draw(SCREEN)
        for region in self.exclusions:
            region.draw(SCREEN)

    ###############################################
    # Winding Number Algorithm                    #
    ###############################################
    # Check whether a given point is inside given region (without checking its children)
    #Input: a region and a point
    #Output: Boolean Value that states whether the point is contained in given region or not
    def is_point_in_polygon(self, point: Point):
        points = [point, None]
        if is_inside_box(point, self.bounding_box):
            # Point is inside current bounding box
            # Compute winding number inorder to determine if point is in current polygon
            last_edge_type = None
            last_edge_intersected = False
            winding_number = 0
            point_line = ImplicitLine(point, Point(self.bounding_box[1].x, point.y))
            for i in range(-1, len(self.border_points) - 1):
                if self.border_points[i].x == self.border_points[i + 1].x and \
                        self.border_points[i].y == self.border_points[i + 1].y:
                    continue
                border_line = ImplicitLine(self.border_points[i], self.border_points[i + 1])
                points[1] = border_line.intersection(point_line)
                # If there is an intersection, the winding number changes
                min_x, max_x = get_min_max_x(self.border_points[i], self.border_points[i+1])
                if type(points[1]) == Point and is_in_range(points[1].x, min_x, max_x):
                    if (point.equals(points[1])):
                        return True
                    winding_number, last_edge_type, last_edge_intersected = \
                        PointInPolygon.update_winding_number(points, winding_number, border_line, \
                                                             last_edge_intersected, last_edge_type)
            if abs(winding_number) > 0:
                return True
        return False

    # Return whether given point is inside this region or not
    # Only checks direct exclusions
    #Input: a region and a point
    #Output: Boolean Value that states whether the point is contained in given region or not
    def is_point_in_region(self, point: Point, in_child=False):
        # evaluate if point is inside bounding box of this region
        points = [point, None]
        if is_inside_box(point, self.bounding_box):
            if not in_child or not self.game_points:
                # Evaluate if the given point lies inside any region contained inside current region
                for exclusion in self.exclusions:
                    in_subregion = exclusion.is_point_in_region(point, True)
                    if in_subregion:
                        return False
            # Point is inside current bounding box
            # Compute winding number inorder to determine if point is in current polygon
            last_edge_type = None
            last_edge_intersected = False
            winding_number = 0
            point_line = ImplicitLine(point, Point(self.bounding_box[1].x, point.y))
            for i in range(-1, len(self.border_points) - 1):
                if self.border_points[i].x == self.border_points[i + 1].x and \
                        self.border_points[i].y == self.border_points[i + 1].y:
                    continue
                border_line = ImplicitLine(self.border_points[i], self.border_points[i + 1])
                points[1] = border_line.intersection(point_line)
                # If there is an intersection, the winding number changes
                min_x, max_x = get_min_max_x(self.border_points[i], self.border_points[i+1])
                if type(points[1]) == Point and is_in_range(points[1].x, min_x, max_x):
                    if (point.equals(points[1])):
                        return True
                    winding_number, last_edge_type, last_edge_intersected = \
                        PointInPolygon.update_winding_number(points, winding_number, border_line, \
                                                             last_edge_intersected, last_edge_type)
            if abs(winding_number) > 0:
                return True
        return False

    # Returns the region the given point is contained in, or None if the region wasn't found
    # Utilizes the  winding number algorithm for solving PIP problems
    # Is called on the region where the search should start
    #Input: a region and a point
    #Output: The region that contains the point or None if no such region was found
    def find_region(self, point: Point):
        points = [point, None]
        # evaluate if point is inside bounding box of this region
        if is_inside_box(point, self.bounding_box):
            # Evaluate if the given point lies inside any region contained inside current region
            for exclusion in self.exclusions:
                # If so, return that region
                in_subregion = exclusion.find_region(point)
                if in_subregion:
                    return in_subregion

            if not self.game_points:
                return None
            # Point is inside current bounding box
            # Compute winding number inorder to determine if point is in current polygon
            last_edge_type = None
            last_edge_intersected = False
            winding_number = 0
            point_line = ImplicitLine(point, Point(self.bounding_box[1].x, point.y))
            for i in range(-1, len(self.border_points) - 1):
                if self.border_points[i].x == self.border_points[i + 1].x and \
                        self.border_points[i].y == self.border_points[i + 1].y:
                    continue
                border_line = ImplicitLine(self.border_points[i], self.border_points[i + 1])
                points[1] = border_line.intersection(point_line)
                # If there is an intersection, the winding number changes
                min_x, max_x = get_min_max_x(self.border_points[i], self.border_points[i+1])
                if type(points[1]) == Point and is_in_range(points[1].x, min_x, max_x):
                    if (points[0].equals(points[1])):
                        return self
                    winding_number, last_edge_type, last_edge_intersected = \
                        PointInPolygon.update_winding_number(points, winding_number, border_line, \
                                                             last_edge_intersected, last_edge_type)
            if abs(winding_number) > 0:
                return self
        return None
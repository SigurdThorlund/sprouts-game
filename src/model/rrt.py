import random

import pygame

import src.config.game_config as gc
from src.model.bounding_box import get_bounding_box
from src.model.path import Path
from src.model.point import Point, GraphicsPoint


### MAIN RESPONSIBILITY: THOMAS AAMAND WITTING S184192 ###
class RRT:
    def __init__(self, start, paths, main_screen, points):
        # start has to be a graphicspoint
        if not isinstance(start, GraphicsPoint):
            raise Exception("Start point is not of type GraphicsPoint")

        self.points = points
        self.screen = main_screen
        self.paths = paths
        self.start = Node(start)
        self.nodes = [self.start]
        self.growth = 50

        # Draw circle on own surface
        self.image = pygame.Surface([gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT])
        self.image.fill(gc.WHITE)

        # All white is considered to be transparent
        self.image.set_colorkey(gc.WHITE)

        self.rect = self.image.get_rect()


    # Draws the new node of the tree
    def draw(self, node):
        pygame.draw.circle(self.image, (122, 200, 122), (int(node.point.x), int(node.point.y)), 2)
        if not node.parent:
            return
        pygame.draw.line(self.image, (200, 100, 200), (int(node.point.x), int(node.point.y)),
                         (int(node.parent.point.x), int(node.parent.point.y)), 1)

        pygame.display.update()

    # Builds the tree and returns the path from start to goal when it is found
    def build(self, goal):
        # goal has to be a graphicspoint
        if not isinstance(goal, GraphicsPoint):
            raise Exception("Goal point is not of type GraphicsPoint")

        # The regions shared between start and goal
        shared_regions = self.start.point.regions & goal.regions
        roi_points = [p for r in shared_regions for p in r.border_points]
        # The bounding box surrounding the shared regions
        roi = self.roi(roi_points)

        fail_counter = 1

        while True:
            cont = False
            # PyGame event handler, in order to cancel the search by pressing escape
            # Also prevents game from crashing as events needs to be popped from the stack
            # as otherwise Windows will think the game is unresponsive.
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return [], None


            # generate random point
            qrand = self.rand_free_conf_roi(roi)
            # find point nearest to this random point
            qnearest = self.nearest_nodes(qrand)
            qnear = None
            valid = False
            qnew = None

            # Create edge between qnew and one of the 15 nearest points (if possible)
            for i in range(min(len(qnearest), 15)):
                print(i)
                qnear = qnearest[i]

                # create new point a distance of self.growth away from qnear, in the direction of the random point
                qnew = self.new_conf(qnear, qrand)

                # point is outside screen, generate new point
                if qnew.point.x < 0 or qnew.point.x >= gc.WINDOW_WIDTH or qnew.point.y < 0 or qnew.point.y >= gc.WINDOW_HEIGHT:
                    continue


                shares_region = False
                for region in shared_regions:
                    if region.is_point_in_region(qnew.point):
                        shares_region = True
                if not shares_region:
                    continue

                path = self.build_sub_path(qnear, alt_start_node=qnew)

                # shrink the growth factor
                if not self.valid_sub_path(path):
                    if fail_counter > 25 and self.growth > 50:
                        self.growth = self.growth * 3 // 4
                        fail_counter = 1
                    elif self.growth > 50:

                        fail_counter += 1
                    valid = False
                    continue
                else:
                    valid = True
                    break

            if not valid or not qnew:
                continue


            qnew.parent = qnear
            self.nodes.append(qnew)
            print(len(self.nodes))

            # draw
            self.draw(qnew)
            self.screen.blit(self.image, self.rect)

            # optional, just to make 'prettier' paths (i.e. not very long straight lines)
            # if goal.distance_sq(qnew.point) > 10000:
            #     continue

            if goal.equals(self.start.point) and len(self.nodes) < 3:
                continue

            # Build sub path from goal node and validate it
            goal_node = Node(goal, qnew)
            path = self.build_sub_path(goal_node)
            if not self.valid_sub_path(path):
                continue

            # if code gets to here, a path, likely to be completely valid, can be found
            path_points, suggested_path = self.build_complete_path(goal_node)

            return path_points, suggested_path

    def build_complete_path(self, node):
        path_points = []
        while node:
            path_points.append(node.point)
            node = node.parent
        return path_points, Path.from_points(path_points)

    def build_sub_path(self, node, alt_start_node=None):
        path_points = []
        if alt_start_node:
            path_points.append(alt_start_node.point)
        i = 0
        while node and i < 4:
            path_points.append(node.point)
            node = node.parent
            i += 1

        return Path.from_points_non_graphic(path_points)

    def valid_sub_path(self, path):
        for p in self.paths:
            if p.intersects(path):
                return False
        for point in self.points:
            if path.point_touches_path(point):
                return False
        return True

    # Returns a point a distance of self.growth away from qnear in the direction of qrand
    def new_conf(self, qnear, qrand):
        if qnear.point.distance_sq(qrand.point) < self.growth * self.growth:
            return qrand
        temp = qrand.point - qnear.point
        temp = temp.normalized()
        return Node(qnear.point + temp.scalar(self.growth))

    # returns the nearest node
    def nearest_node(self, node):
        return min(self.nodes, key=lambda x: x.point.distance_sq(node.point))

    # returns a sorted list based on distance from a given node
    def nearest_nodes(self, node):
        return sorted(self.nodes, key=lambda x: x.point.distance_sq(node.point))

    # legacy function returning a point from all over game board
    def rand_free_conf(self):
        return Node(Point(random.randint(-50, gc.WINDOW_WIDTH+50), random.randint(-50, gc.WINDOW_HEIGHT+50)))

    # returns point within a bounding box/region of interest
    def rand_free_conf_roi(self, roi):
        return Node(Point(random.randint(int(roi[0].x), int(roi[1].x)), random.randint(int(roi[0].y), int(roi[1].y))))

    # debug function which draws the edge between qnew and qnear in red. Should be used to highlight paths which rrt
    # failed on
    def draw_fail(self, qnew, qnear):
        pygame.draw.line(self.image, (255, 0, 0), (int(qnew.point.x), int(qnew.point.y)),
                         (int(qnear.point.x), int(qnear.point.y)), 1)

        self.screen.blit(self.image, self.rect)
        pygame.display.update()

    def roi(self, points):
        upper_left, lower_right = get_bounding_box(points)
        return upper_left, lower_right


class Node:
    def __init__(self, point, parent=None):
        self.point = point
        self.parent = parent
        self.visited = 0

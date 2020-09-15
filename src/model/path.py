from typing import List

import pygame

import src.config.game_config as gc
from src.model.bezier_intersection import Segment
from src.model.cubic_bezier import GraphicsBezier, Bezier
from src.model.point import Point, GraphicsPoint

### MAIN RESPONSIBILITY FOR INTERSECTION FUNCTIONS: OLAV NØRGAARD OLSEN S184195 ###
### MAIN RESPONSIBILITY FOR CALCULATING BEZIERS/CONTROL POINTS: THOMAS AAMAND WITTING S184192 ###
class Path:
    def __init__(self, curves: List[Bezier], start_point, end_point, player = None):
        self.image = pygame.Surface([gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT])
        self.image.fill(gc.WHITE)
        self.image.set_colorkey(gc.WHITE)

        if player == "player 1":
            self.color = gc.PLAYER_1_COLOR
        elif player == "player 2":
            self.color = gc.PLAYER_2_COLOR
        else:
            self.color = gc.LINE_COLOR

        self.beziers = curves
        self.rect = self.image.get_rect()
        self.start_point = start_point
        self.end_point = end_point
        self._clicks = []
        self.approximation = []

        for b in self.beziers:
            if isinstance(b, GraphicsBezier):
                self.image.blit(b.image, (0, 0))

    def change_color(self, color):
        arr = pygame.PixelArray(self.image)
        arr.replace(gc.LINE_COLOR, color)
        del arr

    def draw(self, surf):
        surf.blit(self.image, self.rect)

    def get_other_point(self, p):
        if p == self.start_point:
            return self.end_point
        elif p == self.end_point:
            return self.start_point
        else:
            return None

    def calculate_mid_point(self):
        bezier = self.beziers[len(self.beziers) // 2]

        return bezier.evaluate(0.5)


    @classmethod
    def from_points(cls, clicks, color=gc.LINE_COLOR):
        return cls(compute_graphics_beziers(clicks, color), clicks[0], clicks[-1])

    @classmethod
    def from_points_non_graphic(cls, clicks):
        return cls(compute_beziers(clicks), clicks[0], clicks[-1])

    def to_string(self, flipped):
        if flipped:
            return "end: " + str(self.end_point.index) + ", start: " + str(self.start_point.index)
        else:
            return "start: " + str(self.start_point.index) + ", end: " + str(self.end_point.index)

    # Returns a list of points, as an approximation of the path
    def approximate(self) -> List[Point]:
        if not self.approximation:
            point_list = self.beziers[0].approximate_bezier()
            for curve in self.beziers[1:]:
                curve_points = curve.approximate_bezier()
                if curve_points[0] == point_list[-1]:
                    point_list.extend(curve_points[1:])
                else:
                    point_list.extend(curve_points)
            self.approximation = point_list
        return self.approximation

    # assumes that only the last 2 (?) points have been changed
    def redraw(self, clicks, color):
        compute_all = False
        if len(clicks) - 1 > len(self._clicks):
            self._clicks = clicks[:-1]
            compute_all = True
            print("asdfgsdfg")

        if len(clicks) > 4:
            if compute_all:
                new_beziers = compute_graphics_beziers(clicks, color)
                self.beziers = new_beziers
            else:
                clicks = clicks[-4:]
                new_beziers = compute_graphics_beziers(clicks, color)
                self.beziers[-len(new_beziers) + 1:] = new_beziers[1:]
        else:
            new_beziers = compute_graphics_beziers(clicks, color)
            self.beziers = new_beziers

        self.image.fill(gc.WHITE)
        for b in self.beziers:
            self.image.blit(b.image, (0, 0))

    def point_touches_path(self, point: GraphicsPoint) -> bool:
        approximation = self.approximate()

        if point.equals(self.start_point) or point.equals(self.end_point):
            return False

        for i in range(len(approximation) - 1):
            segment_start = approximation[i]
            segment_end = approximation[i + 1]

            if segment_start.distance_sq(self.start_point) < 81 and point.distance_sq(self.start_point) < 81:
                continue
            if segment_end.distance_sq(self.end_point) < 81 and point.distance_sq(self.end_point) < 81:
                continue

            segment = Segment(segment_start, segment_end)

            if segment.over_segment(point):
                if abs(segment.dist(point)) < point.radius:
                    return True
        return False

    def intersects_bezier(self, bez: Bezier):
        intersections = []
        for b in self.beziers:
            intersections.extend(b.intersects(bez))
        return intersections

    def __intersections(self, other, beziers):
        exclusion_points = []

        if self.start_point == other.start_point or self.end_point == other.start_point:
            exclusion_points.append(other.start_point)

        if self.start_point == other.end_point or self.end_point == other.end_point:
            exclusion_points.append(other.end_point)

        intersections = []
        for i in range(len(self.beziers)):
            for j in range(len(beziers)):
                b = self.beziers[i]
                b2 = beziers[j]

                intersects = b.intersects(b2)

                if not intersects:
                    continue

                i_at_end = i == 0 or i == len(self.beziers) - 1
                j_at_end = j == 0 or j == len(beziers) - 1

                if i_at_end and j_at_end:
                    for p in intersects:
                        valid_intersection = True

                        for q in exclusion_points:
                            if p.distance_sq(q) < 81:
                                valid_intersection = False
                                break

                        if valid_intersection:
                            intersections.append(p)
                else:
                    intersections.extend(intersects)

        return intersections

    def self_intersections(self):
        intersections = []
        bezier_count = len(self.beziers)
        for i in range(bezier_count):
            for j in range(i + 1, bezier_count):
                b1 = self.beziers[i]
                b2 = self.beziers[j]
                intersects = b1.intersects(b2)
                
                # Are the beziers coming right after each other?
                # Avoid finding intersection between start and end point
                if j - i == 1:
                    for p in intersects:
                        if p.distance_sq(b1.end_point) > 5:
                            intersections.append(p)
                else:
                    # Skip points lie on the start/end point
                    for p in intersects:
                        if p.distance_sq(self.start_point) < 1:
                            continue
                        elif p.distance_sq(self.end_point) < 1:
                            continue
                        intersections.append(p)
        return intersections

    def intersects(self, other):
        return self.__intersections(other, other.beziers)

    def partial_intersects(self, other):
        if len(self.beziers) < 3:
            return self.__intersections(other, other.beziers)
        else:
            return self.__intersections(other, other.beziers[len(other.beziers) - 2:])

    def __str__(self):
        return "Path(%d,%d)" % (self.start_point.index, self.end_point.index)


# Method as described in https://www.youtube.com/watch?v=nNmFLWup4_k 7m50s
def calc_control_points(start, middle, end):
    # Compute vectors to next and previous anchor point
    diff_vec_1 = start - middle
    diff_vec_2 = end - middle

    # Compute control points as tangents
    dir_vec_1_normalized = diff_vec_1.normalized() - diff_vec_2.normalized()
    dir_vec_2_normalized = -dir_vec_1_normalized

    # Scale control points accordingly
    control_point_1 = dir_vec_1_normalized.scalar(diff_vec_1.length() / 5) + middle
    control_point_2 = dir_vec_2_normalized.scalar(diff_vec_2.length() / 5) + middle

    return control_point_1, control_point_2


def add_path(p_0: Point, p_1: Point, clicks: List[Point]):
    beziers = compute_graphics_beziers(clicks, gc.LINE_COLOR)

    bezier_count = len(beziers)
    mid_count = bezier_count // 2
    # If the amount of bezier curves is even
    if bezier_count % 2 == 0:
        mid = beziers[mid_count - 1].end_point
        mid_point = GraphicsPoint(mid.x, mid.y, True)

        start_beziers = beziers[0:mid_count]
        if start_beziers[-1].end_point.equals(mid_point):
            start_beziers[-1].end_point = mid_point
        end_beziers = beziers[mid_count:]
        if end_beziers[0].start_point.equals(mid_point):
            end_beziers[0].start_point = mid_point

        start_path = Path(start_beziers, p_0, mid_point)
        end_path = Path(end_beziers, mid_point, p_1)
    # If the amount of bezier curve is odd
    else:
        # Split bezier curvers into two paths and find middle point
        (bezier_first_end, bezier_second_start) = beziers[mid_count].split(0.5)
        mid = beziers[mid_count].evaluate(0.5)
        mid_point = GraphicsPoint(mid.x, mid.y, True)

        start_beziers = beziers[:mid_count]
        start_beziers.append(GraphicsBezier.from_bezier(bezier_first_end))
        if start_beziers[-1].end_point.equals(mid_point):
            start_beziers[-1].end_point = mid_point

        end_beziers = beziers[mid_count:]
        # end_beziers.insert(0, bezier_second_start)
        end_beziers[0] = GraphicsBezier.from_bezier(bezier_second_start)
        if end_beziers[0].start_point.equals(mid_point):
            end_beziers[0].start_point = mid_point
        start_path = Path(start_beziers, p_0, mid_point)
        end_path = Path(end_beziers, mid_point, p_1)

    # Add path to points
    p_0.add_to_path(start_path)
    p_1.add_to_path(end_path)
    mid_point.add_to_path(start_path)
    mid_point.add_to_path(end_path)

    return start_path, end_path, mid_point


def compute_beziers(clicks):
    control_points = []
    beziers = []

    if len(clicks) < 2:
        raise ValueError(
            "Number of points must be greater than or equal to 2")

    # Calculate first control point - halfway between the first and second point
    control_points.append(
        clicks[1] + (clicks[0] - clicks[1]).scalar(0.5))

    for i in range(1, len(clicks) - 1):
        control_point_1, control_point_2 = calc_control_points(clicks[i - 1],
                                                               clicks[i],
                                                               clicks[i + 1])

        control_points.append(control_point_1)
        control_points.append(control_point_2)

    # Calculate last control point - halfway between the last and second-to-last point
    control_points.append(
        clicks[-1] + (clicks[-2] - clicks[-1]).scalar(0.5))

    # Add bezier curve for the two edge cases with one anchor point on the start or end point.
    # If we have only two anchor points we only add a single curve
    bezier_start = Bezier(clicks[0], clicks[1], control_points[0], control_points[1])
    bezier_end = Bezier(clicks[-2], clicks[-1], control_points[-2], control_points[-1])

    beziers.append(bezier_start)

    # Opt out early if we only have two anchorpoints.
    if (len(clicks) == 2): return beziers

    # j counts through the control points, a pair at a time
    j = 2
    for i in range(1, len(clicks) - 2):
        b = Bezier(clicks[i], clicks[i + 1], control_points[j], control_points[j + 1])
        beziers.append(b)
        j += 2

    beziers.append(bezier_end)

    return beziers


def compute_graphics_beziers(clicks, color):
    control_points = []
    beziers = []

    if len(clicks) < 2:
        raise ValueError(
            "Number of points must be greater than or equal to 2")

    # Calculate first control point - halfway between the first and second point
    control_points.append(
        clicks[1] + (clicks[0] - clicks[1]).scalar(0.5))

    for i in range(1, len(clicks) - 1):
        control_point_1, control_point_2 = calc_control_points(clicks[i - 1],
                                                               clicks[i],
                                                               clicks[i + 1])

        control_points.append(control_point_1)
        control_points.append(control_point_2)

    # Calculate last control point - halfway between the last and second-to-last point
    control_points.append(
        clicks[-1] + (clicks[-2] - clicks[-1]).scalar(0.5))

    # Add bezier curve for the two edge cases with one anchor point on the start or end point.
    # If we have only two anchor points we only add a single curve
    bezier_start = GraphicsBezier(clicks[0], clicks[1], color, control_points[0], control_points[1])
    bezier_end = GraphicsBezier(clicks[-2], clicks[-1], color, control_points[-2], control_points[-1])

    beziers.append(bezier_start)

    # Opt out early if we only have two anchorpoints.
    if (len(clicks) == 2): return beziers

    # j counts through the control points, a pair at a time
    j = 2
    for i in range(1, len(clicks) - 2):
        b = GraphicsBezier(clicks[i], clicks[i + 1], color, control_points[j], control_points[j + 1])
        beziers.append(b)
        j += 2

    beziers.append(bezier_end)

    return beziers

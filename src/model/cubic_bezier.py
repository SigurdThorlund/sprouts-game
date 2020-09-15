from typing import List, Tuple

import pygame

import src.config.game_config as gc
from src.model.bezier_intersection import ConvexHullNPoint, Fatline
from src.model.point import Point

INTERSECT_DIST_SQ = 4
PARAMETER_CHANGE = 0.80
BOUNDING_BOX = 3  # Area before recursion is stopped

BOUNDING_TRUE = 1
BOUNDING_BIG = 0
BOUNDING_FAR = -1

INTERSECT_DIFF = 0.01


### MAIN RESPONSIBILITY: OLAV NØRGAARD OLSEN S184195 ###

def lerp(start_p, end_p, t):
    diff_x = end_p.x - start_p.x
    diff_y = end_p.y - start_p.y
    return Point(start_p.x + diff_x * t, start_p.y + diff_y * t)


def quadratic_curve(start_p, end_p, control_p, t):
    t_sub = 1 - t
    start_p.scalar(t_sub * t_sub) + control_p.scalar(2 * t * t_sub) + end_p.scalar(t * t)


# Computes the cubic bezier given by
def cubic_curve(start_p, end_p, control_p1, control_p2, t):
    t_sub = 1 - t
    t_sub_sq = t_sub * t_sub
    t_sq = t * t

    # Factors for the cubic curve
    start_scalar = t_sub * t_sub_sq
    end_scalar = t_sq * t
    control_1_scalar = 3 * t_sub_sq * t
    control_2_scalar = 3 * t_sub * t_sq

    res_x = start_p.x * start_scalar + end_scalar * end_p.x + control_1_scalar * control_p1.x \
            + control_2_scalar * control_p2.x
    res_y = start_p.y * start_scalar + end_scalar * end_p.y + control_1_scalar * control_p1.y \
            + control_2_scalar * control_p2.y

    return Point(res_x, res_y)


def intersect_subcurves(self_split: 'Bezier', other_split: 'Bezier') -> List[Tuple[float, float]]:
    if self_split.start_point.distance_sq(self_split.end_point) < 0.1:
        other_dir = (other_split.end_point - other_split.start_point).normalized().scalar(0.1)
        self_split = Bezier(self_split.start_point, self_split.start_point + other_dir)

    # Find intervals for the parallel fatline
    parallel_fatline = Fatline(self_split)
    parallel_convex_hull = ConvexHullNPoint(parallel_fatline.distance_control_points(other_split))
    parallel_intersections = parallel_convex_hull.fatline_intersection(parallel_fatline)

    # Find intervals for the perpendicular fatline
    perpendicular_fatline = Fatline(self_split, perpendicular=True)
    perpendicular_convex_hull = ConvexHullNPoint(perpendicular_fatline.distance_control_points(other_split))
    perpendicular_intersections = perpendicular_convex_hull.fatline_intersection(perpendicular_fatline)

    return_intervals = perpendicular_intersections

    # Does more than one interval occur?
    if len(parallel_intersections) > 0:
        if len(perpendicular_intersections) > 0:
            # Compute entire parameter interval for the parallel intersections
            parallel_length = 0
            for intersect_interval in parallel_intersections:
                parallel_length += intersect_interval[1] - intersect_interval[0]

            # Compute entire parameter interval for the perpendicular intersections
            perpendicular_length = 0
            for intersect_interval in perpendicular_intersections:
                perpendicular_length += intersect_interval[1] - intersect_interval[0]

            # Find the interval which gives the tightest bounds
            if parallel_length > perpendicular_length:
                return_intervals = perpendicular_intersections
            else:
                return_intervals = parallel_intersections
        else:
            return_intervals = parallel_intersections
    return return_intervals


def bezier_interval_project(tup: Tuple[float, float], t_min: float, t_max: float) -> Tuple[float, float]:
    return t_min + tup[0] * (t_max - t_min), t_min + tup[1] * (t_max - t_min)


def bezier_interval_distance(curve: 'Bezier', interval: Tuple[float, float]):
    return curve.evaluate(interval[0]).distance(curve.evaluate(interval[1]))


def bezier_close_enough(curve_0: 'Bezier', curve_1: 'Bezier') -> int:
    if curve_0.bounding_box_area() < BOUNDING_BOX and curve_1.bounding_box_area() < BOUNDING_BOX:
        # Both Beziérs are reduced to 1 pixel. If close enough, intersection is found
        if curve_0.start_point.distance_sq(curve_1.start_point) < INTERSECT_DIST_SQ or \
                curve_0.end_point.distance_sq(curve_1.start_point) < INTERSECT_DIST_SQ or \
                curve_0.start_point.distance_sq(curve_1.end_point) < INTERSECT_DIST_SQ or \
                curve_0.end_point.distance_sq(curve_1.end_point) < INTERSECT_DIST_SQ:
            return 1
        return -1
    return 0


class Bezier:
    def __init__(self, start_point, end_point, control_point_1=None, control_point_2=None):

        # if no control points, set to be start and end point
        # this creates a straight line
        if control_point_1 is None:
            control_point_1 = start_point
        if control_point_2 is None:
            control_point_2 = end_point

        self.start_point = start_point
        self.end_point = end_point
        self.control_point_1 = control_point_1
        self.control_point_2 = control_point_2
        self.points = [start_point, control_point_1, control_point_2, end_point]

    def evaluate(self, t):
        return cubic_curve(self.start_point, self.end_point, self.control_point_1, self.control_point_2, t)

    # Splits the curve into 2 cubic beziers at the specified interval using de Casteljau's algorithm
    def split(self, t) -> ('Bezier', 'Bezier'):
        # https://pages.mtu.edu/~shene/COURSES/cs3621/NOTES/spline/Bezier/de-casteljau.html

        # Splitting at start/end makes no difference
        if t == 1:
            return [self, Bezier(self.end_point, self.end_point, self.end_point, self.end_point)]
        if t == 0:
            return [Bezier(self.start_point, self.start_point, self.start_point, self.start_point), self]

        split_point = self.evaluate(t)

        m_0 = lerp(self.start_point, self.control_point_1, t)
        m_1 = lerp(self.control_point_1, self.control_point_2, t)
        m_2 = lerp(self.control_point_2, self.end_point, t)

        tangent_0 = lerp(m_0, m_1, t)
        tangent_1 = lerp(m_1, m_2, t)

        return [Bezier(self.start_point, split_point, m_0, tangent_0),
                Bezier(split_point, self.end_point, tangent_1, m_2)]

    # Special implementation de Casteljau's algorithm. Returns the Bézier from t_min to t_max
    def split_interval(self, t_min: float, t_max: float) -> ('Bezier'):
        # https://pages.mtu.edu/~shene/COURSES/cs3621/NOTES/spline/Bezier/de-casteljau.html
        if t_min == 0 and t_max == 1:
            return self

        start_point = self.evaluate(t_min)
        end_point = self.evaluate(t_max)

        second_split_t = (t_max - t_min) / (1 - t_min)

        # Compute upper bezier for first split
        first_control_point_2 = lerp(self.control_point_2, self.end_point, t_min)
        first_mid_point = lerp(self.control_point_1, self.control_point_2, t_min)
        first_control_point_1 = lerp(first_mid_point, first_control_point_2, t_min)

        # Compute lower bezier for second split
        control_point_1 = lerp(start_point, first_control_point_1, second_split_t)
        second_mid_point = lerp(first_control_point_1, first_control_point_2, second_split_t)
        control_point_2 = lerp(control_point_1, second_mid_point, second_split_t)

        return Bezier(start_point, end_point, control_point_1, control_point_2)

    # Determines whether 2 CubicBeziers intersect, using Bezier clipping. Returns a list of intersections
    def intersects(self, other: 'Bezier') -> List[Point]:
        intersections = []
        parameter_stack = [(0, 1, 0, 1)]

        while len(parameter_stack) > 0:
            parameters = parameter_stack.pop()

            # Get old parameter values
            t_min_old = parameters[0]
            t_max_old = parameters[1]
            u_min_old = parameters[2]
            u_max_old = parameters[3]

            if t_max_old - t_min_old <= 0 or u_max_old - u_min_old <= 0:
                continue

            # Compute beziers before intersections
            self_split_old = self.split_interval(t_min_old, t_max_old)
            other_split_old = other.split_interval(u_min_old, u_max_old)

            # Both Beziérs are reduced to 1 pixel. If close enough, intersection is found
            old_status = bezier_close_enough(self_split_old, other_split_old)
            if old_status == BOUNDING_TRUE:
                intersections.append(self.evaluate(t_min_old))
                continue
            elif old_status == BOUNDING_FAR:
                continue

            u_intervals = []
            if other_split_old.bounding_box_area() < BOUNDING_BOX:
                # Stop computing when bezier is less than a pixel
                u_intervals.append((u_min_old, u_max_old))
            else:
                u_intervals = [bezier_interval_project(i, u_min_old, u_max_old)
                               for i in intersect_subcurves(self_split_old, other_split_old)]

            for u_interval in u_intervals:
                u_min = u_interval[0]
                u_max = u_interval[1]

                if u_min == 1 or u_max == 0:
                    continue

                other_split = other.split_interval(u_min, u_max)

                t_intervals = []
                if self_split_old.bounding_box_area() < BOUNDING_BOX:
                    # Stop computing when area of bezier is less than desired precision
                    t_intervals.append((t_min_old, t_max_old))
                else:
                    t_intervals = [bezier_interval_project(i, t_min_old, t_max_old)
                                   for i in intersect_subcurves(other_split, self_split_old)]

                for t_interval in t_intervals:
                    t_min = t_interval[0]
                    t_max = t_interval[1]

                    if t_min == 1 or t_max == 0:
                        continue

                    self_split = self.split_interval(t_min, t_max)

                    # Determine whether split fragments are close enough
                    bounding_status = bezier_close_enough(self_split, other_split)
                    if bounding_status == BOUNDING_TRUE:
                        intersections.append(self.evaluate(t_min))
                    elif bounding_status == BOUNDING_FAR:
                        continue

                    elif (t_max - t_min) / (t_max_old - t_min_old) > PARAMETER_CHANGE \
                            and (u_max - u_min) / (u_max_old - u_min_old) > PARAMETER_CHANGE:
                        # Parameters did not shrink enough - split curve
                        if t_max - t_min < u_max - u_min:
                            # Split other curve
                            mid_u_value = u_min + (u_max - u_min) / 2
                            parameter_stack.append((t_min, t_max, u_min, mid_u_value))
                            parameter_stack.append((t_min, t_max, mid_u_value, u_max))
                        else:
                            # Split self
                            mid_t_value = t_min + (t_max - t_min) / 2
                            parameter_stack.append((t_min, mid_t_value, u_min, u_max))
                            parameter_stack.append((mid_t_value, t_max, u_min, u_max))
                    else:
                        parameter_stack.append((t_min, t_max, u_min, u_max))
        return intersections

    # Computes the area bounding box of the bezier
    def bounding_box_area(self) -> float:
        x_values = [self.start_point.x, self.end_point.x, self.control_point_1.x, self.control_point_2.x]
        y_values = [self.start_point.y, self.end_point.y, self.control_point_1.y, self.control_point_2.y]

        x_min = min(x_values)
        x_max = max(x_values)
        y_min = min(y_values)
        y_max = max(y_values)

        return max((x_max - x_min), 1) * max(y_max - y_min, 1)

    # Check wheter a given approximation of a bezier curve is sufficiently accurate, given the error tolerance
    def sufficient_approximation(self, inaccurracy):
        tolerance = 16 * (inaccurracy * inaccurracy)
        ux = 3.0 * self.control_point_1.x - 2.0 * self.start_point.x - self.end_point.x
        ux = ux * ux
        uy = 3.0 * self.control_point_1.y - 2.0 * self.start_point.y - self.end_point.y
        uy = uy * uy
        vx = 3.0 * self.control_point_2.x - 2.0 * self.end_point.x - self.start_point.x
        vx = vx * vx
        vy = 3.0 * self.control_point_2.y - 2.0 * self.end_point.y - self.start_point.y
        vy = vy * vy
        if ux < vx:
            ux = vx
        if uy < vy:
            uy = vy
        return ux + uy <= tolerance  # tolerance is 16*(inaccuracy in pixels)^2

    # Approximate a Bezier curve as a set of polygonal lines
    def approximate_bezier(self):
        if (self.sufficient_approximation(1)):  # Make global/or class local tolerance constant
            return [self.start_point, self.end_point]  # As list
        else:
            new_curves = self.split(0.5)
            lh_list = new_curves[0].approximate_bezier()
            rh_list = new_curves[1].approximate_bezier()
            return lh_list + rh_list[1:]


class GraphicsBezier(Bezier):
    def __init__(self, start_point, end_point, color=gc.LINE_COLOR, control_point_1=None, control_point_2=None):
        super().__init__(start_point, end_point, control_point_1, control_point_2)
        self.image = pygame.Surface([gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT])
        self.image.fill(gc.WHITE)
        self.image.set_colorkey(gc.WHITE)
        self.color = color

        i = 0
        last_point = start_point

        while i < 1:
            circle_point = cubic_curve(start_point, end_point, self.control_point_1, self.control_point_2, i)
            pygame.draw.line(self.image, self.color, circle_point.pos(), last_point.pos(), 3)
            last_point = circle_point

            i += 0.005

        pygame.draw.line(self.image, self.color, last_point.pos(), end_point.pos())
        self.rect = self.image.get_rect()

    @classmethod
    def from_bezier(cls, bezier):
        return cls(bezier.start_point, bezier.end_point, gc.LINE_COLOR, bezier.control_point_1, bezier.control_point_2)

    def draw(self, surf):
        surf.blit(self.image, self.rect)

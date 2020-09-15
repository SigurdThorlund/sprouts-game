import math
from typing import List, Tuple
from src.model.point import Point

FLOAT_IMPRECISION: float = 0.001
CONVEX_N_POINTS: int = 4

LINE_PARALLEL: int = 1
LINE_EQUAL: int = 2
LINE_NONPARALLEL: int = -1

INTERSECT_BELOW: int = -1
INTERSECT_INSIDE: int = 0
INTERSECT_ABOVE: int = 1


### MAIN RESPONSIBILITY: OLAV NØRGAARD OLSEN S184195 ###
class ImplicitLine:
    def __init__(self, start_point: Point, end_point: Point):
        self.start_point = start_point
        self.end_point = end_point

        self.a, self.b, self.c = self.implicit_coefficients()

    # Computes normalized coefficients (a,b,c) for an implicit line, where a^2 + b^2 = 1
    # https://drive.google.com/open?id=1dpG1NMtT8Mgn7gmPjJGTLbDfkxl9MgLv, page. 1
    # https://drive.google.com/open?id=1O6tTm3zZOcFtXGNxUJxxAAzkYd5CHzrb, page. 1
    def implicit_coefficients(self):
        a_unscaled = self.start_point.y - self.end_point.y
        b_unscaled = self.end_point.x - self.start_point.x
        c_unscaled = self.end_point.x * self.start_point.y - self.start_point.x * self.end_point.y

        normalize_factor = math.sqrt(a_unscaled * a_unscaled + b_unscaled * b_unscaled)

        a_normalized = a_unscaled / normalize_factor
        b_normalized = b_unscaled / normalize_factor
        c_normalized = c_unscaled / normalize_factor

        return a_normalized, b_normalized, c_normalized

    # Distance from a point to the line
    def dist(self, point: Point) -> float:
        return self.a * point.x + self.b * point.y - self.c

    # Returns whether 2 ImplicitLines are nonparallel, parallel or equal
    def equality(self, other: 'ImplicitLine') -> Tuple[int, float]:
        if not isinstance(other, ImplicitLine):
            raise Exception("ImplicitLine.status: Not comparing 2 ImplicitLines")
        denominator = self.a * other.b - other.a * self.b
        # If the denominator is 0, both lines are parallel
        if denominator == 0:
            return LINE_PARALLEL, denominator
        # If both a and b are equal for the lines, they are parallel
        elif math.fabs(self.a - other.a) < 0:
            if math.fabs(self.b - other.b) < 0:
                if math.fabs(self.c - other.c):
                    return LINE_EQUAL, denominator  # Completely equal
                else:
                    return LINE_PARALLEL, denominator  # Parallel
        return LINE_NONPARALLEL, denominator  # Neither equal nor parallel

    # Either returns the intersection point, or whether the lines are parallel/equal
    def intersection(self, other: 'ImplicitLine'):
        line_status, denominator = self.equality(other)
        # No intersections if the lines are parallel, or infinite intersections if they are equal
        if line_status != LINE_NONPARALLEL:
            return line_status
        #  https://en.wikipedia.org/wiki/Intersection_(Euclidean_geometry)#Two_lines
        return Point((self.c * other.b - other.c * self.b) / denominator,
                     (self.a * other.c - other.a * self.c) / denominator)


class Fatline(ImplicitLine):
    def __init__(self, curve, perpendicular=False):
        super().__init__(curve.start_point, curve.end_point)
        # Should the fatline be perpendicular to the centerline?
        if perpendicular:
            a = self.a
            b = self.b

            # Since ^a and ^b are obtained by rotating the normal vector (a,b) by rotating it 90 degrees
            # counterclockwise, only the c-value must be computed
            self.c = - max([p.y * (p.x + a) - (p.y + b) * p.x for p in curve.points])

            self.a = b
            self.b = -a

            # Compute bounds
            self.d_min = 0
            dists = [self.dist(p) for p in curve.points]
            self.d_max = max(dists)
        else:
            # Distance from control points to line
            d_1 = self.dist(curve.control_point_1)
            d_2 = self.dist(curve.control_point_2)

            # Factor to determine fatline interval
            fac = -1
            if d_1 * d_2 > 0:
                fac = 3 / 4
            else:
                fac = 4 / 9

            # Fatline boundaries
            self.d_min = fac * min(0, d_1, d_2)
            self.d_max = fac * max(0, d_1, d_2)

    # Computes the distance of the points defining another Bézier curve
    def distance_control_points(self, curve) -> List[Point]:
        distance_points = []
        for i in range(4):
            distance_points.append(Point(1 / 3 * i, self.dist(curve.points[i])))
        return distance_points


# Implementation of edges, which rely on ImplicitLines
class Segment(ImplicitLine):
    def __init__(self, start_point: Point, end_point: Point):
        super().__init__(start_point, end_point)

    def __str__(self):
        return "Segment(%s,%s)" % (self.start_point, self.end_point)

    # Method for determining points on the segment
    def eval(self, t: float) -> Point:
        if t < 0 or t > 1:
            raise Exception("Segment.eval: parameter t is outside of it's interval [0;1], t=" + str(t))
        return self.start_point + t * (self.end_point - self.start_point)

    # Computes whether a point is on the segment
    def on_segment(self, point: Point) -> bool:
        # Check whether point is on the defined line
        if math.fabs(self.dist(point)) < FLOAT_IMPRECISION:
            # Avoid division by zero
            if math.fabs(self.start_point.x - self.end_point.x) < FLOAT_IMPRECISION:
                # Compute the t-value used in a lerp
                t = ((point.y - self.start_point.y) / (self.end_point.y - self.start_point.y))
            else:
                t = ((point.x - self.start_point.x) / (self.end_point.x - self.start_point.x))
            return 0 <= t <= 1
        return False

    # http://www.cs.swan.ac.uk/~cssimon/line_intersection.html
    def intersection(self, other: 'Segment'):
        intersection_status = super().intersection(other)

        # Single point has been found - test if it is within range of the segment
        if isinstance(intersection_status, Point):
            if self.on_segment(intersection_status) and other.on_segment(intersection_status):
                return intersection_status

        # Lines of the segments are equal. playground whether they intersect. lie on top of one another
        elif intersection_status == LINE_EQUAL:
            return self.on_segment(other.start_point) or self.on_segment(other.end_point)

        # Point was either outside interval, or lines for the segments are parallel
        return False

    # Do 2 segments intersect?
    def intersects(self, other: 'Segment') -> bool:
        intersection_status = self.intersection(other)
        return isinstance(intersection_status, Point) or intersection_status

    # Does the point lie over the segment?
    def over_segment(self, point: Point) -> bool:
        delta_point_start = point - self.start_point
        delta_point_end = point - self.end_point
        delta_segment = self.end_point - self.start_point

        return delta_segment.dot_product(delta_point_start) * (-delta_segment.dot_product(delta_point_end)) >= 0


# Creates a convex hull of N points, where the points are sorted by x-value
class ConvexHullNPoint:
    def __init__(self, points: List[Point]):
        self.top_segments = []
        self.bottom_segments = []
        if len(points) != CONVEX_N_POINTS:
            raise Exception("ConvexHullFourPoint: Number of points was not " + str(CONVEX_N_POINTS))

        # All points inside convex hull
        self.points = points
        self._convex_hull(points)

    # Computes the convex hull of the given points
    def _convex_hull(self, points: List[Point]):
        # 2d array, containing slopes between 2 points
        slopes = [[0] * CONVEX_N_POINTS for i in range(CONVEX_N_POINTS)]

        # Computes the slope for the line from points[i] to points[j]
        for i in range(CONVEX_N_POINTS):
            for j in range(i + 1, CONVEX_N_POINTS):
                slope = (points[j].y - points[i].y) / (points[j].x - points[i].x)
                slopes[i][j] = slope
                slopes[j][i] = slope

        last_point = points[0]
        # Compute the edges on the upper half
        i = 0
        while i < CONVEX_N_POINTS - 1:
            # Find point which gives steepest slope
            max_slope_index = i + 1
            max_slope_value = slopes[i][i + 1]

            for j in range(i + 2, CONVEX_N_POINTS):
                if slopes[i][j] > max_slope_value:
                    max_slope_index = j
                    max_slope_value = slopes[i][j]

            # Go to steepest point
            i = max_slope_index
            self.top_segments.append(Segment(last_point, points[i]))
            last_point = points[i]

        # Compute the vertices on the lower half
        i = CONVEX_N_POINTS - 1
        while i > 0:
            # Find point which gives steepest slope
            max_slope_index = i - 1
            max_slope_value = slopes[i][i - 1]

            for j in range(0, i - 1):
                if slopes[i][j] > max_slope_value:
                    max_slope_index = j
                    max_slope_value = slopes[i][j]

            # Go to steepest point
            i = max_slope_index
            self.bottom_segments.append(Segment(points[i], last_point))
            last_point = points[i]

        self.bottom_segments.reverse()

    # Computes the intervals where the convex hull lies within the fatline
    def fatline_intersection(self, fatline: Fatline) -> List[Tuple[float, float]]:
        x_min: float = self.points[0].x
        x_max: float = self.points[len(self.points) - 1].x

        # Convert horizontal lines into segments
        seg_top = Segment(Point(x_min, fatline.d_max), Point(x_max, fatline.d_max))
        seg_bottom = Segment(Point(x_min, fatline.d_min), Point(x_max, fatline.d_min))

        # Intersect convex hull with fatline
        top_intervals = handle_segment_list_intersection(self.top_segments, seg_top, seg_bottom)
        bottom_intervals = handle_segment_list_intersection(self.bottom_segments, seg_top, seg_bottom)

        top_len = len(top_intervals)
        bottom_len = len(bottom_intervals)
        intervals = []

        # No intersections
        if top_len == 0 or bottom_len == 0:
            return []

        i = 0
        j = 0

        while i < top_len and j < bottom_len:
            top_interval = top_intervals[i]
            bottom_interval = bottom_intervals[j]

            intersect_sum = top_interval[2] + bottom_interval[2]
            if -2 < intersect_sum < 2:
                intervals.append((max(top_interval[0], bottom_interval[0]), min(top_interval[1], bottom_interval[1])))
            if top_interval[1] < bottom_interval[1]:
                # Top changes before bottom
                i += 1
            else:
                j += 1

        if len(intervals) == 0:
            return []
        merged_intervals = [intervals[0]]

        for k in range(1, len(intervals)):
            merged_count = len(merged_intervals)

            # Does the interval start and end at the same value?
            if merged_intervals[merged_count - 1][1] == intervals[k][0]:
                merged_intervals[merged_count - 1] = merged_intervals[merged_count - 1][0], intervals[k][1]

        return merged_intervals


def interval_overlap(interval_a, interval_b):
    return interval_a[0] < interval_b[1] and interval_b[0] < interval_a[1]


def handle_segment_list_intersection(segments: List[Segment], seg_top: Segment, seg_bottom: Segment) -> \
        List[Tuple[float, float, int]]:
    intervals = []

    for seg in segments:
        # Get intervals for which the segment is above, below or inside the segments
        seg_intervals = handle_segment_intersection(seg, seg_top, seg_bottom)

        for seg_interval in seg_intervals:
            interval_count = len(intervals)

            # Merge intervals together if possible
            if interval_count > 0 and (intervals[interval_count - 1][2] == seg_interval[2]) and seg_interval[2] == \
                    intervals[interval_count - 2][2]:
                intervals[interval_count - 1] = intervals[interval_count - 1][0], seg_interval[1], seg_interval[2]
            else:
                intervals.append(seg_interval)
    return intervals


# Handles intersection with a single segment and returns the x-interval which it lies between seg_top and seg_bottom
def handle_segment_intersection(seg: Segment, seg_top: Segment, seg_bottom: Segment) -> List[Tuple[float, float, int]]:
    intersect_top = seg_top.intersection(seg)
    intersect_bottom = seg_bottom.intersection(seg)

    interval_start: float = seg.start_point.x
    interval_end: float = seg.end_point.x
    intersection = []

    # Intersects with top-line
    if isinstance(intersect_top, Point):
        change_x_top = intersect_top.x

        # Intersects with top-line and bottom
        if isinstance(intersect_bottom, Point):
            change_x_bottom = intersect_bottom.x

            if seg.start_point.y > seg.end_point.y:
                # Above, inside, below
                intersection.append((interval_start, change_x_top, INTERSECT_ABOVE))
                intersection.append((change_x_top, change_x_bottom, INTERSECT_INSIDE))
                intersection.append((change_x_bottom, interval_end, INTERSECT_BELOW))

            else:
                # Below, inside, above
                intersection.append((interval_start, change_x_bottom, INTERSECT_BELOW))
                intersection.append((change_x_bottom, change_x_top, INTERSECT_INSIDE))
                intersection.append((change_x_top, interval_end, INTERSECT_ABOVE))

        # Only intersects with top-line
        else:
            # Segments starts below top-line
            if seg.start_point.y < intersect_top.y:
                # Inside, above
                intersection.append((interval_start, change_x_top, INTERSECT_INSIDE))
                intersection.append((change_x_top, interval_end, INTERSECT_ABOVE))
            else:
                # Above, inside
                intersection.append((interval_start, change_x_top, INTERSECT_ABOVE))
                intersection.append((change_x_top, interval_end, INTERSECT_INSIDE))

    # Only intersects with bottom-line
    elif isinstance(intersect_bottom, Point):
        change_x_bottom = intersect_bottom.x

        # Segment starts above bottom-line
        if seg.start_point.y > intersect_bottom.y:
            # Inside, below
            intersection.append((interval_start, change_x_bottom, INTERSECT_INSIDE))
            intersection.append((change_x_bottom, interval_end, INTERSECT_BELOW))
        else:
            # Below, inside
            intersection.append((interval_start, change_x_bottom, INTERSECT_BELOW))
            intersection.append((change_x_bottom, interval_end, INTERSECT_INSIDE))

    # No intersections, either completely inside or outside
    else:
        if seg.start_point.y > seg_top.start_point.y:
            # Above
            intersection.append((interval_start, interval_end, INTERSECT_ABOVE))
        elif seg.start_point.y < seg_bottom.start_point.y:
            # Below
            intersection.append((interval_start, interval_end, INTERSECT_BELOW))
        else:
            # Inside
            intersection.append((interval_start, interval_end, INTERSECT_INSIDE))

    return intersection

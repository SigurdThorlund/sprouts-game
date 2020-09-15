import unittest

import pygame

import src.config.game_config as gc
from src.model.cubic_bezier import Bezier, GraphicsBezier
from src.model.path import add_path, Path
from src.model.point import Point, GraphicsPoint

SHOW_INTERSECTIONS = True
PRINT_RECURSION = False


def print_recursion(recursion):
    if not PRINT_RECURSION:
        return
    print("{")
    for rec in recursion:
        print("{\"%s\",\"%s\"}," % (rec[0], rec[1]))
    print("}")


def show_intersections(p, q, intersections):
    if not SHOW_INTERSECTIONS:
        return
    pygame.init()

    SCREEN = pygame.display.set_mode((gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT))
    SURFACE = pygame.Surface(SCREEN.get_size(), pygame.SRCALPHA)
    SURFACE.fill(gc.BACKGROUND_COLOR)
    SCREEN.blit(SURFACE, (0, 0))

    SCREEN.blit(GraphicsBezier.from_bezier(p).image, (0, 0))
    SCREEN.blit(GraphicsBezier.from_bezier(q).image, (0, 0))

    for point in intersections:
        pygame.draw.circle(SCREEN, gc.BLACK, (int(point.x), int(point.y)), 5)
        pygame.draw.circle(SCREEN, gc.POINT_COLOR_UNAVAILABLE, (int(point.x), int(point.y)), 3)

    pygame.display.flip()
    pygame.display.update()

    done = False

    while not done:
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:  # If user pressed a key
                done = True  # Flag that we are done so we exit this loop

    pygame.quit()


def show_paths(p, q, intersections):
    if not SHOW_INTERSECTIONS:
        return
    pygame.init()

    SCREEN = pygame.display.set_mode((gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT))
    SURFACE = pygame.Surface(SCREEN.get_size(), pygame.SRCALPHA)
    SURFACE.fill(gc.BACKGROUND_COLOR)
    SCREEN.blit(SURFACE, (0, 0))

    SCREEN.blit(p.image, (0, 0))
    SCREEN.blit(q.image, (0, 0))

    for point in intersections:
        pygame.draw.circle(SCREEN, gc.POINT_COLOR_UNAVAILABLE, point.pos(), 5)

    pygame.display.flip()
    pygame.display.update()

    done = False

    while not done:
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:  # If user pressed a key
                done = True  # Flag that we are done so we exit this loop

    pygame.quit()


def show_paths_2(paths, intersections):
    if not SHOW_INTERSECTIONS:
        return
    pygame.init()

    SCREEN = pygame.display.set_mode((gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT))
    SURFACE = pygame.Surface(SCREEN.get_size(), pygame.SRCALPHA)
    SURFACE.fill(gc.BACKGROUND_COLOR)
    SCREEN.blit(SURFACE, (0, 0))

    for path in paths:
        SCREEN.blit(path.image, (0, 0))

    for point in intersections:
        pygame.draw.circle(SCREEN, gc.POINT_COLOR_UNAVAILABLE, (int(point.x), int(point.y)), 5)

    pygame.display.update()

    done = False

    while not done:
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:  # If user pressed a key
                done = True  # Flag that we are done so we exit this loop

    pygame.quit()


class TestBezierIntersection(unittest.TestCase):
    def test_intersect_a(self):
        p0 = Point(200, 50)
        p1 = Point(400, 50)
        p2 = Point(350, 300)
        p3 = Point(400, 250)

        q0 = Point(150, 0)
        q1 = Point(300, 0)
        q2 = Point(300, 250)
        q3 = Point(360, 220)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)
        self.assertEqual(1, len(intersection))

    def test_intersect_b(self):
        p0 = Point(200, 50)
        p1 = Point(300, 40)
        p2 = Point(360, 300)
        p3 = Point(400, 100)

        q0 = Point(350, 100)
        q1 = Point(200, 140)
        q2 = Point(340, 160)
        q3 = Point(360, 220)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)
        self.assertEqual(1, len(intersection))

    def test_no_intersect(self):
        p0 = Point(300, 100)
        p1 = Point(300, 100)
        p2 = Point(350, 300)
        p3 = Point(500, 200)

        q0 = Point(300, 250)
        q1 = Point(500, 250)
        q2 = Point(450, 350)
        q3 = Point(150, 350)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)
        self.assertEqual(0, len(intersection))

    def test_multiple_intersect_a(self):
        p0 = Point(100, 100)
        p1 = Point(300, 50)
        p2 = Point(400, 380)
        p3 = Point(600, 300)

        q0 = Point(200, 50)
        q1 = Point(300, 250)
        q2 = Point(380, 325)
        q3 = Point(400, 50)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)
        self.assertEqual(2, len(intersection))

    def test_zclose_no_intersect_a(self):
        p0 = Point(200, 50)
        p1 = Point(350, 50)
        p2 = Point(350, 300)
        p3 = Point(400, 300)

        q0 = Point(200, 0)
        q1 = Point(300, 0)
        q2 = Point(400, 400)
        q3 = Point(600, 300)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)
        self.assertEqual(0, len(intersection))

    def test_zclose_no_intersect_b(self):
        p0 = Point(200, 50)
        p1 = Point(400, 50)
        p2 = Point(350, 300)
        p3 = Point(400, 250)

        q0 = Point(150, 0)
        q1 = Point(150, 50)
        q2 = Point(350, 250)
        q3 = Point(360, 220)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)
        self.assertEqual(0, len(intersection))

    def test_zclose_no_intersect_c(self):
        p0 = Point(200, 50)
        p1 = Point(400, 50)
        p2 = Point(350, 300)
        p3 = Point(400, 250)

        q0 = Point(280, 100)
        q1 = Point(200, 0)
        q2 = Point(350, 250)
        q3 = Point(360, 220)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)

        self.assertEqual(0, len(intersection))

    def test_straight_intersection(self):
        p0 = Point(600, 300)
        p1 = Point(349.5, 199.0)
        p2 = Point(349.5, 199.0)
        p3 = Point(99, 98)
        q0 = Point(345, 27)
        q1 = Point(391.8255740586339, 78.95156364783563)
        q2 = Point(158.26381544944778, 380.6430605029642)
        q3 = Point(189, 403)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)
        self.assertEqual(1, len(intersection))

    def test_straight_intersection_2(self):
        p0 = Point(425, 85)
        p1 = Point(500.77636499516825, 90.43288595352556)
        p2 = Point(512.5, 192.5)
        p3 = Point(600, 300)

        q0 = Point(638, 105)
        q3 = Point(427.67115932085926, 268.59592697198934)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)
        self.assertEqual(1, len(intersection))

    def test_error_intersection(self):
        p0 = Point(567, 52)
        p1 = Point(623.3749533358998, 96.48394483913664)
        p2 = Point(583.5, 176.0)
        p3 = Point(600, 300)
        q0 = Point(600, 300)
        q1 = Point(460.5, 343.5)
        q2 = Point(460.5, 343.5)
        q3 = Point(321, 387)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)

        self.assertEqual(1, len(intersection))

    def test_error_intersection_2(self):
        p0 = Point(293.72241133583, 196.89385300691802)
        p1 = Point(280.23555111038667, 275.54739962389243)
        p2 = Point(267.174553773, 355.40299523856083)
        p3 = Point(304, 382)

        q0 = Point(384, 219)
        q1 = Point(329.4781702228842, 274.5823432565248)
        q2 = Point(302.4625676163959, 338.5497641105882)
        q3 = Point(274.95634044576843, 330.16468651304956)

        p = Bezier(p0, p3, p1, p2)
        q = Bezier(q0, q3, q1, q2)

        intersection = p.intersects(q)
        show_intersections(p, q, intersection)

        self.assertEqual(1, len(intersection))


class TestPathIntersection(unittest.TestCase):
    # def test_path_no_intersect(self):
    #     anchor_points_0 = [Point(10, 10), Point(20, 20)]
    #     anchor_points_1 = [Point(30, 30), Point(25, 25)]
    #
    #     (start_path_0, end_path_0, mid_point_1) = add_path(anchor_points_0)
    #     (start_path_1, end_path_1, mid_point_1) = add_path(anchor_points_1)
    #
    #     self.assertEqual([], start_path_0.intersects(start_path_1) + start_path_0.intersects(
    #         end_path_1) + end_path_0.intersects(
    #         start_path_1) + end_path_0.intersects(end_path_1))

    def test_path_no_intersect_2(self):
        # anchor_points_0 = [GraphicsPoint(450,100), Point(499.27232558764285,264.34980738137415), Point(520.9894097054131,309.3872169141358), Point(492.6055772197633,350.5497976571671), GraphicsPoint(500,400)]
        anchor_points_1 = [GraphicsPoint(100, 100), GraphicsPoint(350.0, 200.0), GraphicsPoint(600, 300)]
        anchor_points_0 = [GraphicsPoint(450, 100), Point(289.01257267912837, 295.27070180414165),
                           Point(328.57076133309056, 325.8509194360934), Point(377.21153620107134, 337.4299962664114),
                           Point(427.0452569066222, 333.35565206873423), Point(468.7047058662693, 361.0050700079705),
                           GraphicsPoint(500, 400)]
        (start_path_0, end_path_0, mid_point_1) = add_path(anchor_points_0[0], anchor_points_0[-1], anchor_points_0)
        (start_path_1, end_path_1, mid_point_1) = add_path(anchor_points_1[0], anchor_points_1[-1], anchor_points_1)

        intersections = start_path_0.intersects(start_path_1) + start_path_0.intersects(
            end_path_1) + end_path_0.intersects(
            start_path_1) + end_path_0.intersects(end_path_1)

        show_paths_2([start_path_0, end_path_0, start_path_1, end_path_1], intersections)
        self.assertEqual(True, len(intersections) > 0)

    def test_path_intersect_3(self):
        anchor_points_0 = [GraphicsPoint(100, 100), Point(376, 61), Point(639, 217),
                           GraphicsPoint(546, 357)]

        anchor_points_1 = [GraphicsPoint(450, 100),
                           GraphicsPoint(440.3994196807172, 149.06963274300102)]

        path = Path.from_points(anchor_points_0)

        path2 = Path.from_points(anchor_points_1)

        intersections = path2.intersects(path)

        show_paths_2([path, path2], intersections)
        self.assertEqual(False, len(intersections) > 0)

    def test_path_intersect_4(self):
        anchor_points_0 = [GraphicsPoint(440.3994196807172, 149.06963274300102), GraphicsPoint(450, 100)]

        anchor_points_1 = [GraphicsPoint(450, 100),
                           GraphicsPoint(402.0865680692103, 419.70860894843224),
                           GraphicsPoint(422.05639822420903, 417.833171793951)]

        path = Path.from_points(anchor_points_0)

        path2 = Path.from_points(anchor_points_1)

        intersections = path.intersects(path2)

        show_paths_2([path, path2], intersections)
        self.assertEqual(False, len(intersections) > 0)

    def test_path_intersect_5(self):
        anchor_points_0 = [GraphicsPoint(403.01382054213786, 117.09675232181752), GraphicsPoint(450, 100)]

        anchor_points_1 = [GraphicsPoint(422.05639822420903, 417.833171793951),
                           GraphicsPoint(450.55461679819734, 407.4265792951324),
                           GraphicsPoint(500, 400)]

        path = Path.from_points(anchor_points_0)

        path2 = Path.from_points(anchor_points_1)

        intersections = path.intersects(path2)

        show_paths_2([path, path2], intersections)
        self.assertEqual(False, len(intersections) > 0)

    def test_path_intersect_no_mirror(self):
        anchor_points_0 = [GraphicsPoint(450, 100), Point(473.7132417184837, 208.4978496002687),
                           GraphicsPoint(466, 268)]

        anchor_points_1 = [GraphicsPoint(100, 100),
                           Point(230, 177),
                           Point(548, 178),
                           GraphicsPoint(701, 347)]

        path = Path.from_points(anchor_points_0)
        path2 = Path.from_points(anchor_points_1)

        intersections = path.intersects(path2)
        intersections_2 = path2.intersects(path)

        show_paths_2([path, path2], intersections + intersections_2)
        self.assertEqual(len(intersections), len(intersections_2))

    def test_path_intersect_no_mirror_2(self):
        anchor_points_0 = [GraphicsPoint(100, 100), Point(473.7132417184837, 208.4978496002687),
                           GraphicsPoint(457, 125)]

        anchor_points_1 = [GraphicsPoint(500, 400),
                           Point(573, 371),
                           Point(550, 177),
                           Point(586, 146),
                           Point(337, 129),
                           Point(536, 22),
                           Point(689, 67),
                           Point(728, 344),
                           Point(650, 472)]

        p_start = GraphicsPoint(100, 100)
        p_end = GraphicsPoint(457, 125)

        path = Path([GraphicsBezier(p_start, p_end, Point(278.5, 112.5), Point(404.8987230708711, 188.92401096739675))],
                    p_start, p_end)
        path2 = Path.from_points(anchor_points_1)

        intersections = path.intersects(path2)
        intersections_2 = path2.intersects(path)

        show_paths_2([path, path2], intersections + intersections_2)
        self.assertEqual(len(intersections), len(intersections_2))

    def test_path_intersect_no_mirror_3(self):
        anchor_points_0 = [Point(600, 300),
                           Point(763, 232),
                           Point(760, 248),
                           Point(763.3812601455536, 279.9618353762123),
                           Point(759.093503294539, 324.7570933974201),
                           Point(752.2129530873079, 369.22796058983914),
                           Point(728.8190694506658, 407.66916515467096)]

        anchor_points_1 = [Point(100, 100), Point(638, 170), Point(727, 212),
                           Point(594, 357), Point(476, 177), Point(261, 207),
                           Point(167.76045105799363, 197.0495733490862)]
        path = Path.from_points(anchor_points_0)
        path2 = Path.from_points(anchor_points_1)

        intersections = path.intersects(path2)
        intersections_2 = path2.intersects(path)

        show_paths_2([path, path2], intersections + intersections_2)
        self.assertEqual(len(intersections), len(intersections_2))

    def test_path_self_no_intersect(self):
        start_end = GraphicsPoint(376, 95)
        anchor_points = [start_end,
                         Point(154, 199),
                         Point(302, 315),
                         Point(493, 120),
                         start_end]

        path = Path.from_points(anchor_points)
        intersections = path.self_intersections()
        show_paths_2([path], intersections)
        self.assertEqual(0, len(intersections))

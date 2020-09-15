import unittest

from src.model.bezier_intersection import *
from src.model.path import add_path
from src.model.region import Region


class TestRegion(unittest.TestCase):
    def create_test_path(self, game_points):
        p1 = None
        p2 = None
        for point in game_points:
            if point.index == 2:
                p1 = point
            elif point.index == 3:
                p2 = point
            if not (p1 is None or p2 is None):
                return [p1,p2]
        return []

    def simulate_main(self,region,path_click_lists, points):
        Region.APPROXIMATIONS = {}
        for list in path_click_lists:
            # Split path in two and calculate new point
            (start_path, end_path, mid_point) = add_path(list[0],list[-1], list, len(points))
            current_region = region.find_region(mid_point)
            # current_region = region
            #Update approximations
            Region.APPROXIMATIONS[start_path] = start_path.approximate()
            Region.APPROXIMATIONS[end_path] = end_path.approximate()

            # Add the paths to the region
            Region.add_path(current_region.edge_map, start_path)
            Region.add_path(current_region.edge_map, end_path)
            current_region.add_point(mid_point)

            # Check to see if any cycles are made
            cycle = current_region.detect_cycle(mid_point)

            if not (cycle == []):
                border_points = []
                for path in cycle:
                    print(path.to_string())
                print("------------------------\n")
        return current_region

    def test_point_is_in_region(self):
        # Simple Test: Point inside Square
        # Expected outcome: True
        points = [ Point(100,100), Point(100,300), Point(300,300), Point(300,100) ]
        test_point = Point(200,200)
        test_region = Region(points, points, [], [])
        result = test_region.is_point_in_region(test_point)
        self.assertTrue(result)

    def test_point_is_outside_region(self):
        # Simple Test: Point outside Square
        # Expected outcome: True
        points = [ Point(100,100), Point(100,300), Point(300,300), Point(300,100) ]
        test_point = Point(400,200)
        test_region = Region(points, points, [], [])
        result = test_region.is_point_in_region(test_point)
        self.assertFalse(result)

    def test_point_is_in_bbox_out_polygon(self):
        # Test: Point inside region bounding box, but outside the polygon of the region
        # Expected outcome: False
        points = [ Point(100,100), Point(200, 200), Point(100,300), Point(300,300), Point(300,100) ]
        test_point = Point(150,200)
        test_region = Region(points, points, [], [])
        result = test_region.is_point_in_region(test_point)
        self.assertFalse(result)

    def test_is_in_subregion(self):
        # Test: Point in side subregion of region
        #Expected result: False
        border_points = [ Point(100,100), Point(100,300), Point(250,300), Point(300,300), Point(300,100) ]
        subregion_points = [ Point(150,150), Point(150, 250), Point(250,300), Point(250,150) ]
        subregion = Region(subregion_points, subregion_points, [], [])
        test_point = Point(200,200)
        test_region = Region(border_points, border_points, [], [subregion])
        result = test_region.is_point_in_region(test_point)
        self.assertFalse(result)

    def test_is_on_subregion_edge(self):
        # Test: Point on outer edge of subregion
        # Expected result: True
        border_points = [ Point(100,100), Point(100,300), Point(300,300), Point(300,100) ]
        subregion_points = [ Point(150,150), Point(150, 250), Point(250,300), Point(250,150) ]
        subregion = Region(subregion_points, subregion_points, [], [])
        test_point = Point(150,200)
        test_region = Region(border_points, border_points, [], [subregion])
        result = test_region.is_point_in_region(test_point)
        self.assertTrue(result)

    def test_find_region(self):
        # Simple Test: Point inside Square
        # Expected outcome: True
        points = [ Point(100,100), Point(100,300), Point(300,300), Point(300,100) ]
        test_point = Point(200,200)
        test_region = Region(points, points, [], [])
        result = test_region.find_region(test_point)
        self.assertTrue(result == test_region)

    def test_find_no_region(self):
        # Simple Test: Point outside Square
        # Expected outcome: Returned None
        points = [ Point(100,100), Point(100,300), Point(300,300), Point(300,100) ]
        test_point = Point(400,200)
        test_region = Region(points, points, [], [])
        result = test_region.find_region(test_point)
        self.assertTrue(result == None)

    def test_point_find_none_with_polygon(self):
        # Test: Point inside region bounding box, but outside the polygon of the region
        # Expected outcome: Returned None
        points = [ Point(100,100), Point(200, 200), Point(100,300), Point(300,300), Point(300,100) ]
        test_point = Point(150,200)
        test_region = Region(points, points, [], [])
        result = test_region.find_region(test_point)
        self.assertTrue(result == None)

    def test_find_subregion(self):
        # Test: Point in side subregion of region
        #Expected result: Returned Subregion
        border_points = [ Point(100,100), Point(100,300), Point(250,300), Point(300,300), Point(300,100) ]
        subregion_points = [ Point(150,150), Point(150, 250), Point(250,300), Point(250,150) ]
        subregion = Region(subregion_points, subregion_points, [], [])
        test_point = Point(200,200)
        test_region = Region(border_points, border_points, [], [subregion])
        result = test_region.find_region(test_point)
        self.assertTrue(result == subregion)

    def test_on_subregion_edge(self):
        # Test: Point on outer edge of subregion
        # Expected result: returned Subregion
        border_points = [ Point(100,100), Point(100,300), Point(300,300), Point(300,100) ]
        subregion_points = [ Point(150,150), Point(150, 250), Point(250,300), Point(250,150) ]
        subregion = Region(subregion_points, subregion_points, [], [])
        test_point = Point(150,200)
        test_region = Region(border_points, border_points, [], [subregion])
        result = test_region.find_region(test_point)
        self.assertTrue(result)
        

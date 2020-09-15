from src.model.bezier_intersection import ImplicitLine

### MAIN RESPONSIBILITY: BJÖRN WILTING S184214 ###
#The class contains helper functions that execute parts of the winding numbers algorithm
class PointInPolygon:
    @staticmethod
    #Determine if given edge (ImplicitLine) is an upward or downward edge
    #Input: The edge
    #Output: 1 (up) or -1 (down)
    def get_edge_type(edge: ImplicitLine):
        if edge.start_point.y - edge.end_point.y > 0:
            return 1  # up
        else:
            return -1  # down

    @staticmethod
    #Updates the winding number
    def update_winding_number(points, winding_number, border_line:ImplicitLine, last_edge_intersected, last_edge_type):
        edge_type = PointInPolygon.get_edge_type(border_line)
        # The only way two edges of the same type both can intersect with a point_line
        # is if they share the intersection point, therefor the 2nd intersection should be skipped
        if not (last_edge_intersected and last_edge_type == edge_type):
            # The point is strictly to the left of the upward edge
            if edge_type == 1 and points[0].x < points[1].x:
                last_edge_intersected = True
                winding_number += 1
            # The point is strictly to the right of the downward edge
            elif edge_type == -1 and points[0].x < points[1].x:
                last_edge_intersected = True
                winding_number -= 1
        return winding_number, edge_type, last_edge_intersected



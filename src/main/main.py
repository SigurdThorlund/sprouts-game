import random
from typing import List, Tuple
import os, sys
import pygame
import pygame.gfxdraw
import src.config.game_config as gc

from src.model.path import Path, add_path
from src.model.point import Point, GraphicsPoint
from src.model.region import Region
from src.model.rrt import RRT
from src.validation import planarity
from src.model.values import Player, State

from src.ui.component import Button, Label


### MAIN RESPONSIBILITY FOR VALIDATION FUNCTION: OLAV NØRGAARD OLSEN S184195 ###
### MAIN RESPONSIBILITY FOR GAME LOGIC (run_game FUNCTION): THOMAS AAMAND WITTING S184192 ###
### MAIN RESPONSIBILITY FOR MENUS, DRAWING, UI: SIGURD FRANK THORLUND S184189 ###

class Main:
    def __init__(self, initial_points, initial_paths):
        pygame.init()
        pygame.display.set_caption("Sprouts")
        img = pygame.image.load("../../res/sproutsbg.png")
        pygame.display.set_icon(img)

        self.CLOCK = pygame.time.Clock()
        self.SCREEN = pygame.display.set_mode((gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT))
        self.SURFACE = pygame.Surface(self.SCREEN.get_size(), pygame.SRCALPHA)

        self.PLAYER = Player.PLAYER_1
        self.NUM_POINTS = 2

        # control variables
        self.creating_path = False
        self.preview_points = []
        self.preview_path = None
        self.paths = []

        self.suggest_points = []

        self.all_intersections = []
        self.SCREEN.blit(self.SURFACE, (0, 0))

        self.rrt = None

        self.border_points = [GraphicsPoint(0, 0, False), GraphicsPoint(gc.WINDOW_WIDTH, 0, False),
                              GraphicsPoint(gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT, False),
                              GraphicsPoint(0, gc.WINDOW_HEIGHT, False)]

        self.points = None
        self.base_region = None

        self.run(State.MAIN_MENU, [False])

    # Changes which loops to be displayed
    def run(self, state, params):
        while True:
            if state == State.MAIN_MENU:
                state, params = self.main_menu(*params)
            elif state == State.RUN_GAME:
                state, params = self.run_game(*params)
            elif state == State.VALIDATION:
                state, params = self.validation(*params)
            elif state == State.OPTIONS_MENU:
                state, params = self.options_loop()
            elif state == State.GAME_OVER:
                state, params = self.game_over_loop()

    # Resets the variables of the game loop-
    def hard_reset(self):
        self.PLAYER = Player.PLAYER_1

        self.creating_path = False

        self.preview_points = []
        self.preview_path = None
        self.paths = []

        self.suggest_points = []
        self.all_intersections = []
        self.SCREEN.blit(self.SURFACE, (0, 0))

        self.rrt = None

        self.border_points = [GraphicsPoint(0, 0, False), GraphicsPoint(gc.WINDOW_WIDTH, 0, False),
                              GraphicsPoint(gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT, False),
                              GraphicsPoint(0, gc.WINDOW_HEIGHT, False)]
        self.points = None
        self.base_region = None

    def main_menu(self, error=None):

        if not error:
            self.draw_background()

        button_width = 200
        button_height = 50

        filename = "filename"

        start_points = self.generate_starting_points()

        button_1 = Button(50, 100, button_width, button_height, gc.UI_BUTTON_COLOR, gc.UI_BUTTON_BORDER_COLOR, 2,
                          "Play Game", 25, gc.UI_BUTTON_TEXT_COLOR, State.RUN_GAME, [start_points, []])
        button_2 = Button(50, 200, button_width, button_height, gc.UI_BUTTON_COLOR, gc.UI_BUTTON_BORDER_COLOR, 2,
                          "Upload File", 25, gc.UI_BUTTON_TEXT_COLOR, State.VALIDATION, [filename])
        button_3 = Button(50, 300, button_width, button_height, gc.UI_BUTTON_COLOR, gc.UI_BUTTON_BORDER_COLOR, 2,
                          "Options", 25, gc.UI_BUTTON_TEXT_COLOR, State.OPTIONS_MENU)

        input_field = Label(270, 200, button_width, button_height, gc.WHITE, gc.BLACK, 2, filename, 25,
                            gc.UI_BUTTON_TEXT_COLOR)

        surfaces = [button_1.draw(), button_2.draw(), button_3.draw(), input_field.draw()]
        buttons = [button_1, button_2, button_3]

        active = False

        while True:
            mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:

                    for button in buttons:
                        if button.hovering(mouse):
                            state, parameters = button.get_action()
                            return state, parameters

                    active = input_field.hovering(mouse)

                if event.type == pygame.KEYDOWN:
                    print(active)
                    if active:
                        if event.key == pygame.K_RETURN:
                            active = False

                        elif event.key == pygame.K_BACKSPACE:
                            filename = filename[:-1]
                            input_field.text = filename
                            surfaces.append(input_field.draw())
                            button_2.parameters = [filename]

                        else:
                            key = event.unicode

                            if key.isascii():
                                filename += key
                                input_field.text = filename
                                surfaces.append(input_field.draw())
                                button_2.parameters = [filename]

            for button in buttons:
                if button.hovering(mouse):
                    button.color = gc.UI_BUTTON_COLOR_HOVER
                    surfaces.append(button.draw())
                else:
                    button.color = gc.UI_BUTTON_COLOR
                    surfaces.append(button.draw())

            for surface in surfaces:
                self.SCREEN.blit(surface, (0, 0))

            surfaces = []

            pygame.display.update()

    def options_loop(self):
        self.draw_background()

        surfaces = []

        # Create and draw the input fields
        input_label = Label(50, 100, 300, 30, gc.WHITE, gc.WHITE, 0, "Number of points: (between 1 and 20)", 22,
                            gc.UI_BUTTON_TEXT_COLOR)
        input_field = Label(370, 100, 200, 30, gc.WHITE, gc.UI_BUTTON_BORDER_COLOR, 2, str(self.NUM_POINTS), 22,
                            gc.UI_BUTTON_TEXT_COLOR)

        # Button to return back to main menu
        button_back = Button(370, 150, 200, 30, gc.UI_BUTTON_COLOR, gc.UI_BUTTON_BORDER_COLOR, 2, "Back", 25,
                             gc.UI_BUTTON_TEXT_COLOR, State.MAIN_MENU, [])

        surfaces.extend([input_field.draw(), input_label.draw(), button_back.draw()])

        active = False

        while True:
            mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    sys.exit(0)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_field.rect.collidepoint(*mouse):
                        active = True

                    elif button_back.hovering(mouse):
                        state, params = button_back.get_action()
                        return state, params

                    else:
                        active = False

                if event.type == pygame.KEYDOWN:

                    if active:
                        if event.key == pygame.K_RETURN:
                            active = False

                            if len(input_field.text) == 0:
                                continue

                            field_value = int(input_field.text)

                            if field_value <= 20 and field_value > 0:
                                self.NUM_POINTS = field_value

                        elif event.key == pygame.K_BACKSPACE:
                            input_field.text = input_field.text[:-1]
                            surfaces.append(input_field.draw())

                        else:
                            key = event.unicode

                            if key.isnumeric():
                                input_field.text += key
                                surfaces.append(input_field.draw())

            for surface in surfaces:
                self.SCREEN.blit(surface, (0, 0))

            surfaces = []

            pygame.display.update()

    # Screen displayed when game over
    def game_over_loop(self):

        if Player == Player.PLAYER_1:
            winner = "Player 2"
            color = gc.PLAYER_2_COLOR
        else:
            winner = "Player 1"
            color = gc.PLAYER_1_COLOR

        winning_label = Label(0, 0, 800, 50, color, color, 0, winner + " wins!", 50,
                              gc.UI_BUTTON_TEXT_COLOR)

        button_width = 100
        button_height = 70

        button_restart = Button(200, 300, button_width, button_height, gc.UI_BUTTON_COLOR, gc.UI_BUTTON_BORDER_COLOR, 2,
                                "Restart", 25, gc.UI_BUTTON_TEXT_COLOR, State.RUN_GAME,
                                [self.generate_starting_points(), []])

        button_main_menu = Button(500, 300, button_width, button_height, gc.UI_BUTTON_COLOR, gc.UI_BUTTON_BORDER_COLOR,
                                  2,
                                  "Main menu", 25, gc.UI_BUTTON_TEXT_COLOR, State.MAIN_MENU, [])

        surfaces = [button_restart.draw(), button_main_menu.draw(), winning_label.draw()]
        buttons = [button_restart, button_main_menu]

        while True:
            mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:

                    for button in buttons:
                        if button.hovering(mouse):
                            self.hard_reset()
                            state, params = button.get_action()
                            return state, params

            for button in buttons:
                if button.hovering(mouse):
                    button.color = gc.UI_BUTTON_COLOR_HOVER
                    surfaces.append(button.draw())
                else:
                    button.color = gc.UI_BUTTON_COLOR
                    surfaces.append(button.draw())

            for surface in surfaces:
                self.SCREEN.blit(surface, (0, 0))

            surfaces = []

            pygame.display.update()

    # Start in the initial state if running validation
    def set_initial_state(self, initial_points, initial_paths):
        self.base_region = Region(set(initial_points), self.border_points, edge_map={}, exclusions=set(),
                                  surf=self.SCREEN)

        for start_path, end_path, mid_point in initial_paths:
            current_region = self.base_region.find_region(mid_point)
            # Add the paths to the region
            current_region.update_region_tree([start_path, end_path], mid_point)

            self.paths.append(start_path)
            self.paths.append(end_path)

        self.points = set(initial_points)
        GraphicsPoint.setLastID(len(self.points))

    # Validates file given filename
    def validation(self, filename):
        # Alerts, invalid path - non, planar
        try:
            points, paths = planarity.validate_file("../validation/" + filename)
            return (State.RUN_GAME, [points, paths])

        except planarity.LoadException as error:
            error_label = Label(270, 300, 400, 50, gc.UI_BUTTON_COLOR, gc.UI_BUTTON_BORDER_COLOR, 2, str(error), 22,
                                gc.UI_BUTTON_TEXT_COLOR)

            self.SCREEN.blit(error_label.draw(), (0, 0))

            return (State.MAIN_MENU, [True])

    def draw_background(self):
        bg = pygame.image.load("../../res/sproutsbg.png")

        self.SCREEN.fill(gc.WHITE)
        self.SCREEN.blit(bg, (0, 0))

    # Generates the points in the beginning of the game.
    def generate_starting_points(self):
        start_points = []
        GraphicsPoint.setLastID(0)
        for i in range(self.NUM_POINTS):
            start_points.append(
                GraphicsPoint(random.randint(50, gc.WINDOW_WIDTH - 50), random.randint(50, gc.WINDOW_HEIGHT - 50)))

        return start_points

    def is_game_over(self, base_region):

        if base_region.find_open_region():
            return False
        else:
            return True

    # change the players turns
    def change_turn(self, label_1, label_2):
        if self.PLAYER == Player.PLAYER_1:
            label_1.border_color = gc.PLAYER_1_COLOR
            label_2.border_color = gc.BLACK
            self.PLAYER = Player.PLAYER_2
        else:
            label_1.border_color = gc.BLACK
            label_2.border_color = gc.PLAYER_2_COLOR
            self.PLAYER = Player.PLAYER_1

    def get_color(self):
        if self.PLAYER == Player.PLAYER_1:
            return gc.PLAYER_1_COLOR
        else:
            return gc.PLAYER_2_COLOR

    def run_game(self, initial_points, initial_paths):
        self.set_initial_state(initial_points, initial_paths)
        last_mouse_pos = (0, 0)

        spacing = "                 "
        legend_text = "Esc: cancel path" + spacing + "Right Click: Path suggestion" + spacing + "Left Click: Draw path" + spacing + "Backspace: Main menu"
        legend = Label(0, 0, 800, 30, pygame.SRCALPHA, pygame.SRCALPHA, 0, legend_text, 18, gc.UI_BUTTON_TEXT_COLOR)

        player_1_label = Label(0, 0, 60, 30, gc.PLAYER_1_COLOR, gc.BLACK, 2, "Player 1", 20, gc.UI_BUTTON_TEXT_COLOR)
        player_2_label = Label(gc.WINDOW_WIDTH - 60, 0, 60, 30, gc.PLAYER_2_COLOR, gc.PLAYER_2_COLOR, 2, "Player 2", 20,
                               gc.UI_BUTTON_TEXT_COLOR)

        surfaces = []

        surfaces.extend([legend.draw(), player_1_label.draw(), player_2_label.draw()])

        if self.game_over(self.base_region):
            self.update_screen([])
            return (State.GAME_OVER, [initial_points, initial_paths])

        while True:
            current_mouse_pos = pygame.mouse.get_pos()

            surfaces.extend([legend.draw(), player_1_label.draw(), player_2_label.draw()])

            for event in pygame.event.get():
                # exit via X in window corner
                if event.type == pygame.QUIT:
                    sys.exit()
                # key pressed
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        # self.SCREEN.fill(gc.BACKGROUND_COLOR)
                        self.hard_reset()
                        return (State.MAIN_MENU, [])

                    self.key_event_handler(event)

                # mouse clicked
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_point = Point(*event.pos)
                    current_region = self.base_region.find_region(Point(*event.pos))

                    # p is a Point if collision exists, else None
                    p = self.point_collision(current_region.game_points, event.pos)

                    self.update_screen(surfaces)

                    # right click = suggest a path (if point pressed is GraphicsPoint
                    if event.button == 3 and p:
                        self.suggest_points.append(p)
                        if len(self.suggest_points) == 2:

                            suggested_path_points = self.find_path()

                            # User canceled
                            if not suggested_path_points:
                                self.soft_reset()
                                break

                            self.finalize_path(suggested_path_points)

                            self.change_turn(player_1_label, player_2_label)

                            # check for game over state
                            if self.game_over(self.base_region):
                                self.update_screen([])
                                return (State.GAME_OVER, [initial_points, initial_paths])

                            # reset control variables
                            self.soft_reset()
                        break
                    elif event.button == 3:
                        break

                    # Cant draw straight lines by pressing twice in the same pixel
                    if len(self.preview_points) > 0 and mouse_point.equals(self.preview_points[-1]):
                        break

                    # point collision and not drawing a path already
                    if p and not self.creating_path:
                        self.preview_path = None
                        self.all_intersections = []
                        self.creating_path = True
                        self.preview_points = [p]
                        self.preview_path = Path.from_points(self.preview_points + [Point(*event.pos)])

                    # no point collision and creating path already
                    elif not p and self.creating_path:
                        self.preview_points.append(Point(*event.pos))

                    # point collision and creating path already
                    elif p and self.creating_path:
                        if p == self.preview_points[0] and len(self.preview_points) == 1:
                            self.soft_reset()
                            break
                        self.preview_points.append(p)
                        self.preview_path = Path.from_points(self.preview_points)

                        (self.all_intersections, valid_path) = self.validate_path(self.preview_path)

                        # path is not valid, show intersections
                        if not valid_path:
                            self.creating_path = False
                            self.preview_path.change_color(gc.RED)

                            self.all_intersections = self.points_to_graphicspoints(self.all_intersections, gc.BLACK, 5)
                            self.soft_reset()
                            break

                        # Split path in two and calculate new point
                        self.finalize_path(self.preview_points)

                        self.change_turn(player_1_label, player_2_label)
                        if self.game_over(self.base_region):
                            self.update_screen([])
                            return (State.GAME_OVER, [initial_points, initial_paths])

                        self.soft_reset()

            if self.preview_points and self.creating_path:
                cur_point = Point(*pygame.mouse.get_pos())
                self.preview_path.redraw(self.preview_points + [cur_point], self.get_color())

            # Update the screen if the cursor has moved
            if last_mouse_pos != current_mouse_pos:
                self.SCREEN.fill(gc.BACKGROUND_COLOR)
                last_mouse_pos = current_mouse_pos
                self.update_screen(surfaces)
                pygame.display.update()

            surfaces = []
            # controls fps
            self.CLOCK.tick(gc.FPS)

    def update_preview(self, preview_points, cur_point):
        for p in preview_points:
            if p.equals(cur_point):
                return False
        return True

    def shares_region(self, gp1, gp2):
        for r1 in gp1.regions:
            for r2 in gp2.regions:
                if r1 == r2:
                    return True
        return False

    def find_path(self):
        if not self.valid_connection(self.suggest_points[0], self.suggest_points[1]):
            self.soft_reset()
            return []

        searching = True
        canceled = False

        while searching:
            self.update_screen([])

            rrt = RRT(self.suggest_points[0], self.paths, self.SCREEN, self.points)
            suggested_points, suggested_path = rrt.build(self.suggest_points[1])

            # if user canceled path finding
            if not suggested_path:
                canceled = True
                break

            (self.all_intersections, valid_path) = self.validate_path(suggested_path)
            self.all_intersections = self.points_to_graphicspoints(self.all_intersections, gc.BLACK, 5)
            if valid_path:
                searching = False

        if canceled:
            return []
        else:
            return suggested_points

    def valid_connection(self, p1, p2):
        if p1.equals(p2):
            if p1.num_paths + 2 > 3:
                return False
        return self.shares_region(p1, p2)

    def validate_path(self, path: Path) -> Tuple[List[Point], bool]:
        valid_path = True
        all_intersections = []

        # if preview_path.start_point == preview_path.end_point and (len(preview_path.start_point.paths) + 2 >= 3):
        if path.start_point.equals(path.end_point):
            if path.start_point.num_paths + 2 > 3:
                valid_path = False
                print("too many connections")

        # Does created path collide with existing paths, and if so, where
        for p in self.paths:
            intersections = path.intersects(p)
            if intersections:
                all_intersections.extend(intersections)
                valid_path = False
                print("collides with existing paths")

        self_intersections = path.self_intersections()
        if self_intersections:
            all_intersections.extend(self_intersections)
            valid_path = False
            print("collides with itself")

        # If the path is still valid, test if it intersects with any points
        if valid_path:
            for point in self.points:
                if path.point_touches_path(point):
                    all_intersections.append(point)
                    valid_path = False
                    print("collides existing points")
        return all_intersections, valid_path

    def update_screen(self, surfaces):
        # Clear the current screen
        self.SCREEN.fill(gc.BACKGROUND_COLOR)

        # draw paths and points
        if self.preview_path:
            self.preview_path.draw(self.SCREEN)

        # Draw the objects
        self.draw_sprites(self.paths)
        self.draw_sprites(self.points)
        self.draw_sprites(self.all_intersections)

        for surface in surfaces:
            self.SCREEN.blit(surface, (0, 0))

    def draw_sprites(self, sprites):
        sprites = list(sprites)
        # Reversed to draw paths before points
        for sprite in reversed(sprites):
            sprite.draw(self.SCREEN)

    def key_event_handler(self, event):
        # Enter pressed
        if event.key == pygame.K_RETURN:
            new_point = GraphicsPoint(random.randrange(0, gc.WINDOW_WIDTH), random.randrange(0, gc.WINDOW_HEIGHT), True)
            self.base_region.add_point(new_point)
        # ESC pressed
        if event.key == pygame.K_ESCAPE:
            self.preview_path = None
            self.update_screen([])
            pygame.display.update()
            self.soft_reset()

    def point_collision(self, points, pos):
        for point in points:
            if (point.rect.collidepoint(pos)
                    and point.available()):
                return point
        return None

    def points_to_graphicspoints(self, points, color=gc.POINT_COLOR, radius=9):
        lst = []
        for p in points:
            gp = GraphicsPoint.from_point(p, False)

            gp.update_color(color)
            gp.update_radius(radius)

            lst.append(gp)
        return lst

    def game_over(self, base_region):
        if not base_region.find_open_region():
            return True

    def soft_reset(self):
        self.creating_path = False
        self.preview_points = []
        self.suggest_points = []
        # self.all_intersections = []

    def finalize_path(self, path_points):
        (start_path, end_path, mid_point) = add_path(path_points[0],
                                                     path_points[-1],
                                                     path_points)

        current_region = self.base_region.find_region(mid_point)

        # Add the paths to the region
        current_region.update_region_tree([start_path, end_path], mid_point)

        self.paths.extend([start_path, end_path])
        self.points.add(mid_point)


if __name__ == "__main__":
    # Change working directory from Fagprojekt-sprouts to main
    # print(os.getcwd())
    # os.chdir(os.getcwd()+ "/src/main")
    Main([], [])

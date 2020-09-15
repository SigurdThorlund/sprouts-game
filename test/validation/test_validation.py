import unittest
from typing import List

import pygame

import src.config.game_config as gc
from src.model.path import Path
from src.model.point import GraphicsPoint
from src.validation.planarity import validate_file, LoadException

SHOW_DRAWING = True


def draw_embedding(points: List[GraphicsPoint], paths: List[Path]):
    pygame.init()
    py_screen = pygame.display.set_mode([gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT])
    py_screen.fill(gc.BACKGROUND_COLOR)
    font = pygame.font.Font(pygame.font.get_default_font(), 16)

    for start_path, end_path, mid_point in paths:
        start_path.draw(py_screen)
        end_path.draw(py_screen)

    for point in points:
        point.draw(py_screen)

        # text_surface = font.render(str(point.index + 1), True, (0, 0, 0))
        # py_screen.blit(text_surface, point.pos())

    pygame.display.flip()

    done = False
    while not done:
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                done = True  # Flag that we are done so we exit this loop

    pygame.quit()


class TestValidation(unittest.TestCase):
    def test_empty(self):
        try:
            validate_file("")
        except LoadException as error:
            self.assertEqual("File \"\" does not exist.", str(error))

    def test_input01(self):
        params = validate_file("input_01.txt")
        if SHOW_DRAWING:
            draw_embedding(*params)

    def test_sproutes01(self):
        try:
            validate_file("sproutes01.txt")
            self.assertTrue(False)
        except LoadException as error:
            self.assertEqual("Graph became non-planar at when adding edge (10,4).", str(error))

    def test_sproutes02(self):
        try:
            validate_file("sproutes02.txt")
            self.assertTrue(False)
        except LoadException as error:
            self.assertEqual("Point 3 has more than 3 connections, after adding (3,1).", str(error))

    def test_sproutes03(self):
        params = validate_file("sproutes03.txt")
        if SHOW_DRAWING:
            draw_embedding(*params)

    def test_sproutes04(self):
        params = validate_file("sproutes04.txt")
        if SHOW_DRAWING:
            draw_embedding(*params)

    def test_sproutes05(self):
        params = validate_file("sproutes05.txt")
        if SHOW_DRAWING:
            draw_embedding(*params)

    def test_sproutes06(self):
        params = validate_file("sproutes06.txt")
        if SHOW_DRAWING:
            draw_embedding(*params)

    def test_sproutes07(self):
        try:
            validate_file("sproutes07.txt")
            self.assertTrue(False)
        except LoadException as error:
            self.assertEqual("Point 3 has more than 3 connections, after adding (2,3).", str(error))

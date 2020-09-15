import unittest

import pygame

import src.main.main


class TestBezier(unittest.TestCase):

    # test to create a bezier curve between starting points. Don't do much beside that
    def test_create_curve(self):
        events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (101, 100)}),
                  pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (200, 400)}),
                  pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (600, 300)}),
                  pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN}),
                  pygame.event.Event(pygame.KEYUP, {'key': pygame.K_RETURN})
                  ]

        def post_events(events):
            return events

        src.main.main.main(post_events(events))


if __name__ == '__main__':
    unittest.main()

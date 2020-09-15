import pygame

import src.config.game_config as gc


### MAIN RESPONSIBILITY: SIGURD FRANK THORLUND S184189 ###
class Label:
    def __init__(self, left, top, width, height, color, border_color, border_size, text, text_size, text_color):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

        self.rect = pygame.Rect(left, top, width, height)
        self.center = (left + width / 2, top + height / 2)

        self.color = color
        self.border_color = border_color
        self.border_size = border_size

        self.text = text
        self.text_size = text_size
        self.text_color = text_color

        self.surface = pygame.Surface((gc.WINDOW_WIDTH, gc.WINDOW_HEIGHT), pygame.SRCALPHA)

    def draw(self):
        pygame.draw.rect(self.surface, self.color, self.rect)
        pygame.draw.rect(self.surface, self.border_color, self.rect, self.border_size)

        text_font = pygame.font.SysFont(None, self.text_size)
        img = text_font.render(self.text, True, self.text_color)
        rect = img.get_rect()

        self.surface.blit(img, (self.center[0] - rect.width / 2, self.center[1] - rect.height / 2))
        return self.surface

    def hovering(self, mouse):
        if self.rect.collidepoint(*mouse):
            return True
        return False

    def clear_surface(self):
        pygame.draw.rect(self.surface, gc.WHITE, self.rect)

        return self.surface

# Everntuelt upload et image på baggrunden af knappen
class Button(Label):

    def __init__(self, left, top, width, height, color, border_color, border_size, text, text_size, text_color, action, function_parameters = None):
        super().__init__(left, top, width, height, color, border_color, border_size, text, text_size, text_color)
        self.action = action
        self.parameters = function_parameters

    # Transitions to the next state
    def get_action(self):
        return self.action, self.parameters



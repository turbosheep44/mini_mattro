import pygame as pg
from typing import Tuple
from util.constants import *
from entities import Rail


class GUI(object):

    def __init__(self, screen):
        self.rails = column(screen, anchor=(RIGHT, MIDDLE))
        self.score = text("0", position=(20, 20), font_size=40)

    def append_rail(self, rail: Rail):
        self.rails.children.append(button(color=rail.color, on_click=self.select_rail))
        if len(self.rails.children) == 1:
            self.select_rail(self.rails.children[0])

    def select_rail(self, button):
        i = self.rails.children.index(button)
        pg.event.post(pg.event.Event(SELECT_TRACK, track=i))
        for button in self.rails.children:
            button.outline_thickness = -1
        self.rails.children[i].outline_thickness = 2

    def set_score(self, score):
        self.score.text = str(score)

    def update(self, dt):
        self.rails.update(dt)

    def process_event(self, event):
        if self.rails.process_event(event):
            return True

        return False

    def draw(self, surface):
        self.rails.draw(surface)
        self.score.draw(surface)


class button(object):

    def __init__(self, on_click=lambda: None, color=(0, 0, 0), size=(50, 50), outline_color=(255, 255, 255), outline_thickness=-1):
        self.color = color
        self.size = size
        self.outline_color = outline_color
        self.outline_thickness = outline_thickness
        self.position = (0, 0)
        self.on_click = on_click

    def draw(self, surface):
        pg.draw.rect(surface, self.color, pg.Rect(self.position, self.size))
        pg.draw.rect(surface, self.outline_color, pg.Rect(self.position, self.size), self.outline_thickness)

    def process_event(self, event):
        # left click button
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:

            x, y = event.pos
            if x > self.position[0] and x < self.position[0] + self.size[0] \
               and y > self.position[1] and y < self.position[1] + self.size[1]:

                # run the on-click handler
                self.on_click(self)
                return True

    def height(self):
        return self.size[1]

    def width(self):
        return self.size[0]


class text(object):

    def __init__(self, text, position: Tuple[int, int] = (50, 50), font_size: int = 24):
        self.text = text
        self.position = position
        self.font = pg.font.SysFont('OpenSans-Regular', font_size)

    def draw(self, surface):
        score = self.font.render(self.text, False, (255, 255, 255))
        surface.blit(score, self.position)


class column(object):

    def __init__(self, screen, anchor=(LEFT, TOP), padding=20, spacing=10):
        self.screen = screen
        self.children = []
        self.anchor = anchor
        self.spacing = spacing
        self.padding = padding
        self.update_position = True

    def draw(self, surface):
        # draw each child
        for child in self.children:
            child.draw(surface)

    def update(self, dt):
        self.calculate_positions()

    def calculate_positions(self):
        if not self.update_position or len(self.children) == 0:
            return

        self.update_position = False

        # work out the total width and height of this container
        width = max(child.width() for child in self.children)
        height = sum(child.height() for child in self.children) + ((len(self.children)-1) * self.spacing)

        # x anchor
        left = self.padding  # LEFT
        if self.anchor[0] == MIDDLE:
            left = (self.screen[0] - width)/2
        elif self.anchor[0] == RIGHT:
            left = self.screen[0] - width - self.padding

        # y anchor
        top = self.padding  # TOP
        if self.anchor[1] == MIDDLE:
            top = (self.screen[1] - height)/2
        elif self.anchor[1] == BOTTOM:
            top = self.screen[1] - height - self.padding

        # use top-left value to set the point of each child
        offset_top = 0
        for child in self.children:
            child.position = (left + (width - child.width())/2, top + offset_top)
            offset_top += self.spacing + child.height()

    def process_event(self, event):
        for child in self.children:
            if child.process_event(event):
                return True

        return False


def setup_gui(screen) -> GUI:
    gui = GUI(screen)
    return gui

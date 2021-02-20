from entities.train import Train
import pygame as pg
from typing import Tuple
from util.constants import *
from entities import Rail
from abc import ABC, abstractmethod

from util.data import data


class GUI(object):

    def __init__(self, screen):

        button_style = {'size': (25, 25), 'color': (200, 200, 200), 'outline_thickness': 1, 'outline_color': (0, 0, 0)}
        self.__add_train_button = button(on_click=lambda _: pg.event.post(pg.event.Event(REQUEST_TRAIN, rail=data.active_rail)), child=text('+', color=(0, 0, 0)), **button_style)
        self.__available_trains = text('-', color=(0, 0, 0))
        self.__add_train_group = organizer(organizer.VERTICAL, children=[self.__available_trains, self.__add_train_button], padding=5, spacing=8)

        self.rails = organizer(organizer.VERTICAL, screen, anchor=(RIGHT, MIDDLE))
        self.score = text("0", position=(20, 20), font_size=40)
        self.train_block = organizer(organizer.HORIZONTAL, screen, anchor=(RIGHT, TOP), children=[self.__add_train_group])

        self.update_values()

    def append_rail(self, rail: Rail):
        self.rails.append_child(button(color=rail.color, on_click=self.select_rail))

        # select the first rail
        if self.rails.child_count() == 1:
            self.select_rail(self.rails.get_child(0))

    def select_rail(self, clicked_button):
        # find out the index of the rail and select that track
        i = self.rails.index_of_child(clicked_button)
        pg.event.post(pg.event.Event(SELECT_TRACK, track=i))

        # show an outline for the selected rail only
        for j in range(self.rails.child_count()):
            self.rails.get_child(j).outline_thickness = -1 if j != i else 2

        # set the number of trains on this rail
        self.set_trains(data.rails[i])

    def set_trains(self, rail: Rail):
        if rail == None:
            print("strange error")
            return
        self.train_block.set_children([self.__add_train_group]+[train(t) for t in rail.trains])

    def update_values(self):
        self.score.set_text(str(data.score))
        self.__available_trains.set_text(f"{data.available_trains}, {data.available_train_upgrades}")

    def process_event(self, event):
        if event.type == TRAINS_CHANGED:
            self.set_trains(data.active_rail)
            self.update_values()

        if self.rails.process_event(event):
            return True
        if self.train_block.process_event(event):
            return True

        return False

    def draw(self, surface):
        self.rails.draw(surface)
        self.score.draw(surface)
        self.train_block.draw(surface)


class gui_element(ABC):
    @abstractmethod
    def __init__(self):
        self.parent: 'gui_element' = None
        self.position = None

    def maximal_parent(self):
        return self.parent.maximal_parent() if self.parent else self

    @abstractmethod
    def width(self) -> int:
        pass

    @abstractmethod
    def height(self) -> int:
        pass

    @abstractmethod
    def draw(self, surface) -> None:
        pass

    def process_event(self, event) -> bool:
        return False

    def recalculate_size(self) -> None:
        pass

    def set_child_positions(self) -> None:
        pass

    def update_state(self) -> None:
        self.recalculate_size()
        self.set_child_positions()


class button(gui_element):

    def __init__(self, on_click=lambda _: None, child: gui_element = None, color=(0, 0, 0), size=(50, 50), outline_color=(255, 255, 255), outline_thickness=-1):
        super().__init__()

        self.child: gui_element = child
        self.on_click = on_click

        self.__size: 'Tuple[int, int]' = (0, 0)
        self.__min_size: 'Tuple[int, int]' = size

        self.color = color
        self.outline_color = outline_color
        self.outline_thickness = outline_thickness

    def draw(self, surface):
        pg.draw.rect(surface, self.color, pg.Rect(self.position, self.__size))
        pg.draw.rect(surface, self.outline_color, pg.Rect(self.position, self.__size), self.outline_thickness)

        if self.child:
            self.child.draw(surface)

    def process_event(self, event):
        # left click button
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:

            x, y = event.pos
            if x > self.position[0] and x < self.position[0] + self.width() \
               and y > self.position[1] and y < self.position[1] + self.height():

                # run the on-click handler
                self.on_click(self)
                return True

    def set_child(self, child):
        self.child = child
        self.maximal_parent().update_state()

    def height(self) -> int:
        return self.__size[1]

    def width(self) -> int:
        return self.__size[0]

    def recalculate_size(self) -> None:
        self.__size = (max(self.__min_size[0], self.child.width() if self.child else 0),
                       max(self.__min_size[1], self.child.height() if self.child else 0))

        if self.child:
            self.child.recalculate_size()

    def set_child_positions(self) -> None:
        if self.child:
            self.child.position = (self.position[0] + (self.width() - self.child.width())/2,
                                   self.position[1] + (self.height() - self.child.height())/2)


class text(gui_element):

    def __init__(self, text, position: Tuple[int, int] = (50, 50), font_size: int = 24, color=(255, 255, 255)):
        super().__init__()
        self.color = color
        self.position = position
        self.font = pg.font.SysFont('OpenSans-Regular', font_size)
        self.set_text(text)

    def set_text(self, text):
        self.text = text
        self.maximal_parent().update_state()

    def recalculate_size(self) -> None:
        text = self.font.render(self.text,  False, (255, 255, 255))
        self.__width, self.__height = text.get_size()

    def draw(self, surface):
        score = self.font.render(self.text, False, self.color)
        surface.blit(score, self.position)

    def width(self) -> int:
        return self.__width

    def height(self) -> int:
        return self.__height


class sized_box(gui_element):
    def __init__(self, size):
        super().__init__()
        self.__size = size

    def width(self) -> int:
        return self.__size[0]

    def height(self) -> int:
        return self.__size[1]

    def draw(_, __) -> None:
        pass


class organizer(gui_element):
    HORIZONTAL = True
    VERTICAL = False

    def __init__(self, horizontal, screen=None, anchor=(LEFT, TOP), padding=20, spacing=10, children=None):
        super().__init__()
        self.screen = screen

        self.__children: 'list[gui_element]' = []

        self.__horizontal: bool = horizontal
        self.__anchor = anchor
        self.__spacing = spacing
        self.__padding = padding

        self.__width: int = 0
        self.__height: int = 0

        if children:
            self.set_children(children)

    def set_children(self, children: 'list[gui_element]'):
        self.__children = children
        for child in children:
            child.parent = self
        self.maximal_parent().update_state()

    def append_child(self, child: 'gui_element'):
        self.__children.append(child)
        child.parent = self
        self.maximal_parent().update_state()

    def child_count(self) -> int:
        return len(self.__children)

    def get_child(self, i) -> int:
        return self.__children[i]

    def index_of_child(self, child) -> int:
        return self.__children.index(child)

    def process_event(self, event):
        for child in self.__children:
            if child.process_event(event):
                return True

        return False

    def draw(self, surface):
        # l, t = self.__get_position()
        # pg.draw.rect(surface, (50 * len(self.__children), 0, 0), pg.Rect((l, t), (self.width(), self.height())))
        # pg.draw.rect(surface, (0, 50 * len(self.__children),  0), pg.Rect((l + self.__padding, t + self.__padding), (self.width() - 2*self.__padding, self.height() - 2*self.__padding)))
        for child in self.__children:
            child.draw(surface)

    def __get_position(self):
        if self.position:  # respect the given position
            return self.position

        elif self.screen:  # calculate position based on screen anchors
            # x anchor
            left = 0  # LEFT
            if self.__anchor[0] == MIDDLE:
                left = (self.screen[0] - self.__width)/2
            elif self.__anchor[0] == RIGHT:
                left = self.screen[0] - self.__width

            # y anchor
            top = 0  # TOP
            if self.__anchor[1] == MIDDLE:
                top = (self.screen[1] - self.__height)/2
            elif self.__anchor[1] == BOTTOM:
                top = self.screen[1] - self.__height

            return left, top

        else:
            return 0, 0

    def set_child_positions(self):
        # get the base top-left of this container
        left, top = self.__get_position()
        left += self.__padding
        top += self.__padding

        # space the children evenly
        offset = 0
        for child in self.__children:
            if self.__horizontal:
                child.position = (left + offset, top + (self.__height - 2*self.__padding - child.height())/2)
                offset += self.__spacing + child.width()
            else:
                child.position = (left + (self.__width - 2*self.__padding - child.width())/2, top + offset)
                offset += self.__spacing + child.height()

        for child in self.__children:
            child.set_child_positions()

    def recalculate_size(self):
        for child in self.__children:
            child.recalculate_size()

        self.__height = ((max if self.__horizontal else sum)(child.height() for child in self.__children)) + (2 * self.__padding)
        self.__width = ((sum if self.__horizontal else max)(child.width() for child in self.__children)) + (2 * self.__padding)

        if self.__horizontal:
            self.__width += ((len(self.__children)-1) * self.__spacing)
        else:
            self.__height += ((len(self.__children)-1) * self.__spacing)

    def height(self):
        return self.__height

    def width(self):
        return self.__width


class train_icon(gui_element):
    __size = (35, 68)

    def __init__(self, train: Train):
        super().__init__()
        self.train: Train = train

    def draw(self, surface):
        pg.draw.rect(surface, (255, 200, 0) if self.train.is_upgraded else(200, 200, 200), pg.Rect(self.position, train_icon.__size))
        pg.draw.rect(surface, (0, 0, 0), pg.Rect(self.position, train_icon.__size), 1)

        passenger_center = Vector2(self.position[0] + 2+8, self.position[1] + 1+11)
        for i, p in enumerate(self.train.passengers):
            p.shape.draw(surface, passenger_center, 15, True)
            if not i % 2:
                passenger_center.x += 15
            else:
                passenger_center.x -= 15
                passenger_center.y += 22

    def width(self):
        return train_icon.__size[0]

    def height(self):
        return train_icon.__size[1]


class train(organizer):
    button_style = {'size': (30, 15), 'color': (200, 200, 200), 'outline_color': (0, 0, 0), 'outline_thickness': 1}
    text_style = {'color': (0, 0, 0), 'font_size': 20}

    def __init__(self, train: Train):

        self.__train = train
        self.__train_icon = train_icon(train)

        self.__upgrade = sized_box(self.button_style['size'])
        if not train.is_upgraded:
            self.__upgrade = button(child=text("UP", **self.text_style), **self.button_style, on_click=self.upgrade_train)

        self.__remove = button(child=text("X", **self.text_style), **self.button_style, on_click=self.sell_train)
        if train.end_of_life:
            self.__remove = sized_box(self.button_style['size'])

        super().__init__(organizer.VERTICAL,  anchor=(MIDDLE, MIDDLE), padding=5, spacing=5,
                         children=[self.__upgrade, self.__train_icon, self.__remove])

    def upgrade_train(self, _):
        pg.event.post(pg.event.Event(UPGRADE_TRAIN, train=self.__train))

    def sell_train(self, _):
        self.__train.end_of_life = True
        self.__remove = sized_box(self.button_style['size'])
        self.set_children([self.__upgrade, self.__train_icon, self.__remove])


def setup_gui(screen) -> GUI:
    gui = GUI(screen)
    return gui


pg.font.init()

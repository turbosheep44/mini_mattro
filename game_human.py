
from mini_mattro import FPS, MiniMattro
import random
from pygame.constants import K_SPACE
from pygame.event import Event
from util.gui import *
from entities import TrackSegment, Station, Train
from util import *
import pygame as pg


class MiniMattroHuman(MiniMattro):

    def __init__(self):
        super().__init__()
        self.tmp_segment: TrackSegment = None

    def play_step(self):
        dt = self.clock.tick(FPS) / 1000
        game_over = self.update(dt)
        self.draw()

        return game_over

    def handle_events(self, events: 'list[Event]') -> None:
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self.left_click_down(event)
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.left_click_up(event)
            elif event.type == pg.MOUSEBUTTONUP and event.button == 3:
                self.right_click_up(event)
            elif event.type == pg.MOUSEMOTION:
                self.mouse_move(event)

    def left_click_down(self, event):
        pt = event.pos
        s = self.clip_to_station(pt)
        if s != None and data.active_rail.is_station_valid(s):
            self.tmp_segment = TrackSegment(data.active_rail, data.stations[s].location, (s, None))

    def left_click_up(self, event):
        if self.tmp_segment:
            s = self.clip_to_station(event.pos)
            if s != None and not data.active_rail.is_on_rail(s) and s != self.tmp_segment.stations[0]:
                self.tmp_segment.update_dst(data.stations, s)
                data.active_rail.add_segment(self.tmp_segment, data.stations)
                # dont call self.connect here because it might change the way the segment looks
                # self.connect(self.tmp_segment.stations[0], s, data.active_rail_index)
            self.tmp_segment = None

    def right_click_up(self, event):
        s = self.clip_to_station(event.pos)
        if s != None:
            self.remove_station(s, data.active_rail_index)

    def mouse_move(self, event):
        pt = event.pos
        if self.tmp_segment:
            s = self.clip_to_station(pt)
            if data.active_rail.is_on_rail(s):
                s = None
            self.tmp_segment.update_dst(data.stations,  s, pt)

        for train in data.trains():
            train.hover = train.is_hovering(pt)

    def clip_to_station(self, pt):
        for i, s in enumerate(data.stations):
            if s.contains(pt):
                return i
        return None


if __name__ == '__main__':
    game = MiniMattroHuman()

    while True:
        game_over = game.play_step()
        if game_over == True:
            break

    print('Final Score', data.score)

    pg.quit()


from entities.segment import TrackSegment
from util.draw import ortholine
import pygame as pg


class Train(object):

    def __init__(self, segment):
        self.position: float = 0
        self.direction: float = 1
        self.current_segment: TrackSegment = segment

    def update(self, dt):
        self.position += self.current_segment.position_update * dt * self.direction
        if self.position > 1:
            if self.current_segment.next != None:
                self.current_segment = self.current_segment.next
                self.position -= 1
            else:
                self.direction *= -1
                self.position = 1 + (1-self.position)
        elif self.position < 0:
            if self.current_segment.previous != None:
                self.current_segment = self.current_segment.previous
                self.position += 1
            else:
                self.direction *= -1
                self.position = -1 * self.position

    def draw(self, surface):
        pt, dv = self.current_segment.lerp_position(self.position)
        dv.scale_to_length(30)
        ortholine(surface, (255, 255, 255), pt - (dv/2), pt + (dv/2), 16)

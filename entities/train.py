
from entities.passenger import Passenger
from util.constants import SCORE_POINT, TRAIN_SECONDS_PER_ACTION, TRAIN_STOP
from entities.segment import TrackSegment
from util.draw import ortholine
import pygame as pg


class Train(object):

    def __init__(self, segment):
        self.position: float = 0
        self.direction: float = 1
        self.current_segment: TrackSegment = segment

        self.is_stopped: bool = False
        self.next_action: float = TRAIN_SECONDS_PER_ACTION

        self.disembark: list[Passenger] = []
        self.embark: list[Passenger] = []
        self.passengers = []

        self.todelete = False

    def update(self, dt, data):
        # keep moving the train until it gets to another station
        if not self.is_stopped:
            self.move_train(dt)

        # process disembark requests first
        elif len(self.disembark) > 0:

            self.next_action -= dt
            if self.next_action > 0:
                return
            self.next_action = TRAIN_SECONDS_PER_ACTION

            station = data.stations[self.stopped_station]
            passenger = self.disembark.pop()
            if passenger.shape != station.shape:
                station.passengers.append(passenger)
            else:
                pg.event.post(pg.event.Event(SCORE_POINT))

        # embark new passengers
        elif len(self.embark) > 0:

            self.next_action -= dt
            if self.next_action > 0:
                return
            self.next_action = TRAIN_SECONDS_PER_ACTION

            station = data.stations[self.stopped_station]
            passenger = self.embark.pop()
            try:
                station.passengers.remove(passenger)
                self.passengers.append(passenger)
            except:
                pass

        # start moving the train again
        else:
            self.is_stopped = False
            self.next_action = TRAIN_SECONDS_PER_ACTION

    def move_train(self, dt):
        self.position += self.current_segment.position_update * dt * self.direction

        if self.position > 1 or self.position < 0:
            pg.event.post(pg.event.Event(TRAIN_STOP, train=self,
                                         station=self.current_segment.stations[round(self.position)]))

            self.is_stopped = True
            self.stopped_station = self.current_segment.stations[round(self.position)]

            if self.position > 1 and self.current_segment.next != None:
                self.current_segment = self.current_segment.next
                self.position = 0
            elif self.position < 0 and self.current_segment.previous != None:
                self.current_segment = self.current_segment.previous
                self.position = 1
            else:
                self.direction *= -1
                self.position = round(self.position)

    def draw(self, surface):
        pt, dv = self.current_segment.lerp_position(self.position)
        dv.scale_to_length(30)
        ortholine(surface, (255, 255, 255), pt - (dv/2), pt + (dv/2), 15)

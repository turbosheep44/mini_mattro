
from entities.passenger import Passenger
from util.constants import EOL_TRAIN, SCORE_POINT, TRAINS_CHANGED, TRAIN_CAPACITY,  TRAIN_SECONDS_PER_ACTION, TRAIN_STOP
from entities.segment import TrackSegment
from util.draw import ortholine
import pygame as pg
from pygame import Vector2


class Train(object):

    def __init__(self, segment):
        self.last_position: Vector2 = Vector2(0, 0)
        self.position: float = 0.25
        self.direction: float = -1
        self.current_segment: TrackSegment = segment

        self.hover = False
        self.end_of_life: bool = False
        self.is_upgraded: bool = False
        self.is_stopped: bool = False
        self.next_action: float = TRAIN_SECONDS_PER_ACTION

        self.disembark: 'list[Passenger]' = []
        self.embark: 'list[Passenger]' = []
        self.passengers: 'list[Passenger]' = []

    def update(self, dt, data):
        # keep moving the train until it gets to another station
        if not self.is_stopped:
            self.move_train(dt)

        elif self.end_of_life:
            self.process_end_of_life(dt, data)

        elif len(self.disembark) > 0:
            self.process_disembark(dt, data)
            station = data.stations[self.stopped_station]
            passenger = self.disembark.pop()
            if passenger.shape != station.shape:
                station.passengers.append(passenger)
                self.passengers.remove(passenger)

            else:
                pg.event.post(pg.event.Event(SCORE_POINT))
                self.passengers.remove(passenger)


        elif len(self.embark) > 0:
            self.process_embark(dt, data)

        else:
            # start moving the train again
            self.choose_next_segment()
            self.is_stopped = False
            self.next_action = TRAIN_SECONDS_PER_ACTION

    def move_train(self, dt):
        self.position += self.current_segment.position_update * dt * self.direction * (2 if self.is_upgraded else 1)

        if self.position > 1 or self.position < 0:
            pg.event.post(pg.event.Event(TRAIN_STOP, train=self,
                                         station=self.current_segment.stations[round(self.position)]))

            self.is_stopped = True
            self.stopped_station = self.current_segment.stations[round(self.position)]

    def process_end_of_life(self, dt, data):
        if not self.perform_action(dt):
            return

        # leave all of the passengers at this station
        if len(self.passengers) != 0:
            station = data.stations[self.stopped_station]
            passenger = self.passengers.pop()
            if passenger.shape != station.shape:
                station.passengers.append(passenger)
            else:
                pg.event.post(pg.event.Event(SCORE_POINT))

        # remove from the rail once all passengers are gone
        else:
            pg.event.post(pg.event.Event(EOL_TRAIN, train=self))

    def process_disembark(self, dt, data):
        if not self.perform_action(dt):
            return

        station = data.stations[self.stopped_station]
        passenger = self.disembark.pop()
        self.passengers.remove(passenger)
        if passenger.shape != station.shape:
            station.passengers.append(passenger)
        else:
            pg.event.post(pg.event.Event(SCORE_POINT))

    def process_embark(self, dt, data):
        if not self.perform_action(dt):
            return

        # cant take any more passengers when train reaches capacity
        if len(self.passengers) >= TRAIN_CAPACITY:
            for passenger in self.embark:
                passenger.is_boarding = False
            self.embark = []
            return

        # board one passenger
        station = data.stations[self.stopped_station]
        passenger = self.embark.pop()

        #! Sometimes passenger wouldn't be in station.passengers so I added this if-stmt
        if passenger in station.passengers:
            station.passengers.remove(passenger)
        else:
            return

        self.passengers.append(passenger)
        passenger.is_boarding = False

    def perform_action(self, dt) -> bool:
        """
        removes `dt` from the time until next action and returns True if an action can be performed
        """
        self.next_action -= dt

        if self.next_action > 0:
            return False

        self.next_action = TRAIN_SECONDS_PER_ACTION * (0.5 if self.is_upgraded else 1)
        return True

    def choose_next_segment(self):
        self.current_segment, self.direction = self.current_segment.next_segment(self.direction)
        self.position = 0 if self.direction == 1 else 1

    def is_hovering(self, mouse: Vector2):
        if Vector2(mouse).distance_to(self.last_position) < 30:
            return True
        return False

    def draw(self, surface):
        pt, dv = self.current_segment.lerp_position(min(1, max(0, self.position)))
        self.last_position = pt

        dv.scale_to_length(30)
        if self.direction != 1:
            dv.rotate_ip(180)

        start = pt - (dv/2)
        end = pt + (dv/2)
        inset = dv/10
        inset_dv = dv*0.8
        amount_full = len(self.passengers)/TRAIN_CAPACITY

        # draw the train itself
        ortholine(surface, (255, 200, 0) if self.is_upgraded else (255, 255, 255), start, end, 15)
        ortholine(surface, (0, 0, 0), start+inset, start+inset+(inset_dv*amount_full), 11)

        # draw the passenger bubble
        if self.hover:
            splitter = Vector2(-2, 1)
            split_angle = dv.angle_to(splitter)
            if split_angle < 0:
                split_angle = 360 + split_angle
            bubble_direction = dv.rotate(90 if split_angle > 180 else -90)
            bubble_direction.scale_to_length(30)
            bubble_start = pt + bubble_direction
            bubble_end = bubble_start + Vector2((15*len(self.passengers))+20, 0)

            ortholine(surface, (255, 255, 255),  bubble_start, bubble_end, 16)
            bubble_start.x += 10
            pg.draw.circle(surface, self.current_segment.rail.color, bubble_start, 5)
            bubble_start.x += 15
            for i, p in enumerate(self.passengers):
                p.draw(surface, bubble_start, i)

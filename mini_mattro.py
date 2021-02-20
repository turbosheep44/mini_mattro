from entities.dijkstras import Graph
import random
from pygame.event import Event
from util.gui import *
from entities import TrackSegment, Station, Train
from util import *
from abc import ABC, abstractmethod
import pygame as pg
from pygame import Vector2


pg.init()
pg.font.init()
font = pg.font.SysFont('OpenSans-Regular', 24)
FPS = 60


class MiniMattro(ABC):

    def __init__(self, w=1000, h=900):
        self.w = w
        self.h = h

        self.passenger_spawn = 0
        self.gui: GUI = None
        self.reset()

        # surface = display
        pg.display.set_caption("MiniMattro")
        self.display = pg.display.set_mode((self.w, self.h), pg.DOUBLEBUF)
        self.clock = pg.time.Clock()
        self.layers = [pg.Surface((self.w, self.h), pg.SRCALPHA) for _ in range(5)]

    def reset(self):
        data.reset()
        data.stations = [Station(Shape.CIRCLE, Vector2(125, 100)),
                         Station(Shape.CIRCLE, Vector2(350, 150)),
                         Station(Shape.CIRCLE, Vector2(300, 350)),
                         Station(Shape.CIRCLE, Vector2(600, 650)),
                         Station(Shape.SQUARE, Vector2(400, 250)),
                         Station(Shape.SQUARE, Vector2(500, 500)),
                         Station(Shape.TRIANGLE, Vector2(100, 450)),
                         Station(Shape.TRIANGLE, Vector2(100, 250))]
        self.gui = setup_gui([self.w, self.h])
        self.create_rail()
        self.create_rail()
        self.create_rail()

    @abstractmethod
    def play_step(self):
        pass

    @abstractmethod
    def handle_events(self, event: Event) -> None:
        pass

    def update(self, dt) -> bool:
        # UPDATE GUI
        self.passenger(dt)

        # HANDLE EVENTS
        events = []
        for event in pg.event.get():
            if self.gui.process_event(event):
                continue

            events.append(event)

            if event.type == pg.QUIT:
                exit(0)
            elif event.type == SELECT_TRACK:
                data.active_rail = data.rails[event.track]
                data.active_rail_index = event.track
            elif event.type == SCORE_POINT:
                data.score += 1
                self.gui.update_values()
            elif event.type == TRAIN_STOP:
                self.train_stop(event)
            elif event.type == REQUEST_TRAIN:
                self.add_train(data.rails.index(event.rail))
            elif event.type == UPGRADE_TRAIN:
                self.upgrade_train(event.train)
            elif event.type == EOL_TRAIN:
                self.delete_train(event.train)

        self.handle_events(events)

        # UPDATE TRAINS
        for r in data.rails:
            r.update(dt, data)

        # CHECK GAME OVER
        for s in data.stations:
            if s.update(dt):
                return True

        return False

    def draw(self):

        # reset screen
        self.display.fill((100, 100, 100))
        for layer in self.layers:
            layer.fill((0, 0, 0, 0))

        for r in data.rails:
            r.draw(self.layers)

        if hasattr(self, "tmp_segment") and self.tmp_segment:
            self.tmp_segment.draw(self.layers[RAIL_LAYER])

        for s in data.stations:
            s.draw(self.layers[STATION_LAYER])

        self.gui.draw(self.layers[GUI_LAYER])

        # show fps
        fps = font.render(f"FPS: {int(self.clock.get_fps())}", False, (255, 255, 255))
        self.display.blit(fps, (10, self.display.get_size()[1]-fps.get_size()[1]-10))

        # draw each layer
        self.layers[REMOVED_RAIL_LAYER].set_alpha(128)
        for layer in self.layers:
            self.display.blit(layer, (0, 0))

        pg.display.flip()

    def get_stations_by_shape(self, destination_shape: Shape) -> 'list[int]':
        destination_stations: 'list[int]' = []
        for i, s in enumerate(data.stations):
            if s.shape == destination_shape:
                destination_stations.append(i)
        return destination_stations

    def _static_graph(self, station: int) -> Graph:
        """
        construct a `Graph` indicating the current state of connections between stations,
        initialised so that each edge has 1.2x it's actual cost (and no owner) to penalise 
        the use of static lengths

        if a rail passes through `station` then its connections are not added (since they should be 
        added using the live train positions)
        """
        graph = Graph()

        for s in range(len(data.stations)):
            graph.add_node(s)

        for rail in data.rails:
            if rail.is_on_rail(station):
                continue
            for segment in rail.segments:
                src, dst = segment.stations[0], segment.stations[1]
                graph.add_edge(src, dst, segment.length*1.2)  # use 1.2 multiplier to penalise "static" links
                graph.add_edge(dst, src, segment.length*1.2)

        return graph

    def _construct_graph(self, station: int) -> Graph:
        """
        constructs a `Graph` where weights are calculated based on the trains positions 
        for those rails passing through station and calculated statically otherwise
        """
        graph = self._static_graph(station)

        live_rails = [rail for rail in data.rails if rail.is_on_rail(station)]
        for rail in live_rails:
            if len(rail.trains) == 0:
                continue

            for train in rail.trains:

                train_start_station = train.destination()
                train_start_direction = train.direction
                direction = train.direction
                current_segment = train.current_segment
                cost = train.distance_to_dst()

                # work out distance to the station we are interested in
                while current_segment.dst_station(direction) != station:
                    current_segment, direction = current_segment.next_segment(direction)
                    cost += current_segment.length

                # now keep simulating train movement until we complete a loop of the track
                # during this process also give costs to graph edges
                #
                # if the train is approaching the target station, it will not move in the first loop
                # this loop is a do-while to ensure that the train moves at least once
                while True:
                    current_segment, direction = current_segment.next_segment(direction)
                    cost += current_segment.length
                    graph.add_edge(station, current_segment.dst_station(direction), cost * (0.5 if train.is_upgraded else 1), train)

                    if current_segment.dst_station(direction) == train_start_station and direction == train_start_direction:
                        break

        return graph

    def _should_use_train(self, graph: Graph, start: int,  dst: Shape, train: Train):
        """
        given a `Graph` and a starting station, works out the quickest way to get to a station of the given shape.
        then checks whether the first leg of that journey belongs to the given train and returns True if so and false otherwise
        """
        possible_destinations = self.get_stations_by_shape(dst)
        shortest_info = graph.shortest(start, possible_destinations)

        # if there is no possible path, then dont get on any train
        if shortest_info == None:
            return False

        # get on this train if the first edge in the shortest path is owned by this train
        _, __, path, edge_owners = shortest_info
        return len(path) == 1 or edge_owners[0] == train

    def train_stop(self, event):
        s: int = event.station
        station: Station = data.stations[s]
        train: Train = event.train

        graph = self._construct_graph(s)

        for passenger in train.passengers:
            if passenger.shape == station.shape or not self._should_use_train(graph, s, passenger.shape, train):
                train.disembark.append(passenger)

        for passenger in station.passengers:
            if not passenger.is_boarding and self._should_use_train(graph, s, passenger.shape, train):
                train.embark.append(passenger)
                passenger.is_boarding = True

    def passenger(self, dt):
        self.passenger_spawn += dt

        if self.passenger_spawn > PASSENGER_SPAWN:

            randomStation = random.choice(data.stations)
            randomPassenger = random.choice(list(Shape))

            while randomPassenger == randomStation.shape:
                randomStation = random.choice(data.stations)
                randomPassenger = random.choice(list(Shape))

            randomStation.create_passenger(randomPassenger)
            self.passenger_spawn = 0

    def create_rail(self):
        data.rails.append(Rail(COLORS[data.next_color()]))
        self.gui.append_rail(data.rails[-1])

    def add_train(self, r: int) -> bool:
        rail: Rail = data.rails[r]
        if data.available_trains < 1 or len(rail.segments) < 1:
            return False

        data.available_trains -= 1
        rail.trains.append(Train(random.choice(rail.segments)))
        pg.event.post(pg.event.Event(TRAINS_CHANGED))
        return True

    def upgrade_train(self, train: Train) -> bool:
        if not train or data.available_train_upgrades < 1 or train.is_upgraded:
            return False

        data.available_train_upgrades -= 1
        train.is_upgraded = True
        pg.event.post(pg.event.Event(TRAINS_CHANGED))
        return True

    def delete_train(self, train: Train):
        train.current_segment.rail.trains.remove(train)
        data.available_trains += 1
        if train.is_upgraded:
            data.available_train_upgrades += 1
        pg.event.post(pg.event.Event(TRAINS_CHANGED))

    def connect(self, s1: int, s2: int, r: int) -> bool:
        rail = data.rails[r]
        # cant join a station to itself
        if s1 == s2:
            return False

        # if invalid configuration, try to swap them
        if not rail.is_station_valid(s1) or rail.is_on_rail(s2):
            s1, s2 = s2, s1

        if not rail.is_station_valid(s1) or rail.is_on_rail(s2):
            # still invalid configuration -> invalid action
            return False

        segment = TrackSegment(rail, data.stations[s1].location, (s1, None))
        segment.update_dst(data.stations, s2)
        rail.add_segment(segment, data.stations)
        return True

    def remove_station(self, s: int, r: int) -> bool:
        if not data.rails[r].can_remove_station(s):
            # print("invalid remove action")
            return False

        data.rails[r].remove_station(s, data.stations)
        return True

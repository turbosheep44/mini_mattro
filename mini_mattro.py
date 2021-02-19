
import random
from pygame.constants import K_SPACE
from pygame.event import Event
from util.gui import *
from entities import TrackSegment, Station, Train, allpaths, graph
from util import *
from abc import ABC, abstractmethod
import pygame as pg
from pygame import Vector2


pg.init()
pg.font.init()
font = pg.font.SysFont('OpenSans-Regular', 24)
FPS = 120


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
        reset_data()
        data.stations = [Station(Shape.CIRCLE, Vector2(125, 100)),
                         Station(Shape.CIRCLE, Vector2(350, 150)),
                         Station(Shape.CIRCLE, Vector2(300, 350)),
                         Station(Shape.CIRCLE, Vector2(600, 650)),
                         Station(Shape.SQUARE, Vector2(400, 250)),
                         Station(Shape.SQUARE, Vector2(500, 500)),
                         Station(Shape.TRIANGLE, Vector2(100, 450)),
                         Station(Shape.TRIANGLE, Vector2(100, 250))]

        data.stations[3].create_passenger(Shape.SQUARE)
        
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
            if s.update():
                return True, events

        return False, events

    def draw(self):

        # reset screen
        self.display.fill((100, 100, 100))
        for layer in self.layers:
            layer.fill((0, 0, 0, 0))

        for r in data.rails:
            r.draw(self.layers)

        if self.tmp_segment:
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

    def get_stations_by_shape(destination_shape: Shape):

        destination_stations: Station = []
        for i, s in enumerate(data.stations):
            if s.shape == destination_shape:
                destination_stations.append(i)

        return destination_stations


    def get_rails():

        rails = []

        for r in data.rails:
            for s in r.segments:
                rails.append((str(s.stations[0]), str(s.stations[1])))
                rails.append((str(s.stations[1]), str(s.stations[0])))

        paths = {}

        for rail in rails:
            paths[rail[0]] = []
            
        for rail in rails:
            l = paths[rail[0]]
            l.append(rail[1])
        
        return paths

    def find_path(start, end, path=[]):

        paths = MiniMattro.get_rails()

        path = path + [start]
        if start == end:
            return path
        if start not in paths:
            return None
        for node in paths[start]:
            if node not in path:
                newpath = MiniMattro.find_path(node, end, path)
                if newpath: 
                    return newpath
        return None


    def changeover(path, railway_segments, this_railway):

        path_copy = path.copy()

        while this_railway == None:
            for rail in railway_segments:
                if (" ".join(map(str,path_copy)) in " ".join(map(str,rail)))  or (" ".join(map(str,path_copy)) in " ".join(map(str,(reversed(rail))))):
                    this_railway = railway_segments.index(rail)
            if this_railway == None:
                path_copy.pop()
        return this_railway, path_copy


    def calculate_path(passenger, station, train):
        print("Calculating Distance")

        if passenger.shape == station.shape:
            return []

        start = str(data.stations.index(station))
        destination_shape = passenger.shape

        all_path_sums = []
        available_stations = MiniMattro.get_stations_by_shape(destination_shape)

        # weights_graph = graph.Graph()
        connection = allpaths.Graph(len(data.stations))

        for rail in data.rails:
            for seg in rail.segments:
                connection.addEdge(seg.stations[0], seg.stations[1])
                connection.addEdge(seg.stations[1], seg.stations[0])



        for stage in available_stations:
            to = str(stage)

            if MiniMattro.find_path(start, to) != None:

                railway_segments = []
                for count, rail in enumerate(data.rails):
                    railway_segments.append([])
                    if len(rail.segments) ==0:
                        continue
                    for s in rail.segments:
                        railway_segments[count].append(s.stations[0])
                    railway_segments[count].append(rail.segments[-1].stations[-1])
                                
                
                paths = []
                connection.printAllPaths(int(start), int(to), paths)

                for path in paths:

                    this_railway = None

                    static_path = 0

                    for p in range(len(path)-1):
                        static_path += (data.stations[path[p]].location).distance_to(data.stations[path[p+1]].location)
                    
                    this_railway, path= MiniMattro.changeover(path, railway_segments, this_railway)

                    changeover_path = 0
                    for p in range(len(path)-1):
                        changeover_path += data.stations[int(path[p])].location.distance_to(data.stations[int(path[p+1])].location)
                    
                    static_difference = static_path - changeover_path 

                    train = data.rails[this_railway].trains[0]
                    railway = railway_segments[this_railway]

                    path_sum = 0
                    path_sum += MiniMattro.train_travel(path, railway, train, station)

                    path_sum += static_difference
                
                    all_path_sums.append((path, path_sum))
        
        # print("    (Paths, Weights):   ", all_path_sums, "\n\n ")

        if len(all_path_sums) > 0:  
            shortest_path = sorted(all_path_sums, key=lambda tup: tup[1])[0][0]
            return shortest_path
        else:
            return []


        
        
    def train_travel(path, railway, train, station):


        path_sum = 0

        path_seg = [int(i) for i in path][:2]
        path_direction = 0

        this_station = data.stations.index(station)

        dep = path[0]
        arr = path[-1]

        if train.direction == 1:
            next_station = (train.current_segment.stations)[1]
            # print("----Next Station ----", next_station)
        else:
            next_station = (train.current_segment.stations)[0]
            # print("----Next Station ----", next_station)


        if railway.index(dep) < railway.index(arr):
            path_direction = 1
        else:
            path_direction = -1
        

        is_dep = False
        is_arr = False

        next_segment = train.current_segment
        dir_of_travel = train.direction
        pos = train.position

        if pos > 1:
            pos = 1

        # path_sum += (train.current_segment.length * ((1-pos) if train.direction ==1 else pos))
        path_sum += (train.current_segment.length * (1-pos) )

        while (next_station != arr) and (is_dep == False):

            next_segment, dir_of_travel = next_segment.next_segment(dir_of_travel)

            path_sum += next_segment.length

            next_station= next_segment.stations[0 if dir_of_travel == -1 else 1]
            
            if next_station == dep:
                is_dep = True

        return path_sum
            

            

    def board(shortest_path, train, on_station):
    
        if len(shortest_path) == 0:
            return False

        seg = list(map(int, shortest_path))[:2]
        seg.sort()

        next_segment, new_dir =  (train.current_segment).next_segment(train.direction)

        train_seg = list(next_segment.stations)
        train_seg.sort()

        if seg == train_seg:
            return True
        else:
            return False    




    def train_stop(self, event):
        station: Station = data.stations[event.station]
        train: Train = event.train



        for passenger in train.passengers:
            fastest_path  = MiniMattro.calculate_path(passenger, station, train)
            if MiniMattro.board(fastest_path, train, False) == False:
                train.disembark.append(passenger)




        for passenger in station.passengers:
            fastest_path  = MiniMattro.calculate_path(passenger, station, train)
            if MiniMattro.board(fastest_path, train, True):
                train.embark.append(passenger)
                passenger.is_boarding = True



    def passenger(self, dt):
        self.passenger_spawn += dt

        if self.passenger_spawn > 2:

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

    def add_train(self, r: int):
        rail: Rail = data.rails[r]
        if data.available_trains < 1 or len(rail.segments) < 1:
            return

        data.available_trains -= 1
        rail.trains.append(Train(random.choice(rail.segments)))
        pg.event.post(pg.event.Event(TRAINS_CHANGED))

    def upgrade_train(self, train: Train):
        if data.available_train_upgrades < 1 and not train.is_upgraded:
            return

        data.available_train_upgrades -= 1
        train.is_upgraded = True
        pg.event.post(pg.event.Event(TRAINS_CHANGED))

    def delete_train(self, train: Train):
        train.current_segment.rail.trains.remove(train)
        data.available_trains += 1
        if train.is_upgraded:
            data.available_train_upgrades += 1
        pg.event.post(pg.event.Event(TRAINS_CHANGED))

    def connect(self, s1: int, s2: int, r: int):
        rail = data.rails[r]
        if not rail.is_station_valid(s1) or rail.is_on_rail(s2):
            print("invalid connect action")
            return

        segment = TrackSegment(rail, data.stations[s1].location, (s1, None))
        segment.update_dst(data.stations, s2)
        rail.add_segment(segment, data.stations)

    def remove_station(self, s: int, r: int):
        if not data.active_rail.can_remove_station(s):
            print("invalid remove action")
            return

        data.rails[r].remove_station(s, data.stations)

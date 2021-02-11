import pygame as pg
import random
from pygame.constants import K_SPACE

from gui import setup_gui
from entities import TrackSegment, Station, Train, dijkstras
from util import *
import math


# ########### TMP ###############


def setup():
    data.stations = [Station(Shape.CIRCLE, Vector2(125, 100)),
                    #  Station(Shape.CIRCLE, Vector2(350, 150)),
                    #  Station(Shape.CIRCLE, Vector2(300, 350)),
                    #  Station(Shape.CIRCLE, Vector2(600, 650)),
                     Station(Shape.SQUARE, Vector2(400, 250)),
                    #  Station(Shape.SQUARE, Vector2(500, 500)),
                     Station(Shape.TRIANGLE, Vector2(100, 450)),
                     Station(Shape.TRIANGLE, Vector2(100, 250))]

    data.create_rail(gui)
    data.create_rail(gui)
    data.create_rail(gui)



    data.stations[0].create_passenger(Shape.TRIANGLE)

    print(data.stations[0].passengers[0].shape)

    # print(get_stattions_by_shape(Shape.TRIANGLE))

    for s in range(len(data.stations)):
        # s.draw(layers[-1])
        # print(s.location)
        g.add_vertex(str(s))
    
    
    # g.add_edge('a', 'b', 7)  
    # g.add_edge('b', 'f', 9)
    # g.add_edge('e', 'f', 14)
    # g.add_edge('e', 'z', 14)

    # g.add_edge('g', 'd', 11)
    
    print("")
    print("")
    

    
  
    # print ('( %s , %s, %3d)'  % ( vid, wid, v.get_weight(w)))



    print("")
    print("")
    # print(roots)

   
    # for 

    # print(paths)

    


    # for v in g:
    
    


  

    print(calculateDistance(125,350, 100, 150))


# ############## GAME ################


def update(dt):
    gui.update(dt)

    for event in pg.event.get():
        if gui.process_event(event):
            continue

        if event.type == pg.QUIT:
            exit(0)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            left_click_down(event)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            left_click_up(event)
        elif event.type == pg.MOUSEMOTION:
            mouse_move(event)
        elif event.type == SELECT_TRACK:
            data.set_active_rail(event.track)
        elif event.type == SCORE_POINT:
            data.score += 1
            gui.set_score(data.score)
        elif event.type == TRAIN_STOP:
            train_stop(event)

    for r in data.rails:
        r.update(dt, data)

    

    global passenger_spawn
    # passenger_spawn += dt
    # if passenger_spawn > 1:
    #     random.choice(data.stations).create_passenger(random.choice(list(Shape)))
    #     passenger_spawn = 0


def get_rails():
    rails = []

    for v in g:
        for w in v.get_connections():
            vid = v.get_id()
            wid = w.get_id()
            rails.append((vid,wid))

    paths = {}

    for rail in rails:
        paths[rail[0]] = []
        
    for rail in rails:
        l = paths[rail[0]]
        l.append(rail[1])
    
    return paths


def find_path(start, end, path=[]):

    paths = get_rails()

    path = path + [start]
    if start == end:
        return path
    if start not in paths:
        return None
    for node in paths[start]:
        if node not in path:
            newpath = find_path(node, end, path)
            if newpath: return newpath
    return None





def calculate_path(g, passenger, station):


    start = str(clip_to_station(station.location))
    # destination shape
    destination_shape = passenger.shape


    # list of destination shapes
    available_statges = get_stattions_by_shape(destination_shape)
    # print(available_statges, start)

    for stage in available_statges:
        to = str(stage)
        print("")
        print(start, to)
        
        print("Path found",find_path(start, to))
        if find_path(start, to) != None:
            dijkstras.dijkstra(g, g.get_vertex('0'))
            target = g.get_vertex(str('3'))
            path = [target.get_id()]
            print("this is paths",path)
            dijkstras.shortest(target, path)
            print ('The shortest path : %s' %(path[::-1]))
            


    return 2






def train_stop(event):
    
    g = dijkstras.Graph()
    
       
    for s in range(len(data.stations)):
        g.add_vertex(str(s))


    print(g.get_vertices())
    # for v in g:
    
        # print(v.get_connections())
    station: Station = data.stations[event.station]
    train: Train = event.train

    print(station)

    for passenger in train.passengers:
        # shortest_path = calculate_path(g, passenger, station)
        if passenger.should_disembark():
            train.disembark.append(passenger)
    
    for passenger in station.passengers:
        shortest_path = calculate_path(g, passenger, station)
        if passenger.should_embark():
            train.embark.append(passenger)


def left_click_down(event):
    s = clip_to_station(event.pos)
    if s != None and data.active_rail.is_station_valid(s):
        data.tmp_segment = TrackSegment(data.active_rail.color, data.stations[s].location, (s, None))


def left_click_up(event):
    if data.tmp_segment:
        # add the segment to the rail if mouse is released on a station which is not already part of the rail
        print(data.tmp_segment)
        s = clip_to_station(event.pos)
        if s != None and not data.active_rail.is_on_rail(s):
            data.tmp_segment.update_dst(data.stations, data.stations[s].location, s)
            print(clip_to_station(data.tmp_segment.origin), data.stations[s].location, s)
            data.active_rail.add_segment(data.tmp_segment, data.stations)

            x = data.tmp_segment.origin
            y = data.stations[s].location
            # str(clip_to_station(data.tmp_segment.origin)),str(s)
           
            g.add_edge(str(clip_to_station(data.tmp_segment.origin)),str(s), calculateDistance(x[0],y[0],x[1],y[1]))  
            print(str(clip_to_station(data.tmp_segment.origin)),str(s))
            
            g.add_edge("1", "2", calculateDistance(x[0],y[0],x[1],y[1]))  


            # for v in g:
            #     print(v.get_id())
            # print ('Graph data:')

            # start = "a"
            # to = "b"
            joint = False

            # for all pass on all stations
            for s in data.stations:
                for p in s.passengers:
                    # get current station
                    start = str(clip_to_station(s.location))
                    # destination shape
                    shape = p.shape
                    # list of destination shapes
                    available_statges = get_stattions_by_shape(Shape.TRIANGLE)
                    print("DETAILS")
                    print(available_statges, start)
                    for stage in available_statges:
                        to = str(stage)
                        print(to)
                        # for v in g:
                        #     for w in v.get_connections():
                        #         vid = v.get_id()
                        #         wid = w.get_id()
                        #         print ('( %s , %s, %3d)'  % ( vid, wid, v.get_weight(w)))
                        # if g.get_vertex(start)
                               

                                    # return

                    # print(joint)

                    # g.add_edge('0', '1', 7)  
                    # g.add_edge('1', '2', 9)


                    # if joint == True:
                    print(type(g.get_vertex(start)),g.get_vertex(str(available_statges[0])))
                        
                    
            
            data.tmp_segment = None

        for v in g:
            for w in v.get_connections():
                vid = v.get_id()
                wid = w.get_id()
                # if vid == start and wid == to:
                print ('( %s , %s, %3d)'  % ( vid, wid, v.get_weight(w)))
        # dijkstras.dijkstra(g, g.get_vertex(start))
        # target = g.get_vertex(str(available_statges[0]))
        # path = [target.get_id()]
        # dijkstras.shortest(target, path)
        # print ('The shortest path : %s' %(path[::-1]))


def mouse_move(event):
    if data.tmp_segment:
        s = clip_to_station(event.pos)
        if data.active_rail.is_on_rail(s):
            s = None

        location = event.pos if s == None else data.stations[s].location

        data.tmp_segment.update_dst(data.stations, location, s)


def clip_to_station(pt):
    # clip to station first
    for i, s in enumerate(data.stations):
        if s.contains(pt):
            return i

    return None

def get_stattions_by_shape(destination_shape: Shape):

    destination_stations: Station = []
    for i, s in enumerate(data.stations):
        if s.shape == destination_shape:
            destination_stations.append(clip_to_station(s.location))

    return destination_stations

def calculateDistance(x1,y1,x2,y2):
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return dist

def draw():
    # clear the screen
    surface.fill((100, 100, 100))
    for layer in layers:
        layer.fill((0, 0, 0, 0))

    for r in data.rails:
        r.draw(layers)

    if data.tmp_segment:
        data.tmp_segment.draw(layers[0])

    for s in data.stations:
        s.draw(layers[-1])
        # print(s.location)

    gui.draw(layers[-1])

    # show fps
    fps = font.render(str(int(clock.get_fps())), False, (255, 255, 255))
    surface.blit(fps, (surface.get_size()[0]-fps.get_size()[0], 0))

    # draw each layer
    for layer in layers:
        surface.blit(layer, (0, 0))
    pg.display.flip()


# ############ BOOTSTRAP ############
pg.init()
pg.font.init()

surface = pg.display.set_mode([1000, 900], pg.DOUBLEBUF)
layers = [pg.Surface([1000, 900], pg.SRCALPHA) for _ in range(3)]

pg.display.set_caption("MiniMattro")

clock = pg.time.Clock()
font = pg.font.SysFont('OpenSans-Regular', 24)
dt = 0

gui = setup_gui([1000, 900])


g = dijkstras.Graph()

setup()

passenger_spawn = 0

running = False
while not running:
    dt = clock.tick(60)
    # update
    update(dt/1000)

    # display
    draw()

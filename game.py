import pygame as pg
import random
from pygame.constants import K_SPACE

from gui import setup_gui
from entities import TrackSegment, Station, Train, dijkstras, graph, allpaths
from util import *
import math


# ########### TMP ###############


def setup():
    data.stations = [Station(Shape.CIRCLE, Vector2(125, 100)),
                    #  Station(Shape.CIRCLE, Vector2(350, 150)),
                     Station(Shape.CIRCLE, Vector2(300, 350)),
                    #  Station(Shape.CIRCLE, Vector2(600, 650)),
                     Station(Shape.SQUARE, Vector2(400, 250)),
                    #  Station(Shape.SQUARE, Vector2(500, 500)),
                     Station(Shape.TRIANGLE, Vector2(100, 450)),
                     Station(Shape.TRIANGLE, Vector2(100, 250))]

    data.create_rail(gui)
    data.create_rail(gui)
    data.create_rail(gui)



    # data.stations[0].create_passenger(Shape.TRIANGLE)
    # data.stations[1].create_passenger(Shape.SQUARE)


    # print(data.stations[0].passengers[0].shape)

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
    print("sssssssssssss")
    for r in data.rails:
        for s in r.segments:
            print(s.statoins)
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
            train_stop(event, data)

    for r in data.rails:
        # for s in r.segments:

            # print(s.stations)
        r.update(dt, data)


    global passenger_spawn
    # passenger_spawn += dt
    # if passenger_spawn > 1:
    #     random.choice(data.stations).create_passenger(random.choice(list(Shape)))
    #     passenger_spawn = 0

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


def calculate_path(g, passenger, station, train):
    print("Calculating Distance")
    start = str(clip_to_station(station.location))

    # print("Current Position: ", start)
    # destination_shape = passenger.shape
    destination_shape = Shape.SQUARE

    available_statges = get_stattions_by_shape(destination_shape)
    all_path_sums = []

    for stage in available_statges:
        to = str(stage)

        # if len(paths) > 0
        if find_path(start, to) != None:

            num_of_rails = 0
            for r in data.rails:
                if r.is_on_rail(start):
                    num_of_rails += 1

            # if num_of_rails > 1:

            railway_segments = []
            for count, rail in enumerate(data.rails):
                railway_segments.append([])
                for idx,s in enumerate(rail.segments):
                    railway_segments[count].append(s.stations[0])
                    if idx == len(rail.segments)-1:
                        railway_segments[count].append(s.stations[1])
                            
            
            paths = []
            connection.printAllPaths(int(start), int(to), paths)
            print(paths)
            for path in paths:

                # start_of_rail = path[:2]
                this_railway = -1
                for rail in railway_segments:
                    if " ".join(map(str,path)) in " ".join(map(str,rail)):
                        this_railway = railway_segments.index(rail)
                    
                print(" ".join(map(str,path)) ," ".join(map(str,rail)))
                print(data.rails[this_railway].color)
                train = data.rails[this_railway].trains[0]
                railway = railway_segments[this_railway]

                
                print("\n-----THIS IS CONNECTION PATH----")
                print("Railway color: ", data.rails[this_railway].color)
                print(path)

                path_sum = 0
                for p in range(len(path)-1):
                    path_sum += graphnew.weights[(str(path[p]),str(path[p+1]))]
        # for x in range(len(path[::-1])-1):
        #     # print(g.get_vertex(path[x]).get_weight(g.get_vertex(path[x+1])))
        #     # print(path[x], path[x+1])
        #     path_sum += g.get_vertex(path[x]).get_weight(g.get_vertex(path[x+1]))
            
                add_train_travel(path, path_sum, train, railway)
                all_path_sums.append((path, path_sum))
    
    print("    (Paths, Weights):   ", all_path_sums, "\n\n ")

    if len(all_path_sums) > 0:  
        shortest_path = sorted(all_path_sums, key=lambda tup: tup[1])[0][0]
    
        return shortest_path
    else:
        return []


def add_train_travel(path, path_sum, train, railway):
    # print("\nPOSITION",train.position)
    # print("Direction",train.direction)
    # print("Segment",(train.current_segment.stations))

    current_seg = list(train.current_segment.stations)
    path_seg = [int(i) for i in path][:2]
    path_direction = 0

    print(railway,path_seg)

    dep = path_seg[0]
    arr = path_seg[1]
    
    if train.direction == 1:
        next_station = (train.current_segment.stations)[1]
        print("----Next Station ----", next_station)
    else:
        next_station = (train.current_segment.stations)[0]
        print("----Next Station ----", next_station)


    if railway.index(dep) < railway.index(arr):
        path_direction = 1


        if (railway.index(next_station) > railway.index(dep)) and path_direction == train.direction:
            whole_route(train, railway, next_station, dep, path_sum)

        elif train.direction != path_direction:
            soon(train, railway, next_station, dep, path_sum)

        elif (railway.index(next_station) <= railway.index(dep)) and path_direction == train.direction:
            coming(train, railway, next_station, dep, path_sum)

    else:
        path_direction = -1
    



def whole_route(train, railway, next_station, dep, path_sum):

    direction = train.direction
    railway_sum = 0

    for s in range(len(railway)-1):
        railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]

    current_seg = train.current_segment.stations
    pos = train.position
    railway_sum += (graphnew.weights[(str(current_seg[0]),str(current_seg[1]))] * (1-pos))


    if direction == 1:
        # if len(railway[railway.index(next_station):]) > 1:
        # print("li jmiss", railway[railway.index(next_station):])
        # print((str(railway[railway.index(next_station)+0]),str(railway[railway.index(next_station)+1])))

        for s in range(len(railway[railway.index(next_station):])-1):
            railway_sum += graphnew.weights[(str(railway[railway.index(next_station)+s]),str(railway[railway.index(next_station)+s+1]))]
        # print("uPDATE 2: ", railway_sum)

        # else:
        #     seg = train.current_segment.stations
        #     pos = train.position
        #     railway_sum += (graphnew.weights[(str(seg[0]),str(seg[1]))] * (1-pos))
        #     # railway_sum += graphnew.weights[(railway[-2],railway[-1])]


        for s in range(len(railway[:railway.index(dep)])):
            railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]
    

    railway_sum += path_sum

    print("WHOLE ROUTEEEEEEEEEEEEEE:   ", railway_sum)


def soon(train, railway, next_station, dep, path_sum):
    print("\n---- Soon ----")

    direction = train.direction
    railway_sum = 0
    
    current_seg = train.current_segment.stations
    pos = train.position
    railway_sum += (graphnew.weights[(str(current_seg[0]),str(current_seg[1]))] * (pos))

    # print(railway[:railway.index(next_station)],len(railway[:railway.index(next_station)])-1)

    # NAHSEB TRID TAMEL len() -1 
    for s in range(len(railway[:railway.index(next_station)])):
        railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]

    for s in range(len(railway[:railway.index(dep)])):
        railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]

    railway_sum += path_sum
    
    print("WHOLE ROUTEEEEEEEEEEEEEE:   ", railway_sum)


    
def coming(train, railway, next_station, dep, path_sum):
    print("\n---- Comming ----")

    direction = train.direction
    railway_sum = 0

    current_seg = train.current_segment.stations
    pos = train.position
    railway_sum += (graphnew.weights[(str(current_seg[0]),str(current_seg[1]))] * (1-pos))

    for s in range(len(railway[railway.index(next_station):railway.index(dep)])):
        railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]

    railway_sum += path_sum


    print("WHOLE ROUTEEEEEEEEEEEEEE:   ", railway_sum)




def pass_emb(shortest_path, passenger, train, station):
 
    if len(shortest_path) == 0:
        return False

    seg = list(map(int, shortest_path))[:2]
    seg.sort()

    train_seg = list(train.current_segment.stations)
    train_seg.sort()

    print(seg, train_seg)


    current_station = str(clip_to_station(station.location))
    if seg == train_seg:
        # passenger.path = shortest_path
        return True
    else:
        return False


def drop(passenger, station, train):
    current_station = str(clip_to_station(station.location))

    print("Current station: ", current_station)

    # current_stop = passenger.path.index(str(clip_to_station(station.location)))
    # (passenger.path).pop(0)

    print("Journey: ", passenger.path)
    # print("This is segment: ",train.current_segment.stations)

    seg = list(map(int, passenger.path))[:2]
    seg.sort()

    train_seg = list(train.current_segment.stations)
    train_seg.sort()

    # print(seg, train_seg)

    if seg != train_seg:
        print("\n\nDropping passenger at station:", current_station)
        return True
    else:
        return False


def train_stop(event, data):
   
    station: Station = data.stations[event.station]
    train: Train = event.train


    trains = []

    
    temp_g = graphnew
    # if train == trains[1]:
    shortest_path = calculate_path(temp_g, data, data.stations[4], train)

    if False:
        for passenger in train.passengers:
            # shortest_path = calculate_path(g, passenger, station)
            # shortest_path = calculate_path(temp_g, passenger, station)
            # drop(temp_g, passenger, station, train)
            shortest_path = calculate_path(temp_g, passenger, station)

            # if drop( passenger, station, train):
            if pass_emb(shortest_path, passenger, train, station) == False:
                train.disembark.append(passenger)  
                
        
        for passenger in station.passengers:
            print("\nBOARDDING PASSENGER")
            if len(passenger.path)>0:
                shortest_path = passenger.path
            else:
                shortest_path = calculate_path(temp_g, passenger, station)
            if pass_emb(shortest_path, passenger, train, station):
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
           
            # g.add_edge(str(clip_to_station(data.tmp_segment.origin)),str(s), calculateDistance(x[0],y[0],x[1],y[1]))  
            # graphnew.add_edge(str(clip_to_station(data.tmp_segment.origin)),str(s), calculateDistance(x[0],y[0],x[1],y[1]))  
            
            graphnew.add_edge(str(clip_to_station(data.tmp_segment.origin)),str(s), (x).distance_to(y))  

            connection.addEdge(clip_to_station(data.tmp_segment.origin), s)
            connection.addEdge(s, clip_to_station(data.tmp_segment.origin))
         
            data.tmp_segment = None


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

graphnew = graph.Graph()
connection = allpaths.Graph(5)

setup()

passenger_spawn = 0

running = False
while not running:
    dt = clock.tick(60)
    # update
    update(dt/1000)

    # display
    draw()

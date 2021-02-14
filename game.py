import pygame as pg
import random
from pygame.constants import K_SPACE

from gui import setup_gui
from entities import TrackSegment, Station, Train, dijkstras, graph
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

    for v in g:
        for w in v.get_connections():
            vid = v.get_id()
            wid = w.get_id()
            rails.append((vid,wid))
    # rails.append((2,4))
    # rails.append((4,3))

    paths = {}

    for rail in rails:
        paths[rail[0]] = []
        
    for rail in rails:
        l = paths[rail[0]]
        l.append(rail[1])
    
    return paths

# print(get_rails())

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


def calculate_path(g, passenger, station, train, railway):
    print("Calculating Distance")
    start = str(clip_to_station(station.location))

    # print("Current Position: ", start)
    # destination_shape = passenger.shape
    destination_shape = Shape.SQUARE

    available_statges = get_stattions_by_shape(destination_shape)
    all_path_sums = []

    for stage in available_statges:
        to = str(stage)
        # print("")
        # print("Start: ",start,", End: ", to)
        
        # print("Path found",find_path(start, to))
        if find_path(start, to) != None:

            # dijkstras.dijkstra(g, g.get_vertex(str(start)))
            # target = g.get_vertex(str(to))
            # path = [target.get_id()]
            # # print("this is paths",path)
            # dijkstras.shortest(target, path)
            # print ('The shortest path : %s' %(path[::-1]))

            # print("Path:",graph.dijsktra(g, str(start), str(to)))

            path = graph.dijsktra(g, str(start), str(to))
            path_sum = 0

            for p in range(len(path)-1):
                path_sum += graphnew.weights[(path[p],path[p+1])]
            # for x in range(len(path[::-1])-1):
            #     # print(g.get_vertex(path[x]).get_weight(g.get_vertex(path[x+1])))
            #     # print(path[x], path[x+1])
            #     path_sum += g.get_vertex(path[x]).get_weight(g.get_vertex(path[x+1]))
            
            add_train_travel(path, path_sum, train, railway)
            all_path_sums.append((path, path_sum))
    
    print("\n (Paths, Weights):   ", all_path_sums, "\n\n ")

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

    # print("cur seg, path seg", current_seg , path_seg)
    # print("cur seg contains path seg", set(current_seg).issubset(path_seg))

    # print(railway.index(4))
    # print(railway.index(2))

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

        # elif railway.index(next_station) < railway.index(dep):
        elif train.direction != path_direction:
            soon(train, railway, next_station, dep, path_sum)


        elif (railway.index(next_station) <= railway.index(dep)) and path_direction == train.direction:
            coming(train, railway, next_station, dep, path_sum)


    else:
        path_direction = -1
    
    # print("Path Direction", path_direction)



def whole_route(train, railway, next_station, dep, path_sum):

    direction = train.direction
    railway_sum = 0

    for s in range(len(railway)-1):
        railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]
    # print("uPDATE 1: ", railway_sum)

    current_seg = train.current_segment.stations
    pos = train.position
    railway_sum += (graphnew.weights[(str(current_seg[0]),str(current_seg[1]))] * (1-pos))
    # print("uPdate1.1: ", railway_sum, "added, ", (graphnew.weights[(str(current_seg[0]),str(current_seg[1]))] * (1-pos)))


    if direction == 1:
        # if len(railway[railway.index(next_station):]) > 1:
        # print("li jmiss", railway[railway.index(next_station):])
        # print((str(railway[railway.index(next_station)+0]),str(railway[railway.index(next_station)+1])))

        for s in range(len(railway[railway.index(next_station):])-1):
            railway_sum += graphnew.weights[(str(railway[railway.index(next_station)+s]),str(railway[railway.index(next_station)+s+1]))]
        #     print("adding", graphnew.weights[(str(railway[s]),str(railway[s+1]))])
        # print("uPDATE 2: ", railway_sum)

        # else:
        #     seg = train.current_segment.stations
        #     pos = train.position
        #     railway_sum += (graphnew.weights[(str(seg[0]),str(seg[1]))] * (1-pos))
        #     print("this is testing", seg, next_station, railway_sum, "adding: ", graphnew.weights[(str(seg[0]),str(seg[1]))])

        #     # railway_sum += graphnew.weights[(railway[-2],railway[-1])]
        #     print("uPDATE 3: ", railway_sum)


        for s in range(len(railway[:railway.index(dep)])):
            railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]
            # print( "adding", graphnew.weights[(str(railway[s]),str(railway[s+1]))])
    
        # print("uPDATE 4: ", railway_sum)

    railway_sum += path_sum


    print("WHOLE ROUTEEEEEEEEEEEEEE:   ", railway_sum)


def soon(train, railway, next_station, dep, path_sum):
    print("\n---- Soon ----")

    direction = train.direction
    railway_sum = 0

    
    current_seg = train.current_segment.stations
    pos = train.position
    railway_sum += (graphnew.weights[(str(current_seg[0]),str(current_seg[1]))] * (1-pos))
    # print("uPdate1.1: ", railway_sum, "added, ", (graphnew.weights[(str(current_seg[0]),str(current_seg[1]))]))


    # print(railway[:railway.index(next_station)],len(railway[:railway.index(next_station)])-1)


    # NAHSEB TRID TAMEL len() -1 
    for s in range(len(railway[:railway.index(next_station)+1])):
        railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]
        # print("adding", graphnew.weights[(str(railway[s]),str(railway[s+1]))])
        # print("uPDATE 2: ", railway_sum)

    for s in range(len(railway[:railway.index(dep)])):
        railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]
        # print( "adding", graphnew.weights[(str(railway[s]),str(railway[s+1]))])

    # print("uPDATE 4: ", railway_sum)

    railway_sum += path_sum
    
    print("WHOLE ROUTEEEEEEEEEEEEEE:   ", railway_sum)


    
def coming(train, railway, next_station, dep, path_sum):
    print("\n---- Comming ----")

    direction = train.direction
    railway_sum = 0

    current_seg = train.current_segment.stations
    pos = train.position
    railway_sum += (graphnew.weights[(str(current_seg[0]),str(current_seg[1]))] * (1-pos))


    print(railway.index(next_station),railway.index(dep))
    for s in range(len(railway[railway.index(next_station):railway.index(dep)])):
        railway_sum += graphnew.weights[(str(railway[s]),str(railway[s+1]))]
        # print("adding", graphnew.weights[(str(railway[s]),str(railway[s+1]))])
        # print("uPDATE 2: ", railway_sum)


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
   

    # print(graphnew.weights[("3","4")])
    # print("xdd",graphnew.weights[("3","1")])
    # print(graphnew.weights[("2","0")])



    # print("THIS IS DISTANCE", (data.stations[0].location).distance_to(data.stations[1].location))
    
    # print(list2[list2.index('4')+1])
    # print("NANNUU",all(i in list2 for i in list1))
    railway_segments = []
    for count, r in enumerate(data.rails):
        railway_segments.append([])

        for idx,s in enumerate(r.segments):
            railway_segments[count].append(s.stations[0])
            if idx == len(r.segments)-1:
                railway_segments[count].append(s.stations[1])
            # print(s.stations)

    # print(railway_segments)
    

    # print(g.get_vertices())
    # for v in g:
        # print(v.get_distance())
    
        # print(v.get_connections())
    station: Station = data.stations[event.station]
    train: Train = event.train

    # print("\nPOSITION",train.position)
    # print("Direction",train.direction)
    # print("Segment",(train.current_segment.stations))

  

    # print(station.tracks)

    # for rail in data.rails:
    #     print("RAIL: " + str(rail.segments[0].origin))

    
    temp_g = graphnew

    shortest_path = calculate_path(temp_g, data, data.stations[4], train, railway_segments[0])

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
            # str(clip_to_station(data.tmp_segment.origin)),str(s)
           
            g.add_edge(str(clip_to_station(data.tmp_segment.origin)),str(s), calculateDistance(x[0],y[0],x[1],y[1]))  
            print(str(clip_to_station(data.tmp_segment.origin)),str(s))
            
            # graphnew.add_edge(str(clip_to_station(data.tmp_segment.origin)),str(s), calculateDistance(x[0],y[0],x[1],y[1]))  
            graphnew.add_edge(str(clip_to_station(data.tmp_segment.origin)),str(s), (x).distance_to(y))  

            # g.add_edge("1", "2", calculateDistance(x[0],y[0],x[1],y[1]))  


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

graphnew = graph.Graph()

setup()

passenger_spawn = 0

running = False
while not running:
    dt = clock.tick(60)
    # update
    update(dt/1000)

    # display
    draw()

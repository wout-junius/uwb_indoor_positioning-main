from os import O_TRUNC
import time
import cmath
import socket
import json

import argparse
from easy_trilateration.least_squares import *
from easy_trilateration.graph import *
import turtle
from random import randrange
from statistics import mean
from datetime import datetime
import copy

from flask import request

# Settings
offset = { #office
    "x" : -470,
    "y" : -362
}

max_distance_difference = 1     # Maximum Instant Movement Difference
max_uncertainity = 0.4       # Maximum Uncertainity Radius
min_distance_per_anchor = 0.1   # Minimum possible measured distance by an anchor
max_distance_per_anchor = 20    # Maximum possible measured distance by an anchor
metToPixel = 56 # Office

anchors = []
tags = []

class Node:
    def __init__(self, name, id, position):
        self.name = name
        self.id = id
        self.position = position
        self.turtle_center = None
        self.turtle_radius = None
        self.radius = 0
        self.node_color = "black"
        self.radius_color = "black"
        self.txt = "Node"
        self.txt_color = "black"

    # function to initialize turtle objects to be visualized (when verbose = True)
    def init_node_turtle(self):
        self.turtle_center = turtle.Turtle()
        self.turtle_radius = turtle.Turtle()
        turtle_init(self.turtle_center)
        turtle_init(self.turtle_radius)

    # function to draw the center of the node (when verbose = True)
    def draw_uwb_node(self):
        r = 20
        clean(self.turtle_center)
        fill_cycle(self.position["x"] * metToPixel + offset["x"], self.position["y"] * metToPixel + offset["y"], r , self.node_color, self.turtle_center)
        write_txt(self.position["x"] * metToPixel + offset["x"] + 10, self.position["y"] * metToPixel + offset["y"], self.txt, self.txt_color, self.turtle_center, f=('Arial', 8, 'bold'))

    # function to draw the radius of the node, meaning the range from the tag (when verbose = True)
    def draw_uwb_radius(self):
        clean(self.turtle_radius)
        draw_cycle(int(self.position["x"] * metToPixel + offset["x"]),int(self.position["y"]* metToPixel + offset["y"]),self.radius* metToPixel, self.radius_color, self.turtle_radius)
        # write_txt(self.position["x"] * metToPixel + offset["x"] + 10, self.position["y"] * metToPixel + offset["y"] - 30, "R="+str(round(self.radius,4)) + "m", "black", self.turtle_radius, f=('Arial', 8, 'bold'))

class Anchor(Node):
    def __init__(self, name, id, position, calibration):
        super().__init__(name, id, position)
        self.calibration = calibration # for extra calibration if needed
        self.node_color = "red"
        self.radius_color = "darkred"
        self.txt = self.name + "<" + self.id + ">"
        self.txt_color = "darkred"

    # function to set the range with calibration function
    def set_range(self, uwb_range):
        self.radius = uwb_range - self.calibration

class Tag(Node):
    def __init__(self, name, id, position):
        super().__init__(name, id, position)
        self.node_color = "limegreen"
        self.radius_color = "yellow"
        self.txt = "TAG-" + self.name
        self.txt_color = "white"
        self.all_anchors = []
        self.detected_anchors = []
        self.used_anchors_index = []
        self.used_anchors_id = []
        self.anchor_data_list = []
        # self.safe_measurement = True
        # self.prev_x = 0
        # self.prev_y = 0
        # self.roll_x = []
        # self.roll_y = []
        # self.roll_window = 2
        # self.avg_x = 0
        # self.avg_y = 0

    # function to set tag's position and uncertainity
    def set_position(self, x, y, uncertainity):
        self.position["x"] = x
        self.position["y"] = y
        self.radius = uncertainity

    # function to link all defined anchors to a tag
    def set_all_anchors(self, anchors):
        self.all_anchors = anchors

# Turtle Functions
def screen_init(width=1200, height=800, t=turtle):
    print("screen_init")
    t.setup(width, height)
    t.bgpic("AltheriaOffice.png")
    # t.bgpic("CalvarinaMapUWB.png")
    t.tracer(False)
    t.hideturtle()
    t.speed(0)

def turtle_init(t=turtle):
    t.hideturtle()
    t.speed(0)

def draw_line(x0, y0, x1, y1, color="black", t=turtle):
    t.pencolor(color)
    t.up()
    t.goto(x0, y0)
    t.down()
    t.goto(x1, y1)
    t.up()

def draw_fastU(x, y, length, color="black", t=turtle):
    draw_line(x, y, x, y + length, color, t)

def draw_fastV(x, y, length, color="black", t=turtle):
    draw_line(x, y, x + length, y, color, t)

def draw_cycle(x, y, r, color="black", t=turtle):
    t.pencolor(color)
    t.width(3)
    t.up()
    t.goto(x, y - r)
    t.setheading(0)
    t.down()
    t.circle(r)
    t.up()

def fill_cycle(x, y, r, color="black", t=turtle):
    t.up()
    t.goto(x, y)
    t.down()
    t.dot(r, color)
    t.up()

def write_txt(x, y, txt, color="black", t=turtle, f=('Arial', 12, 'normal')):
    t.pencolor(color)
    t.up()
    t.goto(x, y)
    t.down()
    t.write(txt, move=False, align='left', font=f)
    t.up()

def draw_rect(x, y, w, h, color="black", t=turtle):
    t.pencolor(color)
    t.up()
    t.goto(x, y)
    t.down()
    t.goto(x + w, y)
    t.goto(x + w, y + h)
    t.goto(x, y + h)
    t.goto(x, y)
    t.up()

def fill_rect(x, y, w, h, color=("black", "black"), t=turtle):
    t.begin_fill()
    draw_rect(x, y, w, h, color, t)
    t.end_fill()
    pass

def clean(t=turtle):
    t.clear()

# Reading Range Link UWB
def read_data(d):
    global tag_number
    # global detected_anchors
    line = d.recv(1024).decode('UTF-8')
    detected_anchors = []
    try:
        uwb_data = json.loads(line)
        # print(uwb_data)
        detected_anchors = uwb_data["links"]
        tag_number = uwb_data["tag_n"]
        print(">>>>> TAG NUMBER: ",tag_number)
        print("Anchor ID and Range:")
        for uwb_archor in detected_anchors:
            print("\t",uwb_archor)
    except:
        print(line)
    print("")
    tags[tag_number-1].detected_anchors = detected_anchors
    # return detected_anchors

# Main UWB Logic + Turtle
def start_uwb(verbose, sio):
    print("---UWB-->Starting UWB System...")
    # Define Anchors and Tags
    anchors.append(Anchor(name="A1:LB",id="57",position={"x":0.33, "y":0},calibration=0))
    anchors.append(Anchor(name="A2:RB",id="AE",position={"x":16.73,"y":0},calibration=0))
    anchors.append(Anchor(name="A3:RU",id="5", position={"x":17.12,"y":7.18},calibration=0))
    anchors.append(Anchor(name="A4:LU",id="5C",position={"x":0.77, "y":12.97},calibration=0))
    anchors.append(Anchor(name="A5:X1",id="B3",position={"x":0.33, "y":5.76},calibration=0))
    anchors.append(Anchor(name="A6:X2",id="A", position={"x":12,   "y":7.18},calibration=0))
    tags.append(Tag(name="P1",id="1",position={"x":0,"y":0}))
    tags.append(Tag(name="P2",id="2",position={"x":0,"y":0}))

    tags[0].set_all_anchors(anchors)
    tags[1].set_all_anchors(copy.deepcopy(anchors))

    # tags[0].all_anchors[0].radius = 10
    # print(tags[0].all_anchors[0].radius)
    # tags[1].all_anchors[0].radius = 20
    # print(tags[1].all_anchors[0].radius)
    # anchors[0].radius = 30
    # print(anchors[0].radius)

    # print(tags[0].all_anchors[0].radius)
    # print(tags[1].all_anchors[0].radius)
    # print(anchors[0].radius)
    
    # Initializing Turtle Objects
    if verbose:
        screen_init()
        t_info = turtle.Turtle()
        turtle_init(t_info)
        draw_anchors_once = True
        for i in range(len(tags)):
            tags[i].init_node_turtle()
            for j in range(len(anchors)):
                tags[i].all_anchors[j].init_node_turtle()
                if draw_anchors_once: tags[i].all_anchors[j].draw_uwb_node()
            draw_anchors_once = False
        
    # Define Communication with TAG via UDP
    # UDP_IP = "192.168.1.40"
    UDP_IP = "0.0.0.0"
    print("***Local ip:" + str(UDP_IP) + "***")
    UDP_PORT_1 = 80
    
    while True:
        # print("UWB While TRUE")
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # To correctly close socket if not closed properly
        # sock.bind((UDP_IP, UDP_PORT_1))
        # sock.listen(1)
        # data, addr = sock.accept()
        # print("------------------------------ UWB LOCALIZATION ------------------------------")        
        # read_data(data)
        # sock.close()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(15)
        try:
            sock.bind((UDP_IP, UDP_PORT_1))
            sock.listen(1)
            data, addr = sock.accept()
            print("------------------------------ UWB LOCALIZATION ------------------------------")        
            read_data(data)
            sock.close()
            sio.emit(event ='tags_update',data= "True")
            print("✓ ✓ ✓ TAGS STATUS: CONNECTED AND COMMUNICATING ✓ ✓ ✓")
        
        
        
        
        
        except socket.timeout as e:
            sio.emit(event ='tags_update',data= "False")
            print("⚠ ⚠ ⚠ TAGS STATUS: TIMEOUT! NOT CONNECTED / NOT COMMUNICATING ⚠ ⚠ ⚠")
            print("🛈 Please check the TAGS have enough battery and wireless connectivity")
        
        sio.emit(event ='position_calibration',data= {
                            'player': 1,
                            'timestamp':123,
                            'x': 1, 
                            'y': 2, 
                            'uncertainity': 3,
                            'anchors_used':4})
        
        #TODO: Database query for tag number
        print("---UWB-->Emission?...")
        time.sleep(5)

        # sio.emit(event ='position_calibration',data= {
        #             'player': 1,
        #             'timestamp':123,
        #             'x': 1, 
        #             'y': 2, 
        #             'uncertainity': 3,
        #             'anchors_used':4})
        # print("---UWB-->Emission?...")
        # time.sleep(0.1)

        # tags[tag_number-1].safe_measurement = True
        # tags[tag_number-1].used_anchors_index = []
        # tags[tag_number-1].used_anchors_id = []
        # tags[tag_number-1].anchor_data_list = []
        # # print("Detected Anchors: ", len(anchor_list))
        # for anchor in tags[tag_number-1].detected_anchors:
        #     for i in range(len(anchors)):
        #         if anchor["A"] == anchors[i].id:
        #             tags[tag_number-1].all_anchors[i].set_range(float(anchor["R"])) # in meters!
        #             # if verbose: 
        #             #     clean(tags[tag_number-1].all_anchors[i].turtle_radius)
        #             if (tags[tag_number-1].all_anchors[i].radius < max_distance_per_anchor) and (tags[tag_number-1].all_anchors[i].radius > min_distance_per_anchor) and (tags[tag_number-1].all_anchors[i].radius > 0): # Conditions to accept the range
        #                 tags[tag_number-1].used_anchors_index.append(i)
        #                 tags[tag_number-1].used_anchors_id.append(tags[tag_number-1].all_anchors[i].id)
        #                 if verbose: 
        #                     clean(tags[tag_number-1].all_anchors[i].turtle_radius)
        #                     tags[tag_number-1].all_anchors[i].draw_uwb_radius()
        
        # print("Used Anchors: {}, list: {}".format(len(tags[tag_number-1].used_anchors_id),tags[tag_number-1].used_anchors_id))
        
        # if verbose:
        #     clean(t_info)
        #     # if tag_number == 1: metadata.player1["a"] = len(tags[tag_number-1].used_anchors_index)
        #     # elif tag_number == 2: metadata.player2["a"] = len(tags[tag_number-1].used_anchors_index)
        #     write_txt(-50,350,"TAG-P{} < Detected Anchors: {} > < Used Anchors: {} >".format(tag_number,len(tags[tag_number-1].detected_anchors),len(tags[tag_number-1].used_anchors_index)),"black",t_info,f=('Arial', 8, 'bold'))
        
        # if len(tags[tag_number-1].used_anchors_index) >= 3: # at least 3 anchors to calculate position
        #     # create anchor data list
        #     for detected_anchor in tags[tag_number-1].used_anchors_index:
        #         tags[tag_number-1].anchor_data_list.append(Circle(tags[tag_number-1].all_anchors[detected_anchor].position["x"], tags[tag_number-1].all_anchors[detected_anchor].position["y"], tags[tag_number-1].all_anchors[detected_anchor].radius))
        #     result, meta = easy_least_squares(tags[tag_number-1].anchor_data_list) #calculation in meters!
        #     print(result)
        #     tags[tag_number-1].set_position(result.center.x, result.center.y, result.radius)
        #     print("TAG Position: <X:{}> <Y:{}> <Uncertainity:{}m>\n".format(round(result.center.x,2), round(result.center.y,2), round(result.radius,2)))
            
            
            #NOOOOOOOOOOOOOOOOOPE
            # print("Position: ", tags[tag_number-1].position)
            # print("Uncertainity: ", tags[tag_number-1].radius)
            
            # if (abs(tags[tag_number-1].prev_x - result.center.x) > max_distance_difference) or(abs(tags[tag_number-1].prev_y - result.center.y) > max_distance_difference):
            #     tags[tag_number-1].safe_measurement = False
            #     tags[tag_number-1].prev_x = result.center.x
            #     tags[tag_number-1].prev_y = result.center.y

            # if abs(result.radius) < max_uncertainity and tags[tag_number-1].safe_measurement:
            #     tags[tag_number-1].roll_x.append(result.center.x)
            #     tags[tag_number-1].roll_y.append(result.center.y)
            #     if len(tags[tag_number-1].roll_x) > tags[tag_number-1].roll_window:
            #         tags[tag_number-1].roll_x.pop(0)
            #         tags[tag_number-1].roll_y.pop(0)
            #         tags[tag_number-1].avg_x = mean(tags[tag_number-1].roll_x)
            #         tags[tag_number-1].avg_y = mean(tags[tag_number-1].roll_y)
            #         tags[tag_number-1].set_position(tags[tag_number-1].avg_x, tags[tag_number-1].avg_y, result.radius)
            #     else:
            #         tags[tag_number-1].avg_x = result.center.x
            #         tags[tag_number-1].avg_y = result.center.y
            # else:
            #     print("Measurements not reliable at the moment!")
            #     if verbose: write_txt(0,320,"Measurements not reliable at the moment!","red",t_info,f=('Arial', 8, 'bold'))
            
            # Writing to global variables
            # metadata.player1["x"] = avg_x
            # metadata.player1["y"] = avg_y
            
            # if verbose:
            #     tags[tag_number-1].draw_uwb_node()
            #     tags[tag_number-1].draw_uwb_radius()

            # YEEEEEEEEEEEEES
            # if verbose:
            #     tags[tag_number-1].draw_uwb_radius()
            #     tags[tag_number-1].draw_uwb_node()
            # # Getting the current date and time
            # dt = datetime.now()
            # # getting the timestamp
            # ts = datetime.timestamp(dt)
            # print("Date and time is:", dt)
            # print("Timestamp is:", ts)
            # # Web socket to headset
            # sio.emit(event ='position_calibration',data= {
            #     'timestamp':ts,
            #     'tag_number':tag_number,
            #     'x': tags[tag_number-1].position["x"], 
            #     'y': tags[tag_number-1].position["y"], 
            #     'uncertainity': tags[tag_number-1].radius, 
            #     'anchors_used':len(tags[tag_number-1].used_anchors_index)})
            
            #NOOOOOOOOOPE
            # sio.emit(event ='position_calibration',data= {
            #                 'player': 1,
            #                 'timestamp':123,
            #                 'x': 1, 
            #                 'y': 2, 
            #                 'uncertainity': 3,
            #                 'anchors_used':4})
            # print("---UWB-->Emission?...")

            # if abs(result.radius) < max_uncertainity:
            #     if verbose:
            #         tags[tag_number-1].draw_uwb_radius()
            #         tags[tag_number-1].draw_uwb_node()
            #     # Getting the current date and time
            #     dt = datetime.now()
            #     # getting the timestamp
            #     ts = datetime.timestamp(dt)
            #     print("Date and time is:", dt)
            #     print("Timestamp is:", ts)
            #     # Web socket to headset
            #     sio.emit(event ='test',data= {
            #         'timestamp':ts,
            #         'tag_number':tag_number,
            #         'x': tags[tag_number-1].position["x"], 
            #         'y': tags[tag_number-1].position["y"], 
            #         'uncertainity': tags[tag_number-1].radius, 
            #         'anchors_used':len(tags[tag_number-1].used_anchors_index)})

            # else:
            #     print("Uncertainity is too high (bigger than {}m). Therefore, position is not updated yet".format(max_uncertainity))
        # else:
        #     print("TAG Position: Not enough anchors detected!")
        time.sleep(0.1)
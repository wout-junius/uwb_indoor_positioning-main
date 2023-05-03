# LIBRARIES AND IMPORTS REQUIRED
from gevent import monkey
monkey.patch_all()
from flask import Flask, request, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO
# from flask_script import Manager, Server
import uwb_logic_multiplayer
import pdfreport
import os
from dotenv import load_dotenv
from threading import Thread
from pygame import mixer
from datetime import timedelta
import time
import json
# from engineio.async_drivers import gevent

# SERVER INITIALIZATION
def reset_headset():
    all_headsets = Headset.query.all()
    for headset in all_headsets:
        headset.headset_status = False
        headset.socket_id = ""
        headset.player_name = ""
        headset.player_number = 0
    db.session.commit()
    print('MyFlaskApp is starting up!')

class MyFlaskApp(Flask):
  def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
    if not self.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
      with self.app_context():
        reset_headset()
    super(MyFlaskApp, self).run(host=host, port=port, debug=debug, load_dotenv=load_dotenv, **options)

# SERVER CONFIGURATION
# app = Flask(__name__)
app = MyFlaskApp(__name__)

app.config['SECRET_KEY'] = 'secret!'
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///headsets.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.permanent_session_lifetime = timedelta(minutes = 5)
# init sqlalchemy
db = SQLAlchemy(app)
# init marshmallow
ma = Marshmallow(app)
# ,ping_interval = 10, ping_timeout=5
socketio = SocketIO(app,async_mode='threading', cors_allowed_origins="*",ping_interval = 5, ping_timeout=6)

# THREADS:
uwb_thread = None
pdf_thread = None

# DATABASE TABLE
class Headset(db.Model):
    # Primary Key
    id = db.Column("id",db.Integer,primary_key = True)
    # Player Attrubutes
    headset_id = db.Column(db.String(100), nullable = False) # nullable refers that it has to exist!
    socket_id = db.Column(db.String(100), nullable = False)
    headset_name = db.Column(db.String(100), nullable = False)
    player_name = db.Column(db.String(100), nullable = False)
    player_number = db.Column(db.Integer, nullable = False)
    headset_status = db.Column(db.Boolean, nullable = False)

    def __init__(self, headset_id, socket_id):
        self.headset_id = headset_id
        self.socket_id = socket_id
        self.headset_name = ""
        self.player_name = ""
        self.player_number = 0
        self.headset_status = True

    def __repr__(self):
        return f"~~~~|Database Object: Headset:\n\t└>Headset ID: '{self.headset_id}'\n\t\t└>Headset Name: '{self.headset_name}'\n\t\t└>Headset Status: '{self.headset_status}'\n\t\t└>Socket ID: '{self.socket_id}'\n\t\t└>Player Name: '{self.player_name}'\n\t\t└>Player Number: '{self.player_number}'"

# DATABASE SCHEMA
class HeadsetSchema(ma.Schema):
    class Meta:
        fields = ('headset_id', 'socket_id', 'headset_name', 'player_name', 'player_number', 'headset_status')
# Init Schema:
headset_schema = HeadsetSchema()
headsets_schema = HeadsetSchema(many = True)

# GAME CLASS: Includes player names, IoT Status and Scores
class Game():
    def __init__(self):
        # Game Variables
        self.paired_headsets = 0
        self.stage = 0
        self.player_one = Player()
        self.player_two = Player()
        self.lift_open = False
        self.lift_up = False
        self.lift_down = False
        # Tasks and Scores
        self.task_individual = ['Take flashlight',
                                'Use flashlight',
                                'Take right suit',
                                'Take right filter',
                                'Take the camera',
                                'Take sampling kit', 
                                'Take the chem detector',
                                'Take decon. kit',
                                'Take the gun',
                                'Irradiation']
        self.task_team = ['Samples taken',
                        'Pictures taken',
                        'Use lift']
                        # 'Inspect body']
        # Score
        self.team_score = TeamScore()
        self.total_score = 0
        # Settings
        self.permissiveness = False
        self.is_multiplayer = False
        self.tracking = False
        self.settings_are_set = False
        self.start = False
        self.inventories_ready = False
        self.reset_tags = False

    def set_settings(self, permissiveness, is_multiplayer, tracking):
        self.permissiveness = permissiveness
        self.is_multiplayer = is_multiplayer
        self.tracking = tracking
        self.settings_are_set = True

    def calculate_total_score(self):
        self.total_score = self.player_one.individual_score.score + self.player_two.individual_score.score + self.team_score.score


class Player():
    def __init__(self):
        # Name
        self.name = "Player_name"
        # Items
        self.light_status = False
        self.tag_heartbeat = False
        # Position and Rotation (Body and Controllers)
        self.position = []
        self.rotation = []
        self.left_controller_pos = []
        self.left_controller_rot = []
        self.right_controller_pos = []
        self.right_controller_rot = []
        self.left_controller_fingers = []
        self.right_controller_fingers = []

        # Score
        self.individual_score = IndividualScore()
        # States
        self.inventory_selected = False
        self.finalized = False
        # Time
        # self.time_start = 0
        # self.time_end = 0
        # self.elapsed_time = 0

    def __repr__(self):
        return f"~~~~>Player Object:\n\t└>Name: '{self.name}'\n\t\t└>Score: {self.individual_score.take_flashlight},{self.individual_score.use_flashlight},{self.individual_score.take_right_suit},{self.individual_score.take_right_filter},{self.individual_score.take_camera},{self.individual_score.take_sampling_kit},{self.individual_score.take_chem_detector},{self.individual_score.take_gun}"

# INDIVIDUAL SCORE CLASS: Includes all individual tasks
class IndividualScore():
    def __init__(self):
        self.take_flashlight = False
        self.use_flashlight = False
        self.take_suit = ""
        self.take_right_suit = False
        self.take_filter = ""
        self.take_right_filter = False
        self.take_camera = False
        self.take_sampling_kit = False
        self.take_chem_detector = False
        self.take_decon_kit = False
        self.take_gun = False
        self.irradiation = 0
        self.score = 0

        self.correct_suit = "Suite3"
        self.correct_filter = "Multipurposefilter"
        self.irradiation_message = "Low"
    
    def calculate_individual_score(self):
        if self.take_suit == self.correct_suit : self.take_right_suit = True
        if self.take_filter == self.correct_filter : self.take_right_filter = True

        self.score = self.take_flashlight*5+ self.use_flashlight*5 + self.take_right_suit * 15 + self.take_right_filter * 15 + self.take_camera*5 + self.take_sampling_kit*10 + self.take_chem_detector*10 + self.take_gun*5 + self.take_decon_kit*10
        if self.irradiation != 0: self.irradiation = round(float(self.irradiation.replace(",",".")),2)
        if self.irradiation < 10: self.irradiation_message = "Low" # LOW RADIATION DOSE
        elif self.irradiation >= 10 and self.irradiation < 20: self.irradiation_message = "Medium" # MEDIUMN RADIATION DOSE
        elif self.irradiation >= 20 and self.irradiation < 50: self.irradiation_message = "High" # HIGH RADIATION DOSE
        elif self.irradiation >= 50: self.irradiation_message = "Letal" # LETAL RADIATION DOSE

class TeamScore():
    def __init__(self):
        self.take_samples = {"room4":False, "room6":False, "room7":False, "room8":False}
        self.take_pictures = {"room2":False, "room4":False, "room6":False, "room7":False, "room8":False, "room9":False, "room10":False}
        self.use_lift = False
        # self.inspect_body = False0
        self.score = 0

        self.total_samples = 4
        self.total_pictures = 7

    def calculate_team_score(self):
        self.score = sum(self.take_samples.values())*5 + sum(self.take_pictures.values())*5 + self.use_lift*10 # + self.inspect_body*20

# CREATING GAME INSTANCE:
g = Game()

# --------------------------------- ROUTES / ENDPOINTS ---------------------------------

# FUNCTION TO EMIT UPDATE OF A PARTICULAR ACHIEVEMENT
def emit_achievement_update():
    socketio.emit(event ='achievement_update',
                  data= {"player_one" :
                        {
                            "take_flashlight" : g.player_one.individual_score.take_flashlight,
                            "use_flashlight" : g.player_one.individual_score.use_flashlight,
                            "take_right_suit" : g.player_one.individual_score.take_right_suit,
                            "take_right_filter" : g.player_one.individual_score.take_right_filter,
                            "take_camera" : g.player_one.individual_score.take_camera,
                            "take_sampling_kit" : g.player_one.individual_score.take_sampling_kit,
                            "take_chem_detector" : g.player_one.individual_score.take_chem_detector,
                            "take_gun" : g.player_one.individual_score.take_gun,
                            "irradiation" : g.player_one.individual_score.irradiation
                        },
                        "player_two" :
                        {
                            "take_flashlight" : g.player_two.individual_score.take_flashlight,
                            "use_flashlight" : g.player_two.individual_score.use_flashlight,
                            "take_right_suit" : g.player_two.individual_score.take_right_suit,
                            "take_right_filter" : g.player_two.individual_score.take_right_filter,
                            "take_camera" : g.player_two.individual_score.take_camera,
                            "take_sampling_kit" : g.player_two.individual_score.take_sampling_kit,
                            "take_chem_detector" : g.player_two.individual_score.take_chem_detector,
                            "take_gun" : g.player_two.individual_score.take_gun,
                            "irradiation" : g.player_two.individual_score.irradiation
                        },
                        "team" : 
                        {
                            "take_samples" : g.team_score.take_samples,
                            "take_pictures" : g.team_score.take_pictures,
                            "use_lift" : g.team_score.use_lift
                            # "inspect_body" : g.team_score.inspect_body
                        }
                    })

# FUNCTION TO EMIT UPDATE OF A PARTICULAR HEADSET
def emit_headset_update(headset):
    socketio.emit("headset_update", {'headset_id': headset.headset_id, 'headset_status': headset.headset_status, 'player_name':headset.player_name, 'headset_name': headset.headset_name, 'player_number': headset.player_number})

# FRONT-END STEP/STAGE
@app.route('/stage')
def stage():
    response = jsonify({"stage": g.stage, "permissiveness" : g.permissiveness, "is_multiplayer" : g.is_multiplayer, "tracking" : g.tracking})
    # response.headers.add('Access-Control-Allow-Origin', os.getenv("WEB_DOMAIN"))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# # TEST
# @app.route('/sett')
# def sett():
#     g.set_settings(True,True,True)
#     return "MULTIPLAYER PARAMETER PASSED"

@app.route('/tag_1_disconnected')
def tag_1_disconnected():
    print("🕱 🕱 🕱 TAG 1 Disconnected")
    g.player_one.tag_heartbeat = False
    socketio.emit("tag_update", {"tag_n" : 1, "status" : False})
    return "🕱 🕱 🕱 TAG 1 Disconnected"

@app.route('/tag_2_disconnected')
def tag_2_disconnected():
    print("🕱 🕱 🕱 TAG 2 Disconnected")
    g.player_two.tag_heartbeat = False
    socketio.emit("tag_update", {"tag_n" : 2, "status" : False})
    return "🕱 🕱 🕱 TAG 2 Disconnected"

@app.route('/clean_database')
def clean_database():
    Headset.query.delete()
    db.session.commit()
    print("Database Erased!")
    return "Database Erased!"

@app.route('/tag_settings/<id>')
def tag_settings(id):
    if id == "1": 
        g.player_one.tag_heartbeat = True
        socketio.emit("tag_update", {"tag_n" : 1, "status" : True})
    if id == "2": 
        g.player_two.tag_heartbeat = True
        socketio.emit("tag_update", {"tag_n" : 2, "status" : True})
    print(f"♥ ♥ ♥ TAG {id}: Heartbeat received and TAG settings were sent ----> TAG STATUS: <TAG 1:{g.player_one.tag_heartbeat}> <TAG 2:{g.player_two.tag_heartbeat}>")
    detected_tags = g.player_one.tag_heartbeat + g.player_two.tag_heartbeat
    # print("g.settings_are_set", g.settings_are_set)
    if not g.settings_are_set: return f"0{detected_tags}"
    return f"{int(g.is_multiplayer)+1}{detected_tags}"

# RETRIEVE HEADSETS DATABASE
@app.route('/headsets')
def headsets():
    all_headsets = Headset.query.all()
    result = headsets_schema.dump(all_headsets)
    response = jsonify(result)
    # response.headers.add('Access-Control-Allow-Origin', os.getenv("WEB_DOMAIN"))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# FLASHLIGHT
@app.route('/p1_light')
def p1_light():
    if g.player_one.light_status: g.player_one.light_status = False
    else: g.player_one.light_status = True
    socketio.emit("light_button_pressed", {"p1_light" : g.player_one.light_status, "p2_light" : g.player_two.light_status})
    if g.start:
        g.player_one.individual_score.use_flashlight = True    # ✓ CHECK SCORE FOR FLASHLIGHT USE
        emit_achievement_update()
    # Via WiFi to VR Headset (Unity) -> change light from player 1
    return "<h1>Light state from player one changed!</h1>"

@app.route('/p2_light')
def p2_light():
    if g.player_two.light_status: g.player_two.light_status = False
    else: g.player_two.light_status = True
    socketio.emit("light_button_pressed", {"p1_light" : g.player_one.light_status, "p2_light" : g.player_two.light_status})
    if g.start:
        g.player_two.individual_score.use_flashlight = True    # ✓ CHECK SCORE FOR FLASHLIGHT USE
        emit_achievement_update()
    # Via WiFi to VR Headset (Unity) -> change light from player 2
    return "<h1>Light state from player two changed!</h1>"

@socketio.on('light')
def light(player):
    print("Light Used! ",player)
    if player["player_number"] == "1":
        if g.player_one.light_status: g.player_one.light_status = False
        else: g.player_one.light_status = True
        socketio.emit("light_button_pressed", {"p1_light" : g.player_one.light_status, "p2_light" : g.player_two.light_status})
        if g.start: 
            g.player_one.individual_score.use_flashlight = True
            print("Achievement Unlocked: Flashlight Used!",player)
            emit_achievement_update()
    if player["player_number"] == "2":
        if g.player_two.light_status: g.player_two.light_status = False
        else: g.player_two.light_status = True
        socketio.emit("light_button_pressed", {"p1_light" : g.player_one.light_status, "p2_light" : g.player_two.light_status})
        if g.start: 
            g.player_two.individual_score.use_flashlight = True
            print("Achievement Unlocked: Flashlight Used!",player)
            emit_achievement_update()

# LIFT (+SPEAKER)
start = time.time()
wait_time = 0
mixer.init()
@app.route('/lift_button_open') # TRACKING
def lift_button_open():
    if g.start:
        g.team_score.use_lift = True    # ✓ CHECK SCORE FOR LIFT USE
        emit_achievement_update()
        socketio.emit("update_team_score", {"achievement_name" : "use_lift", "value" : True})
        global start
        global wait_time
        now = time.time()
        if now - start > wait_time:
            g.lift_open = True
            socketio.emit("lift_button_pressed", "open") # FRONTEND
            socketio.emit("lift_button_pressed_hs", "open") # HEADSET
            # Via Bluetooth to SPEAKER -> play open door sound
            mixer.music.load('./sounds/lift_open.mp3')
            mixer.music.play()
            start = time.time()
            wait_time = 5
    else:
        socketio.emit("lift_button_pressed", "open")
        mixer.music.load('./sounds/lift_open.mp3')
        mixer.music.play()
    return "<h1>Lift button OPEN state received by the server!</h1>"

@socketio.on('lift_button_open') # NO TRACKING
def lift_button_open_event(player):
    print("Lift Button Open Pressed!",player)
    if player["player_number"] == "1":
        player_two = Headset.query.filter_by(player_number = 2).first()
        if player_two: 
            socketio.emit(event = "lift_button_pressed_hs", data = "open", room = player_two.socket_id)
            socketio.emit("lift_button_pressed", "down")
    if player["player_number"] == "2":
        player_one = Headset.query.filter_by(player_number = 1).first()
        if player_one: 
            socketio.emit(event = "lift_button_pressed_hs", data = "open" ,room = player_one.socket_id)
            socketio.emit("lift_button_pressed", "down")
    if g.start:
        g.team_score.use_lift = True
        socketio.emit("lift_button_pressed", "down")
        print("Achievement Unlocked: Lift Used!")
        emit_achievement_update()

@app.route('/lift_button_up') # TRACKING
def lift_button_up():
    if g.start:
        g.team_score.use_lift = True    # ✓ CHECK SCORE FOR LIFT USE
        emit_achievement_update()
        global start
        global wait_time
        now = time.time()
        if now - start > wait_time:
            g.lift_up = True
            socketio.emit("lift_button_pressed", "up") # FRONTEND
            socketio.emit("lift_button_pressed_hs", "up") # HEADSET
            # Via Bluetooth to SPEAKER -> play lift moving sound
            sound_eff = mixer.Sound("./sounds/lift_up_down.wav")
            sound_eff.play()
            start = time.time()
            wait_time = 20
    else:
        socketio.emit("lift_button_pressed", "up")
        sound_eff = mixer.Sound("./sounds/lift_up_down.wav")
        sound_eff.play()
    return "<h1>Lift button UP state received by the server!</h1>"

@app.route('/lift_button_down')
def lift_button_down():
    if g.start:
        g.team_score.use_lift = True    # ✓ CHECK SCORE FOR LIFT USE
        emit_achievement_update()
        global start
        global wait_time
        now = time.time()
        if now - start > wait_time:
            g.lift_up = True
            socketio.emit("lift_button_pressed", "down")
            socketio.emit("lift_button_pressed_hs", "down")
            # Via Bluetooth to SPEAKER -> play lift moving sound
            sound_eff = mixer.Sound("./sounds/lift_up_down.wav")
            sound_eff.play()
            start = time.time()
            wait_time = 20
    else:
        socketio.emit("lift_button_pressed", "down")
        sound_eff = mixer.Sound("./sounds/lift_up_down.wav")
        sound_eff.play()
    return "<h1>Lift button DOWN state received by the server!</h1>"

@socketio.on('on_lift_use')
def on_elevator_use(player):
    print("Lift Used!",player)
    if player["player_number"] == "1":
        player_two = Headset.query.filter_by(player_number = 2).first()
        if player_two: socketio.emit(event = "lift_button_pressed_hs", data = "down", room = player_two.socket_id)
    if player["player_number"] == "2":
        player_one = Headset.query.filter_by(player_number = 1).first()
        if player_one: socketio.emit(event = "lift_button_pressed_hs", data = "down" ,room = player_one.socket_id)
    if g.start:
        g.team_score.use_lift = True    # ✓ CHECK SCORE FOR LIFT USE
        print("Achievement Unlocked: Lift Used!")
        emit_achievement_update()

# OPEN SETTINGS
@app.route('/open_door')
def open_door():
    socketio.emit("lift_button_pressed_hs", "open") # HEADSET

# TAG SETTINGS
@app.route('/single_or_multi')
def single_or_mult():
    if g.settings_are_set and g.tracking:
        print("----->Sending Single/Multiplayer Parameter")
        global uwb_thread
        if ((uwb_thread is None) and (g.is_multiplayer != None)):
            # uwb_thread = socketio.start_background_task(uwb_logic_multiplayer.start_uwb, False, socketio)      
            print("----->Starting the UWB Tracking")
            uwb_thread = Thread(target = uwb_logic_multiplayer.start_uwb, args=(False,socketio, g)) # args: verbose -> True or False
            uwb_thread.start()
        # Via WiFi to TAG 1 -> send whether it's single or multiplayer
    return "----->Starting the UWB Tracking"
    #     if g.is_multiplayer: return "2"
    #     elif g.is_multiplayer == False: return "1"
    #     return "0"
    # else:
    #     return "0"

# AUTOMATIC REPORT
@app.route('/generate_report')
def generate_report():
    print(g.player_one)
    if g.is_multiplayer: print(g.player_two)
    if g.start:
        global pdf_thread
        if ((pdf_thread is None)):
            print("----->Generating PDF Report")
            g.player_one.individual_score.calculate_individual_score()
            if g.is_multiplayer: g.player_two.individual_score.calculate_individual_score()
            g.team_score.calculate_team_score()
            g.calculate_total_score()
            pdf_thread = Thread(target = pdfreport.generate_pdf_report, args=(g,)) # args: verbose -> True or False
            pdf_thread.start()
        return "<h1>----->Generating PDF Report<h1>"
    else:
        return "<h1>----->Experience hasn't started yet, it's not possible to generate PDF Report</h1>"

# @app.route('/test1')
# def test1():
#     socketio.emit("test1")
#     return "<h1>PLAYER ONE is now sending its position to PLAYER TWO<h1>"

# @app.route('/test2')
# def test2():
#     socketio.emit("test2")
#     return "<h1>PLAYER TWO is now sending its position to PLAYER ONE<h1>"

# --------------------------------- EVENTS / WEBSOCKETS ---------------------------------

# GAME SETTINGS DEFINED (PERMISSIVINESS, IS_MULTIPLAYER AND TRACKING + PLAYER NAMES)
@socketio.on('settings_defined')
def settings_defined(settings):
    socketio.emit("settings_defined_headset",settings)
    print("Game Settings Defined: ", settings)
    g.stage = 2
    g.set_settings(settings["permissiveness"], settings["is_multiplayer"], settings["tracking"])
    player_one = Headset.query.filter_by(player_number = 1).first()
    player_two = Headset.query.filter_by(player_number = 2).first()
    g.player_one.name = settings["players"][0]["player_name"]
    player_one.player_name = g.player_one.name
    db.session.commit()
    if player_one: emit_headset_update(player_one)
    if g.is_multiplayer: 
        g.player_two.name = settings["players"][1]["player_name"]
        player_two.player_name = g.player_two.name
        db.session.commit()
        if player_two: emit_headset_update(player_two)
    elif g.is_multiplayer == False:
        if player_two: player_two.player_number = 0
        db.session.commit()
        if player_two: emit_headset_update(player_two)

# LAUNCH EXPERIENCE (STARTS THE GAME)
@socketio.on('inventory_ready')
def inventory_ready(player):
    print("Inventory Ready Event: ", player)
    # player_one = Headset.query.filter_by(player_number = 1).first()
    # player_two = Headset.query.filter_by(player_number = 2).first()
    if player["player_number"] == "1":
        g.player_one.inventory_selected = True
    elif player["player_number"] == "2":
        g.player_two.inventory_selected = True
    if g.is_multiplayer and g.player_one.inventory_selected and g.player_two.inventory_selected : g.inventories_ready = True
    if g.is_multiplayer == False and g.player_one.inventory_selected : g.inventories_ready = True
    if g.inventories_ready : 
        print("I just sent to FRONTEND!")
        socketio.emit("unblock_launch_button")  # to frontend

# LAUNCH EXPERIENCE (STARTS THE GAME)
@socketio.on('launch_experience')
def launch_experience():
    socketio.emit("launch_experience_headset")
    print("Experience Started!")
    if g.settings_are_set and g.tracking:
        print("----->Sending Single/Multiplayer Parameter")
        global uwb_thread
        if ((uwb_thread is None) and (g.is_multiplayer != None)):
            # uwb_thread = socketio.start_background_task(uwb_logic_multiplayer.start_uwb, False, socketio)      
            print("----->Starting the UWB Tracking")
            uwb_thread = Thread(target = uwb_logic_multiplayer.start_uwb, args=(False,socketio,g)) # args: verbose -> True or False
            uwb_thread.start()
        # Via WiFi to TAG 1 -> send whether it's single or multiplayer
    # g.player_one.time_start = time.time()
    # if g.is_multiplayer: g.player_two.time_start = time.time()
    g.start = True
    g.stage = 3

# FINALIZE EXPERIENCE (STOPS THE GAME AND GENERATES REPORT) -> Triggered by the headset (when the game ends) or when the trainer presses finalize button
@socketio.on('finalize_experience')
def finalize_experience(player):
    # TODO: Generate report
    print("---------------------------> HEADSET: Experience Finalized!")
    if player["player_number"] == "1" : 
        print("PLAYER 1 FINALIZED!")
        g.player_one.finalized = True
        socketio.emit("player_finished", player)
    if player["player_number"] == "2" : 
        print("PLAYER 2 FINALIZED!")
        g.player_two.finalized = True
        socketio.emit("player_finished", player)

    print(g.player_one)
    if g.is_multiplayer: print(g.player_two)

    # GENERATE THE REPORT
    global pdf_thread
    if g.is_multiplayer == False and g.player_one.finalized:
        # if ((pdf_thread is None)):
        print("----->Generating PDF Report")
        g.player_one.individual_score.calculate_individual_score()
        g.team_score.calculate_team_score()
        g.calculate_total_score()
        pdf_thread = Thread(target = pdfreport.generate_pdf_report, args=(g,)) # args: verbose -> True or False
        pdf_thread.start()

        g.start = False
        # time.sleep(1500)
        # g.stage = 0
        # g = Game()
        # reset_headset()
    elif g.is_multiplayer and g.player_one.finalized and g.player_two.finalized:
        # if ((pdf_thread is None)):
        print("----->Generating PDF Report")
        g.player_one.individual_score.calculate_individual_score()
        g.player_two.individual_score.calculate_individual_score()
        g.team_score.calculate_team_score()
        g.calculate_total_score()
        pdf_thread = Thread(target = pdfreport.generate_pdf_report, args=(g,)) # args: verbose -> True or False
        pdf_thread.start()
        
        g.start = False
        # time.sleep(1500)
        # g.stage = 0
        # g = Game()
        # reset_headset()
    
@socketio.on('finalize_experience_frontend')
def finalize_experience_frontend():
    print("---------------------------> FRONTEND: Experience Finalized!")
    global pdf_thread
    # GENERATE THE REPORT
    # if (pdf_thread is None):
    print("----->Generating PDF Report")
    g.player_one.individual_score.calculate_individual_score()
    if g.is_multiplayer: g.player_two.individual_score.calculate_individual_score()
    g.team_score.calculate_team_score()
    g.calculate_total_score()
    pdf_thread = Thread(target = pdfreport.generate_pdf_report, args=(g,)) # args: verbose -> True or False
    pdf_thread.start()
    socketio.emit("finalize_experience_headset")

@socketio.on('restart_experience')
def restart_experience():
    socketio.emit("restart_experience_headset")
    global g
    g = Game()
    # reset_headset() # Flush Database

# HEADSET CONNECTION (NEW OR OLD)
@socketio.on('headset_connected')
def headset_connected(value):
    print("----->Connected to a headset!")
    print("DATA: ",value)
    print("DATA JSON: ", value["headset_id"])
    found_headset = Headset.query.filter_by(headset_id = value["headset_id"]).first()
    player_one = Headset.query.filter_by(player_number = 1).first()
    player_two = Headset.query.filter_by(player_number = 2).first()
    if found_headset: # if nothing it takes value None
        found_headset.socket_id = request.sid
        found_headset.headset_status = True
        if g.paired_headsets == 0 and not player_one: 
            found_headset.player_number = 1
            g.paired_headsets += 1
        elif g.paired_headsets == 1 and not player_two:
            found_headset.player_number = 2
            g.paired_headsets += 1
        db.session.commit()
        print("~~~~|Database Message: Headset already in database")
        print(found_headset)
    else:
        hs = Headset(value["headset_id"],request.sid)
        db.session.add(hs)         # Waiting to be commited
        hs.socket_id = request.sid
        hs.headset_status = True
        if g.paired_headsets == 0 and not player_one: 
            hs.player_number = 1
            g.paired_headsets += 1
        elif g.paired_headsets == 1 and not player_two:
            hs.player_number = 2
            g.paired_headsets += 1
        db.session.commit()         # Commited into the database! (revert it also possible)
        print("~~~~|Database Message: New headset was added to the database")
        print(hs)
        found_headset = hs
    # MESSAGE FOR FRONTEND TO UPDATE INDICATOR
    print('Paired Headsets: ', g.paired_headsets)
    if found_headset: emit_headset_update(found_headset)
    socketio.emit("player_number_assignment",{"player_number":found_headset.player_number}, room = request.sid)
    print("SENT NUMBER: ", found_headset.player_number)

# HEADSET NAME CHANGED
@socketio.on('headset_name_changed')
def headset_name_changed(headset):
    found_headset = Headset.query.filter_by(headset_id = headset["headset_id"]).first()
    if found_headset:
        found_headset.headset_name = headset["headset_name"]
        db.session.commit()
        if found_headset: emit_headset_update(found_headset)
    else:
        print(f"No headset linked to {headset.headset_id} ID")

# SENDING PLAYER POSITION
@socketio.on('player_position') # expect headset id with position
def player_position(player):
    print("Player Position Event: ", player)
    if player["player_number"] == "1":
        g.player_one.position =             [player["x"].replace(",","."),      player["y"].replace(",","."),       player["z"].replace(",",".")]
        g.player_one.rotation =             [player["rotx"].replace(",","."),   player["roty"].replace(",","."),    player["rotz"].replace(",",".")]
        g.player_one.left_controller_pos =  [player["lx"].replace(",","."),     player["ly"].replace(",","."),      player["lz"].replace(",",".")]
        g.player_one.left_controller_rot =  [player["lrotx"].replace(",","."),  player["lroty"].replace(",","."),   player["lrotz"].replace(",",".")]
        g.player_one.right_controller_pos = [player["rx"].replace(",","."),     player["ry"].replace(",","."),      player["rz"].replace(",",".")]
        g.player_one.right_controller_rot = [player["rrotx"].replace(",","."),  player["rroty"].replace(",","."),   player["rrotz"].replace(",",".")]
        g.player_one.left_controller_fingers =  [player['HL0'].replace(",","."), player['HL1'].replace(",","."), player['HL2'].replace(",","."), player['HL3'].replace(",","."), player['HL4'].replace(",",".")]
        g.player_one.right_controller_fingers = [player['HR0'].replace(",","."), player['HR1'].replace(",","."), player['HR2'].replace(",","."), player['HR3'].replace(",","."), player['HR4'].replace(",",".")]

        player_two = Headset.query.filter_by(player_number = 2).first()

        if player_two: 
            print("I'M SENDING TO PLAYER 2")
            socketio.emit(event = "other_player_position", 
                          data = {"player_number":"1",
                                  "x":g.player_one.position[0],                   "y":g.player_one.position[1],                    "z":g.player_one.position[2],
                                  "rotx":g.player_one.rotation[0],                "roty":g.player_one.rotation[1],                 "rotz":g.player_one.rotation[2],
                                  "lx":g.player_one.left_controller_pos[0],       "ly":g.player_one.left_controller_pos[1],        "lz":g.player_one.left_controller_pos[2],
                                  "lrotx":g.player_one.left_controller_rot[0],    "lroty":g.player_one.left_controller_rot[1],     "lrotz":g.player_one.left_controller_rot[2],
                                  "rx":g.player_one.right_controller_pos[0],      "ry":g.player_one.right_controller_pos[1],       "rz":g.player_one.right_controller_pos[2],
                                  "rrotx":g.player_one.right_controller_rot[0],   "rroty":g.player_one.right_controller_rot[1],    "rrotz":g.player_one.right_controller_rot[2],
                                  'HL0':g.player_one.left_controller_fingers[0],  'HL1':g.player_one.left_controller_fingers[1],   'HL2':g.player_one.left_controller_fingers[2],
                                  'HL3':g.player_one.left_controller_fingers[3],  'HL4':g.player_one.left_controller_fingers[4],   'HR0':g.player_one.right_controller_fingers[0],
                                  'HR1':g.player_one.right_controller_fingers[1], 'HR2':g.player_one.right_controller_fingers[2], 'HR3':g.player_one.right_controller_fingers[3],
                                  'HR4':g.player_one.right_controller_fingers[4]},

                          room = player_two.socket_id)
        
        socketio.emit(event = "minimap_update",
                      data = {"player_number":1, "x":float(g.player_one.position[0]), "y":float(g.player_one.position[2])})

    if player["player_number"] == "2":
        g.player_two.position =             [player["x"].replace(",","."),     player["y"].replace(",","."),    player["z"].replace(",",".")]
        g.player_two.rotation =             [player["rotx"].replace(",","."),  player["roty"].replace(",","."), player["rotz"].replace(",",".")]
        g.player_two.left_controller_pos =  [player["lx"].replace(",","."),    player["ly"].replace(",","."),   player["lz"].replace(",",".")]
        g.player_two.left_controller_rot =  [player["lrotx"].replace(",","."), player["lroty"].replace(",","."),player["lrotz"].replace(",",".")]
        g.player_two.right_controller_pos = [player["rx"].replace(",","."),    player["ry"].replace(",","."),   player["rz"].replace(",",".")]
        g.player_two.right_controller_rot = [player["rrotx"].replace(",","."), player["rroty"].replace(",","."),player["rrotz"].replace(",",".")]
        g.player_two.left_controller_fingers =  [player['HL0'].replace(",","."), player['HL1'].replace(",","."), player['HL2'].replace(",","."), player['HL3'].replace(",","."), player['HL4'].replace(",",".")]
        g.player_two.right_controller_fingers = [player['HR0'].replace(",","."), player['HR1'].replace(",","."), player['HR2'].replace(",","."), player['HR3'].replace(",","."), player['HR4'].replace(",",".")]
        
        player_one = Headset.query.filter_by(player_number = 1).first()

        if player_one: 
            print("I'M SENDING TO PLAYER 1")
            socketio.emit(event = "other_player_position", 
                          data = {"player_number":"2",
                                  "x":g.player_two.position[0],                   "y":g.player_two.position[1],                   "z":g.player_two.position[2],
                                  "rotx":g.player_two.rotation[0],                "roty":g.player_two.rotation[1],                "rotz":g.player_two.rotation[2],
                                  "lx":g.player_two.left_controller_pos[0],       "ly":g.player_two.left_controller_pos[1],       "lz":g.player_two.left_controller_pos[2],
                                  "lrotx":g.player_two.left_controller_rot[0],    "lroty":g.player_two.left_controller_rot[1],    "lrotz":g.player_two.left_controller_rot[2],
                                  "rx":g.player_two.right_controller_pos[0],      "ry":g.player_two.right_controller_pos[1],      "rz":g.player_two.right_controller_pos[2],
                                  "rrotx":g.player_two.right_controller_rot[0],   "rroty":g.player_two.right_controller_rot[1],   "rrotz":g.player_two.right_controller_rot[2],
                                  'HL0':g.player_two.left_controller_fingers[0],  'HL1':g.player_two.left_controller_fingers[1],  'HL2':g.player_two.left_controller_fingers[2],
                                  'HL3':g.player_two.left_controller_fingers[3],  'HL4':g.player_two.left_controller_fingers[4],  'HR0':g.player_two.right_controller_fingers[0],
                                  'HR1':g.player_two.right_controller_fingers[1], 'HR2':g.player_two.right_controller_fingers[2], 'HR3':g.player_two.right_controller_fingers[3],
                                  'HR4':g.player_two.right_controller_fingers[4]},

                          room = player_one.socket_id)
        
        socketio.emit(event = "minimap_update",
                      data = {"player_number":2, "x":float(g.player_two.position[0]), "y":float(g.player_two.position[2])})

# PLAYER ACHIEVEMENTS (TASKS)
@socketio.on('door_closed')
def DoorIsClosed(data):
    print("Door is Closed")
    socketio.emit(event = "DoorIsClosed")

# PLAYER ACHIEVEMENTS (TASKS)
@socketio.on('achievement_unlocked')
def achievement_unlocked(data):
    print("Achievement Unlocked", data)

    if data["achievement_name"] == "take_flashlight":           # ✓ CHECK SCORE FOR TAKING FLASHLIGHT
        if data["player_number"] == "1" and data["achievement_value"] == "True": g.player_one.individual_score.take_flashlight = True    
        elif data["player_number"] == "2" and data["achievement_value"] == "True": g.player_two.individual_score.take_flashlight = True
    if data["achievement_name"] == "take_suit":                 # ✓ CHECK SCORE FOR TAKING SUIT
        if data["player_number"] == "1": 
            g.player_one.individual_score.take_suit = data["achievement_value"]
            if data["achievement_value"] == g.player_one.individual_score.correct_suit: g.player_one.individual_score.take_right_suit = True     
        elif data["player_number"] == "2": 
            g.player_two.individual_score.take_suit = data["achievement_value"]
            if data["achievement_value"] == g.player_two.individual_score.correct_suit: g.player_two.individual_score.take_right_suit = True
    if data["achievement_name"] == "take_filter":               # ✓ CHECK SCORE FOR TAKING FILTER
        if data["player_number"] == "1": 
            g.player_one.individual_score.take_filter = data["achievement_value"]
            if data["achievement_value"] == g.player_one.individual_score.correct_filter: g.player_one.individual_score.take_right_filter = True
        elif data["player_number"] == "2": 
            g.player_two.individual_score.take_filter = data["achievement_value"]
            if data["achievement_value"] == g.player_two.individual_score.correct_filter: g.player_two.individual_score.take_right_filter = True
    if data["achievement_name"] == "take_camera":               # ✓ CHECK SCORE FOR TAKING CAMERA
        if data["player_number"] == "1" and data["achievement_value"] == "True": g.player_one.individual_score.take_camera = True
        elif data["player_number"] == "2" and data["achievement_value"] == "True": g.player_two.individual_score.take_camera = True
    if data["achievement_name"] == "take_sampling_kit" :         # ✓ CHECK SCORE FOR TAKING SAMPLING KIT
        if data["player_number"] == "1" and data["achievement_value"] == "True": g.player_one.individual_score.take_sampling_kit = True
        elif data["player_number"] == "2" and data["achievement_value"] == "True": g.player_two.individual_score.take_sampling_kit = True
    if data["achievement_name"] == "take_chem_detector":        # ✓ CHECK SCORE FOR TAKING CHEM DETECTOR
        if data["player_number"] == "1" and data["achievement_value"] == "True": g.player_one.individual_score.take_chem_detector = True
        elif data["player_number"] == "2" and data["achievement_value"] == "True": g.player_two.individual_score.take_chem_detector = True
    if data["achievement_name"] == "take_decon_kit":        # ✓ CHECK SCORE FOR TAKING CHEM DETECTOR
        if data["player_number"] == "1" and data["achievement_value"] == "True": g.player_one.individual_score.take_decon_kit = True
        elif data["player_number"] == "2" and data["achievement_value"] == "True": g.player_two.individual_score.take_decon_kit = True
    if data["achievement_name"] == "take_gun":                  # ✓ CHECK SCORE FOR TAKING GUN
        if data["player_number"] == "1" and data["achievement_value"] == "True":  g.player_one.individual_score.take_gun = True
        elif data["player_number"] == "2" and data["achievement_value"] == "True": g.player_two.individual_score.take_gun = True
    if data["achievement_name"] == "irradiation":               # ✓ CHECK SCORE FOR IRRADIATION AMOUNT
        if data["player_number"] == "1":  g.player_one.individual_score.irradiation = data["achievement_value"]
        elif data["player_number"] == "2": g.player_two.individual_score.irradiation = data["achievement_value"]
    if data["achievement_name"] == "take_samples":              # ✓ CHECK SCORE FOR AMOUNT OF SAMPLES
        if data["achievement_value"] in list(g.team_score.take_samples.keys()):
            g.team_score.take_samples[data["achievement_value"]] = True
        print("List of Taken Samples: ", g.team_score.take_samples)
        socketio.emit("update_team_score", {"achievement_name" : "take_samples", "value" : sum(g.team_score.take_samples.values())})
    if data["achievement_name"] == "take_pictures":
        if data["achievement_value"] in list(g.team_score.take_pictures.keys()):
            g.team_score.take_pictures[data["achievement_value"]] = True
        print("List of Taken Pictures: ", g.team_score.take_pictures)
        socketio.emit("update_team_score", {"achievement_name" : "take_pictures", "value" : sum(g.team_score.take_pictures.values())})
    emit_achievement_update()

# Connection error handling
@socketio.on("my error event")
def on_my_event(data):
    print("Error event")
    raise RuntimeError()

@socketio.on_error_default
def default_error_handler(e):
    print("Error event")
    print(request.event["message"]) # "my error event"
    print(request.event["args"])    # (data,)

# sock_id = 0

# CONNECTION
@socketio.event
def connect():
    print('----->Connected to a client!', "\tSocket ID: ", request.sid)

# DISCONNECTION
@socketio.event
def disconnect():
    found_headset = Headset.query.filter_by(socket_id = request.sid).first()
    if found_headset:
        found_headset.headset_status = False
        # found_headset.player_name = ""
        found_headset.socket_id = ""
        print(f'----->Disconnected from a headset!\n{found_headset}')
        # player_one = Headset.query.filter_by(player_number = 1).first()
        player_two = Headset.query.filter_by(player_number = 2).first()
        another_active_player = Headset.query.filter_by(player_number = 0, headset_status = True).first()
        if not g.settings_are_set:
            if g.paired_headsets == 1 and found_headset.player_number == 1:
                found_headset.player_number = 0
            elif g.paired_headsets == 2 and found_headset.player_number == 1:
                found_headset.player_number = 0
                player_two.player_number = 1
                socketio.emit("player_number_assignment",{"player_number":player_two.player_number}, room = player_two.socket_id)
                if another_active_player:
                    another_active_player.player_number = 2
                    g.paired_headsets += 1
                    socketio.emit("player_number_assignment",{"player_number":another_active_player.player_number}, room = another_active_player.socket_id)
            elif g.paired_headsets == 2 and found_headset.player_number == 2:
                found_headset.player_number = 0
                if another_active_player:
                    another_active_player.player_number = 2
                    g.paired_headsets += 1
                    socketio.emit("player_number_assignment",{"player_number":another_active_player.player_number}, room = another_active_player.socket_id)
            else:
                found_headset.player_number = 0
        if g.paired_headsets > 0: g.paired_headsets -= 1
        db.session.commit()
        if found_headset: emit_headset_update(found_headset)
        
        if another_active_player: 
            emit_headset_update(another_active_player)
            socketio.emit("player_number_assignment",{"player_number":another_active_player.player_number}, room = another_active_player.socket_id)
        print('Paired Headsets: ', g.paired_headsets)
    else:
        print('----->Disconnected from a client!', "\tSocket ID: ",request.sid)

if __name__ == '__main__':
    print("----->Starting the webserver")
    with app.app_context():
        db.create_all()
    # g.set_settings(True,True,True)
    socketio.run(app, debug = False, host = "0.0.0.0", port = os.getenv("PORT"),  allow_unsafe_werkzeug = True)
    print("----->End")
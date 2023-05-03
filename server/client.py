import socketio
sio = socketio.Client()

position = [50,100]
player_number = 0

@sio.event
def connect():
    sio.emit(event ='headset_connected', data = {"headset_id":"ID1"})
    print('Connection established')

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.on('position_calibration')
def position_calibration(data):
    print("Client Side: ",data)

@sio.on('settings_defined_headset')
def settings_defined_headset(player):
    print("I (HEADSET) SELECTED SETTINGS")
    sio.emit(event ='inventory_ready', data = {"player_number":"1"})

@sio.on('test1')
def test():
    global player_number
    global position
    sio.emit(event ='player_position', data= {'player_number': player_number, 'position': position})

@sio.on('other_player_position')
def other_player_position(data):
    print("RECEIVED DATA FROM OTHER PLAYER: ",data)

@sio.on('player_number_assignment')
def player_number_assignment(data):
    global player_number
    player_number = data["player_number"]
    print("CLIENT --------------> PLAYER NUMBER INFO: ",data)

sio.connect('http://127.0.0.1:5000')

sio.wait() 
import socketio
sio = socketio.Client()

@sio.event
def connect():
    sio.emit(event ='headset_connected', data = "HEADSET_ID_IS_THREE")
    print('Connection established')

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.on('position_calibration')
def handle_message(data):
    print("Client Side: ",data)

@sio.on('player_number_assignment')
def player_number_assignment(data):
    print("CLIENT --------------> PLAYER NUMBER INFO: ",data)

sio.connect('http://127.0.0.1:5000')

sio.wait() 
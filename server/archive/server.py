import eventlet
eventlet.monkey_patch()
import socketio
import uwb_logic_multiplayer
from threading import Thread

sio = socketio.Server()
app = socketio.WSGIApp(sio)

@sio.event
def connect(sid, environ):
    print('connect ', sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

@sio.on("light")
def on_message(data):
    print(data)

if __name__ == '__main__':
    print("hola")
    Thread(target = uwb_logic_multiplayer.start_uwb, args=(True,sio)).start() # args: verbose -> True or False
    eventlet.wsgi.server(eventlet.listen(('192.168.1.100', 5000)), app)
    eventlet.monkey_patch()
    # socketio.run(app, port = 5000, debug = True, use_reloader = True)
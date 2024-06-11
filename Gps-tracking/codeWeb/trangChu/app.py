from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
from prettytable import PrettyTable


app = Flask(__name__)
socketio = SocketIO(app)
CORS(app, resources={r"/socket.io/*": {"origins": "*"}})
@app.route('/')
def index():
    return render_template('1.html')
if __name__ == '__main__':
    socketio.run(app, host='192.168.1.111', port=80, debug=True)

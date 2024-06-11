from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import urllib3
import sqlite3
from prettytable import PrettyTable


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app, resources={r"/socket.io/*": {"origins": "*"}})

tenant_username = "gpstrackingoto@gmail.com"
tenant_password = "12345678"
thingsboard_base_url = "https://thingsboard.cloud/"
device_id = "db2ae2c0-1271-11ef-9e10-4570a5104a0d"
device_access_token = "2ZKFUdbBf2xAuPDPXG4l"
telemetry_keys = "h,t"

def get_access_token(username, password):
    url = thingsboard_base_url + "api/auth/login"
    payload = {"username": username, "password": password}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        token = response.json().get('token', None)
        return token
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error during access token retrieval: {e}")

def get_device_telemetry(device_token, keys):
    url = f"{thingsboard_base_url}api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys={keys}&useStrictDataTypes=true"
    headers = {'Content-Type': 'application/json', 'X-Authorization': f'Bearer {device_token}'}

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        telemetry_data = response.json()
        print("Truy cập ThingsBoard thành công")
        return telemetry_data
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Truy cập ThingsBoard thất bại: {e}")

@app.route('/')
def index():
    return render_template('2.html')


def emit_telemetry_data():
    global device_access_token
    global telemetry_keys

    try:
        device_access_token = get_access_token(tenant_username, tenant_password)

        if device_access_token:
            telemetry_data = get_device_telemetry(device_access_token, telemetry_keys)

            if telemetry_data:

                t = telemetry_data.get('t', [{}])[0].get('value', None)
                h = telemetry_data.get('h', [{}])[0].get('value', None)
            else:
                speed,h,t = None, None
        else:
              speed,h,t = None, None

        socketio.emit('telemetry_data', {'t': t, 'h':h}, namespace='/')

    except RuntimeError as e:
        print(f"Error: {e}")
    
        

    
def update_telemetry_periodically():
    while True:
        emit_telemetry_data()
        socketio.sleep(3)

if __name__ == '__main__':
    socketio.start_background_task(target=update_telemetry_periodically)
    socketio.run(app, host='192.168.1.111', port=3000, debug=True)

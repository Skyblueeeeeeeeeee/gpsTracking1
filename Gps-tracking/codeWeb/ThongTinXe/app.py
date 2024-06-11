from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import urllib3
import time
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app, resources={r"/socket.io/*": {"origins": "*"}})

# Configuration
tenant_username = "gpstrackingoto@gmail.com"
tenant_password = "12345678"
thingsboard_base_url = "https://thingsboard.cloud/"
device_id = "db2ae2c0-1271-11ef-9e10-4570a5104a0d"
device_access_token = "2ZKFUdbBf2xAuPDPXG4l"
telemetry_keys = "h,t,cua1,cua2,cua3,cua4"

khoa = 0
timer = None  # Initialize the timer variable
sbtn = 0
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
        print("Successfully accessed ThingsBoard")
        return telemetry_data
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to access ThingsBoard: {e}")



def emit_telemetry_data():
    try:
        device_access_token = get_access_token(tenant_username, tenant_password)
        telemetry_data = get_device_telemetry(device_access_token, telemetry_keys) if device_access_token else {}

        t = telemetry_data.get('t', [{}])[0].get('value', None)
        h = telemetry_data.get('h', [{}])[0].get('value', None)
        cua1 = telemetry_data.get('cua1', [{}])[0].get('value', None)
        cua2 = telemetry_data.get('cua2', [{}])[0].get('value', None)
        cua3 = telemetry_data.get('cua3', [{}])[0].get('value', None)
        cua4 = telemetry_data.get('cua4', [{}])[0].get('value', None)

        print(f"Sending telemetry data - temp: {t}, hum: {h}, cua1: {cua1}, cua2: {cua2}, cua3: {cua3}, cua4: {cua4}")
        socketio.emit('telemetry_data', {'t': t, 'h': h, 'cua1': cua1, 'cua2': cua2, 'cua3': cua3, 'cua4': cua4}, namespace='/')
    except RuntimeError as e:
        print(f"Error: {e}")

def send_telemetry_data(device_token, telemetry_data):
    url = f"{thingsboard_base_url}api/v1/{device_token}/telemetry"
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, json=telemetry_data, verify=False)
        response.raise_for_status()
        print(f"Telemetry data sent successfully: {telemetry_data}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending telemetry data: {e}")

def reset_khoa():
    global khoa
    khoa = 0
    print(f"khoa reset to 0")

@socketio.on('khoa')
def handle_khoa_event(data):
    global khoa, timer
    khoa = 1
    print(f"khoa set to 1")
    if timer is not None:
        timer.cancel()
    timer = threading.Timer(5.0, reset_khoa)
    timer.start()
    
@socketio.on('sbtn')
def handle_sbtn_event(data):
    global sbtn
    sbtn = bool(data)  
    print(f"sbtn set to {sbtn}")  
    
@app.route('/', methods=['GET'])
def index():
    source = request.args.get('source')
    if (source == 'esp8266'):
        print("Received request from ESP8266")
        return jsonify(khoa=khoa,sbtn=sbtn), 200
    else:
        print("Received request from other source")
        return render_template('info.html')
    
def update_telemetry_periodically():
    while True:
        print(khoa)
        print(sbtn)
        emit_telemetry_data()
        time.sleep(1)

if __name__ == '__main__':
    socketio.start_background_task(target=update_telemetry_periodically)
    socketio.run(app, host='192.168.1.111', port=3004, debug=True)

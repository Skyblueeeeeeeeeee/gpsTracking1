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
telemetry_keys = "latitude,longitude,status,speed_kmh,h,t"

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
    return render_template('index.html')


def emit_telemetry_data():
    global device_access_token
    global telemetry_keys

    try:
        device_access_token = get_access_token(tenant_username, tenant_password)

        if device_access_token:
            telemetry_data = get_device_telemetry(device_access_token, telemetry_keys)

            if telemetry_data:
                longitude = telemetry_data.get('longitude', [{}])[0].get('value', None)
                latitude = telemetry_data.get('latitude', [{}])[0].get('value', None)
                status = telemetry_data.get('status', [{}])[0].get('value', None)
                speed = telemetry_data.get('speed_kmh', [{}])[0].get('value', None)
                t = telemetry_data.get('t', [{}])[0].get('value', None)
                h = telemetry_data.get('h', [{}])[0].get('value', None)
            else:
                longitude, latitude, status, speed,h,t = None, None, None, None,None,None
        else:
                longitude, latitude, status, speed,h,t = None, None, None, None,None,None

        print(f"Sending telemetry data - Longitude: {longitude}, Latitude: {latitude}, Status: {status}")
        socketio.emit('telemetry_data', {'longitude': longitude, 'latitude': latitude, 'status': status, 't': t, 'h':h,'speed':speed}, namespace='/')

    except RuntimeError as e:
        print(f"Error: {e}")
    
        
search_histories = []
# Listen for the 'searchHistory' event
@socketio.on('searchHistory')
def handle_search_history(search_history):
    print('Received search history:', search_history)
    search_histories.append(search_history)

    # Extracting values from the received search history
    
    dateTime_value = search_history.get('dateTime', None)
    latitude_value = search_history.get('latitude', None)
    longitude_value = search_history.get('longitude', None)
    google_map_url_value = search_history.get('googleMapUrl', None)

    # Use the extracted values as new variables or perform any desired action
    if all([dateTime_value, latitude_value, longitude_value, google_map_url_value]):
        # Do something with the extracted values
        print('DateTime:', dateTime_value)
        print('Latitude:', latitude_value)
        print('Longitude:', longitude_value)
        print('Google Map URL:', google_map_url_value)

        createTableData()
        dateTime_value = search_history.get('dateTime', None)
        latitude_value = search_history.get('latitude', None)
        longitude_value = search_history.get('longitude', None)
        google_map_url_value = search_history.get('googleMapUrl', None)

        insertData(dateTime_value, latitude_value, longitude_value, google_map_url_value)

        gpslist = getAllData()

        table = PrettyTable(["Id", "Thời gian", "Vĩ độ", "Kinh độ", "Vị trí"])

        # Iterate through the list of data and add rows to the table
        for data in gpslist:
            table.add_row(data)

    else:
        print('Some values are missing in the received search history.')


def createTableData():
    with sqlite3.connect("data.db") as dataConnect:
        query = """
        CREATE TABLE IF NOT EXISTS Data (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            dateTime DATETIME,
            Longitude TEXT,
            Latitude TEXT,
            Link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor = dataConnect.cursor()
        cursor.execute(query)
        

# Khai báo biến toàn cục table
table = PrettyTable(["Id", "Thời gian", "Vĩ độ", "Kinh độ", "Vị trí"])



def insertData(dateTime_value, latitude_value, longitude_value, google_map_url_value):
    with sqlite3.connect("data.db") as dataConnect:
        createTableData()  # Ensure the table exists

        query_insert = """
        INSERT INTO Data (dateTime, Latitude, Longitude, Link) VALUES (?, ?, ?, ?)
        """
        cursor = dataConnect.cursor()

        # Insert new data
        cursor.execute(query_insert, (dateTime_value, latitude_value, longitude_value, google_map_url_value))
        dataConnect.commit()

        # Check if the number of rows is greater than 10
        cursor.execute("SELECT COUNT(*) FROM Data")
        count = cursor.fetchone()[0]

        if count > 20:
            # Delete the oldest row
            query_delete_oldest = """
            DELETE FROM Data WHERE created_at = (SELECT MIN(created_at) FROM Data)
            """
            cursor.execute(query_delete_oldest)
            dataConnect.commit()

        # Print the table after each insert
        cursor.execute("SELECT Id, dateTime, Longitude, Latitude, Link FROM Data")
        rows = cursor.fetchall()
        table = PrettyTable(["Id", "Thời gian", "Vĩ độ", "Kinh độ", "Vị trí"])
        for row in rows:
            table.add_row(row)

        print(table)



def getAllData():
    dataConnect = sqlite3.connect("data.db")
    createTableData()  # Ensure the table exists

    query_select = """
    SELECT Id, dateTime, Longitude, Latitude, Link FROM Data
    """
    cursor = dataConnect.cursor()
    gpslist = cursor.execute(query_select).fetchall()
    dataConnect.close()
    return gpslist


@socketio.on('get_data')
def send_table_data():
    gpslist = getAllData()
    # Create the table object here
    table = PrettyTable(["Id", "Thời gian", "Vĩ độ", "Kinh độ", "Vị trí"])
    for data in gpslist:
        table.add_row(data)

    # Gửi dữ liệu bảng tới front-end qua socket.io
    emit('data', {'table': str(table)})



    
def update_telemetry_periodically():
    while True:
        emit_telemetry_data()
        socketio.sleep(1)

if __name__ == '__main__':
    socketio.start_background_task(target=update_telemetry_periodically)
    socketio.run(app, host='192.168.1.111', port=3002, debug=True)

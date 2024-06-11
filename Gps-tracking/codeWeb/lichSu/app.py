from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3
from prettytable import PrettyTable

# Đường dẫn đến cơ sở dữ liệu (sử dụng chuỗi raw để tránh lỗi với ký tự thoát)
db_path = r"C:\Users\nghia\OneDrive\Máy tính\doan\dinh_vi\data.db"

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app, resources={r"/socket.io/*": {"origins": "*"}})


@app.route('/')
def index():
    return render_template('history-table.html')


def getAllData():
    dataConnect = sqlite3.connect(db_path)
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
    table = PrettyTable(["Id", "Thời gian", "Vĩ độ", "Kinh độ", "Vị trí"])
    for data in gpslist:
        table.add_row(data)

    # Gửi dữ liệu bảng tới front-end qua socket.io
    emit('data', {'table': str(table)})


def update_telemetry_periodically():
    while True:
        # TODO: Thêm code để cập nhật dữ liệu nếu cần thiết
        socketio.sleep(3)

if __name__ == '__main__':
    socketio.start_background_task(target=update_telemetry_periodically)
    socketio.run(app, host='192.168.1.111', port=3003, debug=True)

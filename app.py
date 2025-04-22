from flask import Flask, render_template, Response
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import pyautogui
import numpy as np
import cv2
import time

from collections import deque
from threading import Lock

data_log = deque(maxlen=900)  # 15 fps * 60 seg
data_lock = Lock()

app = Flask(__name__)
auth = HTTPBasicAuth()

# Puedes cambiar estas credenciales
users = {
    "admin": generate_password_hash("5321")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

def generate_frames():
    screen_width, screen_height = pyautogui.size()

    while True:
        time.sleep(10)  # 15 FPS aprox
        screenshot = pyautogui.screenshot()

        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Asegúrate de que la resolución se mantenga igual que la pantalla
        #frame = cv2.resize(frame, (240,426))
        frame = cv2.resize(frame, (480,640))

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        with data_lock:
            data_log.append(len(frame))

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        




@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/data_usage')
@auth.login_required
def data_usage():
    with data_lock:
        bytes_sent = sum(data_log)
    mb_sent = bytes_sent / (1024 * 1024)
    return {'mb_last_minute': round(mb_sent, 2)}

@app.route('/video_feed')
@auth.login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

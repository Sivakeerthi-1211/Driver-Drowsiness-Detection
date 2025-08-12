
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import cv2
import pygame
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

pygame.mixer.init()
pygame.mixer.music.load('alarm.wav')

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye_tree_eyeglasses.xml')

def init_db():
    if not os.path.exists('users.db'):
        conn = sqlite3.connect('users.db')
        conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
        conn.close()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('users.db')
    cursor = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        session['user'] = username
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error='Invalid Credentials')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register_user', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('users.db')
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                 (username, password))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', username=session['user'])

@app.route('/start_detection')
def start_detection():
    sleep_counter = 0
    threshold = 15
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        eyes_detected = False
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            if len(eyes) >= 2:
                eyes_detected = True
                for (ex, ey, ew, eh) in eyes[:2]:
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0,255,0), 2)
        if eyes_detected:
            sleep_counter = 0
        else:
            sleep_counter += 1
        if sleep_counter > threshold:
            cv2.putText(frame, "Drowsy! Wake Up!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            try:
                pygame.mixer.music.play()
            except:
                pass
        cv2.imshow('Driver Drowsiness Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    print("Server starting... Open http://127.0.0.1:5000/")
    app.run(debug=True)

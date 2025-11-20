from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio, db
from app.models import TinNhan, NguoiDung
from datetime import datetime

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        print(f"User {current_user.HoTen} connected.")
        # Join room riêng của user để nhận thông báo cá nhân
        join_room(f"user_{current_user.MaND}")
        
        # Join room theo vai trò (Ví dụ: BacSi, YTa vào room 'medical')
        if current_user.has_role('BacSi') or current_user.has_role('YTa'):
            join_room('medical_team')

@socketio.on('send_message')
def handle_send_message(data):
    """Xử lý tin nhắn chat"""
    msg_content = data.get('message')
    room = data.get('room', 'general')
    
    if current_user.is_authenticated:
        # Lưu tin nhắn vào DB
        new_msg = TinNhan(
            NguoiGui_ID=current_user.MaND,
            NoiDung=msg_content,
            PhongChat=room
        )
        db.session.add(new_msg)
        db.session.commit()

        # Gửi lại cho client
        emit('receive_message', {
            'user': current_user.HoTen,
            'message': msg_content,
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=room)

@socketio.on('trigger_notification')
def handle_notification(data):
    """Gửi thông báo real-time (Ví dụ: Dược sĩ báo hết thuốc)"""
    target_role = data.get('target_role')
    message = data.get('message')
    
    # Logic gửi thông báo tới room cụ thể (cần implement room theo role ở connect)
    emit('receive_notification', {'message': message}, broadcast=True)
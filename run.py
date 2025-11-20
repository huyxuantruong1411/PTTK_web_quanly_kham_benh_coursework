from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # Sử dụng socketio.run thay vì app.run để hỗ trợ WebSocket
    socketio.run(app, debug=True, port=5000)
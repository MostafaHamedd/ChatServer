import socket
import threading
import sqlite3
from datetime import datetime

# Server settings
HOST = '127.0.0.1'
PORT = 42424

# List of connected clients
clients = []  # (client_socket, username)

def connect_db():
    return sqlite3.connect('chat_server.db')

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # Drop existing tables if they exist
    cursor.execute('DROP TABLE IF EXISTS Messages')
    cursor.execute('DROP TABLE IF EXISTS Users')

    # Create Users table
    cursor.execute('''
    CREATE TABLE Users (
        username TEXT PRIMARY KEY NOT NULL,
        connected_at TIMESTAMP NOT NULL,
        disconnected_at TIMESTAMP
    )
    ''')

    # Create Messages table
    cursor.execute('''
    CREATE TABLE Messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (username) REFERENCES Users(username)
    )
    ''')

    conn.commit()
    conn.close()

def create_user(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Users (username, connected_at)
    VALUES (?, ?)
    ON CONFLICT(username) DO UPDATE SET connected_at = excluded.connected_at
    ''', (username, datetime.now()))
    conn.commit()
    conn.close()

def update_user_disconnect(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE Users
    SET disconnected_at = ?
    WHERE username = ?
    ''', (datetime.now(), username))
    conn.commit()
    conn.close()

def save_message(username, message):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Messages (username, message, timestamp)
    VALUES (?, ?, ?)
    ''', (username, message, datetime.now()))
    conn.commit()
    conn.close()

def is_username_taken(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM Users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def notify_clients(message):
    """Send a notification message to all clients."""
    for client, _ in clients:
        client.sendall(message.encode('utf-8'))

def handle_connect(client_socket, username):
    if is_username_taken(username):
        error_message = "ERROR: Username already taken."
        client_socket.sendall(error_message.encode('utf-8'))
        client_socket.close()
        return

    print(f"Client {client_socket.getpeername()} connected with username: {username}")
    clients.append((client_socket, username))

    # Add user to the database
    create_user(username)

    # Notify other clients about the new connection
    join_message = f"{username} has joined the chat."
    notify_clients(join_message)

def handle_disconnect(client_socket, username):
    """Handle a client disconnecting."""
    print(f"Client {client_socket.getpeername()} disconnected.")
    if username:
        clients.remove((client_socket, username))
        update_user_disconnect(username)
        leave_message = f"{username} has left the chat."
        notify_clients(leave_message)

def handle_message(client_socket, username, message):
    """Handle a message from a client."""
    formatted_message = f"{username}: {message}"
    print(formatted_message)
    save_message(username, message)
    notify_clients(formatted_message)

def handle_client(client_socket, client_address):
    """Manage a single client connection."""
    username = None

    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                break

            if data.startswith("CONNECT"):
                username = data[len("CONNECT "):]
                handle_connect(client_socket, username)

            elif data.startswith("DISCONNECT"):
                if username:
                    handle_disconnect(client_socket, username)
                break

            elif data.startswith("MSG"):
                if username:
                    message = data[len("MSG "):]
                    handle_message(client_socket, username, message)

    except Exception as e:
        print(f"Error with client {client_address}: {e}")

    finally:
        if username:
            print(f"Client {client_address} disconnected as {username}")
        client_socket.close()

def server():
    # Set up server and create tables
    create_tables()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Server running on {HOST}:{PORT}")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Client connected: {client_address}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()

        except KeyboardInterrupt:
            print("Server shutting down.")
            break
        except Exception as e:
            print(f"Server error: {e}")

    server_socket.close()

if __name__ == "__main__":
    server()

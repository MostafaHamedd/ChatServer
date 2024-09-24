import socket
import select
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
    cursor.execute('''CREATE TABLE Users (
        username TEXT PRIMARY KEY NOT NULL,
        connected_at TIMESTAMP NOT NULL,
        disconnected_at TIMESTAMP
    )''')

    # Create Messages table
    cursor.execute('''CREATE TABLE Messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (username) REFERENCES Users(username)
    )''')

    conn.commit()
    conn.close()

def create_user(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO Users (username, connected_at)
                      VALUES (?, ?)
                      ON CONFLICT(username) DO UPDATE SET connected_at = excluded.connected_at''',
                   (username, datetime.now()))
    conn.commit()
    conn.close()

def update_user_disconnect(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''UPDATE Users SET disconnected_at = ? WHERE username = ?''',
                   (datetime.now(), username))
    conn.commit()
    conn.close()

def save_message(username, message):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO Messages (username, message, timestamp)
                      VALUES (?, ?, ?)''', (username, message, datetime.now()))
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
        try:
            client.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to client: {e}")

def fetch_last_20_messages():
    """Fetch the last 20 messages from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT username, message, timestamp FROM Messages
                      ORDER BY timestamp DESC LIMIT 20''')
    messages = cursor.fetchall()
    conn.close()
    return messages[::-1]  # Reverse to show them in the correct order (oldest first)

def send_last_20_messages(client_socket):
    """Send the last 20 messages to a newly connected client."""
    messages = fetch_last_20_messages()
    for username, message, timestamp in messages:
        formatted_message = f"{username}: {message}\n"
        client_socket.sendall(formatted_message.encode('utf-8'))
    client_socket.sendall(b'')  # Ensure end of messages

def is_active_user(username):
    """Check if the username is currently connected."""
    for _, active_username in clients:
        if active_username == username:
            return True
    return False

def handle_connect(client_socket, username):
    if is_active_user(username):
        error_message = "ERROR: Username already taken."
        client_socket.sendall(error_message.encode('utf-8'))
        client_socket.close()
        return

    print(f"Client {client_socket.getpeername()} connected with username: {username}")

    if is_username_taken(username):
        print(f"User {username} is rejoining.")
    else:
        create_user(username)

    clients.append((client_socket, username))
    send_last_20_messages(client_socket)

    join_message = f"{username} has joined the chat."
    notify_clients(join_message)

def handle_disconnect(client_socket, username):
    print(f"Client {client_socket.getpeername()} disconnected.")
    try:
        if username:
            clients.remove((client_socket, username))
            update_user_disconnect(username)
            leave_message = f"{username} has left the chat."
            notify_clients(leave_message)
    except Exception as e:
        print(f"Error while handling disconnection: {e}")


def handle_message(client_socket, username, message):
    # Directly use the received message without adding the username again
    formatted_message = message.strip()
    print(formatted_message)  # This will show the message as it is sent by the client
    save_message(username, formatted_message)
    notify_clients(formatted_message)

def server():
    # Set up server and create tables
    create_tables()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server running on {HOST}:{PORT}")

    socket_list = [server_socket]  # Initialize socket_list with the server socket

    while True:
        try:
            read_sockets, _, _ = select.select(socket_list, [], [])
            for notified_socket in read_sockets:
                if notified_socket == server_socket:
                    try:
                        client_socket, client_address = server_socket.accept()
                        print(f"Client connected: {client_address}")
                        socket_list.append(client_socket)

                        # Receive initial connection message from the client
                        data = client_socket.recv(1024).decode('utf-8')
                        if data.startswith("CONNECT"):
                            username = data[len("CONNECT "):]
                            handle_connect(client_socket, username)
                    except Exception as e:
                        print(f"Error accepting connection: {e}")

                else:
                    try:
                        data = notified_socket.recv(1024).decode('utf-8')
                        if data:
                            for client_socket, username in clients:
                                if notified_socket == client_socket:
                                    handle_message(client_socket, username, data)
                        else:
                            # No data means the client has disconnected
                            username = next((u for s, u in clients if s == notified_socket), None)
                            handle_disconnect(notified_socket, username)
                            # Remove the socket from the list
                            if notified_socket in socket_list:
                                socket_list.remove(notified_socket)

                    except Exception as e:
                        # If there's an error while receiving data, handle disconnect
                        username = next((u for s, u in clients if s == notified_socket), None)
                        handle_disconnect(notified_socket, username)
                        # Remove the socket from the list
                        if notified_socket in socket_list:
                            socket_list.remove(notified_socket)

        except KeyboardInterrupt:
            print("Server shutting down.")
            break
        except Exception as e:
            print(f"Server error: {e}")

    server_socket.close()



if __name__ == "__main__":
    server()

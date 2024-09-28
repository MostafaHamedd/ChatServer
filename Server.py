import socket
import sqlite3
from datetime import datetime
import select

# Register adapter and converter for datetime to handle the deprecation warning
def adapt_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def convert_datetime(s):
    return datetime.strptime(s.decode('utf-8'), '%Y-%m-%d %H:%M:%S')

# Register the adapter and converter with sqlite3
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter('timestamp', convert_datetime)

# Server settings
HOST = '127.0.0.1'
PORT = 42424

# List of connected clients
clients = {}  # {client_socket: username}

def connect_db():
    return sqlite3.connect('chat_server.db', detect_types=sqlite3.PARSE_DECLTYPES)

def create_tables():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS Messages')
        cursor.execute('DROP TABLE IF EXISTS Users')

        cursor.execute('''
        CREATE TABLE Users (
            username TEXT PRIMARY KEY NOT NULL,
            connected_at TEXT NOT NULL,
            disconnected_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE Messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES Users(username)
        )
        ''')

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")

def create_user(username):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO Users (username, connected_at)
        VALUES (?, ?)
        ON CONFLICT(username) DO UPDATE SET connected_at = excluded.connected_at
        ''', (username, datetime.now()))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error creating user: {e}")

def update_user_disconnect(username):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE Users
        SET disconnected_at = ?
        WHERE username = ?
        ''', (datetime.now(), username))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error updating user disconnect: {e}")

def save_message(username, message):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO Messages (username, message, timestamp)
        VALUES (?, ?, ?)
        ''', (username, message, datetime.now()))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error saving message: {e}")

def is_username_taken(username):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM Users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except sqlite3.Error as e:
        print(f"Error checking username: {e}")
        return False

def notify_clients(message):
    """Send a notification message to all clients."""
    for client_socket in clients:
        try:
            client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to client: {e}")

def fetch_last_20_messages():
    """Fetch the last 20 messages from the database."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT username, message, timestamp
        FROM Messages
        ORDER BY timestamp DESC
        LIMIT 20
        ''')
        messages = cursor.fetchall()
        conn.close()
        return messages[::-1]  # Reverse to show them in the correct order (oldest first)
    except sqlite3.Error as e:
        print(f"Error fetching last 20 messages: {e}")
        return []


def send_last_20_messages(client_socket):
    """Send the last 20 messages to a newly connected client."""
    try:
        # Get client's IP address and port from the socket
        client_address = client_socket.getpeername()

        messages = fetch_last_20_messages()
        for username, message, timestamp in messages:
            formatted_message = f"{username}: {message}\n"
            # Print each message being sent to the client, including the client's address
            print(f"Sending message to {client_address}: {formatted_message.strip()} at {timestamp}")
            client_socket.sendall(formatted_message.encode('utf-8'))
        client_socket.sendall(b'')  # Ensure end of messages
    except Exception as e:
        print(f"Error sending last 20 messages to {client_address}: {e}")


def handle_connect(client_socket, username):
    try:
        if is_active_user(username):
            error_message = "ERROR: Username already taken."
            client_socket.sendall(error_message.encode('utf-8'))
            return False

        print(f"Client {client_socket.getpeername()} connected with username: {username}")

        if is_username_taken(username):
            print(f"User {username} is rejoining.")
        else:
            create_user(username)

        clients[client_socket] = username
        send_last_20_messages(client_socket)
        notify_clients(f"{username} has joined the chat.")
        return True
    except Exception as e:
        print(f"Error handling connect for {username}: {e}")
        return False

def handle_disconnect(client_socket):
    try:
        username = clients.get(client_socket)
        if username:
            print(f"Client {client_socket.getpeername()} disconnected.")
            del clients[client_socket]
            update_user_disconnect(username)
            notify_clients(f"{username} has left the chat.")
        client_socket.close()
    except Exception as e:
        print(f"Error handling disconnect: {e}")

def handle_message(client_socket, message):
    try:
        username = clients.get(client_socket)
        if username:
            formatted_message = f"{username}: {message}"
            print(formatted_message)
            save_message(username, message)
            notify_clients(formatted_message)
    except Exception as e:
        print(f"Error handling message: {e}")

def is_active_user(username):
    return username in clients.values()

def handle_client(client_socket):
    """Process any data received from the client."""
    try:
        data = client_socket.recv(1024).decode('utf-8').strip()
        if not data:
            handle_disconnect(client_socket)
            return False

        if data.startswith("CONNECT"):
            username = data[len("CONNECT "):]
            if handle_connect(client_socket, username):
                client_socket.sendall("CONNECTED".encode('utf-8'))
            else:
                return False
        elif data.startswith("DISCONNECT"):
            handle_disconnect(client_socket)
            return False
        elif data.startswith("MSG"):
            message = data[len("MSG "):]
            handle_message(client_socket, message)
        else:
            client_socket.sendall("ERROR: Unknown protocol.".encode('utf-8'))
            return False

        return True
    except Exception as e:
        print(f"Error with client {client_socket.getpeername()}: {e}")
        handle_disconnect(client_socket)
        return False

def server():
    try:
        create_tables()

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        server_socket.setblocking(False)

        inputs = [server_socket]
        print(f"Server running on {HOST}:{PORT}")

        while True:
            try:
                readable, _, _ = select.select(inputs, [], [])

                for s in readable:
                    if s is server_socket:
                        try:
                            client_socket, client_address = server_socket.accept()
                            client_socket.setblocking(False)
                            inputs.append(client_socket)
                            print(f"Client connected: {client_address}")
                        except Exception as e:
                            print(f"Error accepting new client: {e}")
                    else:
                        if not handle_client(s):
                            inputs.remove(s)

            except Exception as e:
                print(f"Error in select loop: {e}")

    except KeyboardInterrupt:
        print("Server shutting down.")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    server()

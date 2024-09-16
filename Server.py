import socket
import threading

# Server settings
HOST = '127.0.0.1'
PORT = 42424

# List of connected clients
clients = []  # (client_socket, username)

def is_username_taken(username):
    """Check if the username is already in use."""
    return any(existing_username == username for _, existing_username in clients)

def notify_clients(message):
    """Send a message to all clients except the sender."""
    for client, _ in clients:
        try:
            client.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to a client: {e}")

def handle_connect(client_socket, username):
    if is_username_taken(username):
        # Send error message and close connection
        error_message = "ERROR: Username already taken."
        client_socket.sendall(error_message.encode('utf-8'))
        client_socket.close()
        return

    print(f"Client {client_socket.getpeername()} connected with username: {username}")
    clients.append((client_socket, username))

    # Notify other clients about the new connection
    join_message = f"{username} has joined the chat."
    notify_clients(join_message)

def handle_disconnect(client_socket, username):
    """Handle client disconnection."""
    print(f"Client {client_socket.getpeername()} disconnected.")
    if username:
        clients.remove((client_socket, username))
        leave_message = f"{username} has left the chat."
        notify_clients(leave_message)

def handle_message(client_socket, username, message):
    """Handle incoming message."""
    formatted_message = f"{username}: {message}"
    print(formatted_message)
    notify_clients(formatted_message)

def handle_client(client_socket, client_address):
    """Manage a single client."""
    username = None

    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                break  # Disconnected

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
    # Set up server
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

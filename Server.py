import socket
import threading

# Server parameters
HOST = '127.0.0.1'  # Localhost
PORT = 42424  # Port to listen on

# Global variable to keep track of connected clients
clients = []  # List to store tuples of (client_socket, username)


def handle_connect(client_socket, username):
    """Handle a new connection."""
    print(f"Client {client_socket.getpeername()} connected with username: {username}")

    # Add client to the global list
    clients.append((client_socket, username))

    # Notify other clients about the new connection
    join_message = f"{username} has joined the chat."
    for client, _ in clients:
        if client != client_socket:
            client.sendall(join_message.encode('utf-8'))


def handle_disconnect(client_socket, username):
    """Handle client disconnection."""
    print(f"Client {client_socket.getpeername()} disconnected.")
    if username:
        clients.remove((client_socket, username))
        # Notify other clients about the disconnection
        leave_message = f"{username} has left the chat."
        for client, _ in clients:
            client.sendall(leave_message.encode('utf-8'))


def handle_message(client_socket, username, message):
    """Handle a message from a client."""
    formatted_message = f"{username}: {message}"
    print(formatted_message)  # Print the message on the server side

    # Broadcast the message to all clients
    for client, _ in clients:
        if client != client_socket:
            client.sendall(formatted_message.encode('utf-8'))


def handle_client(client_socket, client_address):
    """Function to handle communication with a single client."""
    username = None

    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                break  # Connection closed

            if data.startswith("CONNECT"):
                # Extract the username
                username = data[len("CONNECT "):]
                handle_connect(client_socket, username)

            elif data.startswith("DISCONNECT"):
                if username:
                    handle_disconnect(client_socket, username)
                break  # Exit the loop

            elif data.startswith("MSG"):
                if username:
                    message = data[len("MSG "):]
                    handle_message(client_socket, username, message)

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")

    finally:
        if username:
            print(f"Client {client_address} disconnected with username: {username}")
        client_socket.close()


def server():
    # Create the socket and set options
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Server listening on {HOST}:{PORT}")

    while True:
        try:
            # Accept a new client connection
            client_socket, client_address = server_socket.accept()
            print(f"Client connected: {client_address}")

            # Start a new thread to handle the client
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

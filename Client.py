import socket
import threading
import argparse
import sys
import os

# Message types:
# Chat: username: message
# Connect: CONNECT username
# Disconnect: DISCONNECT username
# Error: ERROR: <details>

def clear_console():
    """Clear the screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_messages(messages):
    """Show chat messages and prompt."""
    clear_console()
    for message in messages:
        sys.stdout.write(f"{message}\n")
    sys.stdout.write('>> ')
    sys.stdout.flush()

def receive_messages(sock, messages):
    """Receive and display messages."""
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if data:
                messages.append(data)
                display_messages(messages)
            else:
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def client(host, port, username):
    """Run the chat client."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print(f"Failed to connect to {host}:{port}. Check if the server is running.")
        return
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return

    # Send CONNECT command
    client_socket.sendall(f"CONNECT {username}".encode('utf-8'))

    messages = []

    # Start receiving messages
    threading.Thread(target=receive_messages, args=(client_socket, messages), daemon=True).start()

    display_messages(messages)

    while True:
        try:
            message = input().strip()
            if message:
                # Send message
                client_socket.sendall(f"MSG {message}".encode('utf-8'))
                messages.append(f"{username}: {message}")
                display_messages(messages)
        except KeyboardInterrupt:
            print("\nClient shutting down.")
            client_socket.sendall(f"DISCONNECT {username}".encode('utf-8'))
            break
        except Exception as e:
            print(f"Error sending message: {e}")

    client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('username', type=str, help='Chat username')
    parser.add_argument('host', type=str, help='Server host')
    parser.add_argument('port', type=int, help='Server port')

    args = parser.parse_args()

    client(args.host, args.port, args.username)

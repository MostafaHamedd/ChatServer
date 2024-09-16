import socket
import threading
import argparse
import sys
import os

# Message Format:

# Chat Message: username: message
# Connection Message: CONNECT username
# Disconnection Message: DISCONNECT username
# Error Message: ERROR: <error details>




def clear_console():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_messages(messages):
    """Display all chat messages and the prompt."""
    clear_console()
    for message in messages:
        sys.stdout.write(f"{message}\n")
    sys.stdout.write('>> ')
    sys.stdout.flush()

def receive_messages(sock, messages):
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if data:
                messages.append(data)
                # Clear the console and display messages
                display_messages(messages)
            else:
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def client(host, port, username):
    # Create TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print(f"Failed to connect to {host}:{port}. Make sure the server is running.")
        return
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return

    # Send the CONNECT command with the username
    client_socket.sendall(f"CONNECT {username}".encode('utf-8'))

    # List to keep all messages
    messages = []

    # Start receiving messages in a separate thread
    threading.Thread(target=receive_messages, args=(client_socket, messages), daemon=True).start()

    # Display initial messages with prompt
    display_messages(messages)

    while True:
        try:
            # Read the user input
            message = input().strip()
            if message:
                # Format the message with the MSG command
                formatted_message = f"MSG {message}"
                # Send the formatted message to the server
                client_socket.sendall(formatted_message.encode('utf-8'))
                # Add and display the sent message
                messages.append(f"{username}: {message}")
                display_messages(messages)
        except KeyboardInterrupt:
            print("\nClient shutting down.")
            # Send DISCONNECT command
            client_socket.sendall(f"DISCONNECT {username}".encode('utf-8'))
            break
        except Exception as e:
            print(f"Error sending message: {e}")

    client_socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Group Chat Client')
    parser.add_argument('username', type=str, help='Username for the chat')
    parser.add_argument('host', type=str, help='Host to connect to')
    parser.add_argument('port', type=int, help='Port number to connect to')

    args = parser.parse_args()

    client(args.host, args.port, args.username)

import socket
import threading
import argparse
import sys
import os


def clear_console():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def display_messages(messages):
    """Display all chat messages and keep the input prompt."""
    clear_console()  # Clear the screen before displaying messages
    for message in messages:
        sys.stdout.write(f"{message}\n")
    sys.stdout.write('>> ')
    sys.stdout.flush()


def receive_messages(sock, messages):
    """Receive messages from the server and display them."""
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if data:
                # Check if the message is a connection confirmation
                if "CONNECTED" not in data:
                    # Only append other messages to the list
                    messages.append(data)
                    display_messages(messages)
            else:
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def setupChatView():
    clear_console()  # Clear the console upon connection
    sys.stdout.write('>> ')
    sys.stdout.flush()

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

    # Wait for a response from the server
    response = client_socket.recv(1024).decode('utf-8').strip()


    # This will store all received messages
    messages = []

    # Start thread to receive messages from the server
    threading.Thread(target=receive_messages, args=(client_socket, messages), daemon=True).start()

    while True:
        try:
            # Get user input
            message = input('>> ').strip()
            if message:
                # Send the message to the server
                client_socket.sendall(f"MSG {message}".encode('utf-8'))
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

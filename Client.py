import socket
import select
import sys
import os


def clear_console():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def display_messages(messages, current_input=''):
    """Display all chat messages and keep the input prompt with the user's current typed input."""
    clear_console()  # Clear the screen before displaying messages
    for message in messages:
        sys.stdout.write(f"{message.rstrip()}\n")  # Remove trailing newlines before adding one

    # Re-display the current input
    sys.stdout.write(f'>> {current_input}')
    sys.stdout.flush()



def client(host, port, username):

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

    # Store all received messages
    messages = []

    # Reference to the current input buffer
    current_input = ''
    global_input = ''
    # Use select to monitor both the server socket and stdin (user input)
    while True:
        try:

            # `select` to wait for either socket or user input (stdin)
            read_sockets, _, _ = select.select([client_socket, sys.stdin], [], [])

            for sock in read_sockets:
                print(global_input)
                if sock == client_socket:
                    # Receive messages from the server
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        # Server closed connection
                        print("Connection closed by server.")
                        return
                    if not data.startswith("CONNECTED"):
                        # Append the message and redisplay everything
                        messages.append(data)
                        display_messages(messages, current_input)

                elif sock == sys.stdin:
                    # Handle user input
                    current_input = sys.stdin.readline().strip()  # Capture the user input
                   # print("HENNAAAa" + current_input)

                    # Send the message to the server if there's input
                    if current_input:
                        client_socket.sendall(f"MSG {current_input}".encode('utf-8'))
                        current_input = ''  # Clear input after sending
                        display_messages(messages)  # Redisplay messages after sending
                    else:
                     global_input = current_input
        except KeyboardInterrupt:
            print("\nClient shutting down.")
            client_socket.sendall(f"DISCONNECT {username}".encode('utf-8'))
            break
        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('username', type=str, help='Chat username')
    parser.add_argument('host', type=str, help='Server host')
    parser.add_argument('port', type=int, help='Server port')

    args = parser.parse_args()

    client(args.host, args.port, args.username)

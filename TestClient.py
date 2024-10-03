import socket
import select
import time
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


def test_client(host, port, username, message_count=100000, test_duration=60*5):
    """
    Test client that connects to the server and sends messages as fast as possible for a fixed duration.
    Also listens for incoming messages and displays them.

    :param host: The server host.
    :param port: The server port.
    :param username: The username for this client.
    :param message_count: The maximum number of messages to send.
    :param test_duration: The time duration (in seconds) to run the test.
    """
    # Connect to the server
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

    # Start the timer
    start_time = time.time()
    end_time = start_time + test_duration
    messages_sent = 0
    current_input = ''

    try:
        while time.time() < end_time and messages_sent < message_count:
            # Use select to wait for either socket or user input (stdin)
            read_sockets, _, _ = select.select([client_socket], [], [], 0.1)

            # Handle incoming data from the server
            for sock in read_sockets:
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

            # Send message to the server
            message = f"Test message {messages_sent} from {username}"
            client_socket.sendall(f"MSG {message}".encode('utf-8'))
            messages_sent += 1

            # Display updated messages after sending
            display_messages(messages, current_input)

            # Optional: Slight delay to avoid overwhelming the server
            time.sleep(0.00001)

        # Calculate total time and messages per second
        total_time = time.time() - start_time
        messages_per_second = messages_sent / total_time
        print(f"Sent {messages_sent} messages in {total_time:.2f} seconds ({messages_per_second:.2f} messages/second)")

    except KeyboardInterrupt:
        print("\nTest client interrupted.")
    except Exception as e:
        print(f"Error during message sending: {e}")
    finally:
        client_socket.sendall(f"DISCONNECT {username}".encode('utf-8'))
        client_socket.close()
        print("Test client disconnected.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test Client')
    parser.add_argument('username', type=str, help='Username for this client')
    parser.add_argument('host', type=str, help='Server host')
    parser.add_argument('port', type=int, help='Server port')
    parser.add_argument('--message_count', type=int, default=100000,
                        help='Number of messages to send (default: 100000)')
    parser.add_argument('--test_duration', type=int, default=60*5, help='Duration of the test in seconds (default: 60)')

    args = parser.parse_args()

    test_client(args.host, args.port, args.username, args.message_count, args.test_duration)

import subprocess
import time


def run_test_with_clients(num_clients, host, port, message_count, test_duration):
    """
    Run multiple test clients in parallel and measure performance.

    :param num_clients: The number of clients to run.
    :param host: The server host.
    :param port: The server port.
    :param message_count: The number of messages each client should send.
    :param test_duration: How long to run each client (in seconds).
    :return: Total number of messages sent by all clients.
    """
    processes = []
    total_messages_sent = 0

    # Start the clients
    for i in range(num_clients):
        username = f'testclient_{i + 1}'
        command = ['python', 'testClient.py', username, host, str(port), '--message_count', str(message_count),
                   '--test_duration', str(test_duration)]
        p = subprocess.Popen(command)
        processes.append(p)

    # Wait for all clients to finish
    for p in processes:
        p.wait()

    # You may want to capture the output of each client and log it
    # This part depends on how you're collecting the data, whether through logs or direct output capture
    print(f"Completed run with {num_clients} clients")


def main():
    host = 'localhost'
    port = 42424
    message_count = 100000
    test_duration = 60  # seconds

    # Define the number of clients to test with (1, 2, 5, 10, 20, 50, 100, 200)
    client_counts = [1, 2, 5, 10, 20, 50, 100, 200]

    for num_clients in client_counts:
        print(f"Running test with {num_clients} clients...")
        start_time = time.time()

        run_test_with_clients(num_clients, host, port, message_count, test_duration)

        # Log how long the test took
        end_time = time.time()
        duration = end_time - start_time
        print(f"Test with {num_clients} clients took {duration:.2f} seconds")


if __name__ == '__main__':
    main()

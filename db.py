import sqlite3

def create_tables():
    # Connect to SQLite database
    conn = sqlite3.connect('chat_server.db')
    cursor = conn.cursor()

    # Drop existing tables if they exist
    cursor.execute('DROP TABLE IF EXISTS Messages')
    cursor.execute('DROP TABLE IF EXISTS Users')

    # Create Users table
    cursor.execute('''
    CREATE TABLE Users (
        username TEXT PRIMARY KEY NOT NULL,
        connected_at TIMESTAMP NOT NULL,
        disconnected_at TIMESTAMP
    )
    ''')

    # Create Messages table
    cursor.execute('''
    CREATE TABLE Messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (username) REFERENCES Users(username)
    )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# Call the function to create the tables
create_tables()

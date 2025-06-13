"""
Database Creation Script

Author: devsen
"""

import sqlite3

def create_database():
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    
    # Create user_titles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_titles (
            id INTEGER PRIMARY KEY,
            title TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Create users table with foreign key to user_titles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            title_id INTEGER,
            FOREIGN KEY (title_id) REFERENCES user_titles(id)
        )
    ''')
    
    # Insert sample title data
    cursor.executemany(
        'INSERT OR IGNORE INTO user_titles (id, title) VALUES (?, ?)',
        [(1, 'Manager'), (2, 'Supervisor'), (3, 'Staff')]
    )
    
    # Insert sample user data with title references
    cursor.executemany(
        'INSERT OR IGNORE INTO users (name, age, title_id) VALUES (?, ?, ?)',
        [
            ('Alice', 30, 1),    # Alice is Manager
            ('Bob', 25, 3),      # Bob is Staff
            ('Charlie', 35, 2)   # Charlie is Supervisor
        ]
    )
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database 'example.db' created successfully with sample data!")

if __name__ == "__main__":
    create_database()

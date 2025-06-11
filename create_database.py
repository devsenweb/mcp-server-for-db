"""
Database Creation Script

Author: devsen
"""

import sqlite3

def create_database():
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER
        )
    ''')
    
    # Insert sample data
    cursor.executemany(
        'INSERT OR IGNORE INTO users (name, age) VALUES (?, ?)',
        [('Alice', 30), ('Bob', 25)]
    )
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database 'example.db' created successfully with sample data!")

if __name__ == "__main__":
    create_database()

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

app = Flask(__name__)
DATABASE = 'example.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables name-based access to columns
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Get users with their titles (using LEFT JOIN to include users without titles)
    users = conn.execute('''
        SELECT u.id, u.name, u.age, ut.title 
        FROM users u 
        LEFT JOIN user_titles ut ON u.title_id = ut.id
        ORDER BY u.id
    ''').fetchall()
    
    # Get all available titles
    titles = conn.execute('SELECT * FROM user_titles').fetchall()
    
    conn.close()
    return render_template('index.html', users=users, titles=titles)

@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    age = request.form['age']
    title_id = request.form['title_id']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO users (name, age, title_id) VALUES (?, ?, ?)',
                (name, age, title_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    Path('templates').mkdir(exist_ok=True)
    app.run(debug=True)

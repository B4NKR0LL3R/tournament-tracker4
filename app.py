
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Initialize database function
def initialize_database():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            buy_in REAL NOT NULL,
            prize REAL NOT NULL,
            site TEXT NOT NULL,
            type TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Call database initialization at startup
initialize_database()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                         (username, email, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username or email already exists. Please try a different one."
        finally:
            conn.close()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password, user['password']):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        return "Invalid username or password. Please try again."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/view-tournaments')
def view_tournaments():
    conn = get_db_connection()
    tournaments = conn.execute('SELECT * FROM tournaments').fetchall()
    conn.close()

    # Generate HTML table dynamically
    html = '<h1>All Tournaments</h1><table border="1"><tr><th>ID</th><th>Name</th><th>Buy-In</th><th>Prize</th><th>Site</th><th>Type</th></tr>'
    for tournament in tournaments:
        html += f'<tr><td>{tournament["id"]}</td><td>{tournament["name"]}</td><td>{tournament["buy_in"]}</td><td>{tournament["prize"]}</td><td>{tournament["site"]}</td><td>{tournament["type"]}</td></tr>'
    html += '</table>'
    html += '<a href="/">Back to Dashboard</a>'
    return html

@app.route('/add-tournament', methods=['GET', 'POST'])
def add_tournament():
    if request.method == 'POST':
        tournament_name = request.form['tournament_name']
        buy_in = float(request.form['buy_in'])
        prize = float(request.form['prize'])
        site = request.form['site']
        tournament_type = request.form['type']

        # Save data into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO tournaments (name, buy_in, prize, site, type) VALUES (?, ?, ?, ?, ?)',
                     (tournament_name, buy_in, prize, site, tournament_type))
        conn.commit()
        conn.close()

        return f"<h1>Tournament Added!</h1><p>Name: {tournament_name} | Buy-In: {buy_in} | Prize: {prize} | Site: {site} | Type: {tournament_type}</p>"
    
    return '''
        <h1>Add New Tournament</h1>
        <form method="post">
            Tournament Name: <input type="text" name="tournament_name" required><br>
            Buy-In: <input type="number" step="0.01" name="buy_in" required><br>
            Prize: <input type="number" step="0.01" name="prize" required><br>
            Site: 
            <select name="site" required>
                <option value="PokerStars">PokerStars</option>
                <option value="888Poker">888Poker</option>
                <option value="ACR">ACR</option>
                <option value="Winamax">Winamax</option>
                <option value="Unibet">Unibet</option>
                <option value="ClubGG">ClubGG</option>
                <option value="WPTGlobal">WPTGlobal</option>
                <option value="OlyBet">OlyBet</option>
                <option value="CoinPoker">CoinPoker</option>
            </select><br>
            Type: 
            <select name="type" required>
                <option value="MTT">MTT</option>
                <option value="Spin">Spin</option>
            </select><br>
            <button type="submit">Add Tournament</button>
        </form>
    '''

@app.route('/statistics')
def statistics():
    return "<h1>Statistics</h1><p>This page will show stats and graphs.</p>"

if __name__ == '__main__':
    app.run(debug=True)

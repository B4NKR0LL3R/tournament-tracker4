
from flask import Flask, render_template, request, redirect, url_for, session, flash
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

    return render_template('view_tournaments.html', tournaments=tournaments)

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

        flash(f"Tournament '{tournament_name}' added successfully!")
        return redirect(url_for('view_tournaments'))
    
    sites = ["PokerStars", "888Poker", "ACR", "Winamax", "Unibet", "ClubGG", "WPTGlobal", "OlyBet", "CoinPoker", "Betsafe", "TigerGaming", "Optibet"]
    return render_template('add_tournament.html', sites=sites)

@app.route('/statistics')
def statistics():
    conn = get_db_connection()
    tournaments = conn.execute('SELECT * FROM tournaments').fetchall()
    conn.close()

    total_tournaments = len(tournaments)
    total_buy_in = sum(t['buy_in'] for t in tournaments)
    total_prize = sum(t['prize'] for t in tournaments)
    total_profit = total_prize - total_buy_in
    avg_buy_in = total_buy_in / total_tournaments if total_tournaments > 0 else 0
    roi = (total_profit / total_buy_in) * 100 if total_buy_in > 0 else 0

    mtt_count = sum(1 for t in tournaments if t['type'] == 'MTT')
    spin_count = sum(1 for t in tournaments if t['type'] == 'Spin')

    return render_template('statistics.html', total_tournaments=total_tournaments, total_profit=total_profit,
                           avg_buy_in=avg_buy_in, roi=roi, mtt_count=mtt_count, spin_count=spin_count)

if __name__ == '__main__':
    app.run(debug=True)

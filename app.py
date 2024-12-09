
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import sqlite3
import bcrypt
from datetime import datetime
import csv

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Initialize database function
def initialize_database():
    conn = sqlite3.connect('database.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS tournaments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        buy_in REAL NOT NULL,
                        prize REAL NOT NULL,
                        site TEXT NOT NULL,
                        type TEXT NOT NULL,
                        date_played DATE NOT NULL)''')
    conn.commit()
    conn.close()

initialize_database()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db_connection()
        tournaments = conn.execute('SELECT * FROM tournaments').fetchall()
        conn.close()
        total_tournaments = len(tournaments)
        total_profit = sum(t['prize'] - t['buy_in'] for t in tournaments)
        roi = round((total_profit / sum(t['buy_in'] for t in tournaments)) * 100, 2) if total_tournaments > 0 else 0
        return render_template('index.html', total_tournaments=total_tournaments, total_profit=round(total_profit, 2), roi=roi)
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
            flash("Username or email already exists!")
            return redirect(url_for('register'))
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
        flash("Invalid username or password!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/view-tournaments')
def view_tournaments():
    tournament_type = request.args.get('type')
    site = request.args.get('site')
    conn = get_db_connection()
    query = 'SELECT * FROM tournaments WHERE 1=1'
    params = []
    if tournament_type:
        query += ' AND type = ?'
        params.append(tournament_type)
    if site:
        query += ' AND site = ?'
        params.append(site)
    tournaments = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('view_tournaments.html', tournaments=tournaments)

@app.route('/add-tournament', methods=['GET', 'POST'])
def add_tournament():
    if request.method == 'POST':
        name = request.form['tournament_name']
        buy_in = float(request.form['buy_in'])
        prize = float(request.form['prize'])
        site = request.form['site']
        t_type = request.form['type']
        date_played = request.form['date_played']
        conn = get_db_connection()
        conn.execute('INSERT INTO tournaments (name, buy_in, prize, site, type, date_played) VALUES (?, ?, ?, ?, ?, ?)',
                     (name, buy_in, prize, site, t_type, date_played))
        conn.commit()
        conn.close()
        flash("Tournament added successfully!")
        return redirect(url_for('view_tournaments'))
    sites = ["PokerStars", "888Poker", "ACR", "Winamax", "Unibet", "ClubGG", "WPTGlobal", "OlyBet", "CoinPoker", "Betsafe", "TigerGaming", "Optibet"]
    return render_template('add_tournament.html', sites=sites)

@app.route('/statistics')
def statistics():
    conn = get_db_connection()
    tournaments = conn.execute('SELECT * FROM tournaments').fetchall()
    conn.close()

    # Initialize default values
    total_tournaments = len(tournaments)
    total_buy_in = sum(t['buy_in'] for t in tournaments) if total_tournaments > 0 else 0
    total_prize = sum(t['prize'] for t in tournaments) if total_tournaments > 0 else 0
    total_profit = total_prize - total_buy_in
    roi = round((total_profit / total_buy_in) * 100, 2) if total_buy_in > 0 else 0
    itm_count = sum(1 for t in tournaments if t['prize'] > t['buy_in'])
    itm_percentage = round((itm_count / total_tournaments) * 100, 2) if total_tournaments > 0 else 0
    avg_buy_in = round(total_buy_in / total_tournaments, 2) if total_tournaments > 0 else 0

    # Filter MTTs and Spins
    mtt_tournaments = [t for t in tournaments if t['type'] == 'MTT']
    spin_tournaments = [t for t in tournaments if t['type'] == 'Spin']

    mtt_profit = round(sum(t['prize'] - t['buy_in'] for t in mtt_tournaments), 2) if mtt_tournaments else 0
    mtt_roi = round((mtt_profit / sum(t['buy_in'] for t in mtt_tournaments)) * 100, 2) if mtt_tournaments else 0
    spin_profit = round(sum(t['prize'] - t['buy_in'] for t in spin_tournaments), 2) if spin_tournaments else 0
    spin_roi = round((spin_profit / sum(t['buy_in'] for t in spin_tournaments)) * 100, 2) if spin_tournaments else 0

    return render_template(
        'statistics.html',
        total_tournaments=total_tournaments,
        total_profit=round(total_profit, 2),
        roi=roi,
        itm_percentage=itm_percentage,
        avg_buy_in=avg_buy_in,
        mtt_tournaments=len(mtt_tournaments),
        mtt_profit=mtt_profit,
        mtt_roi=mtt_roi,
        spin_tournaments=len(spin_tournaments),
        spin_profit=spin_profit,
        spin_roi=spin_roi
    )

@app.route('/export')
def export():
    conn = get_db_connection()
    tournaments = conn.execute('SELECT * FROM tournaments').fetchall()
    conn.close()
    def generate():
        data = [("ID", "Name", "Buy-In", "Prize", "Site", "Type", "Date Played")]
        data += [(t["id"], t["name"], t["buy_in"], t["prize"], t["site"], t["type"], t["date_played"]) for t in tournaments]
        for row in data:
            yield ','.join(map(str, row)) + '\n'
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=tournaments.csv"})

if __name__ == '__main__':
    app.run(debug=True)

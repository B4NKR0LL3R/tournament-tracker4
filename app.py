
from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/add-tournament', methods=['GET', 'POST'])
def add_tournament():
    sites = ['Pokerstars', '888poker', 'ACR', 'Tigergaming', 'Betsafe', 'Optibet', 'Olybet', 'Unibet', 'ClubGG', 'WPTGlobal']
    if request.method == 'POST':
        name = request.form['name']
        buy_in = float(request.form['buy_in'])
        prize = float(request.form['prize'])
        site = request.form['site']
        tournament_type = request.form['type']
        date_played = request.form['date_played']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO tournaments (name, buy_in, prize, site, type, date_played) VALUES (?, ?, ?, ?, ?, ?)',
            (name, buy_in, prize, site, tournament_type, date_played)
        )
        conn.commit()
        conn.close()
        return redirect('/view-tournaments')
    return render_template('add_tournament.html', sites=sites)

@app.route('/view-tournaments')
def view_tournaments():
    conn = get_db_connection()
    tournaments = conn.execute('SELECT * FROM tournaments').fetchall()
    conn.close()
    return render_template('view_tournaments.html', tournaments=tournaments)

@app.route('/statistics')
def statistics():
    conn = get_db_connection()
    tournaments = conn.execute('SELECT * FROM tournaments').fetchall()
    conn.close()

    mtt_profit = sum(t['prize'] - t['buy_in'] for t in tournaments if t['type'] == 'MTT')
    spin_profit = sum(t['prize'] - t['buy_in'] for t in tournaments if t['type'] == 'Spin')

    return render_template('statistics.html', mtt_profit=mtt_profit, spin_profit=spin_profit)

if __name__ == '__main__':
    app.run(debug=True)

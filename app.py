
from flask import Flask, render_template, request, redirect
import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-tournament', methods=['GET', 'POST'])
def add_tournament():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        buy_in = float(request.form['buy_in'])
        prize = float(request.form['prize'])
        site = request.form['site']
        tournament_type = request.form['type']

        conn.execute(
            'INSERT INTO tournaments (name, buy_in, prize, site, type) VALUES (?, ?, ?, ?, ?)',
            (name, buy_in, prize, site, tournament_type)
        )
        conn.commit()
        conn.close()
        return redirect('/view-tournaments')
    return render_template('add_tournament.html')

@app.route('/view-tournaments')
def view_tournaments():
    conn = get_db_connection()
    tournaments = conn.execute('SELECT * FROM tournaments').fetchall()
    conn.close()
    return render_template('view_tournaments.html', tournaments=tournaments)

@app.route('/statistics')
def statistics():
    conn = get_db_connection()
    try:
        tournaments = conn.execute('SELECT * FROM tournaments').fetchall()

        time_labels = []
        mtt_profit_data = []
        spin_profit_data = []

        total_profit = 0
        total_tournaments = len(tournaments)
        itm_count = 0
        total_buy_in = 0
        mtt_profit = 0
        spin_profit = 0
        mtt_count = 0
        spin_count = 0

        for tournament in tournaments:
            total_profit += tournament['prize'] - tournament['buy_in']
            total_buy_in += tournament['buy_in']
            itm_count += 1 if tournament['prize'] > 0 else 0
            time_labels.append(tournament['date'] if 'date' in tournament.keys() else "")
            if tournament['type'] == 'MTT':
                mtt_profit += tournament['prize'] - tournament['buy_in']
                mtt_count += 1
                mtt_profit_data.append(mtt_profit)
            elif tournament['type'] == 'Spin':
                spin_profit += tournament['prize'] - tournament['buy_in']
                spin_count += 1
                spin_profit_data.append(spin_profit)

        roi = (total_profit / total_buy_in * 100) if total_buy_in > 0 else 0
        itm_percentage = (itm_count / total_tournaments * 100) if total_tournaments > 0 else 0
        avg_buy_in = (total_buy_in / total_tournaments) if total_tournaments > 0 else 0

        return render_template(
            'statistics.html',
            total_tournaments=total_tournaments,
            total_profit=round(total_profit, 2),
            roi=round(roi, 2),
            itm_percentage=round(itm_percentage, 2),
            avg_buy_in=round(avg_buy_in, 2),
            mtt_tournaments=mtt_count,
            mtt_profit=round(mtt_profit, 2),
            mtt_roi=round((mtt_profit / total_buy_in * 100) if total_buy_in > 0 else 0, 2),
            spin_tournaments=spin_count,
            spin_profit=round(spin_profit, 2),
            spin_roi=round((spin_profit / total_buy_in * 100) if total_buy_in > 0 else 0, 2),
            time_labels=time_labels,
            mtt_profit_data=mtt_profit_data,
            spin_profit_data=spin_profit_data
        )
    except Exception as e:
        logging.error(f"Error in statistics route: {e}")
        return "Internal Server Error", 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)

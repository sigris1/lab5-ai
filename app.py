import sqlite3
import string
import random
from flask import Flask, request, jsonify, redirect, abort

app = Flask(__name__)
DB_NAME = "urls.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                long_url TEXT UNIQUE NOT NULL,
                short_code TEXT UNIQUE NOT NULL
            )
        """)


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    if not data or 'url' not in data or not isinstance(data['url'], str):
        return jsonify({"error": "Invalid URL"}), 400

    long_url = data['url']
    conn = get_db()
    try:
        existing = conn.execute("SELECT short_code FROM urls WHERE long_url = ?", (long_url,)).fetchone()
        if existing:
            return jsonify({"short_url": f"http://localhost:5000/{existing['short_code']}"}), 200

        chars = string.ascii_letters + string.digits
        short_code = ''.join(random.choices(chars, k=6))
        conn.execute("INSERT INTO urls (long_url, short_code) VALUES (?, ?)", (long_url, short_code))
        conn.commit()
        return jsonify({"short_url": f"http://localhost:5000/{short_code}"}), 201
    finally:
        conn.close()


@app.route('/<short_code>')
def redirect_url(short_code):
    conn = get_db()
    try:
        row = conn.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,)).fetchone()
        if not row:
            abort(404)
        return redirect(row['long_url'])
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
import sqlite3
import string
import secrets
import os
from flask import Flask, request, jsonify, redirect, abort

app = Flask(__name__)
app.config['DATABASE'] = os.environ.get('DATABASE_PATH', 'urls.db')


def init_db():
    db_path = app.config['DATABASE']
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                long_url TEXT UNIQUE NOT NULL,
                short_code TEXT UNIQUE NOT NULL
            )
        """)


def get_db():
    db_path = app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    if not data or 'url' not in data or not isinstance(data['url'], str):
        return jsonify({"error": "Invalid URL"}), 400

    long_url = data['url'].strip()
    if not long_url:
        return jsonify({"error": "Invalid URL"}), 400

    conn = get_db()
    try:
        existing = conn.execute("SELECT short_code FROM urls WHERE long_url = ?", (long_url,)).fetchone()
        if existing:
            return jsonify({"short_url": f"http://localhost:5000/{existing['short_code']}"}), 200

        chars = string.ascii_letters + string.digits
        max_retries = 10
        for _ in range(max_retries):
            short_code = ''.join(secrets.choice(chars) for _ in range(6))
            try:
                conn.execute("INSERT INTO urls (long_url, short_code) VALUES (?, ?)", (long_url, short_code))
                conn.commit()
                return jsonify({"short_url": f"http://localhost:5000/{short_code}"}), 201
            except sqlite3.IntegrityError:
                continue

        return jsonify({"error": "Failed to generate unique code"}), 500
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
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode)
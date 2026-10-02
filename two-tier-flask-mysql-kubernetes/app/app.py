import os
import time

import pymysql
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "flaskuser"),
    "password": os.getenv("MYSQL_PASSWORD", "flaskpass"),
    "database": os.getenv("MYSQL_DB", "flaskdb"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def init_db(retries=30, delay=2):
    """Create the table. Retry because MySQL may still be starting."""
    for attempt in range(1, retries + 1):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        content VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            conn.commit()
            conn.close()
            print("Database initialised")
            return
        except pymysql.MySQLError as exc:
            print(f"DB not ready (attempt {attempt}/{retries}): {exc}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to MySQL")


@app.route("/")
def index():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC")
        messages = cur.fetchall()
    conn.close()
    return render_template("index.html", messages=messages)


@app.route("/add", methods=["POST"])
def add():
    content = request.form.get("content", "").strip()
    if content:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (content,))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


@app.route("/health")
def health():
    """Liveness: app process is up."""
    return jsonify(status="ok"), 200


@app.route("/ready")
def ready():
    """Readiness: app can reach the database."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        return jsonify(status="ready"), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify(status="not ready", error=str(exc)), 503


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

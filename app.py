from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

app = Flask(__name__)

# Get the folder where app.py is located
BASE_DIR = Path(__file__).resolve().parent

# SQLite database path
DATABASE = BASE_DIR / "database.db"


def get_db_connection():
    """
    Create and return a connection to the SQLite database.
    """
    connection = sqlite3.connect(DATABASE)

    # Allows us to access columns using column names
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    """
    Create the users table if it does not already exist.
    """
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def get_all_users():
    """
    Fetch all users from the database.
    """
    connection = get_db_connection()

    users = connection.execute(
        "SELECT * FROM users ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return users


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Home page.

    GET  -> Display the form and existing users.
    POST -> Save a new user to the database.
    """

    message = None

    if request.method == "POST":

        # Get form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        # Basic validation
        if not name or not email or not phone:
            message = "All fields are required."

            users = get_all_users()

            return render_template(
                "index.html",
                users=users,
                message=message
            )

        # Insert user into database
        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO users (name, email, phone)
            VALUES (?, ?, ?)
            """,
            (name, email, phone)
        )

        connection.commit()
        connection.close()

        # Redirect after successful insertion
        return redirect(url_for("index"))

    # Fetch users for display
    users = get_all_users()

    return render_template(
        "index.html",
        users=users,
        message=message
    )


if __name__ == "__main__":
    # Create database/table before starting the application
    init_db()

    # Start Flask development server
    app.run(debug=True)
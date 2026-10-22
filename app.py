import os
import sqlite3
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


# --------------------------------------------------
# 1. Create Flask application
# --------------------------------------------------

app = Flask(__name__)

# Development key only. Configure a secure environment variable
# before deploying this application.
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-only-change-this-secret-key"
)

# Find the project folder and database file
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"


# --------------------------------------------------
# 2. Connect to SQLite database
# --------------------------------------------------

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# --------------------------------------------------
# 3. Initialize database tables
# --------------------------------------------------

def init_db():
    connection = get_db_connection()

    try:
        # Task 2: Authentication accounts
        connection.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

        # Task 1: User management records
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        """)

        connection.commit()

    finally:
        connection.close()


# --------------------------------------------------
# 4. Home page - FIX FOR THE 404 ERROR
# --------------------------------------------------

@app.route("/")
def home():
    """
    Home page.

    If the user is logged in, open the dashboard.
    Otherwise, redirect to the login page.
    """

    if session.get("user"):
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# --------------------------------------------------
# 5. User registration
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    # Logged-in users do not need to register again
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get("password", "")

        confirm_password = request.form.get(
            "confirm_password", ""
        )

        # Validate the input
        if not username or not password or not confirm_password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(username) > 50:
            flash(
                "Username must be 50 characters or fewer.",
                "error",
            )
            return render_template("register.html")

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error",
            )
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        # Hash the password before storing it
        password_hash = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO accounts (username, password_hash)
                VALUES (?, ?)
                """,
                (username, password_hash),
            )

            connection.commit()

        except sqlite3.IntegrityError:
            flash("That username already exists.", "error")
            return render_template("register.html")

        finally:
            connection.close()

        flash(
            "Account created successfully. Please log in.",
            "success",
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# --------------------------------------------------
# 6. User login
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get("password", "")

        if not username or not password:
            flash(
                "Enter your username and password.",
                "error",
            )
            return render_template("login.html")

        connection = get_db_connection()

        try:
            account = connection.execute(
                """
                SELECT id, username, password_hash
                FROM accounts
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        finally:
            connection.close()

        # Verify the entered password
        if (
            account
            and check_password_hash(
                account["password_hash"],
                password,
            )
        ):
            # Start a new authenticated session
            session.clear()
            session["user"] = account["username"]

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


# --------------------------------------------------
# 7. Retrieve Task 1 user records
# --------------------------------------------------

def get_all_users():
    connection = get_db_connection()

    try:
        users = connection.execute(
            "SELECT * FROM users ORDER BY id DESC"
        ).fetchall()

        return users

    finally:
        connection.close()


# --------------------------------------------------
# 8. Protected dashboard and Task 1 functionality
# --------------------------------------------------

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    # Prevent access without authentication
    if not session.get("user"):
        flash(
            "Please log in to access the dashboard.",
            "error",
        )
        return redirect(url_for("login"))

    if request.method == "POST":

        # Get Task 1 form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        # Validate user details
        if not name or not email or not phone:
            flash(
                "Please fill in all user details.",
                "error",
            )

        elif (
            len(name) > 100
            or len(email) > 254
            or len(phone) > 30
        ):
            flash(
                "One or more fields exceed the allowed length.",
                "error",
            )

        elif (
            "@" not in email
            or "." not in email.rsplit("@", 1)[-1]
        ):
            flash("Enter a valid email address.", "error")

        else:
            connection = get_db_connection()

            try:
                connection.execute(
                    """
                    INSERT INTO users (name, email, phone)
                    VALUES (?, ?, ?)
                    """,
                    (name, email, phone),
                )

                connection.commit()

                flash(
                    "User added successfully.",
                    "success",
                )

            finally:
                connection.close()

        # Redirect after submission to avoid duplicate form submissions
        return redirect(url_for("dashboard"))

    # Display existing Task 1 records
    users = get_all_users()

    return render_template(
        "dashboard.html",
        username=session["user"],
        users=users,
    )


# --------------------------------------------------
# 9. Logout
# --------------------------------------------------

@app.route("/logout", methods=["GET", "POST"])
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# --------------------------------------------------
# 10. Start the application
# --------------------------------------------------

if __name__ == "__main__":

    # Create tables without deleting existing records
    init_db()

    # Start the Flask development server
    app.run(debug=True)

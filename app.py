import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


# 1. Create the Flask application
app = Flask(__name__)

# Development fallback only. Set SECRET_KEY through an environment
# variable when deploying the application.
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-only-change-this-secret-key",
)

# Keep the database beside app.py.
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"


# 2. Database connection
def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# 3. Create tables without deleting existing records
def init_db():
    connection = get_db_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

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


# 4. Protect pages that require login
def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not session.get("user"):
            flash(
                "Please log in to access this page.",
                "error",
            )
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


# 5. Validate user details for Create and Update
def validate_user_form():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name or not email or not phone:
        return None, "Please fill in all user details."

    if len(name) > 100 or len(email) > 254 or len(phone) > 30:
        return None, "One or more fields exceed the allowed length."

    if (
        "@" not in email
        or "." not in email.rsplit("@", 1)[-1]
        or any(character.isspace() for character in email)
    ):
        return None, "Enter a valid email address."

    return (name, email, phone), None


# 6. Retrieve all user records
def get_all_users():
    connection = get_db_connection()

    try:
        users = connection.execute("""
            SELECT id, name, email, phone
            FROM users
            ORDER BY id DESC
        """).fetchall()

        return users

    finally:
        connection.close()


# 7. Home page
@app.route("/")
def home():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# 8. Account registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password or not confirm_password:
            flash("Please fill in all fields.", "error")

        elif len(username) > 50:
            flash(
                "Username must be 50 characters or fewer.",
                "error",
            )

        elif len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error",
            )

        elif password != confirm_password:
            flash("Passwords do not match.", "error")

        else:
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

            else:
                flash(
                    "Account created successfully. Please log in.",
                    "success",
                )
                return redirect(url_for("login"))

            finally:
                connection.close()

    return render_template("register.html")


# 9. Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
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

        if account and check_password_hash(
            account["password_hash"],
            password,
        ):
            # Start a fresh session after successful authentication.
            session.clear()
            session["user"] = account["username"]

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


# 10. CREATE and READ: add records and show the dashboard
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        details, error = validate_user_form()

        if error:
            flash(error, "error")

        else:
            connection = get_db_connection()

            try:
                connection.execute(
                    """
                    INSERT INTO users (name, email, phone)
                    VALUES (?, ?, ?)
                    """,
                    details,
                )

                connection.commit()

            finally:
                connection.close()

            flash("User added successfully.", "success")

        # Post/Redirect/Get avoids resubmission when refreshing.
        return redirect(url_for("dashboard"))

    return render_template(
        "dashboard.html",
        username=session["user"],
        users=get_all_users(),
    )


# 11. UPDATE: load a record and save its changes
@app.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    connection = get_db_connection()

    try:
        user = connection.execute(
            """
            SELECT id, name, email, phone
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    finally:
        connection.close()

    if user is None:
        flash("User record not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        details, error = validate_user_form()

        if error:
            flash(error, "error")
            return render_template(
                "edit_user.html",
                username=session["user"],
                user=user,
            )

        connection = get_db_connection()

        try:
            cursor = connection.execute(
                """
                UPDATE users
                SET name = ?, email = ?, phone = ?
                WHERE id = ?
                """,
                (*details, user_id),
            )

            updated_rows = cursor.rowcount
            connection.commit()

        finally:
            connection.close()

        if updated_rows:
            flash("User updated successfully.", "success")
        else:
            flash("User record no longer exists.", "error")

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_user.html",
        username=session["user"],
        user=user,
    )


# 12. DELETE: remove a record using a POST request
@app.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )

        deleted_rows = cursor.rowcount
        connection.commit()

    finally:
        connection.close()

    if deleted_rows:
        flash("User deleted successfully.", "success")
    else:
        flash("User record not found.", "error")

    return redirect(url_for("dashboard"))


# 13. Logout
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# 14. Initialize the database and start the development server
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
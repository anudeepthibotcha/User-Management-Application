import os
import re
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


# ---------------------------------------------------------
# 1. APPLICATION CONFIGURATION
# ---------------------------------------------------------

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "database.db"))

app.config.update(
    SECRET_KEY=os.environ.get(
        "SECRET_KEY",
        "dev-only-change-this-secret-key",
    ),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------
# 2. DATABASE CONNECTION AND MIGRATION
# ---------------------------------------------------------

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create tables and safely add roles to existing accounts."""

    connection = get_db_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
                    CHECK (role IN ('admin', 'user'))
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

        # Check whether the existing accounts table has a role column.
        account_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(accounts)"
            ).fetchall()
        }

        # Task 2 and Task 3 databases do not have this column yet.
        # Existing accounts automatically receive the normal-user role.
        if "role" not in account_columns:
            connection.execute("""
                ALTER TABLE accounts
                ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
                CHECK (role IN ('admin', 'user'))
            """)

        # Any unexpected role is changed to the least-privileged role.
        connection.execute("""
            UPDATE accounts
            SET role = 'user'
            WHERE role IS NULL OR role NOT IN ('admin', 'user')
        """)

        connection.commit()

    finally:
        connection.close()


# ---------------------------------------------------------
# 3. ACCOUNT AND ROLE HELPERS
# ---------------------------------------------------------

def get_current_account():
    """
    Retrieve the logged-in account from SQLite.

    The role is reloaded on each protected request so that
    permission changes in the database take effect.
    """

    account_id = session.get("account_id")

    if not account_id:
        return None

    connection = get_db_connection()

    try:
        account = connection.execute(
            """
            SELECT id, username, role
            FROM accounts
            WHERE id = ?
            """,
            (account_id,),
        ).fetchone()

    finally:
        connection.close()

    if account is None:
        session.clear()
        return None

    session["user"] = account["username"]
    session["role"] = account["role"]

    return account


# Authentication decorator
def login_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        account = get_current_account()

        if account is None:
            flash(
                "Please log in to access this page.",
                "error",
            )
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


# Authorization decorator for administrator-only web routes
def admin_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        account = get_current_account()

        if account is None:
            flash(
                "Please log in to access this page.",
                "error",
            )
            return redirect(url_for("login"))

        if account["role"] != "admin":
            flash(
                "Access denied. Administrator permission is required.",
                "error",
            )
            return redirect(url_for("dashboard"))

        return view_function(*args, **kwargs)

    return wrapped_view


# Authentication and authorization decorator for REST APIs
def api_auth_required(admin_only=False):

    def decorator(view_function):

        @wraps(view_function)
        def wrapped_view(*args, **kwargs):

            account = get_current_account()

            if account is None:
                return jsonify({
                    "error": "Authentication required."
                }), 401

            if admin_only and account["role"] != "admin":
                return jsonify({
                    "error": "Administrator permission required."
                }), 403

            return view_function(account, *args, **kwargs)

        return wrapped_view

    return decorator


# ---------------------------------------------------------
# 4. INPUT VALIDATION
# ---------------------------------------------------------

def validate_user_values(name, email, phone):

    if not all(
        isinstance(value, str)
        for value in (name, email, phone)
    ):
        return None, "Name, email, and phone must be text values."

    name = name.strip()
    email = email.strip()
    phone = phone.strip()

    if not name or not email or not phone:
        return None, "Please fill in all user details."

    if (
        len(name) > 100
        or len(email) > 254
        or len(phone) > 30
    ):
        return None, "One or more fields exceed the allowed length."

    if not EMAIL_PATTERN.fullmatch(email):
        return None, "Enter a valid email address."

    return (name, email, phone), None


# Validate HTML form data
def validate_user_form():

    return validate_user_values(
        request.form.get("name", ""),
        request.form.get("email", ""),
        request.form.get("phone", ""),
    )


# Validate JSON data received by the REST API
def validate_user_json():

    if not request.is_json:
        return None, (
            "Send JSON data with Content-Type: application/json."
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, "The JSON body must be an object."

    return validate_user_values(
        data.get("name"),
        data.get("email"),
        data.get("phone"),
    )


# ---------------------------------------------------------
# 5. DATABASE READ HELPERS
# ---------------------------------------------------------

def get_all_users():

    connection = get_db_connection()

    try:
        return connection.execute("""
            SELECT id, name, email, phone
            FROM users
            ORDER BY id DESC
        """).fetchall()

    finally:
        connection.close()


def get_user_by_id(user_id):

    connection = get_db_connection()

    try:
        return connection.execute(
            """
            SELECT id, name, email, phone
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    finally:
        connection.close()


# ---------------------------------------------------------
# 6. HOME PAGE, REGISTRATION, AND LOGIN
# ---------------------------------------------------------

@app.route("/")
def home():

    account = get_current_account()

    if account:

        if account["role"] == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# Account registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if get_current_account():
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get("password", "")

        confirm_password = request.form.get(
            "confirm_password", ""
        )

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
                # Public registration always creates a normal user.
                connection.execute(
                    """
                    INSERT INTO accounts
                        (username, password_hash, role)
                    VALUES (?, ?, 'user')
                    """,
                    (username, password_hash),
                )

                connection.commit()

            except sqlite3.IntegrityError:
                flash(
                    "That username already exists.",
                    "error",
                )

            else:
                flash(
                    "Account created successfully. Please log in.",
                    "success",
                )
                return redirect(url_for("login"))

            finally:
                connection.close()

    return render_template("register.html")


# User login
@app.route("/login", methods=["GET", "POST"])
def login():

    if get_current_account():
        return redirect(url_for("home"))

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
                SELECT id, username, password_hash, role
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

            # Start a fresh session after successful login.
            session.clear()

            session["account_id"] = account["id"]
            session["user"] = account["username"]
            session["role"] = account["role"]

            # Redirect according to the account role.
            if account["role"] == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        flash(
            "Invalid username or password.",
            "error",
        )

    return render_template("login.html")


# ---------------------------------------------------------
# 7. TASK 3 WEB DASHBOARD: CREATE AND READ
# ---------------------------------------------------------

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    account = get_current_account()
    is_admin = account["role"] == "admin"

    if request.method == "POST":

        # Only administrators can create records.
        if not is_admin:
            abort(403)

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

            flash(
                "User record added successfully.",
                "success",
            )

        return redirect(url_for("dashboard"))

    return render_template(
        "dashboard.html",
        username=account["username"],
        role=account["role"],
        is_admin=is_admin,
        users=get_all_users(),
    )


# ---------------------------------------------------------
# 8. TASK 4 ADMIN PANEL
# ---------------------------------------------------------

@app.route("/admin")
@admin_required
def admin_dashboard():

    connection = get_db_connection()

    try:

        # Retrieve registered accounts and their roles.
        accounts = connection.execute("""
            SELECT id, username, role
            FROM accounts
            ORDER BY id DESC
        """).fetchall()

        total_records = connection.execute(
            "SELECT COUNT(*) AS total FROM users"
        ).fetchone()["total"]

        total_admins = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM accounts
            WHERE role = 'admin'
            """
        ).fetchone()["total"]

        total_normal_users = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM accounts
            WHERE role = 'user'
            """
        ).fetchone()["total"]

    finally:
        connection.close()

    return render_template(
        "admin_dashboard.html",
        username=session["user"],
        accounts=accounts,
        total_records=total_records,
        total_admins=total_admins,
        total_normal_users=total_normal_users,
    )


# ---------------------------------------------------------
# 9. TASK 3 WEB CRUD: UPDATE AND DELETE
# ADMINISTRATORS ONLY
# ---------------------------------------------------------

@app.route(
    "/users/<int:user_id>/edit",
    methods=["GET", "POST"],
)
@admin_required
def edit_user(user_id):

    user = get_user_by_id(user_id)

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
            flash(
                "User record updated successfully.",
                "success",
            )
        else:
            flash(
                "User record no longer exists.",
                "error",
            )

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_user.html",
        username=session["user"],
        user=user,
    )


@app.route(
    "/users/<int:user_id>/delete",
    methods=["POST"],
)
@admin_required
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
        flash(
            "User record deleted successfully.",
            "success",
        )
    else:
        flash(
            "User record not found.",
            "error",
        )

    return redirect(url_for("dashboard"))


# ---------------------------------------------------------
# 10. REST API: GET ALL USERS
# ---------------------------------------------------------

@app.route("/api/users", methods=["GET"])
@api_auth_required(admin_only=False)
def api_get_users(account):

    users = get_all_users()

    return jsonify({
        "count": len(users),
        "users": [
            dict(user)
            for user in users
        ],
    }), 200


# ---------------------------------------------------------
# 11. REST API: CREATE USER
# ADMINISTRATORS ONLY
# ---------------------------------------------------------

@app.route("/api/users", methods=["POST"])
@api_auth_required(admin_only=True)
def api_create_user(account):

    details, error = validate_user_json()

    if error:
        return jsonify({"error": error}), 400

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, phone)
            VALUES (?, ?, ?)
            """,
            details,
        )

        new_id = cursor.lastrowid
        connection.commit()

    finally:
        connection.close()

    created_user = get_user_by_id(new_id)

    return jsonify({
        "message": "User record created successfully.",
        "user": dict(created_user),
    }), 201


# ---------------------------------------------------------
# 12. REST API: GET ONE USER
# ---------------------------------------------------------

@app.route(
    "/api/users/<int:user_id>",
    methods=["GET"],
)
@api_auth_required(admin_only=False)
def api_get_user(account, user_id):

    user = get_user_by_id(user_id)

    if user is None:
        return jsonify({
            "error": "User record not found."
        }), 404

    return jsonify({
        "user": dict(user)
    }), 200


# ---------------------------------------------------------
# 13. REST API: UPDATE USER
# ADMINISTRATORS ONLY
# ---------------------------------------------------------

@app.route(
    "/api/users/<int:user_id>",
    methods=["PUT"],
)
@api_auth_required(admin_only=True)
def api_update_user(account, user_id):

    details, error = validate_user_json()

    if error:
        return jsonify({"error": error}), 400

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

    if not updated_rows:
        return jsonify({
            "error": "User record not found."
        }), 404

    updated_user = get_user_by_id(user_id)

    return jsonify({
        "message": "User record updated successfully.",
        "user": dict(updated_user),
    }), 200


# ---------------------------------------------------------
# 14. REST API: DELETE USER
# ADMINISTRATORS ONLY
# ---------------------------------------------------------

@app.route(
    "/api/users/<int:user_id>",
    methods=["DELETE"],
)
@api_auth_required(admin_only=True)
def api_delete_user(account, user_id):

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

    if not deleted_rows:
        return jsonify({
            "error": "User record not found."
        }), 404

    return jsonify({
        "message": "User record deleted successfully.",
        "deleted_id": user_id,
    }), 200


# ---------------------------------------------------------
# 15. LOGOUT
# ---------------------------------------------------------

@app.route("/logout", methods=["GET", "POST"])
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success",
    )

    return redirect(url_for("login"))


# ---------------------------------------------------------
# 16. INITIALIZE DATABASE AND START APPLICATION
# ---------------------------------------------------------

# This also migrates existing Task 2/Task 3 databases.
init_db()


if __name__ == "__main__":
    app.run(debug=True)
# User Management Web Application

A full-stack web application developed using Python, Flask,
HTML, CSS, SQLite, and Werkzeug.

Task 4 extends the Task 3 application with Role-Based Access
Control (RBAC), an administrator dashboard, and REST API
integration.

## 1. Project Overview

The application provides account registration, login
authentication, session management, and user-record management.

It supports two application roles:

- Admin
- Normal User

Administrators can perform CRUD operations, access the admin
panel, and view registered application accounts.

Normal users can log in and view user records but cannot
create, update, or delete them.

The application also provides REST API endpoints that return
JSON responses.

## 2. Technologies Used

| Technology | Purpose |
| --- | --- |
| Python 3 | Backend programming |
| Flask | Web framework and routing |
| SQLite | Database storage |
| HTML5 | Page structure |
| CSS3 | Styling and layout |
| Werkzeug | Password hashing and verification |
| Jinja2 | Dynamic HTML rendering |
| Flask Sessions | User authentication |
| JSON | REST API request and response format |
| Postman / Thunder Client | API testing |
| VS Code | Development environment |
| Git and GitHub | Version control |

No additional web framework is introduced.

## 3. Project Folder Structure

User Management App/
│
├── app.py                           # Flask app: config, DB helpers, auth decorators, web routes, REST API
├── set_admin.py                     # Command-line script to assign the admin / user role to an account
├── requirements.txt                 # Python dependencies (Flask, Werkzeug)
├── README.md                        # Project documentation
├── database.db                      # SQLite database (created automatically by init_db())
├── database_backup_before_task4.db  # Backup taken before the Task 4 (RBAC) migration
│
├── templates/                       # Jinja2 HTML templates
│   ├── register.html                # Account registration form
│   ├── login.html                   # Login form
│   ├── dashboard.html               # Registered Users table (admin: add / edit / delete, user: read-only)
│   ├── edit_user.html               # Update form for a user record (admin only)
│   ├── admin_dashboard.html         # Admin panel: statistics and registered accounts
│   └── index.html                   # Not rendered by any route in app.py
│
├── static/
│   └── style.css                    # Shared styling for all pages
│
├── venv/                            # Local virtual environment (not committed)
├── __pycache__/                     # Python bytecode cache (auto-generated)
└── .git/                            # Git repository data
## Project Workflow Flowchart

The following flowchart illustrates the overall workflow, from opening the application to registration, authentication, role-based access, database operations, and logout.

```text
Browser request (GET / POST)
   ↓
Flask URL routing → matches @app.route()
   ↓
Public route?  (/, /register, /login, /logout)
   ├── /register → request.form.get() → validate username & password
   │      ↓
   │   generate_password_hash() → INSERT INTO accounts (role = 'user')
   │      ↓
   │   flash("Account created...") + redirect(url_for("login"))
   │
   ├── /login → SELECT ... FROM accounts WHERE username = ?
   │      ↓
   │   check_password_hash() valid?
   │      ├── No  → flash("Invalid username or password.") + login page again
   │      └── Yes → session.clear() → store account_id, user, role in session
   │                 ↓
   │              role == "admin"?
   │                 ├── Yes → redirect(url_for("admin_dashboard"))
   │                 └── No  → redirect(url_for("dashboard"))
   │
   └── /logout → session.clear() → flash("You have been logged out.") + redirect(url_for("login"))

Protected route  (dashboard / admin / edit_user / delete_user / REST API)
   ↓
@login_required / @admin_required / @api_auth_required → get_current_account()
   ↓
Valid session?
   ├── No  → web: flash("Please log in...") + redirect(url_for("login"))
   │         API: 401 JSON error
   └── Yes ↓
Admin-only route and role != "admin"?
   ├── Yes → web: flash("Access denied...") + redirect(url_for("dashboard"))
   │         API: 403 JSON error
   └── No ↓
Route function runs (dashboard / admin_dashboard / edit_user / delete_user / api_*)
   ↓
request.form.get() or request.get_json() → validate_user_form() / validate_user_json()   [Create & Update only]
   ├── Invalid → flash(error) or 400 JSON error
   └── Valid ↓
get_db_connection() → parameterized SQL query (SELECT / INSERT / UPDATE / DELETE)
   ↓
connection.commit() → connection.close()
   ↓
Web route: flash() message + redirect(url_for("dashboard"))
API route: jsonify(...) → 200 OK / 201 Created / 404 Not Found
   ↓
get_all_users() → SELECT id, name, email, phone FROM users ORDER BY id DESC
   ↓
render_template("dashboard.html" / "admin_dashboard.html", ...)
   ↓
Jinja {% for user in users %}
   ↓
Registered Users table in the browser
   ├── Admin       → Add User form + Edit / Delete buttons + Admin Panel link
   └── Normal user → read-only table
```
# User Management Web Application

## Project Overview

The User Management Web Application simplifies the process of registering accounts, authenticating users, and maintaining user information through a web interface.

The application uses Flask for backend processing, SQLite for persistent data storage, HTML and CSS for the user interface, and Werkzeug for password hashing and verification. Authenticated users can access the dashboard, add user details, view registered records, and log out securely.

## Features

- Account registration with password confirmation
- Unique usernames
- Password hashing using Werkzeug
- Login and password verification
- Session-based authentication
- Protected dashboard and CRUD routes
- Create user records
- Read and display saved user records
- Edit existing user records
- Delete records with browser confirmation
- Server-side field validation
- Parameterized SQL queries
- Success and error flash messages
- Persistent SQLite storage
- Responsive dashboard interface

## Technologies

Technology - Purpose

Python - Backend programming
Flask - Web framework and routing
HTML5 - Structure of web pages
CSS3 - Styling and layout
SQLite - Persistent database storage
Werkzeug - Password hashing and verification
Jinja2 - Dynamic HTML template rendering
Flask Sessions - Maintaining authenticated user sessions
VS Code - Development environment
Git and GitHub - Version control and source code hosting

## Project Structure

User Management App/
├── app.py
├── requirements.txt
├── README.md
├── database.db
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── edit_user.html
│   └── index.html
└── static/
    └── style.css

## Project Workflow Flowchart

The following flowchart illustrates the overall workflow, from opening the application to registration, authentication, database operations, and logout.

Browser request (GET / POST)
   ↓
Flask URL routing → matches @app.route()
   ↓
@login_required → session.get("user") exists?
   ├── No  → flash("Please log in...") + redirect(url_for("login"))
   └── Yes ↓
Route function runs (dashboard / edit_user / delete_user)
   ↓
request.form.get() → validate_user_form()   [Create & Update only]
   ↓
get_db_connection() → parameterized SQL query
   ↓
connection.commit() → connection.close()
   ↓
flash() message + redirect(url_for("dashboard"))
   ↓
get_all_users() → SELECT id, name, email, phone FROM users ORDER BY id DESC
   ↓
render_template("dashboard.html", username=..., users=users)
   ↓
Jinja {% for user in users %}
   ↓
Registered Users table with Edit / Delete buttons in the browser
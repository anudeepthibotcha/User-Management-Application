# User Management Web Application

## Project Overview

This project upgrades the original Task 1 User Management Web
Application by adding user registration, login, password hashing,
session-based authentication, a protected dashboard, and logout.

The application uses Python, Flask, HTML, CSS, SQLite, and
Werkzeug password-hashing utilities.

## Features

- User account registration
- Unique usernames
- Password hashing
- Password confirmation
- User login and password verification
- Session-based authentication
- Protected dashboard
- Add user details: name, email, and phone
- Display registered user records
- Logout functionality
- SQLite database persistence
- Responsive interface

## Technologies

- Python
- Flask
- HTML
- CSS
- SQLite
- Werkzeug

## Project Structure

```text
user_management_app/
├── app.py
├── requirements.txt
├── README.md
├── database.db
├── templates/
│   ├── register.html
│   ├── login.html
│   └── dashboard.html
└── static/
    └── style.css

## Project Workflow Flowchart

The following flowchart illustrates the overall workflow, from opening the application to registration, authentication, database operations, and logout.

Browser form (POST)
   ↓
request.form.get()
   ↓
Server-side validation
   ↓
get_db_connection()
   ↓
INSERT INTO users / accounts (parameterized query)
   ↓
connection.commit() → connection.close()
   ↓
flash() message + redirect(url_for("dashboard"))
   ↓
get_all_users() → SELECT * FROM users ORDER BY id DESC
   ↓
render_template("dashboard.html", users=users)
   ↓
Jinja {% for user in users %}
   ↓
Registered Users table in the browser
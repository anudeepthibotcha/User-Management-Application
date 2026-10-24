# User Management Web Application

## Project Overview

The User Management Web Application simplifies the process of registering accounts, authenticating users, and maintaining user information through a web interface.

The application uses Flask for backend processing, SQLite for persistent data storage, HTML and CSS for the user interface, and Werkzeug for password hashing and verification. Authenticated users can access the dashboard, add user details, view registered records, and log out securely.

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
│
├── app.py
├── requirements.txt
├── README.md
├── database.db
│
├── templates/
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   └── index.html
│
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
import sqlite3
import bcrypt
import streamlit as st

# Setup database and tables
def setup_database():
    conn = sqlite3.connect("campus_directory.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Hash the password
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Verify the password
def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode(), stored_password.encode())

# Authenticate a user
def authenticate_user(username, password):
    conn = sqlite3.connect("campus_directory.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT password, role FROM students WHERE username = ?
    """, (username,))
    result = cursor.fetchone()
    conn.close()
    if result and verify_password(result[0], password):
        return result[1]  # Return role if authentication is successful
    return None

# Fetch news from the database
def fetch_news():
    conn = sqlite3.connect("campus_directory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM news")
    news = cursor.fetchall()
    conn.close()
    return news

# Add or update news
def save_news(news_id, title, content):
    conn = sqlite3.connect("campus_directory.db")
    cursor = conn.cursor()
    if news_id:
        cursor.execute("""
            UPDATE news SET title = ?, content = ? WHERE id = ?
        """, (title, content, news_id))
    else:
        cursor.execute("""
            INSERT INTO news (title, content) VALUES (?, ?)
        """, (title, content))
    conn.commit()
    conn.close()

# Delete news
def delete_news(news_id):
    conn = sqlite3.connect("campus_directory.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()

# Initialize the database
setup_database()

# Streamlit app
st.title("Southern University Directory")

# Manage session state for logged-in user
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
if "refresh_news" not in st.session_state:
    st.session_state.refresh_news = False

# Menu options
if not st.session_state.logged_in:
    menu = ["Home", "Login", "Register"]
else:
    menu = ["Home", "Admin Dashboard" if st.session_state.role == "admin" else "Student Dashboard", "Logout"]

choice = st.sidebar.selectbox("Menu", menu)

# Home Page
if choice == "Home":
    st.subheader("Welcome to Southern University Directory")
    news = fetch_news()
    if news:
        st.write("### Latest Campus News")
        for item in news:
            st.write(f"**{item[1]}**")
            st.write(item[2])
            st.write("---")
    else:
        st.write("No news available at the moment.")

# Register Page
elif choice == "Register":
    st.subheader("Register New Account")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    role = st.selectbox("Role", ["student", "admin"])
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if first_name and last_name and role and password:
            username = f"{first_name.lower()}.{last_name.lower()}@sus.edu"
            hashed_password = hash_password(password)
            conn = sqlite3.connect("campus_directory.db")
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO students (first_name, last_name, username, password, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (first_name, last_name, username, hashed_password, role))
                conn.commit()
                st.success(f"Registration successful! Your username is {username}")
            except sqlite3.IntegrityError:
                st.error("Username already exists!")
            finally:
                conn.close()
        else:
            st.error("All fields are required!")

# Login Page
elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        role = authenticate_user(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.success(f"Welcome {username}! You are logged in as {role}.")
        else:
            st.error("Invalid username or password.")

# Logout
elif choice == "Logout":
    st.session_state.logged_in = False
    st.session_state.role = None
    st.success("You have been logged out.")

# Admin Dashboard
elif choice == "Admin Dashboard":
    st.subheader("Admin Dashboard - Manage News")

    if st.session_state.refresh_news:
        st.session_state.refresh_news = False  # Reset refresh state

    news = fetch_news()

    # Display existing news for editing
    for item in news:
        with st.expander(f"Edit News: {item[1]}"):
            updated_title = st.text_input(f"Edit Title (ID: {item[0]})", value=item[1], key=f"title_{item[0]}")
            updated_content = st.text_area(f"Edit Content (ID: {item[0]})", value=item[2], key=f"content_{item[0]}")
            if st.button(f"Save Changes for ID {item[0]}", key=f"save_{item[0]}"):
                save_news(item[0], updated_title, updated_content)
                st.session_state.refresh_news = True
                st.success("News updated successfully!")
            if st.button(f"Delete News for ID {item[0]}", key=f"delete_{item[0]}"):
                delete_news(item[0])
                st.session_state.refresh_news = True
                st.success("News deleted successfully!")

    # Add new news
    st.write("### Add New News")
    new_title = st.text_input("New News Title", key="new_title")
    new_content = st.text_area("New News Content", key="new_content")
    if st.button("Add News", key="add_news"):
        if new_title and new_content:
            save_news(None, new_title, new_content)
            st.session_state.refresh_news = True
            st.success("News added successfully!")

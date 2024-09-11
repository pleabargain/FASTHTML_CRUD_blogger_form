from fasthtml.common import *
from datetime import datetime
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_db():
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()

        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='users' OR name='entries')")
        existing_tables = cursor.fetchall()

        if len(existing_tables) < 2:  # If either users or entries table is missing
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL
                )
            ''')
            
            # Create entries table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    occupation TEXT,
                    week_details TEXT,
                    hobbies TEXT,
                    hometown TEXT,
                    weekend_plans TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            logging.info("Database setup successful - tables created")
        else:
            logging.info("Database already exists - no setup needed")

    except sqlite3.Error as e:
        logging.error(f"Database setup failed: {e}")
    finally:
        conn.close()

# Call setup_db() at the start of your application
setup_db()

# Initialize database
setup_db()

def create_user(username):
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        user_id = cursor.lastrowid
        logging.info(f"User created successfully: {username}")
        return user_id
    except sqlite3.IntegrityError:
        logging.warning(f"User already exists: {username}")
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        logging.error(f"Error creating user: {e}")
        return None
    finally:
        conn.close()

def get_user_id(username):
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Error getting user ID: {e}")
        return None
    finally:
        conn.close()

def create_entry(user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans):
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO entries (user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans))
        conn.commit()
        entry_id = cursor.lastrowid
        logging.info(f"Entry created successfully for user {user_id}")
        return entry_id
    except sqlite3.Error as e:
        logging.error(f"Error creating entry: {e}")
        return None
    finally:
        conn.close()

def get_entries(user_id):
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, content, occupation, week_details, hobbies, hometown, weekend_plans, timestamp
            FROM entries WHERE user_id = ? ORDER BY timestamp DESC
        """, (user_id,))
        entries = cursor.fetchall()
        logging.info(f"Retrieved {len(entries)} entries for user {user_id}")
        return entries
    except sqlite3.Error as e:
        logging.error(f"Error retrieving entries: {e}")
        return []
    finally:
        conn.close()

def get_entry(entry_id):
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans, timestamp
            FROM entries WHERE id = ?
        """, (entry_id,))
        entry = cursor.fetchone()
        if entry:
            logging.info(f"Retrieved entry {entry_id}")
            return entry
        else:
            logging.warning(f"No entry found with id {entry_id}")
            return None
    except sqlite3.Error as e:
        logging.error(f"Error retrieving entry: {e}")
        return None
    finally:
        conn.close()



def get_all_entries():
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.title, u.username
            FROM entries e
            JOIN users u ON e.user_id = u.id
            ORDER BY e.timestamp DESC
        """)
        entries = cursor.fetchall()
        logging.info(f"Retrieved {len(entries)} total entries")
        return entries
    except sqlite3.Error as e:
        logging.error(f"Error retrieving all entries: {e}")
        return []
    finally:
        conn.close()

def update_entry(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans):
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE entries 
            SET title = ?, content = ?, occupation = ?, week_details = ?, hobbies = ?, hometown = ?, weekend_plans = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, content, occupation, week_details, hobbies, hometown, weekend_plans, entry_id))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Entry {entry_id} updated successfully")
            return True
        else:
            logging.warning(f"No entry found with id {entry_id}")
            return False
    except sqlite3.Error as e:
        logging.error(f"Error updating entry: {e}")
        return False
    finally:
        conn.close()

# Initialize FastHTML app
app, rt = fast_app()

@rt('/')
def get():
    return Titled("Story Journal",
        Form(
            Input(id='username', placeholder='Enter your username'),
            Button("Start Journaling", hx_post='/journal', hx_target='#content'),
            id='login-form'
        ),
        A("View All Entries", href='/all_entries'),
        Div(id='content')
    )

@rt('/journal')
def post(username: str):
    user_id = create_user(username)
    if user_id:
        return journal_page(user_id, username)
    else:
        return "Error creating user. Please try again."

def journal_page(user_id, username):
    # Generate title with current date
    current_date = datetime.now().strftime("%Y%m%d")
    title = f"Entry {current_date}"
    return Div(
        H2(f"Welcome, {username}!"),
        Form(
            Div("Title:", Input(id='entry-title', name='title', value=title)),
            Div("Story:", Textarea(id='entry-content', name='content', placeholder='Write your story here...')),
            Div("Occupation:", Input(id='occupation', name='occupation', placeholder='Your occupation')),
            Div("Week Details:", Textarea(id='week-details', name='week_details', placeholder='Details about your week')),
            Div("Hobbies:", Textarea(id='hobbies', name='hobbies', placeholder='Your hobbies')),
            Div("Hometown:", Input(id='hometown', name='hometown', placeholder='Your hometown')),
            Div("Weekend Plans:", Textarea(id='weekend-plans', name='weekend_plans', placeholder='Your upcoming weekend plans')),
            Button("Submit", hx_post=f'/submit/{user_id}', hx_target='#entries'),
            id='entry-form'
        ),
        A("View Previous Entries", href=f'/view_entries/{user_id}'),
        Div(id='entries')
    )

@rt('/submit/{user_id}')
def post(user_id: int, title: str, content: str, occupation: str, week_details: str, hobbies: str, hometown: str, weekend_plans: str):
    entry_id = create_entry(user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans)
    if entry_id:
        return entry_div(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans, datetime.now())
    else:
        return "Error submitting entry. Please try again."

@rt('/view_entries/{user_id}')
def get(user_id: int):
    entries = list_entries(user_id)
    return Titled("Previous Entries",
        A("Home", href='/'),
        Div(*entries)
    )

@rt('/all_entries')
def get():
    entries = get_all_entries()
    entry_links = [Div(A(f"{entry[1]} by {entry[2]}", href=f'/view_entry/{entry[0]}')) for entry in entries]
    return Titled("All Entries",
        A("Home", href='/'),
        Div(*entry_links)
    )

@rt('/view_entry/{entry_id}')
def get(entry_id: int):
    entry = get_entry(entry_id)
    if entry:
        fields = [
            ("Title", entry[1]),
            ("Content", entry[2]),
            ("Occupation", entry[3]),
            ("Week Details", entry[4]),
            ("Hobbies", entry[5]),
            ("Hometown", entry[6]),
            ("Weekend Plans", entry[7]),
            ("Last Updated", entry[8])
        ]
        entry_details = [Div(
            Div(field[0], style="font-weight: bold; display: inline-block; width: 150px;"),
            ": ",
            field[1],
            style="margin-bottom: 10px;"
        ) for field in fields]
        return Titled(f"View Entry {entry_id}",
            A("Home", href='/'),
            Div(*entry_details),
            A("Edit Entry", href=f'/edit/{entry_id}')
        )
    else:
        return Titled("Entry Not Found",
            A("Home", href='/'),
            P(f"Entry {entry_id} not found.")
        )

def list_entries(user_id):
    entries = get_entries(user_id)
    return [entry_div(entry[0], entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7], entry[8]) for entry in entries]

def entry_div(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans, timestamp):
    return Div(
        H3(title),
        P(f"Story: {content}"),
        P(f"Occupation: {occupation}"),
        P(f"Week Details: {week_details}"),
        P(f"Hobbies: {hobbies}"),
        P(f"Hometown: {hometown}"),
        P(f"Weekend Plans: {weekend_plans}"),
        P(f"Posted on: {timestamp}"),
        Button("Edit", hx_get=f'/edit/{entry_id}', hx_target=f'#entry-{entry_id}'),
        id=f'entry-{entry_id}'
    )


@rt('/update/{entry_id}')
def post(entry_id: int, title: str, content: str, occupation: str, week_details: str, hobbies: str, hometown: str, weekend_plans: str):
    if update_entry(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return Div(
            P(f"Changes saved successfully at {current_time}"),
            Script("setTimeout(function() { window.location.href = '/view_entry/" + str(entry_id) + "'; }, 2000);")
        )
    else:
        return "Error updating entry. Please try again."


@rt('/edit/{entry_id}')
def get(entry_id: int):
    entry = get_entry(entry_id)
    if entry:
        return Titled(f"Edit Entry {entry_id}",
            Form(
                Div("Title:", Input(id=f'edit-title-{entry_id}', name='title', value=entry[2])),
                Div("Story:", Textarea(id=f'edit-content-{entry_id}', name='content', placeholder='Write your story here...')(entry[3])),
                Div("Occupation:", Input(id=f'edit-occupation-{entry_id}', name='occupation', placeholder='Your occupation', value=entry[4])),
                Div("Week Details:", Textarea(id=f'edit-week-details-{entry_id}', name='week_details', placeholder='Details about your week')(entry[5])),
                Div("Hobbies:", Textarea(id=f'edit-hobbies-{entry_id}', name='hobbies', placeholder='Your hobbies')(entry[6])),
                Div("Hometown:", Input(id=f'edit-hometown-{entry_id}', name='hometown', placeholder='Your hometown', value=entry[7])),
                Div("Weekend Plans:", Textarea(id=f'edit-weekend-plans-{entry_id}', name='weekend_plans', placeholder='Your upcoming weekend plans')(entry[8])),
                Button("Save", hx_post=f'/update/{entry_id}', hx_target='#notification'),
                id=f'edit-form-{entry_id}'
            ),
            Div(id='notification')
        )
    else:
        return Titled("Entry Not Found",
            A("Home", href='/'),
            P(f"Entry {entry_id} not found.")
        )

def update_entry(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans):
    try:
        conn = sqlite3.connect('stories.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE entries 
            SET title = ?, content = ?, occupation = ?, week_details = ?, hobbies = ?, hometown = ?, weekend_plans = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, content, occupation, week_details, hobbies, hometown, weekend_plans, entry_id))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Entry {entry_id} updated successfully")
            return True
        else:
            logging.warning(f"No entry found with id {entry_id}")
            return False
    except sqlite3.Error as e:
        logging.error(f"Error updating entry: {e}")
        return False
    finally:
        conn.close()

# Start the server
serve()

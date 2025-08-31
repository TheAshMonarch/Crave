import sqlite3
from werkzeug.security import generate_password_hash
from flask import g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('recipes.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                ingredients TEXT,
                instructions TEXT,
                category TEXT,
                tags TEXT,
                image TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                recipe_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(recipe_id) REFERENCES recipes(id),
                PRIMARY KEY (user_id, recipe_id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON recipes(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipes_category ON recipes(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipes_tags ON recipes(tags)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)')
        conn.commit()

def add_user(username, password):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password, method='pbkdf2:sha256:600000'))
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Username already exists")

def get_user_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()

def add_recipe_to_db(user_id, title, ingredients, instructions, category, tags, image=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO recipes (user_id, title, ingredients, instructions, category, tags, image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, title, ingredients, instructions, category, tags, image))
    db.commit()
    return cursor.lastrowid

def get_all_recipes():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM recipes')
    return cursor.fetchall()

def add_favorite(user_id, recipe_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO favorites (user_id, recipe_id) VALUES (?, ?)",
        (user_id, recipe_id)
    )
    db.commit()

def get_user_favorites(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT r.* 
        FROM recipes r 
        JOIN favorites f ON r.id = f.recipe_id
        WHERE f.user_id = ?
    ''', (user_id,))
    return cursor.fetchall()

def remove_favorite_from_db(user_id, recipe_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?",
        (user_id, recipe_id)
    )
    db.commit()

def delete_recipe_from_db(recipe_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
    db.commit()

def update_recipe(recipe_id, title, ingredients, instructions, category, tags, image=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE recipes SET
            title = ?,
            ingredients = ?,
            instructions = ?,
            category = ?,
            tags = ?,
            image = COALESCE(?, image)
        WHERE id = ?
    ''', (title, ingredients, instructions, category, tags, image, recipe_id))
    db.commit()

def get_user_recipes(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM recipes WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

def get_recipe_by_id(recipe_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    return cursor.fetchone()

def get_recipes_by_category(category):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM recipes WHERE category LIKE ?', (f'%{category}%',))
    return cursor.fetchall()

def get_recipes_by_tag(tag):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM recipes WHERE tags LIKE ?', (f'%{tag}%',))
    return cursor.fetchall()

def get_all_recipes_with_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT r.*, u.username 
        FROM recipes r 
        JOIN users u ON r.user_id = u.id 
        ORDER BY r.id DESC
    ''')
    return cursor.fetchall()

def get_user_favorites_with_username(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT r.*, u.username 
        FROM recipes r 
        JOIN favorites f ON r.id = f.recipe_id 
        JOIN users u ON r.user_id = u.id
        WHERE f.user_id = ?
    ''', (user_id,))
    return cursor.fetchall()

def get_user_recipes_with_username(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT r.*, u.username 
        FROM recipes r 
        JOIN users u ON r.user_id = u.id 
        WHERE r.user_id = ?
    ''', (user_id,))
    return cursor.fetchall()
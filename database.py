import sqlite3
from werkzeug.security import generate_password_hash

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
        conn.commit()

def add_user(username, password):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password))
        )
        conn.commit()

def get_user_by_username(username):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

def add_recipe_to_db(user_id, title, ingredients, instructions, category, tags, image=None):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO recipes (user_id, title, ingredients, instructions, category, tags, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, title, ingredients, instructions, category, tags, image))
        conn.commit()
        return cursor.lastrowid

def get_all_recipes():
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM recipes
        ''')
        return cursor.fetchall()

def add_favorite(user_id, recipe_id):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO favorites (user_id, recipe_id) VALUES (?, ?)",
            (user_id, recipe_id)
        )
        conn.commit()
        print(f"Debug: Added favorite - user_id: {user_id}, recipe_id: {recipe_id}")

def get_user_favorites(user_id): 
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.* 
            FROM recipes r 
            JOIN favorites f ON r.id = f.recipe_id
            WHERE f.user_id = ?
        ''', (user_id,))
        favorites = cursor.fetchall()
        print(f"Debug: Favorites for user_id {user_id}: {favorites}")  # Debug output
        return favorites
    
def remove_favorite_from_db(user_id, recipe_id):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id)
        )
        conn.commit()
        
def get_recipe_by_id(recipe_id):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM recipes WHERE id = ?
            ''', (recipe_id,))
        return cursor.fetchone()
    
def delete_recipe_from_db(recipe_id):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM recipes WHERE id = ?
        ''', (recipe_id,))
        conn.commit()
        
def update_recipe(recipe_id, title, ingredients, instructions, category, tags, image=None):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
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
        conn.commit()

def get_user_recipes(user_id):
    with sqlite3.connect('recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE user_id = ?", (user_id,))
        return cursor.fetchall()
    
def get_recipe_by_id(recipe_id):
    with sqlite3.connect('recipes.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        recipe = cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        return recipe
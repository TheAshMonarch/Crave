import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g, flash, get_flashed_messages
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask_wtf.csrf import CSRFProtect
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
csrf = CSRFProtect(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.info("Application started")

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('recipes.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def allowed_file(filename):
    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return False
    return True

@app.route('/')
def home():
    from database import init_db
    init_db()  # Initialize database on first load
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    from database import get_user_by_username
    app.logger.info(f"Login attempt, method: {request.method}, form: {request.form}")
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            app.logger.info(f"Attempting login for username: {username}")
            if not username or not password:
                app.logger.error("Missing username or password")
                return "Username and password are required", 400
            user = get_user_by_username(username)
            app.logger.info(f"User query result: {user}")
            if user is None:
                app.logger.error(f"No user found for username: {username}")
                return "Invalid username or password", 401
            if check_password_hash(user['password'], password):
                session['username'] = username
                session['user_id'] = user['id']
                app.logger.info(f"Login successful for {username}")
                return redirect(url_for('view_recipes'))
            app.logger.error("Password check failed")
            return "Invalid username or password", 401
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            return f"Server error: {str(e)}", 500
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    from database import add_user, get_user_by_username
    app.logger.info(f"Register attempt, method: {request.method}, form: {request.form}")
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            app.logger.info(f"Attempting to register username: {username}")
            if not username or not password:
                app.logger.error("Missing username or password")
                return "Username and password are required", 400
            if get_user_by_username(username):
                app.logger.error(f"Username already exists: {username}")
                return "Username already exists", 400
            add_user(username, password)
            app.logger.info(f"User registered successfully: {username}")
            return redirect(url_for('login'))
        except ValueError as e:
            app.logger.error(f"Registration error: {str(e)}")
            return str(e), 400
        except Exception as e:
            app.logger.error(f"Server error during registration: {str(e)}")
            return f"Server error: {str(e)}", 500
    return render_template('register.html')

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    from database import add_recipe_to_db
    if 'user_id' not in session:
        app.logger.info("No user_id in session, redirecting to login")
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            ingredients = request.form.get('ingredients', '').strip()
            instructions = request.form.get('instructions', '').strip()
            category = request.form.get('category', '').strip()
            tags = request.form.get('tags', '').strip()
            app.logger.info(f"Adding recipe: {title}")
            if not all([title, ingredients, instructions, category]):
                app.logger.error("Missing required fields")
                return "All fields except tags and image are required", 400
            image = request.files.get('image')
            filename = None
            if image and allowed_file(image.filename):
                try:
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    app.logger.info(f"Image saved: {filename}")
                except Exception as e:
                    app.logger.error(f"Invalid image file: {str(e)}")
                    return f"Invalid image file: {str(e)}", 400
            add_recipe_to_db(
                session['user_id'], title, ingredients, instructions, category, tags, filename
            )
            flash('Recipe added!')
            return redirect(url_for('view_recipes'))
            app.logger.info(f"Recipe added successfully: {title}")
            return redirect(url_for('view_recipes'))
        except Exception as e:
            app.logger.error(f"Add recipe error: {str(e)}")
            return f"Server error: {str(e)}", 500
    return render_template('add_recipe.html')

@app.route('/recipes')
def view_recipes():
    from database import get_all_recipes_with_users, get_user_favorites  # Changed import
    if 'user_id' not in session:
        app.logger.info("No user_id in session, redirecting to login")
        return redirect(url_for('login'))
    try:
        app.logger.info(f"Fetching recipes for user_id: {session['user_id']}")
        page = request.args.get('page', 1, type=int)
        per_page = 8
        offset = (page - 1) * per_page
        all_recipes = get_all_recipes_with_users()  # Use new function
        app.logger.info(f"Retrieved {len(all_recipes)} recipes")
        paginated_recipes = all_recipes[offset:offset + per_page]
        has_next = len(all_recipes) > offset + per_page
        user_favorites_ids = [fav['id'] for fav in get_user_favorites(session['user_id'])]
        app.logger.info(f"User favorites: {user_favorites_ids}")
        return render_template(
            'recipes.html',
            recipes=paginated_recipes,
            user_favorites_ids=user_favorites_ids,
            page=page,
            has_next=has_next
        )
    except Exception as e:
        app.logger.error(f"View recipes error: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/favorites')
def view_favorites():
    from database import get_user_favorites
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 8
        offset = (page - 1) * per_page
        all_favorites = get_user_favorites(session['user_id'])
        paginated_favorites = all_favorites[offset:offset + per_page]
        has_next = len(all_favorites) > offset + per_page
        return render_template(
            'favorites.html',
            favorites=paginated_favorites,
            page=page,
            has_next=has_next
        )
    except Exception as e:
        app.logger.error(f"View favorites error: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    from database import get_recipe_by_id, get_user_favorites, get_comments_for_recipe  # ADD get_comments_for_recipe
    if 'user_id' not in session:
        app.logger.info("No user_id in session, redirecting to login")
        return redirect(url_for('login'))
    try:
        recipe = get_recipe_by_id(recipe_id)
        if not recipe:
            app.logger.error(f"Recipe not found: {recipe_id}")
            return "Recipe not found", 404
        
        user_favorites_ids = [fav['id'] for fav in get_user_favorites(session['user_id'])]
        comments = get_comments_for_recipe(recipe_id)  # ADD THIS LINE to get comments
        
        app.logger.info(f"Recipe detail loaded: {recipe['title']}, favorites: {user_favorites_ids}")
        if recipe['image']:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe['image'])
            app.logger.info(f"Checking image for recipe {recipe_id}: {image_path}, exists: {os.path.exists(image_path)}")
        
        return render_template(
            'recipe_detail.html',
            recipe=recipe,
            comments=comments  ,
            user_id=session.get("user_id"),
            user_favorites_ids=user_favorites_ids,
        )
    except Exception as e:
        app.logger.error(f"Recipe detail error: {str(e)}")
        return f"Server error: {str(e)}", 500
    
@app.route('/favorite/<int:recipe_id>', methods=['POST'])
def add_favorite(recipe_id):
    from database import get_db
    if 'user_id' not in session:
        # Return error if the user is not logged in
        return jsonify({'success': False, 'error': 'You need to log in to perform this action.'}), 401

    try:
        db = get_db()
        cursor = db.cursor()

        # Check if the recipe is already in the user's favorites
        cursor.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (session['user_id'], recipe_id)
        )
        is_favorited = bool(cursor.fetchone())

        if is_favorited:
            # Remove from favorites if already favorited
            cursor.execute(
                "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?",
                (session['user_id'], recipe_id)
            )
            db.commit()
            action = 'removed'
            message = 'Recipe removed from favorites.'
        else:
            # Add to favorites if not already favorited
            cursor.execute(
                "INSERT INTO favorites (user_id, recipe_id) VALUES (?, ?)",
                (session['user_id'], recipe_id)
            )
            db.commit()
            action = 'added'
            message = 'Recipe added to favorites.'

        # Return success response
        return jsonify({'success': True, 'action': action, 'message': message})

    except Exception as e:
        app.logger.error(f"Error in add_favorite: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while updating favorites.'}), 500
    
@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    from database import get_comment_by_id, delete_comment_from_db, get_comments_for_recipe
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401

    comment = get_comment_by_id(comment_id)
    if not comment or comment["user_id"] != session["user_id"]:
        return jsonify({"success": False, "error": "Comment deleted"}), 403

    delete_comment_from_db(comment_id)

    comments = get_comments_for_recipe(comment["recipe_id"])
    return jsonify({
        "success": True,
        "html": render_template("partials/_comments.html", comments=comments, user_id=session.get("user_id")),
        "message": "Comment deleted"
    })

@app.route('/search_suggestions')
def search_suggestions():
    query = request.args.get('q', '').lower()
    results = []

    if query:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM recipes WHERE title LIKE ? LIMIT 5", (f"%{query}%",))
        rows = cursor.fetchall()
        conn.close()

        results = [{"id": row["id"], "title": row["title"]} for row in rows]

    return jsonify(results)

@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        query = request.args.get('query', '').strip()
        if not query:
            return redirect(url_for('view_recipes'))
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM recipes
            WHERE LOWER(title) LIKE ? OR LOWER(tags) LIKE ? OR LOWER(category) LIKE ?
        ''', (f'%{query.lower()}%', f'%{query.lower()}%', f'%{query.lower()}%'))
        results = cursor.fetchall()
        return render_template('recipes.html', recipes=results)
    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    from database import get_recipe_by_id, update_recipe
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        recipe = get_recipe_by_id(recipe_id)
        if not recipe or recipe['user_id'] != session['user_id']:
            app.logger.error(f"Not authorized to edit recipe_id: {recipe_id}")
            return "Not authorized", 403
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            ingredients = request.form.get('ingredients', '').strip()
            instructions = request.form.get('instructions', '').strip()
            category = request.form.get('category', '').strip()
            tags = request.form.get('tags', '').strip()
            if not all([title, ingredients, instructions, category]):
                app.logger.error("Missing required fields for edit recipe")
                return "All fields except tags and image are required", 400
            new_image = request.files.get('new_image')
            filename = recipe['image']
            if new_image and allowed_file(new_image.filename):
                try:
                    filename = secure_filename(new_image.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    new_image.save(image_path)
                    app.logger.info(f"Image saved for edit: {image_path}")
                except Exception as e:
                    app.logger.error(f"Invalid image file: {str(e)}")
                    return f"Invalid image file: {str(e)}", 400
            update_recipe(
                recipe_id, title, ingredients, instructions, category, tags, filename
            )
            flash('Recipe updated!')
            app.logger.info(f"Recipe updated successfully: {recipe_id}")
            return redirect(url_for('view_recipes'))
        return render_template('edit_recipe.html', recipe=recipe)
    except Exception as e:
        app.logger.error(f"Edit recipe error: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    from database import get_recipe_by_id, delete_recipe_from_db
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        recipe = get_recipe_by_id(recipe_id)
        if recipe and recipe['user_id'] == session['user_id']:
            # Delete image file if it exists
            if recipe['image']:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe['image'])
                if os.path.exists(image_path):
                    os.remove(image_path)
            delete_recipe_from_db(recipe_id)
            flash('Recipe deleted!')
            app.logger.info(f"Recipe deleted: {recipe_id}")
        return redirect(url_for('view_recipes'))
    except Exception as e:
        app.logger.error(f"Delete recipe error: {str(e)}")
        return f"Server error: {str(e)}", 500


@app.route('/profile')
def profile():
    from database import get_user_favorites, get_user_recipes
    if 'user_id' not in session:
        app.logger.info("No user_id in session, redirecting to login")
        return redirect(url_for('login'))
    try:
        user_id = session['user_id']
        username = session['username']
        favorites = get_user_favorites(user_id)
        user_recipes = get_user_recipes(user_id)
        app.logger.info(f"Profile loaded for user_id: {user_id}, username: {username}, recipes: {len(user_recipes)}, favorites: {len(favorites)}")
        for recipe in user_recipes + favorites:
            if recipe['image']:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe['image'])
                app.logger.info(f"Checking image for recipe {recipe['id']}: {image_path}, exists: {os.path.exists(image_path)}")
        return render_template(
            'profile.html',
            username=username,
            user_recipes=user_recipes,
            favorites=favorites,
            user_favorites_ids=[fav['id'] for fav in favorites]
        )
    except Exception as e:
        app.logger.error(f"Profile error: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/tags/<tag>')
def recipes_by_tag(tag):
    from database import get_recipes_by_tag
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        recipes = get_recipes_by_tag(f'%{tag}%')
        return render_template('recipes.html', recipes=recipes)
    except Exception as e:
        app.logger.error(f"Recipes by tag error: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/recipe/<int:recipe_id>/share')
def share_recipe(recipe_id):
    from database import get_recipe_by_id
    try:
        recipe = get_recipe_by_id(recipe_id)
        if not recipe:
            app.logger.error(f"Recipe not found: {recipe_id}")
            return "Recipe not found", 404
        app.logger.info(f"Share recipe loaded: {recipe['title']}")
        if recipe['image']:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe['image'])
            app.logger.info(f"Checking image for recipe {recipe_id}: {image_path}, exists: {os.path.exists(image_path)}")
        return render_template('recipe_detail.html', recipe=recipe, user_favorites_ids=[])
    except Exception as e:
        app.logger.error(f"Share recipe error: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/copy_share_link/<int:recipe_id>', methods=['POST'])
def copy_share_link(recipe_id):
    from database import get_recipe_by_id
    try:
        recipe = get_recipe_by_id(recipe_id)
        if not recipe:
            app.logger.error(f"Recipe not found: {recipe_id}")
            return jsonify({'error': 'Recipe not found'}), 404
        share_url = url_for('share_recipe', recipe_id=recipe_id, _external=True)
        flash('Share link copied!', 'success')
        # Get flashed messages to clear them
        flashed_messages = get_flashed_messages(with_categories=True)
        app.logger.info(f"Share link copied for recipe_id: {recipe_id}")
        return jsonify({
            'success': True,
            'message': flashed_messages[0][1] if flashed_messages else 'Share link copied!',
            'url': share_url
        })
    except Exception as e:
        app.logger.error(f"Copy share link error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# In app.py, add this new route:

@app.route("/add_comment/<int:recipe_id>", methods=["POST"])
def add_comment_route(recipe_id):
    from database import add_comment, get_comments_for_recipe
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401

    comment_text = request.form.get("comment_text")
    if not comment_text:
        return jsonify({"success": False, "error": "Comment cannot be empty"}), 400

    add_comment(session["user_id"], recipe_id, comment_text)

    comments = get_comments_for_recipe(recipe_id)
    return jsonify({
        "success": True,
        "html": render_template("partials/_comments.html", comments=comments, user_id=session.get("user_id")),
        "message": "Comment added successfully!"
    })



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
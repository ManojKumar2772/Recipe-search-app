from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.http import parse_cookie
from flask_migrate import Migrate
import spoonacular as sp
from models import db, User, SearchHistory, RecipeDetail
from sqlalchemy.exc import OperationalError
from functools import wraps
from dotenv import load_dotenv
import os

load_dotenv()  

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

api = sp.API(os.getenv('SPOONACULAR_API_KEY'))

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user and user.account_disabled:
        return None
    return user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        try:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            print(f"User {username} registered successfully.")
            login_user(user)
            return redirect(url_for('home'))
        except OperationalError as e:
            db.session.rollback()
            flash('Database connection error. Please try again later.', 'danger')
        except Exception as e:
            db.session.rollback()
            print(f"Registration failed: {str(e)}")
            flash(f'Registration failed: {str(e)}', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            if user.account_disabled:
                flash('This account has been disabled.', 'danger')
                return redirect(url_for('login'))
            if user.verify_password(password):
                login_user(user)
                flash('Login successful.', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        recipe_name = request.form.get('recipe_name')
        response = api.search_recipes_complex(query=recipe_name, number=10)
        data = response.json()
        search_history = SearchHistory(user_id=current_user.id, recipe_name=recipe_name)
        db.session.add(search_history)
        db.session.commit()
        return render_template('search.html', data=data)
    return render_template('search.html')

@app.route('/search/<int:recipe_id>', methods=['GET'])
@login_required
def get_recipe_details(recipe_id):
    recipe_detail = RecipeDetail.query.filter_by(recipe_id=recipe_id).first()
    if recipe_detail:
        data = recipe_detail.data
    else:
        response = api.get_recipe_information(recipe_id)
        data = response.json()
        recipe_detail = RecipeDetail(recipe_id=recipe_id, data=data)
        db.session.add(recipe_detail)
        db.session.commit()
    search_history = SearchHistory(user_id=current_user.id, recipe_name=data['title'])
    db.session.add(search_history)
    db.session.commit()
    return render_template('recipe_details.html', data=data)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_password = request.form.get('new_password')
    current_user.password = new_password
    try:
        db.session.commit()
        flash('Password changed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to change password: {str(e)}', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    try:
        current_user.account_disabled = True
        db.session.commit()
        logout_user()  
        flash('Account deleted successfully.', 'success')
        return redirect(url_for('register'))
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete account: {str(e)}', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    history = SearchHistory.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', history=history)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    try:
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except OperationalError as e:
        db.session.rollback()
        return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.verify_password(password):
        login_user(user)
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 400

@app.route('/api/search', methods=['POST'])
@login_required
def api_search():
    data = request.get_json()
    recipe_name = data.get('recipe_name')
    response = api.search_recipes_complex(query=recipe_name, number=10)
    if response.status_code == 200:
        data = response.json()
        search_history = SearchHistory(user_id=current_user.id, recipe_name=recipe_name, data=data)
        db.session.add(search_history)
        db.session.commit()
        return jsonify(data), 200
    else:
        return jsonify({'error': 'Failed to fetch recipes'}), 500

@app.route('/api/search/<int:recipe_id>', methods=['GET'])
@login_required
def api_get_recipe_details(recipe_id):
    recipe_detail = RecipeDetail.query.filter_by(recipe_id=recipe_id).first()
    if recipe_detail:
        data = recipe_detail.data
    else:
        response = api.get_recipe_information(recipe_id)
        if response.status_code == 200:
            data = response.json()
            recipe_detail = RecipeDetail(recipe_id=recipe_id, data=data)
            db.session.add(recipe_detail)
            db.session.commit()
        else:
            return jsonify({'error': 'Failed to fetch recipe details'}), 500
    search_history = SearchHistory.user_id=current_user.id, recipe_name=data['title']
    db.session.add(search_history)
    db.session.commit()
    return jsonify(data), 200

@app.route('/api/search_history', methods=['GET'])
@login_required
def api_search_history():
    history = SearchHistory.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': item.id,
        'recipe_name': item.recipe_name,
        'data': item.data
    } for item in history]), 200

@app.route('/delete_search_history/<int:item_id>', methods=['DELETE'])
@login_required
def delete_search_history(item_id):
    item = SearchHistory.query.get(item_id)
    if item and item.user_id == current_user.id:
        try:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'success': True}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'Item not found or unauthorized'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, ssl_context=('path/to/cert.pem', 'path/to/key.pem'))


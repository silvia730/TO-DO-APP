from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import mysql.connector
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv
from functools import wraps


load_dotenv()

app = Flask(__name__)
CORS(app, 
    supports_credentials=True,
    resources={r"/*": {"origins": "http://127.0.0.1:5500"}},
    expose_headers=["Content-Type", "Authorization"],
    allow_headers=["Content-Type", "Authorization"]
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')


# Add after_request handler to set CORS headers for all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5500')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '#07silvia,njeri'),
    'database': os.getenv('DB_NAME', 'todo_app')
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Authentication middleware
def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return jsonify({'message': 'Authentication required'}), 401
            
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorator

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required_fields = ['fullName', 'email', 'phone', 'username', 'password']
    
    if not all(field in data for field in required_fields):
        response = make_response(jsonify({'message': 'Missing required fields'}), 400)
        return response

    try:
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, username, password)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            data['fullName'],
            data['email'],
            data['phone'],
            data['username'],
            hashed_password.decode('utf-8')
        ))
        conn.commit()
        response = make_response(jsonify({'message': 'User registered successfully'}), 201)
        return response
        
    except mysql.connector.IntegrityError as e:
        response = make_response(jsonify({'message': 'Username or email already exists'}), 400)
        return response
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}")  # Add logging
        response = make_response(jsonify({'message': 'Registration failed'}), 500)
        return response
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing credentials'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, username, password FROM users 
            WHERE username = %s
        ''', (data['username'],))
        user = cursor.fetchone()

        if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'message': 'Invalid credentials'}), 401

        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'])

        response = make_response(jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username']
            }
        }))
        response.set_cookie('token', token, httponly=True, samesite='Strict', secure=True)
        return response

    except Exception as e:
        return jsonify({'message': 'Login failed'}), 500
    finally:
        cursor.close()
        conn.close()

# Todo Routes
@app.route('/todos', methods=['GET'])
@token_required
def get_todos(current_user):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, task, status, created_at 
            FROM todos 
            WHERE user_id = %s
            ORDER BY created_at DESC
        ''', (current_user,))
        todos = cursor.fetchall()
        return jsonify(todos)
    except Exception as e:
        return jsonify({'message': 'Failed to fetch todos'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/todos', methods=['POST'])
@token_required
def create_todo(current_user):
    data = request.get_json()
    if not data.get('task'):
        return jsonify({'message': 'Task is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO todos (user_id, task)
            VALUES (%s, %s)
        ''', (current_user, data['task']))
        conn.commit()
        return jsonify({'message': 'Todo created successfully'}), 201
    except Exception as e:
        return jsonify({'message': 'Failed to create todo'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/todos/<int:todo_id>', methods=['PUT'])
@token_required
def update_todo(current_user, todo_id):
    data = request.get_json()
    if not data.get('task') or not data.get('status'):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE todos
            SET task = %s, status = %s
            WHERE id = %s AND user_id = %s
        ''', (data['task'], data['status'], todo_id, current_user))
        
        if cursor.rowcount == 0:
            return jsonify({'message': 'Todo not found'}), 404
            
        conn.commit()
        return jsonify({'message': 'Todo updated successfully'})
    except Exception as e:
        return jsonify({'message': 'Failed to update todo'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
@token_required
def delete_todo(current_user, todo_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM todos
            WHERE id = %s AND user_id = %s
        ''', (todo_id, current_user))
        
        if cursor.rowcount == 0:
            return jsonify({'message': 'Todo not found'}), 404
            
        conn.commit()
        return jsonify({'message': 'Todo deleted successfully'})
    except Exception as e:
        return jsonify({'message': 'Failed to delete todo'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
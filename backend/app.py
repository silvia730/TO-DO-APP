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

# CORS Configuration
CORS(app,
     resources={r"/api/*": {
         "origins": ["http://127.0.0.1:5500", "http://localhost:5500", "null"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True
     }}
)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '#07silvia,njeri'),
    'database': os.getenv('DB_NAME', 'todo_app')
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

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

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['fullName', 'email', 'phone', 'username', 'password']
    if not all(k in data for k in required):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt())
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO users (full_name, email, phone, username, password)
               VALUES (%s, %s, %s, %s, %s)''',
            (data['fullName'], data['email'], data['phone'], data['username'], hashed.decode())
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201

    except mysql.connector.IntegrityError:
        return jsonify({'message': 'Username or email already exists'}), 400
    except Exception as e:
        app.logger.error("Registration error: %s", e)
        return jsonify({'message': 'Registration failed'}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing credentials'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id, username, password FROM users WHERE username = %s',
                    (data['username'],))
        user = cur.fetchone()

        if not user or not bcrypt.checkpw(data['password'].encode(), user['password'].encode()):
            return jsonify({'message': 'Invalid credentials'}), 401

        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'])

        resp = make_response(jsonify({
            'message': 'Login successful',
            'user': {'id': user['id'], 'username': user['username']}
        }))
        resp.set_cookie('token', token,
                        httponly=True,
                        samesite='None',
                        secure=False)
        return resp

    except Exception as e:
        app.logger.error("Login error: %s", e)
        return jsonify({'message': 'Login failed'}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/todos', methods=['GET'])
@token_required
def get_todos(current_user):
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            '''SELECT id, text, date, time, created_at, updated_at, completed, bookmarked
               FROM todos WHERE user_id = %s
               ORDER BY created_at DESC''',
            (current_user,)
        )
        todos = cur.fetchall()
        # Convert datetime objects to string for JSON serialization
        for todo in todos:
            if todo['date']:
                todo['date'] = todo['date'].strftime('%Y-%m-%d')
            if todo['time']:
                todo['time'] = todo['time'].strftime('%H:%M')
            todo['created_at'] = todo['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            todo['updated_at'] = todo['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(todos)
    except Exception as e:
        app.logger.error("Fetch todos error: %s", e)
        return jsonify({'message': 'Failed to fetch todos'}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/todos', methods=['POST'])
@token_required
def create_todo(current_user):
    data = request.get_json()
    if not data.get('text'):
        return jsonify({'message': 'Todo text is required'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            '''INSERT INTO todos (user_id, text, date, time, completed, bookmarked)
               VALUES (%s, %s, %s, %s, %s, %s)''',
            (current_user, data['text'], data.get('date'), data.get('time'), 
             False, False)
        )
        conn.commit()
        
        # Fetch the created todo
        cur.execute(
            '''SELECT id, text, date, time, created_at, updated_at, completed, bookmarked
               FROM todos WHERE id = LAST_INSERT_ID()'''
        )
        new_todo = cur.fetchone()
        
        # Format dates for JSON
        if new_todo['date']:
            new_todo['date'] = new_todo['date'].strftime('%Y-%m-%d')
        if new_todo['time']:
            new_todo['time'] = new_todo['time'].strftime('%H:%M')
        new_todo['created_at'] = new_todo['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        new_todo['updated_at'] = new_todo['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(new_todo), 201
    except Exception as e:
        app.logger.error("Create todo error: %s", e)
        return jsonify({'message': 'Failed to create todo'}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
@token_required
def update_todo(current_user, todo_id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No update data provided'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        if 'text' in data:
            update_fields.append('text = %s')
            params.append(data['text'])
        if 'date' in data:
            update_fields.append('date = %s')
            params.append(data['date'])
        if 'time' in data:
            update_fields.append('time = %s')
            params.append(data['time'])
        if 'completed' in data:
            update_fields.append('completed = %s')
            params.append(data['completed'])
        if 'bookmarked' in data:
            update_fields.append('bookmarked = %s')
            params.append(data['bookmarked'])
            
        if not update_fields:
            return jsonify({'message': 'No valid fields to update'}), 400
            
        # Add todo_id and user_id to params
        params.extend([todo_id, current_user])
        
        query = f'''UPDATE todos SET {', '.join(update_fields)}
                   WHERE id = %s AND user_id = %s'''
        cur.execute(query, params)
        
        if cur.rowcount == 0:
            return jsonify({'message': 'Todo not found'}), 404
            
        # Fetch the updated todo
        cur.execute(
            '''SELECT id, text, date, time, created_at, updated_at, completed, bookmarked
               FROM todos WHERE id = %s''',
            (todo_id,)
        )
        updated_todo = cur.fetchone()
        
        # Format dates for JSON
        if updated_todo['date']:
            updated_todo['date'] = updated_todo['date'].strftime('%Y-%m-%d')
        if updated_todo['time']:
            updated_todo['time'] = updated_todo['time'].strftime('%H:%M')
        updated_todo['created_at'] = updated_todo['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        updated_todo['updated_at'] = updated_todo['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        conn.commit()
        return jsonify(updated_todo)
    except Exception as e:
        app.logger.error("Update todo error: %s", e)
        return jsonify({'message': 'Failed to update todo'}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
@token_required
def delete_todo(current_user, todo_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM todos WHERE id=%s AND user_id=%s',
                    (todo_id, current_user))
        if cur.rowcount == 0:
            return jsonify({'message': 'Todo not found'}), 404
        conn.commit()
        return jsonify({'message': 'Todo deleted successfully'})
    except Exception as e:
        app.logger.error("Delete todo error: %s", e)
        return jsonify({'message': 'Failed to delete todo'}), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
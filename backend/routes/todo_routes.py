from flask import Blueprint, request, jsonify, session
from app import mysql

todo_bp = Blueprint('todos', __name__)

@todo_bp.route('/todos', methods=['GET'])
def get_todos():
    if 'user_id' not in session:
        return jsonify(message='Unauthorized'), 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, task, status FROM todos WHERE user_id = %s", (session['user_id'],))
    todos = [{'id': row[0], 'task': row[1], 'status': row[2]} for row in cur.fetchall()]
    cur.close()
    return jsonify(todos), 200


@todo_bp.route('/todos', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return jsonify(message='Unauthorized'), 401

    data = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO todos (user_id, task, status) VALUES (%s, %s, %s)",
                (session['user_id'], data['task'], 'pending'))
    mysql.connection.commit()
    cur.close()
    return jsonify(message='Todo added'), 201


@todo_bp.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    if 'user_id' not in session:
        return jsonify(message='Unauthorized'), 401

    data = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("UPDATE todos SET task=%s, status=%s WHERE id=%s AND user_id=%s",
                (data['task'], data['status'], todo_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    return jsonify(message='Todo updated'), 200


@todo_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    if 'user_id' not in session:
        return jsonify(message='Unauthorized'), 401

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM todos WHERE id=%s AND user_id=%s", (todo_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    return jsonify(message='Todo deleted'), 200

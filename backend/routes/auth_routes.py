from flask import Blueprint, request, jsonify, session
from app import mysql, bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO users (full_name, email, phone, username, password) VALUES (%s, %s, %s, %s, %s)",
        (data['fullName'], data['email'], data['phone'], data['username'], hashed_pw)
    )
    mysql.connection.commit()
    cur.close()
    return jsonify(message='User registered successfully'), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.check_password_hash(user[1], password):
        session['user_id'] = user[0]
        return jsonify(message='Login successful'), 200
    else:
        return jsonify(message='Invalid credentials'), 401


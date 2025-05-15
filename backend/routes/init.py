import os
from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_cors import CORS

mysql = MySQL()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

    # MySQL Config
    app.config['MYSQL_HOST']     = os.getenv('DB_HOST', 'localhost')
    app.config['MYSQL_USER']     = os.getenv('DB_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD', '')
    app.config['MYSQL_DB']       = os.getenv('DB_NAME', 'todo_app')

    # Session cookie must allow cross-site
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE']   = False  # OK for local dev

    mysql.init_app(app)
    bcrypt.init_app(app)

    # Only allow our front-end origin to talk, with credentials
    CORS(app,
         resources={r"/api/*": {"origins": "http://127.0.0.1:5500"}},
         supports_credentials=True)

    # register blueprints
    from routes.auth_routes import auth_bp
    from routes.todo_routes import todo_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(todo_bp, url_prefix='/api/todos')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

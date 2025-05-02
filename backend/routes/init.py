from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask import session

mysql = MySQL()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'

    # MySQL Config
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'todo_app'

    mysql.init_app(app)
    bcrypt.init_app(app)
    CORS(app, supports_credentials=True)

    # Register routes
    from routes.auth_routes import auth_bp
    from routes.todo_routes import todo_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(todo_bp, url_prefix='/api/todos')
    

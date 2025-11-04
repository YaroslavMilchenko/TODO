import os
from flask import Flask, request, redirect, render_template, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Error, log in to continue"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), unique = True, nullable = False)
    password = db.Column(db.String(256), nullable = False)
    tasks = db.relationship('Task', backref = 'author', lazy = True)

    def __repr__(self):
        return f'<User {self.username}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String(200), nullable = False)
    completed = db.Column(db.Boolean, default = False, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __repr__(self):
        return f'<Task {self.text[:20]}>'

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_username = request.form["username"]
        user_password = request.form["password"]
        hash_password = generate_password_hash(user_password)
        new_user = User(username = user_username, password = hash_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            flash("Registration successful!", 'success')
            return(redirect(url_for('login')))
        except IntegrityError:
            db.session.rollback()
            flash("Error, this name is taken", 'error')
            return render_template("register.html")
        except:
            db.session.rollback()
            flash("Unknown error", 'error')
            return render_template("register.html")
    else:
        return render_template("register.html")

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        user_username = request.form["username"]
        user_password = request.form["password"]
        
        user = User.query.filter_by(username=user_username).first()
        
        if user and check_password_hash(user.password, user_password):
            login_user(user)
            flash("Login success", 'success')
            return redirect(url_for('home'))
        else:
            flash("Error! Uncorrect login or password!", 'error')
            return redirect(url_for('login'))
    else:
        return render_template("login.html")
            
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You are logged out", 'info')
    return redirect(url_for('home'))
            
@app.route("/", methods = ["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        task_text = request.form['task-text']
        if task_text:
            new_task = Task(text = task_text, author = current_user)
            
            try:
                db.session.add(new_task)
                db.session.commit()
                flash("Task added", 'success')
            except:
                flash("Error, try more", 'error')
        return redirect(url_for('home'))
    else:
        user_tasks = current_user.tasks
        return render_template("index.html", tasks=user_tasks)
        
        
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    ebin_coins = db.Column(db.Integer, default=0)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class EwasteRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    waste_type = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    coins_awarded = db.Column(db.Integer)
    date_submitted = db.Column(db.DateTime, default=db.func.current_timestamp())

class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(200))
    coins_required = db.Column(db.Integer)
    code = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=10)
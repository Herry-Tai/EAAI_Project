from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.String(255))

    def has_perm(self, code: str) -> bool:
        if not self.permissions:
            return False
        return code in self.permissions.split(',')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    role = db.relationship('Role', backref='users')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:  # Flask-Login uses this to gate login sessions
        return self.active
    
class Detection(db.Model):
    __tablename__ = 'detections'

    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.String(64), nullable=False)

    # tool columns
    drill = db.Column(db.Integer, default=0)
    hammer = db.Column(db.Integer, default=0)
    pliers = db.Column(db.Integer, default=0)
    scissors = db.Column(db.Integer, default=0)
    screwdriver = db.Column(db.Integer, default=0)
    tape_measure = db.Column(db.Integer, default=0)  # renamed from tape-measure
    wrench = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
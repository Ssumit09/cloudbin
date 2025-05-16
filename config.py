import os
import boto3

class Config:
    # === Flask Security Key ===
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

    # === SQLAlchemy Default Local DB (SQLite) ===
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cloudbin.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === Cognito Integration (manual JWT) ===
    COGNITO_REGION = "ap-south-1"
    COGNITO_USERPOOL_ID = "ap-south-1_8Tc9LaxpD"  # Replace if different
    COGNITO_AUDIENCE = "43u1tar1ranvnlio2pqs4t8qjh"  # App Client ID (Audience)
    COGNITO_DOMAIN = "cloudbin.auth.ap-south-1.amazoncognito.com"
    COGNITO_REDIRECT_URI = "http://13.203.227.20/callback"  # Replace with actual EC2 public IP

    # === Optional Hosted UI Scopes ===
    COGNITO_AUTH_REQUEST_SCOPE = "email openid profile"

class ProductionConfig(Config):
    # === PostgreSQL on RDS ===
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://admin17:Aarav1857@cloudbindb.c7i0gmsmw7yz.ap-south-1.rds.amazonaws.com:5432/cloudbindb"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10
    }

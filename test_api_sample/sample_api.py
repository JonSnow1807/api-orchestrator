
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    return jsonify({"users": []})

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user"""
    return jsonify({"user_id": user_id})

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    return jsonify({"message": "User created"})

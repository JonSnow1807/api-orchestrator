#!/usr/bin/env python3
"""
Test file with intentional vulnerabilities for testing auto-remediation
"""

import hashlib
from flask import Flask, request

app = Flask(__name__)

# Vulnerability 1: Debug mode enabled
app.config['DEBUG'] = True
debug = True

# Vulnerability 2: Weak hash function (MD5)
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# Vulnerability 3: Missing authentication
@app.route('/api/user/<user_id>')
def get_user(user_id):
    # No authentication check here
    return f"User data for {user_id}"

# Vulnerability 4: Hardcoded secret
API_KEY = "sk-1234567890abcdef"
SECRET_KEY = "my-secret-key-123"

if __name__ == "__main__":
    app.run(debug=True)
"""
Locust load testing script
Auto-generated from OpenAPI specification
"""

from locust import HttpUser, task, between
import random
import json

class APIUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"
    
    def on_start(self):
        """Setup method called when user starts"""
        # Perform authentication if needed
        self.headers = {"Content-Type": "application/json"}
        self.test_data = {
            "name": f"LoadTest_{random.randint(1, 10000)}",
            "value": random.randint(1, 1000)
        }

    @task(10)
    def get_users(self):
        """Test GET /users"""
        self.client.get("/users", headers=self.headers, name="GET /users")

    @task(5)
    def post_users(self):
        """Test POST /users"""
        self.client.post("/users", json=self.test_data, headers=self.headers, name="POST /users")

    @task(10)
    def get_users_id(self):
        """Test GET /users/{id}"""
        self.client.get(f"/users/{random.randint(1, 100)}", headers=self.headers, name="GET /users/{id}")

    @task(5)
    def delete_users_id(self):
        """Test DELETE /users/{id}"""
        self.client.delete(f"/users/{random.randint(1, 100)}", headers=self.headers, name="DELETE /users/{id}")

    @task(2)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/health", name="Health Check")
    
class AdminUser(HttpUser):
    """Simulates admin users with different behavior"""
    wait_time = between(5, 10)
    host = "http://localhost:8000"
    
    @task
    def admin_operations(self):
        """Perform admin-specific operations"""
        # Add admin-specific tasks here
        pass

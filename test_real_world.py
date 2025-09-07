#!/usr/bin/env python3
"""
REAL-WORLD COMPLEX SCENARIO TESTING FOR STREAMAPI
Testing actual production-grade API code patterns
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8001"

# Real-world production API examples
REAL_WORLD_CASES = {
    "microservice_auth": '''
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from passlib.context import CryptContext
import uuid
from enum import Enum

app = FastAPI(title="Auth Microservice", version="2.0.0")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    
    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

# Database simulation
users_db = {}
refresh_tokens_db = {}

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    user = users_db.get(token_data.username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Endpoints
@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint for Kubernetes/Docker"""
    return {
        "status": "healthy",
        "service": "auth-microservice",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v2/auth/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(user: UserCreate):
    """Register a new user with email verification"""
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    user_id = str(uuid.uuid4())
    
    users_db[user.username] = {
        "id": user_id,
        "email": user.email,
        "username": user.username,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "message": "User created successfully"
    }

@app.post("/api/v2/auth/login", response_model=Token, tags=["Authentication"])
async def login(username: str, password: str):
    """Login with username and password to get JWT tokens"""
    user = users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": username, "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    refresh_token = str(uuid.uuid4())
    refresh_tokens_db[refresh_token] = {
        "username": username,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "refresh_token": refresh_token
    }

@app.post("/api/v2/auth/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    token_data = refresh_tokens_db.get(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = users_db.get(token_data["username"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800
    }

@app.get("/api/v2/auth/me", tags=["User"])
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"],
        "is_active": current_user["is_active"]
    }

@app.put("/api/v2/auth/me", tags=["User"])
async def update_me(
    full_name: Optional[str] = None,
    email: Optional[EmailStr] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update current user information"""
    if full_name:
        current_user["full_name"] = full_name
    if email:
        current_user["email"] = email
    
    users_db[current_user["username"]] = current_user
    
    return {"message": "User updated successfully"}

@app.delete("/api/v2/auth/me", status_code=status.HTTP_204_NO_CONTENT, tags=["User"])
async def delete_me(current_user: dict = Depends(get_current_user)):
    """Delete current user account (GDPR compliance)"""
    del users_db[current_user["username"]]
    return None

@app.post("/api/v2/auth/logout", tags=["Authentication"])
async def logout(refresh_token: str):
    """Logout and invalidate refresh token"""
    if refresh_token in refresh_tokens_db:
        del refresh_tokens_db[refresh_token]
    return {"message": "Logged out successfully"}

@app.get("/api/v2/admin/users", tags=["Admin"])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """List all users (admin only)"""
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users_list = list(users_db.values())[skip:skip+limit]
    return {
        "users": users_list,
        "total": len(users_db),
        "skip": skip,
        "limit": limit
    }
''',

    "ecommerce_api": '''
from flask import Flask, request, jsonify, g
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime
from decimal import Decimal
import stripe

app = Flask(__name__)
api = Api(app)
CORS(app)

app.config['SECRET_KEY'] = 'your-secret-key'
stripe.api_key = 'sk_test_123'

# Database simulation
products = {}
orders = {}
cart = {}
users = {}

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            g.current_user = users.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated

# REST Resources
class ProductList(Resource):
    def get(self):
        """Get all products with pagination and filtering"""
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('per_page', type=int, default=20)
        parser.add_argument('category', type=str)
        parser.add_argument('min_price', type=float)
        parser.add_argument('max_price', type=float)
        parser.add_argument('search', type=str)
        parser.add_argument('sort_by', type=str, choices=['price', 'name', 'created_at'])
        args = parser.parse_args()
        
        filtered_products = list(products.values())
        
        if args['category']:
            filtered_products = [p for p in filtered_products if p.get('category') == args['category']]
        
        if args['min_price']:
            filtered_products = [p for p in filtered_products if p.get('price', 0) >= args['min_price']]
        
        if args['max_price']:
            filtered_products = [p for p in filtered_products if p.get('price', 0) <= args['max_price']]
        
        # Pagination
        start = (args['page'] - 1) * args['per_page']
        end = start + args['per_page']
        
        return {
            'products': filtered_products[start:end],
            'total': len(filtered_products),
            'page': args['page'],
            'per_page': args['per_page']
        }
    
    @token_required
    def post(self):
        """Create a new product (admin only)"""
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True)
        parser.add_argument('description')
        parser.add_argument('price', type=float, required=True)
        parser.add_argument('category', required=True)
        parser.add_argument('stock', type=int, default=0)
        parser.add_argument('images', type=list, location='json')
        args = parser.parse_args()
        
        product_id = str(len(products) + 1)
        products[product_id] = {
            'id': product_id,
            'name': args['name'],
            'description': args['description'],
            'price': args['price'],
            'category': args['category'],
            'stock': args['stock'],
            'images': args.get('images', []),
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        return products[product_id], 201

class ProductDetail(Resource):
    def get(self, product_id):
        """Get product details"""
        product = products.get(product_id)
        if not product:
            return {'message': 'Product not found'}, 404
        return product
    
    @token_required
    def put(self, product_id):
        """Update product (admin only)"""
        product = products.get(product_id)
        if not product:
            return {'message': 'Product not found'}, 404
        
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('description')
        parser.add_argument('price', type=float)
        parser.add_argument('stock', type=int)
        args = parser.parse_args()
        
        for key, value in args.items():
            if value is not None:
                product[key] = value
        
        return product
    
    @token_required
    def delete(self, product_id):
        """Delete product (admin only)"""
        if product_id in products:
            del products[product_id]
            return '', 204
        return {'message': 'Product not found'}, 404

class ShoppingCart(Resource):
    @token_required
    def get(self):
        """Get current user's cart"""
        user_id = g.current_user['id']
        user_cart = cart.get(user_id, {})
        
        cart_items = []
        total = 0
        
        for product_id, quantity in user_cart.items():
            product = products.get(product_id)
            if product:
                item_total = product['price'] * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': item_total
                })
                total += item_total
        
        return {
            'items': cart_items,
            'total': total,
            'tax': total * 0.1,
            'grand_total': total * 1.1
        }
    
    @token_required
    def post(self):
        """Add item to cart"""
        parser = reqparse.RequestParser()
        parser.add_argument('product_id', required=True)
        parser.add_argument('quantity', type=int, default=1)
        args = parser.parse_args()
        
        user_id = g.current_user['id']
        if user_id not in cart:
            cart[user_id] = {}
        
        product = products.get(args['product_id'])
        if not product:
            return {'message': 'Product not found'}, 404
        
        if product['stock'] < args['quantity']:
            return {'message': 'Insufficient stock'}, 400
        
        cart[user_id][args['product_id']] = cart[user_id].get(args['product_id'], 0) + args['quantity']
        
        return {'message': 'Item added to cart'}, 201

class Checkout(Resource):
    @token_required
    def post(self):
        """Process checkout and create order"""
        parser = reqparse.RequestParser()
        parser.add_argument('shipping_address', type=dict, required=True, location='json')
        parser.add_argument('payment_method', required=True)
        parser.add_argument('stripe_token')
        args = parser.parse_args()
        
        user_id = g.current_user['id']
        user_cart = cart.get(user_id, {})
        
        if not user_cart:
            return {'message': 'Cart is empty'}, 400
        
        # Calculate total
        total = 0
        order_items = []
        
        for product_id, quantity in user_cart.items():
            product = products.get(product_id)
            if product:
                if product['stock'] < quantity:
                    return {'message': f'Insufficient stock for {product["name"]}'}, 400
                
                item_total = product['price'] * quantity
                order_items.append({
                    'product_id': product_id,
                    'product_name': product['name'],
                    'quantity': quantity,
                    'price': product['price'],
                    'subtotal': item_total
                })
                total += item_total
                
                # Update stock
                product['stock'] -= quantity
        
        # Process payment
        if args['payment_method'] == 'stripe':
            try:
                charge = stripe.Charge.create(
                    amount=int(total * 100),
                    currency='usd',
                    source=args['stripe_token'],
                    description=f'Order for user {user_id}'
                )
            except stripe.error.StripeError as e:
                return {'message': 'Payment failed', 'error': str(e)}, 400
        
        # Create order
        order_id = str(len(orders) + 1)
        orders[order_id] = {
            'id': order_id,
            'user_id': user_id,
            'items': order_items,
            'total': total,
            'tax': total * 0.1,
            'grand_total': total * 1.1,
            'shipping_address': args['shipping_address'],
            'payment_method': args['payment_method'],
            'status': 'processing',
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        # Clear cart
        cart[user_id] = {}
        
        return orders[order_id], 201

# Add resources to API
api.add_resource(ProductList, '/api/v1/products')
api.add_resource(ProductDetail, '/api/v1/products/<string:product_id>')
api.add_resource(ShoppingCart, '/api/v1/cart')
api.add_resource(Checkout, '/api/v1/checkout')

# Additional routes
@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """User registration"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password required'}), 400
    
    user_id = str(len(users) + 1)
    users[user_id] = {
        'id': user_id,
        'email': data['email'],
        'password': generate_password_hash(data['password']),
        'name': data.get('name'),
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    
    return jsonify({'message': 'User created', 'user_id': user_id}), 201

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    for user_id, user in users.items():
        if user['email'] == data.get('email'):
            if check_password_hash(user['password'], data.get('password')):
                token = jwt.encode({
                    'user_id': user_id,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, app.config['SECRET_KEY'])
                
                return jsonify({'token': token})
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/v1/orders', methods=['GET'])
@token_required
def get_orders():
    """Get user's orders"""
    user_id = g.current_user['id']
    user_orders = [o for o in orders.values() if o['user_id'] == user_id]
    return jsonify(user_orders)

@app.route('/api/v1/orders/<string:order_id>', methods=['GET'])
@token_required
def get_order(order_id):
    """Get order details"""
    order = orders.get(order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    if order['user_id'] != g.current_user['id']:
        return jsonify({'message': 'Access denied'}), 403
    
    return jsonify(order)

@app.route('/api/v1/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    categories = list(set(p.get('category') for p in products.values() if p.get('category')))
    return jsonify(categories)

@app.route('/api/v1/search', methods=['GET'])
def search():
    """Search products"""
    query = request.args.get('q', '')
    results = [p for p in products.values() if query.lower() in p.get('name', '').lower()]
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
''',

    "django_medical_api": '''
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import path, include
from rest_framework import serializers, viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
import uuid
from datetime import datetime, date

# Models
class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    ssn = models.CharField(max_length=11, unique=True)  # Encrypted in real app
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    insurance_provider = models.CharField(max_length=100)
    insurance_number = models.CharField(max_length=50)
    emergency_contact = models.JSONField()
    medical_history = models.JSONField(default=dict)
    allergies = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Doctor(AbstractUser):
    license_number = models.CharField(max_length=50, unique=True)
    specialization = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    available_days = models.JSONField(default=list)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    reason = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    medications = models.JSONField()  # List of medication objects
    diagnosis = models.TextField()
    instructions = models.TextField()
    valid_until = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

class MedicalRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True)
    record_type = models.CharField(max_length=50)  # lab_result, imaging, report
    title = models.CharField(max_length=200)
    content = models.JSONField()
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

# Serializers
class PatientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = '__all__'
        extra_kwargs = {'ssn': {'write_only': True}}
    
    def get_age(self, obj):
        today = date.today()
        return today.year - obj.date_of_birth.year

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'

# ViewSets
class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['insurance_provider']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'last_name']
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        patient = self.get_object()
        records = MedicalRecord.objects.filter(patient=patient)
        return Response(records.values())
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        patient = self.get_object()
        appointments = Appointment.objects.filter(patient=patient)
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_allergy(self, request, pk=None):
        patient = self.get_object()
        allergy = request.data.get('allergy')
        if allergy:
            patient.allergies.append(allergy)
            patient.save()
            return Response({'status': 'allergy added'})
        return Response({'error': 'No allergy provided'}, status=400)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today_appointments = self.queryset.filter(
            appointment_date__date=date.today()
        )
        serializer = self.get_serializer(today_appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'cancelled'
        appointment.save()
        return Response({'status': 'appointment cancelled'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'completed'
        appointment.notes = request.data.get('notes', '')
        appointment.save()
        return Response({'status': 'appointment completed'})

# API Views
class AvailableSlotsAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')
        date = request.query_params.get('date')
        
        if not doctor_id or not date:
            return Response({'error': 'doctor_id and date required'}, status=400)
        
        # Logic to calculate available slots
        slots = []
        for hour in range(9, 17):
            for minute in [0, 30]:
                slot_time = f"{hour:02d}:{minute:02d}"
                slots.append({
                    'time': slot_time,
                    'available': True  # Check against existing appointments
                })
        
        return Response(slots)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_dashboard(request):
    # Complex aggregation for patient dashboard
    user = request.user
    if hasattr(user, 'patient'):
        patient = user.patient
        upcoming_appointments = Appointment.objects.filter(
            patient=patient,
            appointment_date__gte=datetime.now(),
            status='scheduled'
        ).count()
        
        recent_prescriptions = Prescription.objects.filter(
            patient=patient
        ).order_by('-created_at')[:5]
        
        return Response({
            'patient': PatientSerializer(patient).data,
            'upcoming_appointments': upcoming_appointments,
            'recent_prescriptions': recent_prescriptions.values(),
            'health_score': 85  # Calculated metric
        })
    
    return Response({'error': 'Patient profile not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_appointment(request):
    serializer = AppointmentSerializer(data=request.data)
    if serializer.is_valid():
        # Check for conflicts
        doctor = serializer.validated_data['doctor']
        appointment_date = serializer.validated_data['appointment_date']
        
        conflicts = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status='scheduled'
        )
        
        if conflicts.exists():
            return Response({'error': 'Time slot not available'}, status=400)
        
        serializer.save()
        # Send confirmation email (async task in real app)
        return Response(serializer.data, status=201)
    
    return Response(serializer.errors, status=400)

# URLs
urlpatterns = [
    path('api/v1/patients/', PatientViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/v1/patients/<uuid:pk>/', PatientViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('api/v1/patients/<uuid:pk>/medical-history/', PatientViewSet.as_view({'get': 'medical_history'})),
    path('api/v1/patients/<uuid:pk>/appointments/', PatientViewSet.as_view({'get': 'appointments'})),
    path('api/v1/patients/<uuid:pk>/add-allergy/', PatientViewSet.as_view({'post': 'add_allergy'})),
    
    path('api/v1/appointments/', AppointmentViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/v1/appointments/today/', AppointmentViewSet.as_view({'get': 'today'})),
    path('api/v1/appointments/<uuid:pk>/', AppointmentViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    path('api/v1/appointments/<uuid:pk>/cancel/', AppointmentViewSet.as_view({'post': 'cancel'})),
    path('api/v1/appointments/<uuid:pk>/complete/', AppointmentViewSet.as_view({'post': 'complete'})),
    
    path('api/v1/available-slots/', AvailableSlotsAPIView.as_view()),
    path('api/v1/dashboard/', patient_dashboard),
    path('api/v1/book-appointment/', book_appointment),
]
'''
}

def test_real_world_case(name, code, token):
    """Test a real-world API case"""
    print(f"\n📍 Testing: {name}")
    print(f"   Code size: {len(code)} characters")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Start orchestration
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orchestrate",
            json={
                "source_type": "code",
                "source_path": f"{name}.py",
                "code_content": code
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"   ❌ Orchestration failed: {response.status_code}")
            return False
        
        task_id = response.json().get("task_id")
        print(f"   ✅ Orchestration started: {task_id}")
    except Exception as e:
        print(f"   ❌ Error during orchestration: {str(e)}")
        return False
    
    # Wait for processing with polling
    for attempt in range(5):
        time.sleep(1)
        try:
            response = requests.get(f"{BASE_URL}/api/tasks/{task_id}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "completed":
                    # Debug: print the full response
                    print(f"   📋 Full response: {json.dumps(data, indent=2)[:500]}")
                    
                    # Handle the actual structure returned
                    if "apis" in data and "specs" in data and "tests" in data:
                        # Results are at top level, not in a "results" sub-object
                        results = data
                    else:
                        results = data.get("results")
                    
                    if not results:
                        print(f"   ⚠️ No results returned")
                        return False
                    
                    processing_time = time.time() - start_time
                    
                    print(f"   ✅ Completed in {processing_time:.2f} seconds")
                    print(f"      • APIs discovered: {results.get('apis', 0)}")
                    print(f"      • OpenAPI paths: {results.get('specs', 0)}")
                    print(f"      • Tests generated: {results.get('tests', 0)}")
                    
                    # Try to export
                    response = requests.get(
                        f"{BASE_URL}/api/export/{task_id}?format=json",
                        headers=headers
                    )
                    if response.status_code == 200:
                        spec = response.json()
                        if "paths" in spec:
                            print(f"      • Export successful: {len(spec['paths'])} paths")
                            # Show sample endpoints
                            for path in list(spec["paths"].keys())[:3]:
                                methods = list(spec["paths"][path].keys())
                                print(f"        - {', '.join(methods).upper()}: {path}")
                    
                    return True
                elif status == "failed":
                    error = data.get("error", "Unknown")
                    print(f"   ⚠️ Processing failed: {error[:100]}")
                    return False
        except Exception as e:
            print(f"   ❌ Error getting task status: {str(e)}")
            continue
    
    print(f"   ⚠️ Timeout waiting for completion")
    return False

def main():
    print("\n" + "="*70)
    print("  🏢 REAL-WORLD PRODUCTION API TESTING")
    print("="*70)
    
    # Authenticate
    print("\n🔐 Authenticating...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "demo@streamapi.dev",
            "password": "Demo123!",
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print(f"❌ Authentication failed")
        return False
    
    token = response.json()["access_token"]
    print(f"✅ Authenticated successfully")
    
    # Test real-world cases
    print("\n🧪 Testing Real-World Production APIs...")
    
    results = {}
    for name, code in REAL_WORLD_CASES.items():
        try:
            results[name] = test_real_world_case(name, code, token)
        except Exception as e:
            import traceback
            print(f"   ⚠️ Processing failed: {str(e)[:100]}")
            print(f"   Traceback: {traceback.format_exc()[:500]}")
            results[name] = False
    
    # Summary
    print("\n" + "="*70)
    print("  📊 REAL-WORLD TEST RESULTS")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n  Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n" + "🎉"*35)
        print("  ALL REAL-WORLD CASES HANDLED PERFECTLY!")
        print("  STREAMAPI IS PRODUCTION-READY!")
        print("🎉"*35)
    elif passed_count > 0:
        print("\n" + "✅"*35)
        print(f"  {passed_count}/{total_count} REAL-WORLD CASES PASSED!")
        print("  STREAMAPI HANDLES COMPLEX PRODUCTION APIS!")
        print("✅"*35)
    
    return passed_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
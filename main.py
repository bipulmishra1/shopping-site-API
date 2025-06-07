from fastapi import FastAPI, Query, Depends, HTTPException
import os
import pandas as pd
import uvicorn
from pydantic import BaseModel
from typing import Optional
from fastapi_utils.tasks import repeat_every
from passlib.context import CryptContext
from jose import JWTError, jwt
import requests
from datetime import datetime, timedelta

# Initialize FastAPI app
app = FastAPI()

# Keep-Alive Task (Prevents Shutdown)
@app.on_event("startup")
@repeat_every(seconds=600)  # Runs every 10 minutes
def keep_alive():
    print("Keeping server active...")

# ------------------- Shopping Search API -------------------

# Load CSV file
file_path = os.path.join(os.path.dirname(__file__), "data", "Flipkart_Mobiles.csv")

try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    df = None
    print(f"Error: CSV file not found at {file_path}. Ensure it's included in GitHub.")

@app.get("/home")
def home():
    return {"message": "Search API is running!"}

@app.get("/search/")
def search_mobiles(
    brand: str = Query(None, description="Search for a brand"),
    model: str = Query(None, description="Search for a model"),
    color: str = Query(None, description="Search for a color"),
    sort_by: str = Query(None, description="Sort by 'price' or 'rating'"),
    order: str = Query("asc", description="Sort order: 'asc' or 'desc'"),
    limit: int = Query(10, description="Number of results per page")
):
    if df is None:
        return {"error": "CSV file missing or not loaded correctly."}

    result = df.copy()

    filters = {"Brand": brand, "Model": model, "Color": color}
    for column, value in filters.items():
        if value:
            result = result[result[column].str.contains(value, case=False, na=False)]

    if sort_by in ["price", "rating"]:
        column = "Selling Price" if sort_by == "price" else "Rating"
        result = result.sort_values(by=column, ascending=(order == "asc"))

    result = result.head(limit).dropna()

    return result.to_dict(orient="records")

# ------------------- User Authentication API -------------------

# Secret key & algorithm for JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simulated user database
fake_users_db = {
    "test_user": {
        "username": "test_user",
        "full_name": "Test User",
        "hashed_password": pwd_context.hash("test123"),
        "disabled": False
    }
}

# Pydantic models
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    return fake_users_db.get(username)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login", response_model=Token)
def login(user: User):
    db_user = get_user(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=60))
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------- Test Login Request -------------------

def test_login():
    url = "http://127.0.0.1:8000/login"
    data = {
        "username": "test_user",
        "password": "test123"
    }
    response = requests.post(url, json=data)
    print(response.json())  # Should return JWT token

# Uncomment below to test login from a script:
# test_login()

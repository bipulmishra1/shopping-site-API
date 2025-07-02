import os
import pandas as pd
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, Query
from contextlib import asynccontextmanager

# Load environment variables (like MONGO_URI)
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Setup MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client["Shopcart"]
cart_collection = db["carts"]
products_collection = db["products"]
users_collection = db["users"]
orders_collection = db["orders"]

# Load the CSV file for Flipkart mobile data
file_path = os.path.join(os.path.dirname(__file__), "data", "Flipkart_Mobiles.csv")
try:
    df = pd.read_csv(file_path)
    print("✅ CSV loaded successfully.")
except FileNotFoundError:
    df = None
    print(f"❌ CSV file not found at {file_path}.")

# Lifespan event handler for MongoDB connectivity
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
    yield

# FastAPI app instance
app = FastAPI(lifespan=lifespan)

# Home route
@app.get("/home")
def home():
    return {"message": "Search API is running!"}

# CSV-based product search with Product Photo field included
@app.get("/search/")
def search_mobiles(
    brand: str = Query(None, description="Search for a brand"),
    model: str = Query(None, description="Search for a model"),
    color: str = Query(None, description="Search for a color"),
    sort_by: str = Query(None, description="Sort by 'price' or 'rating'"),
    order: str = Query("asc", description="Sort order: 'asc' or 'desc'")
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

    result = result.dropna()

    # ✅ Ensure Product Photo is included in response
    return result.to_dict(orient="records")

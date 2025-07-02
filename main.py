import os
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import Optional
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

# Load env variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Connect to Atlas
client = AsyncIOMotorClient(MONGO_URI)
db = client["fastapi_auth"]
products_collection = db["products"]

# Handle lifespan startup tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
    yield

# FastAPI instance
app = FastAPI(lifespan=lifespan)

# Root route
@app.get("/home")
def home():
    return {"message": "Search API is running from MongoDB Atlas!"}

# Search endpoint
@app.get("/search/")
async def search_mobiles(
    brand: Optional[str] = Query(None, description="Search by brand"),
    model: Optional[str] = Query(None, description="Search by model"),
    color: Optional[str] = Query(None, description="Search by color"),
    sort_by: Optional[str] = Query(None, description="Sort by 'price' or 'rating'"),
    order: Optional[str] = Query("asc", description="Sort order: 'asc' or 'desc'")
):
    query = {}

    if brand:
        query["Brand"] = {"$regex": brand, "$options": "i"}
    if model:
        query["Model"] = {"$regex": model, "$options": "i"}
    if color:
        query["Color"] = {"$regex": color, "$options": "i"}

    sort_field = None
    if sort_by == "price":
        sort_field = "Selling Price"
    elif sort_by == "rating":
        sort_field = "Rating"

    cursor = products_collection.find(query)
    if sort_field:
        cursor = cursor.sort(sort_field, 1 if order == "asc" else -1)

    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string for JSON serialization
        doc["Product Photo"] = doc.get("Product Photo", "")
        results.append(doc)

    return JSONResponse(content=results)

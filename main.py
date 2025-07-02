import os
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URI)
db = client["fastapi_auth"]
products_collection = db["Project"]



# Lifespan event for MongoDB ping
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
    yield

# FastAPI app instance
app = FastAPI(lifespan=lifespan)

# Mount static folder for favicon
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve favicon.ico
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))

# Home route
@app.get("/home")
def home():
    return {"message": "Search API is running from MongoDB Atlas!"}

# Search route
@app.get("/search/")
async def search_mobiles(
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query("asc")
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
        doc["_id"] = str(doc["_id"])
        doc["Product Photo"] = doc.get("Product Photo", "")
        results.append(doc)

    return JSONResponse(content=results)

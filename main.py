from fastapi import FastAPI, Query
import os
import pandas as pd
import uvicorn
from pydantic import BaseModel
from typing import Optional
from fastapi_utils.tasks import repeat_every



# Change the path to match Render's directory structure
file_path = os.path.join(os.path.dirname(__file__), "data", "Flipkart_Mobiles.csv")

try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    df = None
    print(f"Error: CSV file not found at {file_path}. Ensure it's included in GitHub.")




# Initialize FastAPI app
app = FastAPI()

# Keep-Alive Task (Prevents Shutdown)
@app.on_event("startup")
@repeat_every(seconds=600)  # Runs every 10 minutes
def keep_alive():
    print("Keeping server active...")

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
    result = df.copy()

    # Apply filters based on query parameters (case-insensitive, partial matches)
    if brand:
        result = result[result["Brand"].str.contains(brand, case=False, na=False)]
    if model:
        result = result[result["Model"].str.contains(model, case=False, na=False)]
    if color:
        result = result[result["Color"].str.contains(color, case=False, na=False)]

    # Sort results
    if sort_by in ["price", "rating"]:
        column = "Selling Price" if sort_by == "price" else "Rating"
        result = result.sort_values(by=column, ascending=(order == "asc"))

    # Limit results (pagination)
    result = result.head(limit)

    result = result.dropna()  # Remove rows with NaN values


    print(result.head())
    return result.to_dict(orient="records")


# # class FilterItems(BaseModel):
# #     brand: str 
# #     model: Optional[str] = None
# #     color: Optional[str] = None 
# #     sort_by: Optional[str] = None 
# #     order: Optional[str] = None 
# #     limit: Optional[int] = 10 



# @app.post("/search/")
# def search_mobiles_post(body:FilterItems):
#     result = df.copy()

#     # Apply filters based on query parameters (case-insensitive, partial matches)
#     if body.brand:
#         result = result[result["Brand"].str.contains(body.brand, case=False, na=False)]
#     if body.model:
#         result = result[result["Model"].str.contains(body.model, case=False, na=False)]
#     if body.color:
#         result = result[result["Color"].str.contains(body.color, case=False, na=False)]

#     # Sort results
#     if body.sort_by in ["price", "rating"]:
#         column = "Selling Price" if body.sort_by == "price" else "Rating"
#         result = result.sort_values(by=column, ascending=(body.order == "asc"))

#     # Limit results (pagination)
#     result = result.head(body.limit)

#     # Handle case where no matches are found
#     if result.empty:
#         return {"message": "No matches found for the given filters"}

#     return result.to_dict(orient="records")


# if __name__== "__main__":
#     uvicorn.run(app, host ="127.0.0.1",port= 8000 )




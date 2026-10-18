from fastapi import  FastAPI

app=FastAPI()
@app.get("/")
def home():
    return {"message":"hello"}
@app.get("/users")
def get_users():
    return {"users":["a","b","c"]}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

@app.get("/products")
def get_products(category: str, limit: int = 10):
    return {
        "category": category,
        "limit": limit
    }


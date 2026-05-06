from fastapi import FastAPI, HTTPException
import requests
import os
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


Instrumentator().instrument(app).expose(app)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://data-service:8000")

@app.get("/status")
def get_system_status():
    return {
        "service": "Logic Gateway",
        "auth_health": requests.get(f"{AUTH_SERVICE_URL}/health").json(),
        "status": "Ready to process rentals"
    }

@app.get("/catalog")
def get_catalog():
    response = requests.get(f"{DATA_SERVICE_URL}/scooters")
    return response.json()

@app.post("/admin/add-scooter")
def add_scooter(scooter_data: dict):
    response = requests.post(f"{DATA_SERVICE_URL}/scooters", json=scooter_data)
    return response.json()

@app.post("/rent")
def rent_scooter(rental_data: dict):
    # Get user info from Data Service
    scooters = requests.get(f"{DATA_SERVICE_URL}/scooters").json()
    
    # 2. Search for the scooter in the list and check availability
    target = next((s for s in scooters if s['id'] == rental_data['scooter_id']), None)
    
    if not target:
        raise HTTPException(status_code=404, detail="Scooter not found")
    
    if not target['is_available']:
        raise HTTPException(status_code=400, detail="Scooter already rented")

    # 3. Execute the rental by updating the scooter's availability in the Data Service
    requests.put(f"{DATA_SERVICE_URL}/scooters/{target['id']}/rent?available=false")
    
    return {
        "status": "Success",
        "message": f"User {rental_data['username']} has rented {target['model']}"
    }
from fastapi import FastAPI, HTTPException
import requests
import os
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
import time


def release_scooter_task(scooter_id: int):
    time.sleep(15) 
    requests.put(f"{DATA_SERVICE_URL}/scooters/{scooter_id}/rent?available=true")
    print(f"DEBUG: Scooter {scooter_id} has been automatically released.")


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
def rent_scooter(rental_data: dict, background_tasks: BackgroundTasks):
    # 1. Validate user (same as before)
    user_response = requests.get(f"{DATA_SERVICE_URL}/users/{rental_data['username']}")
    if user_response.status_code != 200:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check scooter availability
    scooters = requests.get(f"{DATA_SERVICE_URL}/scooters").json()
    target = next((s for s in scooters if s['id'] == rental_data['scooter_id']), None)
    
    if not target or not target['is_available']:
        raise HTTPException(status_code=400, detail="Scooter not available")

    # 3. Execute rental
    requests.put(f"{DATA_SERVICE_URL}/scooters/{target['id']}/rent?available=false")
    
    background_tasks.add_task(release_scooter_task, target['id'])
    
    return {
        "status": "Success",
        "message": f"Rental started for 15 seconds. It will expire automatically."
    }
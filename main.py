from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://data-service:8000")

@app.get("/status")
def get_system_status():
    return {
        "service": "Logic Gateway",
        "auth_health": requests.get(f"{AUTH_SERVICE_URL}/health").json(),
        "status": "Ready to process rentals"
    }

@app.post("/rent")
def rent_scooter(rental_data: dict):
    # Logica de business: 
    # 1. Verificăm userul prin Data Service
    # 2. Dacă e valid, procesăm închirierea
    return {"message": f"Scooter {rental_data['scooter_id']} rented to user {rental_data['username']}"}
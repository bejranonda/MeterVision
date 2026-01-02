from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from typing import List
from .database import create_db_and_tables, get_session
from .models import (
    Project, ProjectBase, 
    Customer, CustomerBase, 
    Building, BuildingBase, 
    Place, PlaceBase, 
    Meter, MeterBase, 
    Reading, ReadingBase
)
from .services.ocr import MockMeterReader, save_upload_file
import os
import uuid

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Dependency
def get_db():
    from .database import get_session
    return next(get_session())

# --- Projects ---
@app.post("/projects/", response_model=Project)
def create_project(project: ProjectBase, session: Session = Depends(get_session)):
    db_project = Project.from_orm(project)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[Project])
def read_projects(session: Session = Depends(get_session)):
    projects = session.exec(select(Project)).all()
    return projects

# --- Customers ---
@app.post("/customers/", response_model=Customer)
def create_customer(customer: CustomerBase, session: Session = Depends(get_session)):
    db_customer = Customer.from_orm(customer)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer

# --- Buildings ---
@app.post("/buildings/", response_model=Building)
def create_building(building: BuildingBase, session: Session = Depends(get_session)):
    db_building = Building.from_orm(building)
    session.add(db_building)
    session.commit()
    session.refresh(db_building)
    return db_building

# --- Places ---
@app.post("/places/", response_model=Place)
def create_place(place: PlaceBase, session: Session = Depends(get_session)):
    db_place = Place.from_orm(place)
    session.add(db_place)
    session.commit()
    session.refresh(db_place)
    return db_place

# --- Meters ---
@app.post("/meters/", response_model=Meter)
def create_meter(meter: MeterBase, session: Session = Depends(get_session)):
    db_meter = Meter.from_orm(meter)
    session.add(db_meter)
    session.commit()
    session.refresh(db_meter)
    return db_meter

@app.get("/meters/{serial_number}", response_model=Meter)
def read_meter_by_serial(serial_number: str, session: Session = Depends(get_session)):
    meter = session.exec(select(Meter).where(Meter.serial_number == serial_number)).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    return meter

# --- Readings ---
@app.post("/meters/{serial_number}/reading", response_model=Reading)
async def upload_reading(
    serial_number: str, 
    file: UploadFile = File(...), 
    session: Session = Depends(get_session)
):
    # 1. Verify Meter Exists
    meter = session.exec(select(Meter).where(Meter.serial_number == serial_number)).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    
    # 2. Save Image
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    upload_dir = "/home/ogema/MeterReading/uploads"
    file_path = os.path.join(upload_dir, filename)
    save_upload_file(file, file_path)
    
    # 3. Process Image (Mock for now)
    reader = MockMeterReader()
    reading_value = reader.read_meter(file_path)
    
    # 4. Save Reading
    reading = Reading(
        value=reading_value,
        raw_image_path=file_path,
        meter_id=meter.id,
        status="Verified", # Mock is always right?
        ocr_confidence=1.0
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)
    return reading

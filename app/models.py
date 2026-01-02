from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel

class ProjectBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customers: List["Customer"] = Relationship(back_populates="project")

class CustomerBase(SQLModel):
    name: str
    email: Optional[str] = None
    project_id: int = Field(foreign_key="project.id")

class Customer(CustomerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project: Project = Relationship(back_populates="customers")
    buildings: List["Building"] = Relationship(back_populates="customer")

class BuildingBase(SQLModel):
    name: str
    address: str
    customer_id: int = Field(foreign_key="customer.id")

class Building(BuildingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer: Customer = Relationship(back_populates="buildings")
    places: List["Place"] = Relationship(back_populates="building")

class PlaceBase(SQLModel):
    name: str
    description: Optional[str] = None
    building_id: int = Field(foreign_key="building.id")

class Place(PlaceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    building: Building = Relationship(back_populates="places")
    meters: List["Meter"] = Relationship(back_populates="place")

class MeterBase(SQLModel):
    serial_number: str = Field(index=True, unique=True)
    meter_type: str # Gas, Electricity, Heat
    unit: str # m3, kWh
    place_id: int = Field(foreign_key="place.id")

class Meter(MeterBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    place: Place = Relationship(back_populates="meters")
    readings: List["Reading"] = Relationship(back_populates="meter")

class ReadingBase(SQLModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float
    raw_image_path: str
    meter_id: int = Field(foreign_key="meter.id")
    status: str = Field(default="Pending") # Pending, Verified, Failed
    ocr_confidence: Optional[float] = None

class Reading(ReadingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meter: Meter = Relationship(back_populates="readings")

"""Asset hierarchy models (Project → Customer → Building → Place → Meter → Reading)."""
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from .base import TimestampMixin

if TYPE_CHECKING:
    from .tenant import Organization
    from .device import Camera
    from .installation import InstallationSession



class ProjectBase(SQLModel):
    """Base project attributes."""
    name: str = Field(index=True)
    description: Optional[str] = None
    organization_id: int = Field(foreign_key="organization.id", index=True)


class Project(ProjectBase, TimestampMixin, table=True):
    """
    Project - Top-level container in the asset hierarchy.
    
    Now scoped to organizations for multi-tenancy.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    organization: "Organization" = Relationship(back_populates="projects")
    customers: List["Customer"] = Relationship(back_populates="project")


class CustomerBase(SQLModel):
    """Base customer attributes."""
    name: str
    email: Optional[str] = None
    project_id: int = Field(foreign_key="project.id")
    organization_id: int = Field(foreign_key="organization.id", index=True)


class Customer(CustomerBase, TimestampMixin, table=True):
    """Customer - Second level in the asset hierarchy."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    project: Project = Relationship(back_populates="customers")
    buildings: List["Building"] = Relationship(back_populates="customer")


class BuildingBase(SQLModel):
    """Base building attributes."""
    name: str
    address: str
    customer_id: int = Field(foreign_key="customer.id")
    organization_id: int = Field(foreign_key="organization.id", index=True)


class Building(BuildingBase, TimestampMixin, table=True):
    """Building - Third level in the asset hierarchy."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    customer: Customer = Relationship(back_populates="buildings")
    places: List["Place"] = Relationship(back_populates="building")


class PlaceBase(SQLModel):
    """Base place attributes."""
    name: str
    description: Optional[str] = None
    building_id: int = Field(foreign_key="building.id")
    organization_id: int = Field(foreign_key="organization.id", index=True)


class Place(PlaceBase, TimestampMixin, table=True):
    """Place - Fourth level in the asset hierarchy (e.g., 'Basement', 'Kitchen')."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    building: Building = Relationship(back_populates="places")
    meters: List["Meter"] = Relationship(back_populates="place")


class MeterBase(SQLModel):
    """Base meter attributes."""
    serial_number: str = Field(index=True, unique=True)
    meter_type: str  # Gas, Electricity, Heat
    unit: str  # m3, kWh
    place_id: Optional[int] = Field(default=None, foreign_key="place.id")
    organization_id: int = Field(foreign_key="organization.id", index=True)
    aoi_config: Optional[str] = None  # JSON string for AOI coordinates
    custom_prompt: Optional[str] = None  # Optimized prompt for this specific meter
    expected_reading: Optional[float] = None  # The reading provided during calibration


class Meter(MeterBase, TimestampMixin, table=True):
    """
    Meter - Fifth level in the asset hierarchy (the actual device).
    
    Enhanced with organization_id for quick filtering.
    Can have an associated camera for automated readings.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    place: Place = Relationship(back_populates="meters")
    readings: List["Reading"] = Relationship(back_populates="meter")
    camera: Optional["Camera"] = Relationship(back_populates="meter")
    installation_sessions: List["InstallationSession"] = Relationship(back_populates="meter")


class ReadingBase(SQLModel):
    """Base reading attributes."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float
    raw_image_path: str
    meter_id: int = Field(foreign_key="meter.id")
    organization_id: int = Field(foreign_key="organization.id", index=True)
    status: str = Field(default="Pending")  # Pending, Verified, Failed
    ocr_confidence: Optional[float] = None


class Reading(ReadingBase, table=True):
    """
    Reading - Historical data points from meters.
    
    Enhanced with organization_id for audit trail and multi-tenant queries.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    meter: Meter = Relationship(back_populates="readings")

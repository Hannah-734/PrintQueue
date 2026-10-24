"""Pydantic models: what the API accepts and returns."""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    queued = "queued"
    printing = "printing"
    post_processing = "post_processing"
    inspection = "inspection"
    shipped = "shipped"


class InspectionResult(str, Enum):
    passed = "pass"
    failed = "fail"


class Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Inspections ----
class InspectionCreate(BaseModel):
    result: InspectionResult
    notes: Optional[str] = None


class InspectionOut(Orm):
    id: int
    result: InspectionResult
    notes: Optional[str]
    inspected_at: datetime


# ---- Jobs ----
class JobBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    customer: Optional[str] = Field(default=None, max_length=120)
    material: str = Field(min_length=1, max_length=30)
    deadline: date
    printer_id: Optional[int] = None
    layer_height_mm: Optional[float] = Field(default=None, gt=0, le=1)
    infill_pct: Optional[int] = Field(default=None, ge=0, le=100)
    nozzle_temp_c: Optional[int] = Field(default=None, ge=0, le=500)
    bed_temp_c: Optional[int] = Field(default=None, ge=0, le=200)
    notes: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    """All fields optional so the client can send only what changed."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    customer: Optional[str] = None
    material: Optional[str] = None
    deadline: Optional[date] = None
    status: Optional[Status] = None
    printer_id: Optional[int] = None
    layer_height_mm: Optional[float] = Field(default=None, gt=0, le=1)
    infill_pct: Optional[int] = Field(default=None, ge=0, le=100)
    nozzle_temp_c: Optional[int] = Field(default=None, ge=0, le=500)
    bed_temp_c: Optional[int] = Field(default=None, ge=0, le=200)
    notes: Optional[str] = None


class JobOut(Orm):
    id: int
    name: str
    customer: Optional[str]
    material: str
    deadline: date
    status: Status
    printer_id: Optional[int]
    printer_name: Optional[str]
    layer_height_mm: Optional[float]
    infill_pct: Optional[int]
    nozzle_temp_c: Optional[int]
    bed_temp_c: Optional[int]
    notes: Optional[str]
    created_at: datetime
    inspections: list[InspectionOut] = []


# ---- Printers ----
class PrinterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    model: Optional[str] = None


class MaintenanceCreate(BaseModel):
    task: str = Field(min_length=1, max_length=120)
    notes: Optional[str] = None


class MaintenanceOut(Orm):
    id: int
    task: str
    notes: Optional[str]
    performed_at: datetime


class PrinterOut(Orm):
    id: int
    name: str
    model: Optional[str]
    last_maintenance_at: Optional[datetime]
    maintenance_logs: list[MaintenanceOut] = []

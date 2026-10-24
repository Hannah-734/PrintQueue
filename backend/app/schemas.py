from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

Status = Literal["queued", "printing", "post_processing", "inspection", "shipped"]


class JobCreate(BaseModel):
    name: str = Field(min_length=1)
    material: str = Field(min_length=1)
    deadline: date
    printer_id: Optional[int] = None
    layer_height: Optional[float] = Field(None, gt=0)
    infill: Optional[int] = Field(None, ge=0, le=100)
    nozzle_temp: Optional[int] = None
    bed_temp: Optional[int] = None
    notes: str = ""


class JobUpdate(BaseModel):
    name: Optional[str] = None
    material: Optional[str] = None
    deadline: Optional[date] = None
    status: Optional[Status] = None
    printer_id: Optional[int] = None
    layer_height: Optional[float] = Field(None, gt=0)
    infill: Optional[int] = Field(None, ge=0, le=100)
    nozzle_temp: Optional[int] = None
    bed_temp: Optional[int] = None
    notes: Optional[str] = None


class JobOut(JobCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: Status
    inspection_note: str = ""
    created_at: datetime


class Inspection(BaseModel):
    passed: bool
    note: str = ""


class PrinterCreate(BaseModel):
    name: str = Field(min_length=1)


class MaintenanceCreate(BaseModel):
    note: str = Field(min_length=1)


class MaintenanceOut(MaintenanceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    performed_at: datetime


class PrinterOut(PrinterCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    logs: list[MaintenanceOut] = []

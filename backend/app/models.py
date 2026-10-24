from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

STATUSES = ["queued", "printing", "post_processing", "inspection", "shipped"]


class Printer(Base):
    __tablename__ = "printers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    logs = relationship("MaintenanceLog", cascade="all, delete-orphan",
                        order_by="MaintenanceLog.performed_at.desc()")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    id = Column(Integer, primary_key=True)
    printer_id = Column(Integer, ForeignKey("printers.id"), nullable=False)
    note = Column(Text, nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    material = Column(String, nullable=False)
    deadline = Column(Date, nullable=False)
    status = Column(String, default="queued", nullable=False)
    printer_id = Column(Integer, ForeignKey("printers.id"), nullable=True)
    layer_height = Column(Float, nullable=True)
    infill = Column(Integer, nullable=True)
    nozzle_temp = Column(Integer, nullable=True)
    bed_temp = Column(Integer, nullable=True)
    notes = Column(Text, default="")
    inspection_note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

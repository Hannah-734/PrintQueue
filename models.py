"""Database schema.

printers      -> the machines
jobs          -> one row per print job, with the print settings used
inspections   -> pass/fail record for a job (many per job: a reprint gets re-inspected)
maintenance   -> service log per printer
"""
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Printer(Base):
    __tablename__ = "printers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    model: Mapped[Optional[str]] = mapped_column(String(80))

    jobs: Mapped[list["Job"]] = relationship(back_populates="printer")
    maintenance_logs: Mapped[list["MaintenanceLog"]] = relationship(
        back_populates="printer",
        cascade="all, delete-orphan",
        order_by="MaintenanceLog.performed_at.desc()",
    )

    @property
    def last_maintenance_at(self) -> Optional[datetime]:
        return self.maintenance_logs[0].performed_at if self.maintenance_logs else None


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    customer: Mapped[Optional[str]] = mapped_column(String(120))
    material: Mapped[str] = mapped_column(String(30))
    deadline: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    printer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("printers.id"))

    # Print settings, logged so the process is repeatable
    layer_height_mm: Mapped[Optional[float]] = mapped_column(Float)
    infill_pct: Mapped[Optional[int]] = mapped_column(Integer)
    nozzle_temp_c: Mapped[Optional[int]] = mapped_column(Integer)
    bed_temp_c: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    printer: Mapped[Optional[Printer]] = relationship(back_populates="jobs")
    inspections: Mapped[list["Inspection"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="Inspection.inspected_at.desc()",
    )

    @property
    def printer_name(self) -> Optional[str]:
        return self.printer.name if self.printer else None


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    result: Mapped[str] = mapped_column(String(10))  # "pass" | "fail"
    notes: Mapped[Optional[str]] = mapped_column(Text)
    inspected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped[Job] = relationship(back_populates="inspections")


class MaintenanceLog(Base):
    __tablename__ = "maintenance"

    id: Mapped[int] = mapped_column(primary_key=True)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id"))
    task: Mapped[str] = mapped_column(String(120))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    printer: Mapped[Printer] = relationship(back_populates="maintenance_logs")

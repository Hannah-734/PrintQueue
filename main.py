import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine, get_db


def seed_printers() -> None:
    """Give a fresh database a few machines so the dashboard isn't empty."""
    with SessionLocal() as db:
        if db.scalar(select(models.Printer).limit(1)) is None:
            db.add_all(
                [
                    models.Printer(name="Prusa MK4", model="Prusa MK4"),
                    models.Printer(name="Ender 3 V3", model="Creality Ender 3 V3"),
                    models.Printer(name="Bambu P1S", model="Bambu Lab P1S"),
                ]
            )
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_printers()
    yield


app = FastAPI(title="PrintQueue API", version="1.0.0", lifespan=lifespan)

# Comma-separated list of allowed frontend origins, e.g.
# FRONTEND_ORIGINS=https://printqueue.vercel.app,http://localhost:5173
origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------------ jobs
def get_job_or_404(db: Session, job_id: int) -> models.Job:
    job = db.get(models.Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def check_printer(db: Session, printer_id: Optional[int]) -> None:
    if printer_id is not None and db.get(models.Printer, printer_id) is None:
        raise HTTPException(status_code=422, detail="Printer does not exist")


@app.get("/api/jobs", response_model=list[schemas.JobOut])
def list_jobs(
    status: Optional[schemas.Status] = None,
    material: Optional[str] = None,
    printer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Jobs sorted by deadline, soonest first. Filter by status, material or printer."""
    query = select(models.Job).order_by(models.Job.deadline, models.Job.created_at)
    if status:
        query = query.where(models.Job.status == status.value)
    if material:
        query = query.where(models.Job.material == material)
    if printer_id:
        query = query.where(models.Job.printer_id == printer_id)
    return db.scalars(query).all()


@app.post("/api/jobs", response_model=schemas.JobOut, status_code=201)
def create_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    check_printer(db, payload.printer_id)
    job = models.Job(**payload.model_dump(), status=schemas.Status.queued.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.get("/api/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    return get_job_or_404(db, job_id)


@app.patch("/api/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(job_id: int, payload: schemas.JobUpdate, db: Session = Depends(get_db)):
    job = get_job_or_404(db, job_id)
    changes = payload.model_dump(exclude_unset=True)
    check_printer(db, changes.get("printer_id"))
    if "status" in changes:
        changes["status"] = changes["status"].value
    for field, value in changes.items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    db.delete(get_job_or_404(db, job_id))
    db.commit()


@app.post("/api/jobs/{job_id}/inspections", response_model=schemas.JobOut, status_code=201)
def inspect_job(job_id: int, payload: schemas.InspectionCreate, db: Session = Depends(get_db)):
    """Record an inspection. If the job is in inspection, a pass ships it and a fail sends it back to the queue."""
    job = get_job_or_404(db, job_id)
    db.add(models.Inspection(job_id=job.id, result=payload.result.value, notes=payload.notes))
    if job.status == schemas.Status.inspection.value:
        job.status = (
            schemas.Status.shipped.value
            if payload.result == schemas.InspectionResult.passed
            else schemas.Status.queued.value
        )
    db.commit()
    db.refresh(job)
    return job


# -------------------------------------------------------------- printers
@app.get("/api/printers", response_model=list[schemas.PrinterOut])
def list_printers(db: Session = Depends(get_db)):
    return db.scalars(select(models.Printer).order_by(models.Printer.name)).all()


@app.post("/api/printers", response_model=schemas.PrinterOut, status_code=201)
def create_printer(payload: schemas.PrinterCreate, db: Session = Depends(get_db)):
    if db.scalar(select(models.Printer).where(models.Printer.name == payload.name)):
        raise HTTPException(status_code=409, detail="A printer with that name already exists")
    printer = models.Printer(**payload.model_dump())
    db.add(printer)
    db.commit()
    db.refresh(printer)
    return printer


@app.post(
    "/api/printers/{printer_id}/maintenance",
    response_model=schemas.PrinterOut,
    status_code=201,
)
def log_maintenance(printer_id: int, payload: schemas.MaintenanceCreate, db: Session = Depends(get_db)):
    printer = db.get(models.Printer, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="Printer not found")
    db.add(models.MaintenanceLog(printer_id=printer.id, **payload.model_dump()))
    db.commit()
    db.refresh(printer)
    return printer

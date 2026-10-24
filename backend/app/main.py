from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)
app = FastAPI(title="PrintQueue")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


def get_job_or_404(db: Session, job_id: int) -> models.Job:
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


def check_printer(db: Session, printer_id: Optional[int]):
    if printer_id is not None and not db.get(models.Printer, printer_id):
        raise HTTPException(422, "Printer does not exist")


@app.get("/api/jobs", response_model=list[schemas.JobOut])
def list_jobs(material: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Job)
    if material:
        q = q.filter(models.Job.material == material)
    return q.order_by(models.Job.deadline, models.Job.id).all()


@app.post("/api/jobs", response_model=schemas.JobOut, status_code=201)
def create_job(data: schemas.JobCreate, db: Session = Depends(get_db)):
    check_printer(db, data.printer_id)
    job = models.Job(**data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.get("/api/jobs/{job_id}", response_model=schemas.JobOut)
def read_job(job_id: int, db: Session = Depends(get_db)):
    return get_job_or_404(db, job_id)


@app.patch("/api/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(job_id: int, data: schemas.JobUpdate, db: Session = Depends(get_db)):
    job = get_job_or_404(db, job_id)
    changes = data.model_dump(exclude_unset=True)
    check_printer(db, changes.get("printer_id"))
    for key, value in changes.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    db.delete(get_job_or_404(db, job_id))
    db.commit()


@app.post("/api/jobs/{job_id}/inspection", response_model=schemas.JobOut)
def inspect_job(job_id: int, result: schemas.Inspection, db: Session = Depends(get_db)):
    job = get_job_or_404(db, job_id)
    if job.status != "inspection":
        raise HTTPException(409, "Job is not in inspection")
    if not result.passed and not result.note.strip():
        raise HTTPException(422, "A failed inspection needs a note")
    job.status = "shipped" if result.passed else "queued"
    job.inspection_note = result.note
    db.commit()
    db.refresh(job)
    return job


@app.get("/api/printers", response_model=list[schemas.PrinterOut])
def list_printers(db: Session = Depends(get_db)):
    return db.query(models.Printer).order_by(models.Printer.name).all()


@app.post("/api/printers", response_model=schemas.PrinterOut, status_code=201)
def create_printer(data: schemas.PrinterCreate, db: Session = Depends(get_db)):
    printer = models.Printer(name=data.name)
    db.add(printer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A printer with that name already exists")
    db.refresh(printer)
    return printer


@app.post("/api/printers/{printer_id}/maintenance", response_model=schemas.PrinterOut,
          status_code=201)
def add_maintenance(printer_id: int, data: schemas.MaintenanceCreate,
                    db: Session = Depends(get_db)):
    printer = db.get(models.Printer, printer_id)
    if not printer:
        raise HTTPException(404, "Printer not found")
    db.add(models.MaintenanceLog(printer_id=printer_id, note=data.note))
    db.commit()
    db.refresh(printer)
    return printer

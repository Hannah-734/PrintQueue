# PrintQueue
Full-stack web app for tracking 3D-print jobs by deadline, material, and machine. Built with FastAPI, React, and SQLite
# PrintQueue

A full-stack web app for managing a 3D-print queue. It tracks each job by deadline,
material, and machine, and moves it through every stage from queued to shipped.

**Live demo:** https://YOUR-PRINTQUEUE-SITE.vercel.app

## Features

- Create, update, and delete print jobs through a REST API
- Live dashboard that shows jobs in columns: Queued, Printing, Post-processing, Inspection, Shipped
- Jobs sorted by deadline, with overdue and due-soon warnings
- Filter the queue by material
- Logs the print settings for each job (layer height, infill, nozzle and bed temperature) so results are repeatable
- Records inspection results: a pass ships the job, and a fail sends it back to the queue with a note
- Tracks maintenance history for each printer

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy |
| Database | SQLite |
| Frontend | React, Vite |
| Testing | pytest |

## Why I built it

I wanted a tool that treats 3D printing like a documented manufacturing process:
every job has a deadline, recorded settings, an inspection result, and a known printer.

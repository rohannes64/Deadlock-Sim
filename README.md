# Deadlock Detection Toolkit — Group 15

**OS CA2 Project** | R3E052B43, R3E052B44, R3E052B45

A web-based toolkit for detecting, visualizing, and recovering from deadlocks in operating systems.

## How to Run

```bash
pip install flask
python app.py
```

Then open your browser at: **http://localhost:5000**

## Features

- **Dashboard** — Live Resource Allocation Graph (RAG) + system log
- **Simulate** — Edit allocation/request matrices manually or load presets
- **Detection** — DFS cycle detection + Resource Allocation Matrix method
- **Recovery** — Terminate, Preempt, or Rollback processes to resolve deadlocks
- **Banker's Algorithm** — Safety check with safe sequence output

## Preset Scenarios

| Preset | Description |
|--------|-------------|
| 3-Process Circular | P0→R1→P1→R2→P2→R0→P0 |
| 2-Process Circular | Simple 2-process deadlock |
| Partial Deadlock | Only some processes deadlocked |
| Safe State | Textbook safe state (Banker's example) |

## Project Structure

```
deadlock_toolkit/
├── app.py              # Flask backend + algorithm implementations
├── requirements.txt
└── templates/
    └── index.html      # Single-page frontend (HTML + CSS + JS)
```

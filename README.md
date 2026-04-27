# AgriTwin-ZM v1.0

**Agricultural Digital Twin Simulation for Zambia**

A Python-based simulation tool for modelling Zambia's agricultural commodity supply chains, focusing on maize and tomato production, storage losses, supply-demand dynamics, and food security policy evaluation.

## Project Structure

```
AgriTwin-ZM/
├── main.py                  # Tkinter GUI launcher
├── gui.py                   # Desktop application interface
├── models/
│   ├── __init__.py
│   ├── maize.py             # Maize commodity model
│   └── tomato.py            # Tomato commodity model
├── engines/
│   ├── __init__.py
│   ├── supply_demand.py     # Supply & demand simulation engine
│   ├── storage_loss.py      # Storage loss simulator
│   └── policy.py            # Policy evaluation engine
├── reports/
│   ├── __init__.py
│   └── dashboard.py         # Reporting & export dashboard
├── data/
│   └── simulation_data.json # Sample / saved simulation data
├── tests/
│   └── test_all.py          # Unit tests
└── README.md
```

## Getting Started

```bash
python main.py
```

This launches the GUI with 4 tabs:
- Run Simulation: Execute maize or tomato simulations
- Dashboard: View reports and export to CSV/JSON/TXT
- Policy: Check FRA reserves and policy alerts
- Data: Manage simulation data

Sample data is pre-loaded, so you can immediately explore the Dashboard tab.

### API Mode (for web/mobile)

You can also launch a lightweight JSON API from the same entrypoint:

```bash
python main.py --mode api --host 127.0.0.1 --port 8000
```

Available endpoints:
- `GET /api/health`
- `POST /api/simulate/maize`
- `POST /api/simulate/tomato`

## Commodities

- **Maize**: staple grain; models production, storage capacity, moisture, monthly loss rates.
- **Tomato**: perishable crop; models shelf life, cold/open storage, daily spoilage.

## Running Tests

```bash
python -m unittest tests.test_all -v
```

## Web and Mobile Starter Guide

Keep the existing models and engines as the shared core. Build web and mobile as thin clients around them.

### 1) Start web support first (API-first)

- Expose simulations through one backend API route for maize and one for tomato.
- Return the same result dictionary already used by `ReportingDashboard`.
- Reuse current validation logic from model classes.

Suggested initial stack:

```bash
pip install fastapi uvicorn
```

### 2) Add a lightweight web UI

- Build a simple form page that posts to the API.
- Render returned JSON into cards or a table.
- Keep calculations only in Python backend.

### 3) Add mobile from the same API

- React Native, Flutter, or a PWA can all consume the same endpoints.
- Keep one backend contract for both web and mobile.
- Start with read-only simulation screens, then add export/download flows.

### 4) Migration sequence that keeps momentum

1. Stabilize API routes and payload schema.
2. Build web frontend against the API.
3. Reuse the same API in mobile app.
4. Keep GUI available as a local fallback while web/mobile mature.

## Documentation

For complete system architecture and documentation (Chunks 7 & 8), see **[DOCUMENTATION.md](DOCUMENTATION.md)**:
- System Documentation Overview
- UML Class Diagram specifications
- All class attributes, methods, and relationships
- Design patterns and extension examples

## License

Academic project - University of Zambia.


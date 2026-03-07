## RouteSense Logistics Dashboard

RouteSense is a Streamlit-based operations dashboard for route planning using real input files.

### What this app does

- Loads delivery points from `data/deliveries.csv`
- Loads vehicle capacity data from `data/fleet.csv`
- Builds an optimized route using OR-Tools (VRP)
- Shows operations, dispatch, and route performance views

### Run locally

1. Create/activate your virtual environment
2. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

3. Start the app:

	```bash
	streamlit run app.py
	```

### Data files

- `data/deliveries.csv` required columns: `id`, `location`, `lat`, `lon`
- Optional delivery column: `demand`
- `data/fleet.csv` required columns: `vehicle_id`, `capacity`

If any required columns are missing, the app shows a clear error in the UI.

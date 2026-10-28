# Supplier Reliability Scoring System

A Python and Streamlit project for evaluating supplier reliability using delivery, quality, cost, capacity, compliance, and disruption indicators. The included dataset is synthetic and should not be used for real supplier decisions without reviewing the scoring assumptions.

## Setup

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generate_data.py
python load_database.py
python scoring.py
python validate_data.py
python -m pytest -v -p no:cacheprovider
streamlit run app.py
```

The dashboard uses `supplier_reliability.db` in the project directory. `generate_data.py` creates the CSV input files in `output/`.

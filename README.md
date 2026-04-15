# NbS Project Financial Tracker

[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-30%2B%20passing-brightgreen)](tests/)

Streamlit web app for tracking Nature-based Solutions (NbS) project finances — budget allocation, disbursement timeline, partner payments, and burn rate. Built for PUR's project management workflow.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
# Open http://localhost:8501
```

## Features

- **Budget vs Actuals** — Grouped bar chart comparing budget, disbursed, and spent amounts per project
- **Burn Rate** — Monthly spending trends by category with utilization gauge
- **Partner Payments** — Payment status and pending disbursements per partner organization
- **Disbursement Timeline** — Cumulative disbursement area chart with category breakdown
- **Interactive Filters** — Filter by category, partner, and location
- **Excel Export** — Download multi-sheet financial report
- **CSV Upload** — Use your own data or the bundled Indonesian NbS sample dataset

## Sample Output

The app loads with 25 rows of realistic Indonesian NbS project data covering:
- Mangrove restoration, peatland rewetting, agroforestry, marine conservation
- Partners across Kalimantan, Riau, Sulawesi, Papua, Java, and more
- Budget range: $55,000 – $250,000 USD

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Data | Pandas |
| Charts | Plotly |
| Export | openpyxl |
| Tests | pytest |

## Project Structure

```
nbs-financial-tracker/
├── app.py                  # Main Streamlit application
├── src/
│   ├── data_loader.py      # CSV loading, validation, filtering
│   ├── calculations.py     # Financial computations
│   ├── charts.py           # Plotly chart builders
│   └── export.py           # Excel/CSV export utilities
├── demo/
│   └── sample_data.csv     # 25 rows of Indonesian NbS project data
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_data_loader.py # Data loading & validation tests
│   ├── test_calculations.py# Financial calculation tests
│   ├── test_charts.py      # Chart generation tests
│   ├── test_export.py      # Export functionality tests
│   └── test_integration.py # End-to-end pipeline tests
├── requirements.txt
├── LICENSE
└── README.md
```

## Running Tests

```bash
pytest tests/ -v
```

## License

[MIT](LICENSE)

# 🚀 TransactIQ — Enterprise Data Quality Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python) ![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=for-the-badge&logo=streamlit) ![SQLite](https://img.shields.io/badge/SQLite-Local-003B57?style=for-the-badge&logo=sqlite) ![Pandas](https://img.shields.io/badge/Pandas-Data%20Engine-150458?style=for-the-badge&logo=pandas)

TransactIQ is a premium, high-performance web application designed for enterprise data quality workflows. Built entirely in Python using Streamlit, it allows users to upload, validate, clean, and analyze massive transaction datasets with zero cloud dependencies.

![TransactIQ Screenshot](assets/logo.svg) <!-- Replace with actual screenshot path if available -->

## ✨ Features

- **Blazing Fast Processing** — Drag-and-drop CSV uploads processed via Pandas, instantly detecting schema anomalies and missing data.
- **Dynamic Validation Engine** — Flexible rule sets loaded straight from the database. Configure phone digits by country (e.g., India +91 requires 10 digits) right from the Settings UI.
- **Native Excel Generation** — Avoids the classic "Excel scientific notation bug". The engine natively exports cleaned datasets and error logs as auto-formatted `.xlsx` files. No more mangled phone numbers (`7.33E+10`) or squished dates (`########`)!
- **Offline "AI" Insights** — Generates incredibly smart data profiling insights without an API key. Uses a deterministic heuristic engine to find the most problematic fields, error types, and geographic failure trends.
- **Interactive Analytics** — Features global and per-dataset dashboards built with Plotly. Explore Data Survival Funnels, Hierarchical Error Treemaps, and historical Quality Score timelines.
- **Premium UI / UX** — Complete overhaul of Streamlit's default components. Features glassmorphism cards, vibrant gradient KPIs, smooth native AgGrid data tables, and intuitive tabbed navigation.

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend UI** | Streamlit, Streamlit-AgGrid |
| **Data Engine** | Pandas |
| **Database** | SQLite (SQLAlchemy ORM) |
| **Visualizations** | Plotly Express & Graph Objects |
| **Exports** | OpenPyXL (Excel), ReportLab (PDF) |

## 🚀 Quick Start

TransactIQ is designed to be effortlessly portable. You don't need Docker, PostgreSQL, or Node.js. 

### 1. Clone & Install
```bash
git clone https://github.com/PrachiMishra7/TransactIQ.git
cd TransactIQ

# Create a virtual environment (optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Platform
```bash
streamlit run app.py
```
Open **http://localhost:8501** in your browser.

## ☁️ Deployment (Streamlit Community Cloud)

TransactIQ features cross-platform pathing, making it 100% ready for free cloud deployment:
1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Click **New app**, select your repository, and set the Main file path to `app.py`.
4. Click **Deploy**!
*(Note: Because the "AI Insights" are built locally, you **do not** need to configure an `OPENAI_API_KEY` secret!)*

## 🧪 Testing with Sample Data

Upload `sample-data/transactions_sample.csv` (or any CSV) on the Upload page. The sample contains intentional data corruption to demonstrate the validation engine:
- Phone numbers lacking country codes or correct digit lengths.
- Malformed email domains.
- Total price calculation mismatches (Qty × Unit Price != Total).
- Delivery dates occurring *before* order dates.

## 📄 License
MIT License. Built as a demonstration for enterprise transaction processing pipelines.

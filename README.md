# TransactIQ — Transaction Data Quality Platform

A production-quality web application for validating, cleaning, and analyzing transaction datasets. Built for enterprise-grade data quality workflows with AI-assisted reporting.

![TransactIQ](https://img.shields.io/badge/Next.js-15-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-blue)

## Features

- **Upload & Process** — Drag-and-drop CSV/XLSX upload with real-time processing pipeline
- **Modular Validation Engine** — Phone, email, date, time, payment, product, and order validation
- **Smart Column Mapping** — Auto-maps `mobile`, `phone_no`, `contact_number` → `phone`
- **Data Cleaning** — Auto-fixes whitespace, phone formats, names, dates
- **Quality Score** — 0–100 score (Completeness 40%, Accuracy 40%, Duplicates 10%, Formatting 10%)
- **AI Summary** — Intelligent validation report with recommendations
- **Error Dashboard** — Searchable, filterable, sortable error table with export
- **Admin Rules** — Configure validation rules without code changes
- **Analytics Dashboard** — KPIs, charts, quality trends, country-wise errors
- **Report Downloads** — Cleaned CSV, error CSV, validation PDF
- **CSV Chunking** — Split large files by row count or file size
- **Upload History** — View past uploads and re-download reports
- **Rule Versioning** — Tracks which rule set processed each file

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| State | React Query, Zustand |
| Backend | FastAPI, Pandas, Polars |
| Database | PostgreSQL (Neon), Prisma ORM |
| Reports | ReportLab (PDF generation) |

## Project Structure

```
TransatIQ/
├── frontend/          # Next.js 15 App Router
│   ├── src/app/       # Pages (Dashboard, Upload, Results, Rules, etc.)
│   ├── src/components/# UI components
│   ├── src/lib/       # API client, utilities
│   ├── prisma/        # Database schema & seed
├── backend/           # FastAPI processing engine
│   ├── app/services/  # Validation, cleaning, AI summary, reports
│   ├── app/routers/   # API endpoints
├── sample-data/       # Sample CSV for testing
└── docker-compose.yml # Local PostgreSQL
```

## Quick Start

### 1. Start PostgreSQL

```bash
docker compose up -d
```

Or use [Neon](https://neon.tech) free tier and copy your connection string.

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL

uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
cp .env.example .env
npm install
npx prisma generate
npx prisma db push
npm run db:seed
npm run dev
```

Open **http://localhost:3000**

### 4. Test with Sample Data

Upload `sample-data/transactions_sample.csv` from the Upload page. The sample contains intentional errors to demonstrate validation:

- Invalid phone lengths (India/Singapore)
- Malformed emails (`bob@gmail`)
- Duplicate order IDs
- Delivery date before order date
- Price calculation mismatches
- Missing transaction IDs
- Unsupported payment methods

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/uploads` | Upload and process file |
| GET | `/api/uploads/{id}/status` | Processing status |
| GET | `/api/uploads/{id}/results` | Validation results |
| GET | `/api/uploads/{id}/errors` | Paginated errors |
| GET | `/api/uploads/{id}/download/{type}` | Download cleaned/errors/report |
| GET | `/api/dashboard/stats` | Dashboard KPIs |
| GET/POST | `/api/rules` | Manage validation rules |
| POST | `/api/uploads/chunk` | CSV chunking |

## Deployment

### Frontend (Vercel)
1. Connect repo, set root to `frontend/`
2. Set `NEXT_PUBLIC_API_URL` to your backend URL

### Backend (Railway/Render)
1. Set root to `backend/`
2. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set `DATABASE_URL` to Neon connection string

### Database (Neon)
1. Create free PostgreSQL database at neon.tech
2. Use connection string in both frontend and backend `.env`

## Validation Rules

Default rules are seeded on first load:

| Country | Code | Field | Rule |
|---------|------|-------|------|
| India | +91 | phone | 10 digits |
| Singapore | +65 | phone | 8 digits |

Admin can add/edit/disable rules at `/rules` without code changes.

## License

MIT — Built for Xeno internship assignment demonstration.

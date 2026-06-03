# Purplle Store Intelligence System 🚀

![Dashboard Preview](https://via.placeholder.com/1200x600/0f0f13/a855f7?text=Store+Intelligence+Dashboard)

Welcome to the **Purplle Tech Challenge 2026** submission for the ultimate AI-driven Store Intelligence System. This platform converts raw CCTV footage into a highly scalable, real-time analytics dashboard, leveraging state-of-the-art Computer Vision and Event Streaming architectures.

## 🌟 Key Features
- **Real-Time Computer Vision Pipeline**: YOLOv8 Person Detection + ByteTrack Multi-Object Tracking.
- **Cross-Camera Re-ID**: ResNet50-based feature extraction for global visitor session deduplication.
- **Event Streaming Architecture**: Idempotent batch ingestion capable of handling 100,000+ events natively via async queues and background DB flushing.
- **Gamified Dashboard**: A premium, Next.js + Framer Motion glassmorphism dashboard featuring Live Heatmaps, Queue Forecasting, and AI NLP Insights.
- **Production-Ready**: Pytest coverage >70%, Docker Compose orchestrations, and Swagger-documented APIs.

---

## 🛠 Setup & Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Run via Docker (Recommended)
Simply spin up the entire stack using docker-compose:
```bash
docker-compose up --build -d
```
The Backend API will run on `http://localhost:8000` and the Dashboard on `http://localhost:3000`.

### 2. Local Development Setup
**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🏗 Architecture Overview

The system is decoupled into three primary layers:
1. **CV Processing Layer**: Ingests CCTV frames, tracks bounding boxes, extracts visual embeddings, and generates challenge-schema events (`ENTRY`, `ZONE_DWELL`, etc.).
2. **Streaming & Analytics Layer**: Accepts batch payloads (`POST /events/ingest`), deduplicates them using a sliding time-window, and persists them via background executors. Exposes live WebSockets and REST analytics (`/metrics`, `/funnel`, `/anomalies`).
3. **Presentation Layer**: A Next.js App Router frontend consuming REST APIs for static analytics and WebSockets for live traffic blips and anomaly feeds.

*For deep architectural details, see [DESIGN.md](./DESIGN.md).*

---

## 📡 Core APIs

Interactive Swagger documentation is automatically generated at `http://localhost:8000/docs`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events/ingest` | `POST` | Batch ingest up to 500 events (idempotent, partial-success capable) |
| `/stores/{id}/metrics` | `GET` | Returns live KPIs: visitors, queue depth, conversion rate |
| `/stores/{id}/funnel` | `GET` | Calculates progressive drop-off from Entry → Purchase |
| `/stores/{id}/heatmap`| `GET` | Returns zone-by-zone dwell and visit density |
| `/stores/{id}/anomalies`| `GET` | AI-detected anomalies (e.g., Queue Spikes) with actionable advice |
| `/ws/live` | `WS` | Real-time event firehose for the frontend dashboard |

---

## 🧪 Testing

The backend is thoroughly tested using `pytest`.
```bash
cd backend
pytest -v --cov=app tests/
```
We also provide an **Event Replay Mode** script (`backend/tests/event_replay.py`) which can simulate real-time CCTV streams by pushing artificial detection bounding boxes through the pipeline.

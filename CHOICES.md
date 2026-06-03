# Technical Choices & Rationale (CHOICES.md)

During the development of the Purplle Store Intelligence System, I collaborated with an AI coding assistant. This document outlines the architectural debates we had, what I accepted, what I rejected, and why.

### 1. Object Detection: YOLOv8 vs RT-DETR vs MediaPipe
- **What AI Suggested**: The AI suggested using RT-DETR (Real-Time DEtection TRansformer) for state-of-the-art accuracy in dense crowds.
- **What I Rejected**: I rejected RT-DETR because transformer architectures, while highly accurate, require significantly more VRAM and compute, which can bottleneck edge deployments.
- **What I Accepted**: I forced the use of **YOLOv8n**. It is incredibly fast, lightweight enough to run on CPU if necessary, and natively integrates with robust tracking algorithms, perfectly satisfying the hackathon's real-time constraints.

### 2. Tracking: ByteTrack vs DeepSORT
- **What AI Suggested**: The AI initially proposed DeepSORT, citing its robust appearance-based feature matching (Re-ID) for handling occlusions.
- **What I Rejected**: I rejected DeepSORT as the primary tracker because extracting deep features on *every* frame for *every* bounding box destroys FPS.
- **What I Accepted**: I implemented **ByteTrack** for frame-to-frame tracking (associating every box, even low-confidence ones, purely by motion/IoU). I then implemented a *fallback* Re-ID mechanism using a custom ResNet50 feature extractor that only runs sporadically (e.g., across camera boundaries), giving us the speed of ByteTrack with the cross-camera intelligence of DeepSORT.

### 3. Database: SQLite vs PostgreSQL
- **What AI Suggested**: The AI strongly recommended PostgreSQL right away to easily handle the 100,000+ event requirement.
- **What I Rejected**: I rejected mandating PostgreSQL for local dev, as it makes spinning up the hackathon project cumbersome for judges who might just want to run `python main.py`.
- **What I Accepted**: I accepted a **SQLAlchemy abstracted SQLite database** with a background batch-insert worker. By implementing `bulk_save_objects` and an async memory buffer, SQLite easily handles 100k+ events locally, while remaining 100% code-compatible with a PostgreSQL drop-in for production.

### 4. Event Schema Design
- **What AI Suggested**: The AI suggested a deeply nested NoSQL/JSON document schema to handle dynamic zone metadata and varying event types.
- **What I Rejected**: I rejected a purely NoSQL approach because calculating funnels and aggregations over 100k nested JSON documents is extremely slow without specialized indexing.
- **What I Accepted**: I enforced a **flat, strongly typed relational schema** (using Pydantic and SQLAlchemy) with a strict `EventType` Enum. We isolated the dynamic data to a single `metadata_blob` JSON column, keeping the primary indices (`timestamp`, `visitor_id`, `event_type`) lightning fast for analytics queries.

### 5. Frontend Dashboard Design
- **What AI Suggested**: The AI suggested a standard, clean Tailwind CSS template (white background, basic shadows, standard charts).
- **What I Rejected**: I rejected the generic SaaS look. I wanted this to feel like a premium, next-generation intelligence platform.
- **What I Accepted**: I directed the AI to implement a **Gamified UI with Glassmorphism**. We utilized Framer Motion for entrance animations, glowing radial mesh backgrounds, and gamification elements (Achievements, Top Zone Leaderboards) to ensure the judges would immediately recognize the product's premium feel.

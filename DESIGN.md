# System Design Document (DESIGN.md)

This document outlines the architectural decisions, data flow, and scalability considerations for the Purplle Store Intelligence System.

## 1. High-Level Architecture

Our platform follows a decoupled, event-driven microservices architecture:

1. **Edge CV Nodes**: YOLOv8 + ByteTrack running on edge devices or GPU servers. These nodes do NOT write to a database. They only POST JSON payloads to the central Event API.
2. **Event Broker**: A lightweight asyncio-based pub/sub queue (emulating Kafka/Redis Streams) that accepts bursts of events and buffers them.
3. **Analytics Engine**: Reads from the database to compute complex aggregations (Funnels, Heatmaps, Anomalies).
4. **WebSocket Broadcaster**: Subscribes directly to the Event Broker to pump live events to the React frontend without touching the disk.

## 2. Data Flow

1. **Frame Capture**: Frame arrives from Entry, Main Floor, or Billing CCTV.
2. **Detection & Tracking**: YOLOv8 identifies `person`. ByteTrack assigns a continuous `track_id`.
3. **Feature Extraction**: Every N frames, a ResNet50 embedding is generated and passed to the `SessionManager`.
4. **Re-Identification**: `SessionManager` checks cosine similarity against active shoppers. If matched, deduplicates visitor. If unmatched, generates a new `visitor_id` UUID.
5. **Event Emission**: `ZoneManager` triggers a `ZONE_ENTER` or `ENTRY` event.
6. **Ingestion API**: The edge node sends a batch of 500 events to `POST /events/ingest`.
7. **Deduplication**: The API validates the signature (`visitor_id + event_type + time`). Duplicates are dropped.
8. **Persistence**: The valid events are pushed to an in-memory queue. A background thread flushes them to SQLite/PostgreSQL using `bulk_save_objects`.

## 3. Scalability (Supporting 100,000+ Events)

Handling 100,000+ events per day requires careful I/O management:
- **No Blocking DB Writes**: The `/ingest` API never waits for a database disk write. It drops events into memory and returns `202 ACCEPTED` instantly.
- **Batching**: The `EventRepository` flushes to the DB in chunks of 500 or every 2 seconds, massively reducing transaction overhead.
- **Indexing**: The SQL tables are heavily indexed on `(visitor_id, event_type, timestamp)`, ensuring that the Analytics Engine can run `GROUP BY` operations over massive datasets in milliseconds.

## 4. AI Assisted Decisions

The `AIInsightsEngine` goes beyond raw data aggregation by providing actionable intelligence:
- **Queue Forecasting**: Predicts future queue depths based on moving averages of Entry vs Checkout rates.
- **Dead Zone Detection**: Automatically classifies store zones based on Visit Count * Avg Dwell Time thresholds.
- **NLP Generation**: Synthesizes the quantitative data into qualitative, manager-ready text (e.g., "The Fragrance Bar is a high-traffic dead zone. Consider upselling.").

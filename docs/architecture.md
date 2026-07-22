# Architecture Overview

This document elaborates the **six‑layer reference architecture** for an AI‑driven industrial IoT platform.

## 1. Data Sources
- **Fleet/IoT telemetry** – high‑frequency sensor streams (GPS, speed, load, driver behavior).
- **ERP / SCM / MES** – procurement, inventory, production schedules.
- **Supplier & Quality** – inspection records, certificates, scorecards.
- **BMS & Charging** – cell voltage, temperature, state‑of‑charge, cycle counts.

## 2. Ingestion & Integration
- **Streaming** – Kafka / MQTT pipelines for sub‑minute data (deduplication, unit normalization, timestamp alignment).
- **Batch / API** – scheduled ETL jobs, REST/OData connectors, auth & rate‑limit handling.

## 3. Unified Data Platform
- **Lakehouse** – raw + curated tables (Delta Lake / Iceberg).
- **Feature Store** – reusable engineered features for all agents.
- **Knowledge Graph** – entities & relationships (supplier → component → battery → vehicle → fleet) enabling cross‑domain reasoning.

## 4. Multi‑Agent Orchestration
- **Orchestrator** – LangGraph state‑graph that routes tasks, monitors shared state, and triggers specialist agents.
- **Specialist Agents** – APM, Supply‑Chain Risk, QMS, Sustainability, Maintenance Optimiser (see `agents/` for specs).

## 5. Application & Serving Layer
- **API / Workflow Engine** – REST (FastAPI) or GraphQL gateway.
- **Alerting / Event Bus** – Kafka topics for real‑time alerts.

## 6. Presentation
- Dashboards (Grafana / Superset), digital twin UI (React/Vite), mobile alerts (Flutter).

---
*Each folder in the repository contains a `README.md` with local setup instructions.*

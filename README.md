# EV Supply Chain & Asset Intelligence – Project Overview

This repository contains a reference implementation of a six‑layer architecture for building AI platforms that integrate industrial IoT telemetry, supply‑chain risk, manufacturing quality, sustainability tracking, and maintenance operations.

## Directory Structure
```
/ (project root)
├── README.md                     # Project overview (this file)
├── docs/
│   ├── architecture.md           # Detailed description of the six‑layer architecture
│   ├── agents.md                 # Specification of each specialist agent
│   └── data_model.md            # Knowledge‑graph schema and feature‑store design
├── data_sources/
│   ├── fleet_telemetry/          # Simulated or raw fleet IoT data
│   ├── erp_scm/                  # ERP/SCM data extracts (CSV/JSON)
│   ├── supplier_quality/         # Supplier inspection records
│   └── bms_charging/             # Battery Management System logs
├── ingestion/
│   ├── streaming/                # Kafka / MQTT ingestion pipelines (Docker/Compose config)
│   └── batch/                    # ETL scripts, API connectors
├── data_platform/
│   ├── lakehouse/                # Delta Lake / Iceberg tables (SQL scripts)
│   ├── feature_store/            # Feature engineering notebooks & registry
│   └── knowledge_graph/          # Neo4j / GraphDB schema and import scripts
├── orchestrator/
│   ├── langgraph_workflow/       # Orchestration state‑graph definition (Python)
│   └── event_bus/                # Pub/Sub topics definitions (Kafka config)
├── agents/
│   ├── apm_agent/                # Asset Performance Management agent
│   ├── supply_chain_agent/       # Supply‑chain risk & traceability agent
│   ├── qms_agent/                # Quality Management System agent
│   ├── sustainability_agent/     # Net‑zero tracking agent
│   └── maintenance_optimizer/    # Maintenance scheduling optimizer
├── api/
│   ├── rest_api/                 # FastAPI / Flask services exposing agent outputs
│   └── graphql/                  # Optional GraphQL gateway
└── presentation/
    ├── dashboards/               # Grafana / Superset dashboard configs
    ├── digital_twin/             # Web‑based twin UI (React/Vite)
    └── mobile_alerts/            # Simple mobile notification mock (Flutter)
```

## Getting Started
1. **Data ingestion** – spin up the streaming and batch pipelines in `./ingestion`.
2. **Unified platform** – run the lakehouse initialisation scripts and populate the feature store.
3. **Orchestrator** – start the LangGraph workflow; it will invoke the specialist agents as data becomes available.
4. **API** – launch the REST API to query agent insights.
5. **Presentation** – open the dashboard or digital‑twin UI to visualise the coordinated intelligence.

Each layer contains a `README.md` with setup instructions and sample commands.

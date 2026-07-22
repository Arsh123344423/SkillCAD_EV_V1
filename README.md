# ⚡ SkillCAD EV — Battery Supply Chain & Predictive Maintenance Platform

<div align="center">

**Multi-agent AI for EV battery health prediction + supply chain risk intelligence**

[![Status](https://img.shields.io/badge/status-draft%20v0.1-yellow)]()
[![LangGraph](https://img.shields.io/badge/agents-LangGraph%20%2B%20LangChain-1C3C3C)]()
[![Gemini](https://img.shields.io/badge/LLM-Gemini--3.5--flash--lite-8E75B2?logo=googlegemini&logoColor=white)]()
[![Kafka](https://img.shields.io/badge/streaming-Kafka-231F20?logo=apachekafka&logoColor=white)]()
[![MongoDB](https://img.shields.io/badge/db-MongoDB-47A248?logo=mongodb&logoColor=white)]()
[![React](https://img.shields.io/badge/frontend-React-61DAFB?logo=react&logoColor=black)]()

**Team:** SkillCAD EV — Arsh Srivastava ([arshsrivastava00@gmail.com](mailto:arshsrivastava00@gmail.com)) · [Repo](https://github.com/Arsh123344423/SkillCAD_EV_V1)

</div>

---

## 🎯 Problem

India's EV/battery supply chain relies on few upstream chokepoints, with low trust between users and manufacturers. This platform tackles both sides with two agent arms:

- 🔋 **Telemetry arm** — predicts battery **Remaining Useful Life (RUL)** from live sensor data and routes issues to the right specialist agent.
- 🌍 **Supply chain arm** — quantifies geopolitical/ESG risk over India's supply graph, with recommendations tied to **KABIL**, the **ACC PLI scheme**, and Quad/IPEF partnerships.

**Hypothesis:** intent-routed multi-agent systems beat a single general chatbot on accuracy and explainability.

---

## 🏗 Architecture

```mermaid
flowchart TB
    HF["Hugging Face API"] --> KAFKA[["🟨 Kafka"]]
    SIM["Simulator"] --> KAFKA
    KAFKA --> MONGO[("🛢 MongoDB")]

    MONGO --> SOH["SoH Agent"]
    MONGO --> RUL["Multi_RUL_Agent"]
    RUL -->|route| MAINT["Maintenance"] & QUAL["Quality"] & PROC["Procurement"]
    MAINT & QUAL & PROC --> DEC1{{"tool?"}}
    DEC1 -->|no| NULLV["Null return"]
    DEC1 -->|yes| REFINE["Refined response"] --> RUL

    MONGO --> SCM["Supply Chain Agent"]
    SCM --> SUPINFO["Supplier Info"] --> DEC2{{"Viable for India?"}}
    DEC2 -->|yes| RISK["Risk Agent"] & SUPLLM["Supplier LLM Agent"]
    DEC2 -->|no| SUPINFO

    SOH & RUL & SCM --> MAINP["Main.py"] --> API["FastAPI"] --> REACT["🟦 React Dashboard"]
```

**Legend:** 🟪 Purple = LLM agent · 🛢 = MongoDB · ◆ = decision · 🟨 = Kafka · 🟦 = frontend

---

## 🤖 Agents at a Glance

| Subsystem | Key Agents | Status |
|---|---|:---:|
| **Supply Chain Risk** | Supply Chain Mgmt Agent, Supplier Info, Risk Factor LLM Agent, Supplier Info LLM Agent | ✅ Implemented |
| **Telemetry / RUL** | SoH Agent, Multi_RUL_Agent, Maintenance / Quality / Procurement Agents, Null Value return | ✅ Implemented |
| **Response Handling** | Orchestrate / Response Agent | 🟡 In Progress |

---

## 🛠 Tech Stack

| Layer | Tech |
|---|---|
| Streaming | Apache Kafka (Docker) |
| Database | MongoDB |
| RUL Agents | LangGraph + LangChain |
| Supply Chain Agents | Gemini-3.5-flash-lite (function calling) |
| Graph Modeling | NetworkX (DiGraph) |
| Backend | FastAPI |
| Frontend | React (Next.js) |

---

## 🔌 API

| Method | Path | Description |
|---|---|---|
| POST | `/agents/coordinator` | Query → Multi_RUL_Agent |
| POST | `/analyze/db` | Deterministic SoH / RUL |
| POST | `/supply-chain/agent` | Query → Supply Chain Agent |
| POST | `/supply-chain/analyze-node` | Risk breakdown per supplier |
| GET | `/supply-chain/nodes` | Graph data for frontend |

---

## 🚀 Getting Started

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## ⚠️ Limitations

No real-time live data · no login-based RAG · no raw-material shipment tracking · no cross-subsystem LLM communication · no TTL on records.

---

<div align="center">Made with ⚡ by Team SkillCAD EV</div>

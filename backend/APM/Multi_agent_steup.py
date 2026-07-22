import json
import os
from typing import Literal, TypedDict, Annotated

from dotenv import load_dotenv
from pymongo import MongoClient
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# ==========================================================
# CONFIG
# ==========================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    api_key=GEMINI_API_KEY,
    temperature=0.3
) if GEMINI_API_KEY else None

# ==========================================================
# MONGODB CONFIG
# ==========================================================
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")

# Single global DB connection
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION_NAME]

def _serialize(doc: dict | None) -> dict:
    """Mongo's ObjectId isn't JSON-serializable — stringify it, or return {} if no doc."""
    if not doc:
        return {}
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# ==========================================================
# STATE
# ==========================================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    ev_model: str | None
    current_agent: str | None
    final_response: str | None

# ==========================================================
# TOOLS 
# ==========================================================
@tool
def get_latest_asset(ev_model: str):
    """Get latest asset status."""
    # Using _id for sorting since it contains a chronological timestamp
    doc = collection.find_one(
        {"ev_model": ev_model},
        sort=[("_id", -1)]
    )
    if not doc:
        return {"error": f"No asset found for ev_model={ev_model}"}
    return _serialize(doc)

@tool
def get_recent_telemetry(ev_model: str, limit: int = 10):
    """Get recent battery telemetry."""
    cursor = collection.find(
        {"ev_model": ev_model}
    ).sort("_id", -1).limit(limit)

    docs = [_serialize(d) for d in cursor]
    if not docs:
        return {"error": f"No telemetry found for ev_model={ev_model}"}
    return docs

@tool
def get_inventory_summary():
    """Get inventory status."""
    # Assuming inventory items might still have a specific identifier, or just returning all if small
    # Adjust this query if your inventory items have a specific field like {"type": "inventory"}
    docs = [_serialize(d) for d in collection.find().limit(50)]
    return {"items": docs, "count": len(docs)}

tools = [get_latest_asset, get_recent_telemetry, get_inventory_summary]
tool_node = ToolNode(tools)

# ==========================================================
# AGENT FUNCTION
# ==========================================================
def create_agent_agent(name: str, system_prompt: str):
    def agent(state: AgentState):
        if not llm:
            return {
                "messages": [AIMessage(content=f"[{name} Agent] Analysis complete (mock mode).")],
                "current_agent": name.lower()
            }

        bound_llm = llm.bind_tools(tools)
        messages = [SystemMessage(content=system_prompt)] + state["messages"]

        response = bound_llm.invoke(messages)

        return {
            "messages": [response],
            "current_agent": name.lower()
        }
    return agent

# Define Agents
maintenance_agent = create_agent_agent(
    "Maintenance",
    "You are an EV Maintenance Expert. Focus on health, service, and recommendations. "
    "Use get_latest_asset for service/health questions."
)

quality_agent = create_agent_agent(
    "Quality",
    "You are an EV Battery Quality Analyst. Focus on temperature, voltage, anomalies, and risks. "
    "Use get_recent_telemetry to inspect actual temperature/voltage readings before answering."
)

procurement_agent = create_agent_agent(
    "Procurement",
    "You are a Procurement Specialist. Analyze stock levels and recommend actions. "
    "Use get_inventory_summary for stock questions."
)

# ==========================================================
# ROUTER
# ==========================================================
def router(state: AgentState) -> Literal["maintenance", "quality", "procurement", "final"]:
    query = state["query"].lower()

    if any(word in query for word in ["maintenance", "service", "repair", "soh", "health", "charging"]):
        return "maintenance"
    elif any(word in query for word in ["temperature", "voltage", "anomaly", "drift", "quality", "thermal"]):
        return "quality"
    elif any(word in query for word in ["inventory", "stock", "procurement", "spare", "supply"]):
        return "procurement"
    return "final"

def make_tool_router(agent_name: str):
    def route(state: AgentState) -> Literal["tools", "final"]:
        last_msg = state["messages"][-1]
        if getattr(last_msg, "tool_calls", None):
            return "tools"
        return "final"
    return route

def final_response(state: AgentState):
    last_msg = state["messages"][-1]
    content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    return {"final_response": content}

# ==========================================================
# BUILD GRAPH
# ==========================================================
workflow = StateGraph(AgentState)

workflow.add_node("maintenance", maintenance_agent)
workflow.add_node("quality", quality_agent)
workflow.add_node("procurement", procurement_agent)
workflow.add_node("tools", tool_node) 
workflow.add_node("final", final_response)

workflow.add_conditional_edges(
    START,
    router,
    {
        "maintenance": "maintenance",
        "quality": "quality",
        "procurement": "procurement",
        "final": "final"
    }
)

workflow.add_conditional_edges("maintenance", make_tool_router("maintenance"), {"tools": "tools", "final": "final"})
workflow.add_conditional_edges("quality", make_tool_router("quality"), {"tools": "tools", "final": "final"})
workflow.add_conditional_edges("procurement", make_tool_router("procurement"), {"tools": "tools", "final": "final"})

def route_back_to_agent(state: AgentState) -> Literal["maintenance", "quality", "procurement"]:
    return state["current_agent"]

workflow.add_conditional_edges(
    "tools",
    route_back_to_agent,
    {
        "maintenance": "maintenance",
        "quality": "quality",
        "procurement": "procurement",
    }
)

graph = workflow.compile()

# ==========================================================
# RUNNER
# ==========================================================
def run_ev_agent(query: str, ev_model: str = "Model C"):
    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "ev_model": ev_model,
        "current_agent": None,
        "final_response": None
    }

    result = graph.invoke(initial_state)
    return {
        "agent": result.get("current_agent"),
        "response": result.get("final_response", "No response generated.")
    }


def run_coordinator_agent(query: str, asset_id: str | None = None):
    """Compatibility wrapper for the FastAPI coordinator endpoint."""
    ev_model = asset_id or "Model C"
    return run_ev_agent(query=query, ev_model=ev_model)

# Test
if __name__ == "__main__":
    result = run_ev_agent(
        query="Analyze temperature drift and voltage anomalies in Model C",
        ev_model="Model C"
    )
    print(json.dumps(result, indent=2))
import os
import networkx as nx
from google import genai
from google.genai import types

# ---------------------------------------------------------
# GRAPH GENERATION & RISK ENGINE
# ---------------------------------------------------------
def build_supply_chain_graph() -> nx.DiGraph:
    """Supply chain graph modeled for India's EV & Battery manufacturing ecosystem."""
    G = nx.DiGraph()

    # Tier 1: Indian Cell Manufacturers / Gigafactories (Downstream)
    G.add_node("India_ACC_Gigafactories", tier=1, geo_risk=0.1, quality_risk=0.2, esg_flag=True)

    # Tier 2: Material Processing & Refining (Midstream Bottleneck)
    G.add_node("China_Cobalt_Refining", tier=2, geo_risk=0.7, quality_risk=0.1, esg_flag=True)
    G.add_node("China_Lithium_Refining", tier=2, geo_risk=0.65, quality_risk=0.1, esg_flag=True)
    G.add_node("China_Graphite_Refining", tier=2, geo_risk=0.6, quality_risk=0.1, esg_flag=True)
    G.add_node("Indonesia_Nickel_Smelting", tier=2, geo_risk=0.4, quality_risk=0.2, esg_flag=False)
    G.add_node("Australia_Lithium_Refining", tier=2, geo_risk=0.1, quality_risk=0.1, esg_flag=True)

    # Tier 3: Raw Material Mines (Upstream Sources & KABIL Targets)
    G.add_node("DRC_Cobalt_Mines", tier=3, geo_risk=0.9, quality_risk=0.3, esg_flag=False) 
    G.add_node("Argentina_Lithium_Brine_KABIL", tier=3, geo_risk=0.25, quality_risk=0.1, esg_flag=True)
    G.add_node("Australia_Lithium_Spodumene", tier=3, geo_risk=0.1, quality_risk=0.1, esg_flag=True)
    G.add_node("Indonesia_Nickel_Mines", tier=3, geo_risk=0.8, quality_risk=0.2, esg_flag=False)

    # Edges & Concentration Weights
    G.add_edge("DRC_Cobalt_Mines", "China_Cobalt_Refining", weight=0.85)
    G.add_edge("Argentina_Lithium_Brine_KABIL", "China_Lithium_Refining", weight=0.40)
    G.add_edge("Australia_Lithium_Spodumene", "China_Lithium_Refining", weight=0.50)
    G.add_edge("Australia_Lithium_Spodumene", "Australia_Lithium_Refining", weight=0.30)
    G.add_edge("Indonesia_Nickel_Mines", "Indonesia_Nickel_Smelting", weight=0.95)

    G.add_edge("China_Lithium_Refining", "India_ACC_Gigafactories", weight=0.80)
    G.add_edge("China_Cobalt_Refining", "India_ACC_Gigafactories", weight=0.75)
    G.add_edge("China_Graphite_Refining", "India_ACC_Gigafactories", weight=0.90)
    G.add_edge("Indonesia_Nickel_Smelting", "India_ACC_Gigafactories", weight=0.50)
    G.add_edge("Australia_Lithium_Refining", "India_ACC_Gigafactories", weight=0.20)

    return G

# Initialize internal graph instance
G_SUPPLY = build_supply_chain_graph()


def analyze_supplier_risk(supplier_id: str) -> dict:
    """Walks the supply chain graph upstream to compute propagated risk for a supplier."""
    if supplier_id not in G_SUPPLY:
        return {"error": f"Supplier '{supplier_id}' not found in supply chain graph."}

    def _get_risk(node_id):
        node_data = G_SUPPLY.nodes[node_id]
        local_risk = (node_data.get('geo_risk', 0) * 40) + \
                     (node_data.get('quality_risk', 0) * 40) + \
                     (0 if node_data.get('esg_flag', True) else 20)
        
        upstream_details = []
        for upstream in G_SUPPLY.predecessors(node_id):
            weight = G_SUPPLY.get_edge_data(upstream, node_id).get('weight', 0)
            upstream_total = _get_risk(upstream)["total_risk"]
            inherited = upstream_total * weight
            upstream_details.append({
                "upstream_node": upstream,
                "concentration_percentage": f"{weight * 100}%",
                "inherited_risk": round(inherited, 2)
            })

        max_inherited = max([u["inherited_risk"] for u in upstream_details]) if upstream_details else 0
        total_risk = max(local_risk, max_inherited)

        return {
            "supplier": node_id,
            "tier": node_data.get("tier"),
            "local_risk": round(local_risk, 2),
            "total_risk": round(total_risk, 2),
            "esg_compliant": node_data.get("esg_flag"),
            "upstream_dependencies": upstream_details
        }

    return _get_risk(supplier_id)


def list_all_suppliers() -> list:
    """Returns a list of all supplier IDs available in the supply chain network."""
    return list(G_SUPPLY.nodes)


def get_graph_visualization_data() -> dict:
    """Helper to return node-edge list for frontend rendering."""
    nodes = [
        {
            "id": node,
            "tier": data.get("tier"),
            "geo_risk": data.get("geo_risk"),
            "quality_risk": data.get("quality_risk"),
            "esg_compliant": data.get("esg_flag")
        }
        for node, data in G_SUPPLY.nodes(data=True)
    ]
    edges = [
        {
            "source": u,
            "target": v,
            "weight": data.get("weight")
        }
        for u, v, data in G_SUPPLY.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------
# MAIN TRACK B AGENT FUNCTION
# ---------------------------------------------------------
def run_supply_chain_agent(user_query: str) -> str:
    """
    Executes the Gemini Supply Chain Agent with function-calling tool access.
    Can be called directly by main.py or by your Coordinator Agent.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not configured.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=user_query,
        config=types.GenerateContentConfig(
            tools=[analyze_supplier_risk, list_all_suppliers],
            temperature=0.2,
            system_instruction=(
                "Response should be concise, actionable, and focused on supply chain risk mitigation strategies for India and with 150 words. "
                "You are an expert Strategic Supply Chain & Critical Mineral Risk Agent for India. "
                "Your objective is to advise Indian government bodies (e.g., NITI Aayog, Ministry of Heavy Industries) "
                "and Indian EV manufacturers on supply chain security. "
                "Always analyze risk from India's geopolitical perspective: "
                "1. Identify hidden upstream vulnerabilities (such as high concentration in Chinese midstream refining and DRC cobalt ESG risks). "
                "2. Formulate optimal outcomes for India, including leveraging KABIL (Khanij Bidesh India Ltd) for lithium block acquisitions in Argentina/Australia, "
                "building domestic refining infrastructure under the ACC PLI Scheme, expanding Quad/IPEF partnerships, "
                "and transitioning toward LFP/Sodium-ion chemistry to bypass cobalt bottlenecks."
            )
        )
    )

    return response.text
from langgraph.graph import StateGraph, END
from app.core.state import TravelPlanState
from app.nodes.bus_search import bus_search_node
from app.nodes.hotel_search import hotel_search_node
from app.nodes.tourist_places import tourist_places_node
from app.nodes.synthesizer import synthesizer_node

def build_travel_graph():
    """Build and compile the LangGraph travel planning state machine."""
    workflow = StateGraph(TravelPlanState)

    # Add workflow nodes
    workflow.add_node("bus_search", bus_search_node)
    workflow.add_node("hotel_search", hotel_search_node)
    workflow.add_node("tourist_places", tourist_places_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # Define parallel entry edges
    workflow.set_entry_point("bus_search")
    workflow.add_edge("bus_search", "hotel_search")
    workflow.add_edge("hotel_search", "tourist_places")
    workflow.add_edge("tourist_places", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile()

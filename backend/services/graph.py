# backend/services/graph.py
"""Stand-in for Member 1's graph_retriever.retrieve_from_graph().

PROPOSED CONTRACT — confirm with Member 1:
    retrieve_from_graph(query: str) -> list[str]
        returns human-readable relationship paths
"""


def retrieve_from_graph(query: str) -> list[str]:
    """Return structured graph relationships for the query."""
    return [
        "Game meat, bison --CONTAINS--> Protein",
        "Protein --IMPORTANT_FOR--> Muscle gain",
        "Salmon --CONTAINS--> Omega-3 fatty acids",
        "Omega-3 fatty acids --IMPORTANT_FOR--> Heart health",
    ]
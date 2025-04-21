from graphiti_core import Graphiti

graphiti_connection: Graphiti | None = None


def get_graphiti_connection() -> Graphiti:
    if graphiti_connection is None:
        raise RuntimeError("Graphiti connection not initialized. Ensure the lifespan event ran.")
    return graphiti_connection

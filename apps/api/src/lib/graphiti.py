from graphiti_core import Graphiti

from src.settings import settings

graphiti = Graphiti(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)

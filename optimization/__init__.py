"""
Módulo de Optimización para Ruteo Resiliente

Este módulo contiene implementaciones de algoritmos de optimización
para encontrar rutas resilientes considerando amenazas.
"""

try:
    from .gurobi_model import ResilientRouter
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False
    ResilientRouter = None

from .metaheuristics import AStarResilientRouter

__all__ = ['ResilientRouter', 'AStarResilientRouter', 'GUROBI_AVAILABLE']

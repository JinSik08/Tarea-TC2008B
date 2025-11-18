from mesa import Model
from mesa.datacollection import DataCollector # DataCollector para recolectar los stats del modelo
from mesa.discrete_space import OrthogonalMooreGrid

from .agent import RandomAgent, ObstacleAgent, DirtyPatch, ChargingStation

class RandomModel(Model):
    """
    Modelo de limpieza de habitación con múltiples agentes aspiradora.
    (Simulación 2)

    Parámetros:
    width, height: Dimensiones de la cuadrícula (M x N)
    num_agents: Número de agentes aspiradora
    dirty_percent: Porcentaje de celdas sucias al inicio
    obstacle_percent: Porcentaje de celdas con obstáculos al inicio
    max_steps: Número máximo de pasos de la simulación
    """
    def __init__(self, width=10, height=10, num_agents=3, dirty_percent=0.4, obstacle_percent=0.1, max_steps=500, seed=None):

        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.num_agents = num_agents
        self.dirty_percent = dirty_percent
        self.obstacle_percent = obstacle_percent
        self.max_steps = max_steps

        # Crea el grid sin torus
        self.grid = OrthogonalMooreGrid([width, height], torus=False)

        # Métricas del modelo
        self.actual_step = 0
        self.move_count = 0
        self.time_to_clean = None

        # Total de celdas en la cuadrícula
        total_cells = width * height

        # Crear obstáculos en la cuadrícula
        all_cells = list(self.grid.all_cells)
        num_obstacles = int(total_cells * obstacle_percent)
        num_obstacles = min(num_obstacles, len(all_cells))

        obstacle_cells = []
        available_cells = list(all_cells)
        for _ in range(num_obstacles):
            if not available_cells:
                break
            cell = self.random.choice(available_cells)
            obstacle_cells.append(cell)
            available_cells.remove(cell)
        
        for cell in obstacle_cells:
            ObstacleAgent(self, cell = cell)

        # Crear posiciones iniciales de los agentes aspiradora
        free_for_agents = [
            cell for cell in self.grid.all_cells
            if not any(isinstance(a, ObstacleAgent) for a in cell.agents)
        ]
        num_agents_to_create = min(num_agents, len(free_for_agents))
        agent_start_cells = []
        available_for_start = list(free_for_agents)

        for _ in range(num_agents_to_create):
            if not available_for_start:
                break
            cell = self.random.choice(available_for_start)
            agent_start_cells.append(cell)
            available_for_start.remove(cell)

        # Crear estaciones de recarga en la posición de los agentes
        self.chargers = []
        charger_positions = []
        for cell in agent_start_cells:
            charger = ChargingStation(self, cell=cell)
            self.chargers.append(charger)
            charger_positions.append(cell.coordinate)

        # Crear celdas sucias en la cuadrícula
        free_for_dirty = [
            cell for cell in self.grid.all_cells
            if not any(isinstance(a, ObstacleAgent) for a in cell.agents)
            and cell.coordinate not in charger_positions
        ]

        num_dirty = int(total_cells * dirty_percent)
        num_dirty = min(num_dirty, len(free_for_dirty))

        dirty_cells = []
        available_dirty_cells = list(free_for_dirty)
        for _ in range(num_dirty):
            if not available_dirty_cells:
                break
            cell = self.random.choice(available_dirty_cells)
            dirty_cells.append(cell)
            available_dirty_cells.remove(cell)
        
        for cell in dirty_cells:
            DirtyPatch(self, cell = cell, dirty = True)

        # Total de celdas en la cuadrícula
        self.total_floor_cells = total_cells - num_obstacles
        self.initial_dirty_cells = len(dirty_cells)
        self.remaining_dirty_cells = self.initial_dirty_cells
        self.cleaned_cells = 0

        # Crear los agentes en sus posiciones iniciales
        self.cleaners = []
        for idx, cell in enumerate(agent_start_cells):
            self.cleaners.append(
                RandomAgent(
                    self,
                    cell=cell,
                    agent_id=idx,
                    main_charger_location=cell.coordinate,
                    battery=100
                )
            )

        # Recolección de datos del agente para la estadística
        model_reporters = {
            "Step": lambda m: m.actual_step,
            "Remaining Dirty Cells": lambda m: m.remaining_dirty_cells,
            "CleanPercent": lambda m: (
                0.0 if m.initial_dirty_cells == 0
                else 100.0 * (m.initial_dirty_cells - m.remaining_dirty_cells) / m.initial_dirty_cells
            ),
            "Movements": lambda m: m.move_count,
            "AvgBattery": lambda m: (
                sum(r.battery for r in m.cleaners) / len(m.cleaners)
            ) if len(m.cleaners) > 0 else 0.0,
        }
        
        # Agregar batería individual para cada agente
        for i in range(self.num_agents):
            model_reporters[f"Battery_{i}"] = lambda m, idx=i: (
                m.cleaners[idx].battery if idx < len(m.cleaners) else 0
            )
        
        self.datacollector = DataCollector(
            model_reporters=model_reporters,
            agent_reporters={
                "Battery": lambda a: a.battery if isinstance(a, RandomAgent) else None,
                "Movements": lambda a: a.move_count if isinstance(a, RandomAgent) else None,
                "CleanedCells": lambda a: a.cleaned_cells if isinstance(a, RandomAgent) else None,
            }
        )

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """
        Avanza un paso en la simulación
        """
        if not self.running:
            return
        self.actual_step += 1

        # Los agentes actúan en orden aleatorio cada paso
        agent_order = list(self.cleaners)
        self.random.shuffle(agent_order)
        for agent in agent_order:
            agent.step()

        # Si ya no hay celdas sucias, se detiene la simulación
        if self.remaining_dirty_cells == 0 and self.time_to_clean is None:
            self.time_to_clean = self.actual_step
            self.running = False

        # Si se llega al tiempo máximo, se detiene la simulación
        if self.actual_step >= self.max_steps:
            self.running = False
        
        # Recolecta los datos del modelo
        self.datacollector.collect(self)
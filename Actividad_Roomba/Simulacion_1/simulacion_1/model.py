from mesa import Model # Importa la clase base Model de Mesa
from mesa.datacollection import DataCollector # DataCollector para recolectar las estadísticas
from mesa.discrete_space import OrthogonalMooreGrid # Importa la cuadrícula ortogonal de Moore

# Importamos los agentes definidos
from .agent import RandomAgent, ObstacleAgent, DirtyPatch, ChargingStation

class RandomModel(Model):
    """
    Modelo de limpieza de habitación con un agente aspiradora.
    (Simulación 1)

    Parámetros:
    width, height: Dimensiones de la cuadrícula (M x N)
    dirty_percent: Porcentaje de celdas sucias al inicio
    obstacle_percent: Porcentaje de celdas con obstáculos al inicio
    max_steps: Número máximo de pasos de la simulación
    """
    def __init__(self, width=10, height=10, dirty_percent=0.4, obstacle_percent=0.1, max_steps=500, seed=None):

        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.dirty_percent = dirty_percent
        self.obstacle_percent = obstacle_percent
        self.max_steps = max_steps

        # Crea el grid sin torus
        self.grid = OrthogonalMooreGrid([width, height], torus=False)

        # Métricas del modelo
        self.actual_step = 0
        self.move_count = 0
        self.time_to_clean = None # Se guarda el paso en que se limpió todo
        self.cleaned_cells = 0

        # Coordinada fija de la estación de recarga
        self.charger_location = (1, 1)

        # Crear la estación de recarga
        charger_cell = next(
            cell for cell in self.grid.all_cells if cell.coordinate == self.charger_location
        )
        self.charger = ChargingStation(self, cell = charger_cell)

        # Total de celdas en la cuadrícula
        total_cells = width * height

        # Crear obstáculos en la cuadrícula
        cells_without_charger = [
            cell for cell in self.grid.all_cells if cell is not charger_cell
        ]

        num_obstacles = int(total_cells * obstacle_percent)
        num_obstacles = min(num_obstacles, len(cells_without_charger))

        obstacle_cells = []
        available_cells = list(cells_without_charger)
        for _ in range(num_obstacles):
            if not available_cells:
                break
            cell = self.random.choice(available_cells)
            obstacle_cells.append(cell)
            available_cells.remove(cell)
        for cell in obstacle_cells:
            ObstacleAgent(self, cell = cell)

        # Crear celdas sucias en la cuadrícula
        free_for_dirty = [
            cell for cell in self.grid.all_cells
            if (cell is not charger_cell)
            and not any(isinstance(a, ObstacleAgent) for a in cell.agents)
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

        # Crear el agente aspiradora
        self.num_agent = RandomAgent(self, cell = charger_cell)

        # Recolección de datos del agente para la estadística
        self.datacollector = DataCollector(
            model_reporters={
                "Step": lambda m: m.actual_step,
                "Remaining Dirty Cells": lambda m: m.remaining_dirty_cells,
                "CleanPercent": lambda m: (
                    0.0 if m.initial_dirty_cells == 0
                    else 100.0 * (m.initial_dirty_cells - m.remaining_dirty_cells) / m.initial_dirty_cells
                ),
                "Movements": lambda m: m.move_count,
                "BatteryLevel": lambda m: m.num_agent.battery,
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
        self.agents.shuffle_do("step")

        # Si ya no hay celdas sucias, se detiene la simulación
        if self.remaining_dirty_cells == 0 and self.time_to_clean is None:
            self.time_to_clean = self.actual_step
            self.running = False

        # Si se llega al tiempo máximo, se detiene la simulación
        if self.actual_step >= self.max_steps:
            self.running = False
        
        # Recolecta los datos del modelo
        self.datacollector.collect(self)
from tracemalloc import start
from mesa.discrete_space import CellAgent, FixedAgent
import heapq # Importa heapq para la implementación del algoritmo A*
# CellAgent: Agente que puede moverse entre celdas (agente aspiradora)
# FixedAgent: Agente que permanece fijo en una celda (obstáculo, suciedad, estación de recarga)

class ObstacleAgent(FixedAgent):
    """
    Celda con obstáculo. El agente no puede entrar aquí
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def step(self):
        pass

class DirtyPatch(FixedAgent):
    """
    Celda que puede estar sucia o limpia
    """
    def __init__(self, model, cell, dirty=True):
        super().__init__(model)
        self.cell = cell
        self.dirty = dirty # True si está sucia, False si está limpia

    def step(self):
        pass

class ChargingStation(FixedAgent):
    """
    Celda de estación de recarga que se va encontrar en la posición (1,1)
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass

class RandomAgent(CellAgent):
    """
    Agente aspiradora que hace:
    - Se mueve aleatoriamente por la cuadrícula
    - Limpia las celdas sucias
    - Gasta batería al moverse
    - Se regresa a recargar en la estación de recarga
    """
    def __init__(self, model, cell, battery=100):
        """
        Creamos un nuevo agente aspiradora.
        Args:
            model: Modelo al que pertenece el agente
            cell: Celda inicial del agente
            battery: Nivel inicial de batería
        """
        super().__init__(model)
        self.cell = cell
        self.battery = battery
        self.move_count = 0
        self.cleaned_cells = 0
        self.visited = set()
        if hasattr(self.cell, "coordinate"):
            self.visited.add(self.cell.coordinate)

    # @property permite acceder al método como si fuera un atributo
    @property
    def at_charger(self):
        """
        Verifica si el agente está localizado en mi estación de recarga
        """
        return any(isinstance(a, ChargingStation) for a in self.cell.agents)
    
    def neighbors_without_obstacles(self):
        """
        Regresa las celdas vecinas que no tiene obstaculos
        """
        neighbors = self.cell.neighborhood
        freeCell = neighbors.select(
            lambda cell: not any(isinstance(a, ObstacleAgent) for a in cell.agents)
        )
        return freeCell
    
    def distance_to_charger(self, cell = None):
        """
        Calcula la distancia que falta para llegar a la estación de recarga
        """
        if cell is None:
            cell = self.cell
        x, y = cell.coordinate
        chargerX, chargerY = self.model.charger_location
        return abs(x - chargerX) + abs(y - chargerY)
    
    def need_to_charge(self):
        """
        Verifica si el agente necesita recargar
        """
        distancia = self.distance_to_charger()
        return self.battery <= 30 or self.battery <= distancia + 5
    
    def movement(self, new_cell):
        """Actualizar posición y métricas al moverse a new_cell (Cell object)"""
        if new_cell is None:
            return
        self.cell = new_cell
        self.battery = max(0, self.battery - 1)
        self.move_count += 1
        self.model.move_count += 1
        if hasattr(self.model, "move_count"):
            self.model.move_count += 1
        if hasattr(self.cell, "coordinate"):
            self.visited.add(self.cell.coordinate)

    def move_towards_charger(self):
        """Selecciona la vecina que reduce la distancia Manhattan al cargador y se mueve"""
        freeCell = self.neighbors_without_obstacles()
        if len(freeCell) == 0:
            return
        best = None
        best_dist = None
        for c in freeCell:
            d = self.distance_to_charger(c)
            if best_dist is None or d < best_dist:
                best_dist = d
                best = c
        if best is not None:
            self.movement(best)
    
    def astar_path(start, goal, cells_by_coord, is_blocked=None, heuristica=None):
        """
        Función A* sobre coordenadas en una grilla.
        Args:
            start: Tupla (x, y) de la coordenada inicial
            goal: Tupla (x, y) de la coordenada objetivo
            cells_by_coord: Diccionario que mapea coordenadas a objetos Cell
            is_blocked: Función que recibe una coordenada y devuelve True si está bloqueada
            heuristic: Función heurística que recibe dos coordenadas y devuelve una estimación de costo
        """

        if start == goal:
            return [start]
        if goal not in cells_by_coord:
            return None

        if is_blocked is None:
            is_blocked = lambda c: False
        if heuristica is None:
            heuristica = lambda a, b: abs(a[0]-b[0]) + abs(a[1]-b[1])

        def neighbors(coordinada):
            x, y = coordinada
            for n in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if n in cells_by_coord and not is_blocked(n):
                    yield n

        open_heap = []
        g_score = {start: 0}
        desde = {start: None}
        heapq.heappush(open_heap, (heuristica(start, goal), 0, start))

        while open_heap:
            f, g, current = heapq.heappop(open_heap)
            if current == goal:
                # reconstruir camino
                path = []
                cur = current
                while cur is not None:
                    path.append(cur)
                    cur = desde[cur]
                path.reverse()
                return path

            for vecino in neighbors(current):
                tentative_g = g_score[current] + 1
                if vecino not in g_score or tentative_g < g_score[vecino]:
                    g_score[vecino] = tentative_g
                    desde[vecino] = current
                    heapq.heappush(open_heap, (tentative_g + heuristica(vecino, goal), tentative_g, vecino))

        return None

    def move(self):
        """
        Mueve el agente con prioridad:
        1) Si necesita recargar (o batería 0) y no está en cargador -> ir al cargador
        2) Vecina sucia
        3) Vecina limpia no visitada
        4) Vecina aleatoria sin obstáculo
        """

        # prioridad máxima: volver al cargador si hace falta
        if (self.need_to_charge() or self.battery == 0) and not self.at_charger:
            self.move_towards_charger()
            return
        
        freeCell = self.neighbors_without_obstacles()
        if len(freeCell) == 0:
            return
        
        # 1) Vecinas sucias
        dirty_neighbors = freeCell.select(
            lambda cell: any(isinstance(a, DirtyPatch) and a.dirty for a in cell.agents)
        )
        if len(dirty_neighbors) > 0:
            new_cell = dirty_neighbors.select_random_cell()
        else:
            # 2) Vecinas limpias no visitadas
            unvisited_clean = freeCell.select(
                lambda cell: not any(isinstance(a, DirtyPatch) and a.dirty for a in cell.agents)
                             and (not hasattr(cell, "coordinate") or cell.coordinate not in self.visited)
            )
            if len(unvisited_clean) > 0:
                new_cell = unvisited_clean.select_random_cell()
            else:
                # 3) fallback aleatorio
                new_cell = freeCell.select_random_cell()

        if new_cell is None:
            return

        # Actualizar posición y métricas
        self.movement(new_cell)

    def explore(self):
        """
        El agente explora moviendose a una celda vecina aleatoria
        """
        self.move()

    def clean(self):
        """
        Limpia la celda que localiza el agente
        """
        dirty_patches = [
            a for a in self.cell.agents
            if isinstance(a, DirtyPatch) and a.dirty
        ]
        if dirty_patches:
            dirty_patch = dirty_patches[0]
            dirty_patch.dirty = False
            self.battery = max(0, self.battery - 1)
            self.model.remaining_dirty_cells = max(0, self.model.remaining_dirty_cells - 1)
            self.model.cleaned_cells += 1

    def charge(self):
        """
        Recarga la bateria si está en la estación de recarga
        """
        if self.at_charger and self.battery < 100:
            self.battery = min(100, self.battery + 5)

    def step(self):
        # Si la celda está sucia, limpiar
        if any(isinstance(a, DirtyPatch) and a.dirty for a in self.cell.agents):
            if self.battery > 0:
                self.clean()
            return
        # Si necesita recargar y no está en la estación, moverse hacia ella
        elif self.need_to_charge() and not self.at_charger:
            if self.battery > 0:
                self.move()
            return
        # Si está en la estación y no está completamente cargado, recargar
        elif self.at_charger and self.battery < 100:
            self.charge()
            return
        # Si no necesita recargar, explorar
        elif self.battery > 0:
            self.explore()
            return
from mesa.discrete_space import CellAgent, FixedAgent

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
        self.dirty = dirty

    def step(self):
        pass

class ChargingStation(FixedAgent):
    """
    Celda de estación de recarga que se inicia en una posición aleatoria
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass

class RandomAgent(CellAgent):
    """
    Agente aspiradora que hace:
    - Conoce su estación inicial, pero puede recargar en cualquier estación
    - Se mueve aleatoriamente por la cuadrícula
    - Limpia las celdas sucias
    - Gasta batería al moverse
    - Se regresa a recargar en la estación de recarga
    """
    def __init__(self, model, cell, agent_id, main_charger_location, battery=100):
        """
        Creamos el agente con su celda inicial, 
        ubicación de la estación de recarga y batería inicial
        args:
            model: Modelo al que pertenece el agente
            cell: Celda inicial del agente
            agent_id: id del agente
            main_charger_location: (x, y) con la ubicación de la estación de recarga
            battery: Nivel inicial de batería
        """
        super().__init__(model)
        self.cell = cell
        self.agent_id = agent_id
        self.main_charger_location = main_charger_location
        self.battery = battery
        self.move_count = 0
        self.cleaned_cells = 0
        self.visited = set()
        if hasattr(self.cell, "coordinate"):
            self.visited.add(self.cell.coordinate)

    @property
    def at_charger(self):
        """
        Verifica si el agente está localizado en cualquier estación de recarga
        """
        return any(isinstance(a, ChargingStation) for a in self.cell.agents)
    
    def neighbors_without_obstacles(self):
        """
        Regresa las celdas vecinas que no tiene obstaculos ni están ocupadas por otro agente
        """
        neighbors = self.cell.neighborhood
        freeCell = neighbors.select(
            lambda cell: not any(isinstance(a, ObstacleAgent) for a in cell.agents)
            and not any(isinstance(a, RandomAgent) for a in cell.agents)
        )
        return freeCell
    
    def get_my_charger_location(self):
        """
        Es la ubicación de la estación de recarga principal para el agente
        """
        return self.main_charger_location if self.main_charger_location else self.cell.coordinate
    
    def distance_to_charger(self, cell = None):
        """
        Calcula la distancia que falta para llegar a mi estación main
        """
        if cell is None:
            cell = self.cell
        x, y = cell.coordinate
        chargerX, chargerY = self.get_my_charger_location()
        return abs(x - chargerX) + abs(y - chargerY)
    
    def need_to_charge(self):
        """
        Verifica si el agente necesita recargar
        Pero puede recargar en cualquier estación que encuentre
        """
        distancia = self.distance_to_charger()
        return self.battery <= 10 or self.battery <= distancia + 5
    
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

        # 2) Vecinas sucias
        dirty_neighbors = freeCell.select(
            lambda cell: any(isinstance(a, DirtyPatch) and a.dirty for a in cell.agents)
        )
        if len(dirty_neighbors) > 0:
            new_cell = dirty_neighbors.select_random_cell()
        else:
            # 3) Vecinas limpias no visitadas
            unvisited_clean = freeCell.select(
                lambda cell: not any(isinstance(a, DirtyPatch) and a.dirty for a in cell.agents)
                             and (not hasattr(cell, "coordinate") or cell.coordinate not in self.visited)
            )
            if len(unvisited_clean) > 0:
                new_cell = unvisited_clean.select_random_cell()
            else:
                # 4) fallback aleatorio
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
            self.cleaned_cells += 1

    def charge(self):
        """
        Recarga la bateria si está en una de las estaciones de recarga
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
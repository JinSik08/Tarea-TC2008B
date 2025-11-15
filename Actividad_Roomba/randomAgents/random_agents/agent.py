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

    @property
    def at_charger(self):
        """
        Verifica si el agente está localizado en la estación de batería
        """
        return self.cell.coordinate == self.model.charger_location
    
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
        return self.battery <= 20 or self.battery <= distancia + 5
    
    def move(self):
        """
        Mueve el agente a una celda vecina aleatoria donde no hay obstaculos
        """
        freeCell = self.neighbors_without_obstacles()
        if len(freeCell) == 0:
            return
        
        """
        Si necesita recargar, se selecciona la celda más cercana a la estación
        """
        actual_distance = self.distance_to_charger()
        close_cells = freeCell.select(
            lambda cell: self.distance_to_charger(cell) < actual_distance
        )

        """
        Si hay celdas más cercanas a la estación, se selecciona una de ellas aleatoriamente.
        """
        target_cells = close_cells if len(close_cells) > 0 else freeCell
        new_cell = target_cells.select_random_cell()
        if new_cell is None:
            return
        
        """Calcula la bateria restante y mueve el agente"""
        self.cell = new_cell
        self.battery -= 1
        self.model.move_count += 1

    def explore(self):
        """
        El agente explora moviendose a una celda vecina aleatoria
        """
        freeCells = self.neighbors_without_obstacles()
        if len(freeCells) == 0:
            return
        new_cell = freeCells.select_random_cell()
        self.cell = new_cell
        self.battery -= 1
        self.model.move_count += 1

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
            self.battery -= 1
            self.model.remaining_dirty_cells -= 1
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
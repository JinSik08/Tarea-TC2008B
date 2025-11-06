# FixedAgent: Immobile agents permanently fixed to cells
from mesa.discrete_space import FixedAgent

# Clase Cell hereda de FixedAgent
class Cell(FixedAgent):
    """Represents a single ALIVE or DEAD cell in the simulation."""

    # Constantes para los estados de la célula
    DEAD = 0
    ALIVE = 1

    # Property es un decorador que convierte un método en un atributo de solo lectura
    @property
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    @property
    def neighbors(self):
        return self.cell.neighborhood.agents
    
    # Constructor de la clase Cell
    def __init__(self, model, cell, init_state=DEAD):
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model) # super = llama al constructor de la clase padre FixedAgent
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    # Calcular siguiente estado sólo a partir de los 3 vecinos de la fila de arriba
    def set_next_state(self, left_state, center_state, right_state):
        """Calculate next state based on the three neighbors above"""
        # Convertir estados a patrón de cadena
        a = 1 if left_state == self.ALIVE else 0
        b = 1 if center_state == self.ALIVE else 0
        c = 1 if right_state == self.ALIVE else 0
        pattern = f"{a}{b}{c}"

        # Busca en la tabla de reglas el siguiente estado
        if pattern in ["111", "101", "010", "000"]:
            self._next_state = self.DEAD
        else:
            self._next_state = self.ALIVE

    # Actualiza el estado de la célula al siguiente estado calculado
    def assume_state(self):
        if self._next_state is not None:
            self.state = self._next_state
            self._next_state = None
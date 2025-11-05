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

    # Identifica el siguiente posible estado de la célula
    def determine_state(self):
        """Compute if the cell will be dead or alive at the next tick.  This is
        based on the number of alive or dead neighbors.  The state is not
        changed here, but is just computed and stored in self._nextState,
        because our current state may still be necessary for our neighbors
        to calculate their next state.
        """

        live_neighbors = 0
        for n in self.neighbors:
            live_neighbors += n.is_alive

        # Get the neighbors and apply the rules on whether to be alive or dead
        # at the next tick.
        #live_neighbors = sum(neighbor.is_alive for neighbor in self.neighbors)

        # Assume nextState is unchanged, unless changed below.
        self._next_state = self.state

        # Si los vecinos vivos son menos de 2 o más de 3, la célula muere
        if self.is_alive:
            if live_neighbors < 2 or live_neighbors > 3:
                self._next_state = self.DEAD
        # Si hay exactamente 3 vecinos vivos, la célula revive
        else:
            if live_neighbors == 3:
                self._next_state = self.ALIVE

    # Actualiza el estado de la célula al siguiente estado calculado
    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        self.state = self._next_state

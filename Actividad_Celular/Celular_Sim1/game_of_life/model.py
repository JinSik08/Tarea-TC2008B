from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import Cell


class ConwaysGameOfLife(Model):
    """Represents the 2-dimensional array of cells in Conway's Game of Life."""

    def __init__(self, width=50, height=50, initial_fraction_alive=0.2, seed=None):
        """Create a new playing area of (width, height) cells."""
        super().__init__(seed=seed) # seed es para la aleatoridad pero se dice desde donde de la secuencial se empieza

        """Grid where cells are connected to their 8 neighbors.

        Example for two dimensions:
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1),
        ]
        """
        self.grid = OrthogonalMooreGrid((width, height), capacity=1, torus=True)
        # torus significa que los bordes están unidos para que tengan los 8 vecinos siempre

        # Place a cell at each location, with some initialized to
        # ALIVE and some to DEAD.
        for cell in self.grid.all_cells:
            Cell(
                self, # modelo
                cell, # celda donde estoy
                init_state=(
                    Cell.ALIVE
                    if self.random.random() < initial_fraction_alive
                    else Cell.DEAD
                ),
            )

        self.running = True

    def step(self):
        """Perform the model step in two stages:

        - First, all cells assume their next state (whether they will be dead or alive)
        - Then, all cells change state to their next state.
        """
        self.agents.do("determine_state") # Determino el siguiente estado
        self.agents.do("assume_state") # Actualizo al siguiente estado

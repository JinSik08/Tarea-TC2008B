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
        self.cell_grid = {}  # Para acceso rápido a los agentes por posición

        # Inicializar las células en la fila superior (height-1)
        for cell in self.grid.all_cells:
            x, y = cell.coordinate
            init_state = (
                Cell.ALIVE
                if (self.random.random() < initial_fraction_alive)
                else Cell.DEAD
            )
            self.cell_grid[(x, y)] = Cell(
                self,  # modelo
                cell,  # celda donde estoy
                init_state=init_state,
            )

        self.running = True

    def step(self):
        """Avanza una fila para cada step. Cada step actualiza la fila siguiente en base a
        los 3 vecinos de la fila anterior usando la tabla de reglas dada."""
        # 
        width = self.grid.width
        height = self.grid.height

        # Calcula los siguientes estados para cada célula
        for agent in self.agents:
            x, y = agent.pos
            
            # Posiciones de los 3 vecinos de la fila
            above = (y + 1) % height # fila de arriba (torus)
            left_pos = ((x - 1) % width, above)
            center_pos = ((x) % width, above)
            right_pos = ((x + 1) % width, above)

            # Obtener estados de los vecinos (0 o 1)
            left_state = self.cell_grid[left_pos].state
            center_state = self.cell_grid[center_pos].state
            right_state = self.cell_grid[right_pos].state

            # Calcular el siguiente estado
            agent.set_next_state(left_state, center_state, right_state)

        # Actualiza todos los agentes al siguiente estado calculado
        for agent in self.agents:
            agent.assume_state()
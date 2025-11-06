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

        # Mantener referencias a los agentes por posición para acceso directo
        self.cell_grid = {}

        # La fila que ya fue actualizada (height-1 = fila superior ya inicializada)
        self.current_row = height - 1

        # Inicializar las células en la fila superior (height-1)
        for cell in self.grid.all_cells:
            x, y = cell.coordinate
            init_state = (
                Cell.ALIVE
                if (y == self.current_row and self.random.random() < initial_fraction_alive)
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
        los 3 vecinos de la fila anterior usando la tabla de reglas dada.

        Regla (donde 1=Alive, 0=Dead):
        111 -> 0
        110 -> 1
        101 -> 0
        100 -> 1
        011 -> 1
        010 -> 0
        001 -> 1
        000 -> 0

        Se detiene cuando se alcanza la última fila.
        """
        width = self.grid.width

        # Si ya actualizamos hasta la última fila (fila 0 en el bottom), detenemos la simulación.
        if self.current_row <= 0:
            self.running = False
            return

        prev_row = self.current_row
        next_row = prev_row - 1

        # Para cada columna calculamos el estado de la celda en la fila siguiente
        for x in range(width):
            # Posiciones de los 3 vecinos de la fila
            left_pos = ((x - 1) % width, prev_row)
            center_pos = (x, prev_row)
            right_pos = ((x + 1) % width, prev_row)

            # Guardamos los agentes vecinos en el grid
            left_agent = self.cell_grid[left_pos]
            center_agent = self.cell_grid[center_pos]
            right_agent = self.cell_grid[right_pos]

            # Pasamos los estados a la siguiente celda
            next_pos = (x, next_row)
            next_agent = self.cell_grid[next_pos]

            # Calculamos el siguiente estado
            next_agent.set_next_state(
                left_agent.state,
                center_agent.state,
                right_agent.state,
            )
        
        # Ahora aplicamos los next_state en la fila siguiente
        for x in range(width):
            next_agent = self.cell_grid[(x, next_row)]
            next_agent.assume_state()

        # Marcamos que la siguiente fila ya fue actualizada
        self.current_row = next_row
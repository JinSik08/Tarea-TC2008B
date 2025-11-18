# Importamos las librerías necesarias que tenemos
from simulacion_1.agent import RandomAgent, ObstacleAgent, DirtyPatch, ChargingStation
from simulacion_1.model import RandomModel
import time, solara
# time para utilizar como seed aleatoria
# solara para utilizarlo para impresión de estadísticas en la página en formato markdown

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component, # Componente de visualización del espacio
    make_plot_component, # Componente de visualización de gráficos
)

from mesa.visualization.components import AgentPortrayalStyle # Estilo de representación de agentes

def random_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=80,
        marker = "s",
        color="red",
    )

    if isinstance(agent, RandomAgent):
        portrayal.zorder = 3
        if agent.battery == 0:
            portrayal.color = "lightgray"
            portrayal.size = 100
        else:
            portrayal.color = "red"
            portrayal.size = 100
    elif isinstance(agent, ChargingStation):
        portrayal.color = "green"
        portrayal.size = 100
        portrayal.zorder = 2
    elif isinstance(agent, ObstacleAgent):
        portrayal.color = "black"
        portrayal.size = 100
        portrayal.zorder = 1
    elif isinstance(agent, DirtyPatch):
        portrayal.zorder = 0
        if agent.dirty:
            portrayal.color = "orange"
            portrayal.size = 100
            portrayal.alpha = 1.0
        else:
            portrayal.color = "white"
            portrayal.size = 0
            portrayal.alpha = 0.0

    return portrayal

# Función para ajustar el aspecto del espacio
def post_process_space(ax):
    ax.set_aspect("equal")

# Función para ajustar el aspecto de los gráficos
def post_process_lines(ax):
    ax.legend(loc = "center left", bbox_to_anchor = (1, 0.9))

model_params = {
    "seed": {
        "type": "InputText",
        "value": int(time.time()),
        "label": "Random Seed",
    },
    "width": Slider("Grid width (M)", 10, 5, 40),
    "height": Slider("Grid height (M)", 10, 5, 40),
    "dirty_percent": Slider("Dirty %", 0.4, 0.0, 1.0, 0.05),
    "obstacle_percent": Slider("Obstacle %", 0.1, 0.0, 0.5, 0.05),
    "max_steps": Slider("Max Steps", 500, 50, 5000, 50),
}

# Crear la instancia del modelo
model = RandomModel(
    width=model_params["width"].value,
    height=model_params["height"].value,
    dirty_percent=model_params["dirty_percent"].value,
    obstacle_percent=model_params["obstacle_percent"].value,
    max_steps=model_params["max_steps"].value,
)

# Componente de visualización del espacio
space_component = make_space_component(
        random_portrayal,
        draw_grid = False,
        post_process=post_process_space,
)

# Componente de visualización de gráficos
plot_component = make_plot_component(
    {
        "CleanPercent": "blue",
        "BatteryLevel": "orange",
    },
    post_process_lines,
)

def stats_component(model):
    df = model.datacollector.get_model_vars_dataframe()
    last = df.iloc[-1]

    # Datos para el porcentaje de celdas limpias
    clean_percent = last["CleanPercent"]
    # Datos para el número de movimientos realizados
    movements = last["Movements"]
    # Datos para el estado de celdas sucias restantes
    dirty_remaining = model.remaining_dirty_cells
    current_step = model.actual_step
    if dirty_remaining == 0:
        status = "**Todas las celdas están limpias!**"
        time_info = f"Tiempo utilizado: {current_step} pasos"
    elif current_step >= model.max_steps:
        status = "**Tiempo agotado**"
        time_info = f"Celdas sucias restantes: {dirty_remaining}"
    else:
        status = "**Limpieza en progreso...**"
        time_info = f"Celdas sucias restantes: {dirty_remaining}"

    return solara.Markdown(
        f""" 
###
### Estadísticas de la Simulación
                           
- {status}
- {time_info}

- **Porcentaje de celdas limpias:** `{clean_percent:.2f}%`

- **Cambio de celdas realizados:** `{movements}`

- **Batería que sobra:** `{last["BatteryLevel"]:.2f}%`
""")

# Página de visualización del modelo
page = SolaraViz(
    model,
    components=[space_component, plot_component, stats_component],
    model_params=model_params,
    name="Simulación 1: Aspiradora (Jin Sik - A01026630)",
)

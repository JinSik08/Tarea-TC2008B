from random_agents.agent import RandomAgent, ObstacleAgent, DirtyPatch, ChargingStation
from random_agents.model import RandomModel

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
    make_plot_component, # Para crear gráficos de estadísticas
)

from mesa.visualization.components import AgentPortrayalStyle

def random_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, RandomAgent):
        portrayal.color = "blue"
        portrayal.size = 80
    elif isinstance(agent, ObstacleAgent):
        portrayal.color = "black"
        portrayal.marker = "s"
        portrayal.size = 100
    elif isinstance(agent, DirtyPatch):
        portrayal.color = "sienna" if agent.dirty else "lightgrey"
        portrayal.marker = "s"
        portrayal.size = 70
    elif isinstance(agent, ChargingStation):
        portrayal.color = "green"
        portrayal.marker = "p"
        portrayal.size = 100

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
        "value": 42,
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
    seed=None
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

# Página de visualización del modelo
page = SolaraViz(
    model,
    components=[space_component, plot_component],
    model_params=model_params,
    name="Simulación 1: Aspiradora",
)

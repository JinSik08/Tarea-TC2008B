from simulacion_2.agent import RandomAgent, ObstacleAgent, DirtyPatch, ChargingStation
from simulacion_2.model import RandomModel
import time, solara

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def random_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=100,
        marker="s",
        color="red",
        alpha=0.0,
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
    "num_agents": Slider("Number of Agents", 3, 1, 10, 1),
    "dirty_percent": Slider("Dirty %", 0.4, 0.0, 1.0, 0.05),
    "obstacle_percent": Slider("Obstacle %", 0.1, 0.0, 0.5, 0.05),
    "max_steps": Slider("Max Steps", 500, 50, 5000, 50),
}

# Función para crear una instancia del modelo
model = RandomModel(
    width=model_params["width"].value,
    height=model_params["height"].value,
    num_agents=model_params["num_agents"].value,
    dirty_percent=model_params["dirty_percent"].value,
    obstacle_percent=model_params["obstacle_percent"].value,
    max_steps=model_params["max_steps"].value,
    seed=model_params["seed"]["value"],
)

# Componente de visualización del espacio
space_component = make_space_component(
        random_portrayal,
        draw_grid = False,
        post_process=post_process_space,
)

def plot_component(model):
    import matplotlib.pyplot as plt # Importar matplotlib
    
    model_data = model.datacollector.get_model_vars_dataframe()
    
    if model_data.empty:
        return solara.Markdown("**No hay datos aún**")
    
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # CleanPercent
    if "CleanPercent" in model_data.columns:
        ax.plot(model_data.index, model_data["CleanPercent"], 
                label="CleanPercent", color="blue", linewidth=2)
    
    # Batería de cada agente
    colors = ["red", "green", "orange", "purple", "brown", "pink", "gray", "cyan", "magenta", "yellow"]
    for i in range(model.num_agents):
        battery_col = f"Battery_{i}"
        if battery_col in model_data.columns:
            ax.plot(model_data.index, model_data[battery_col], 
                   label=f"Agente {i+1}", 
                   color=colors[i % len(colors)])
    
    ax.set_xlabel('Step')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.9))
    ax.set_ylim(0, 100) # Limitar el eje Y de 0 a 100
    
    return solara.FigureMatplotlib(fig)

def stats_component(model):
    df = model.datacollector.get_model_vars_dataframe()
    last = df.iloc[-1]

    # Datos para el porcentaje de celdas limpias
    clean_percent = last["CleanPercent"]
    # Datos para el número de movimientos realizados
    movements = last["Movements"]
    # Datos para el nivel promedio de batería
    avg_battery = last["AvgBattery"]
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

    # Estadísticas por cada agente
    agent_stats = []
    for i, agent in enumerate(model.cleaners):
        agent_stats.append(
            f"  - **Agente {i+1}:** Batería: `{agent.battery}%`, "
            f"Cambio de celdas: `{agent.move_count}`, "
            f"Limpiadas: `{agent.cleaned_cells}`"
        )
    
    agent_stats_str = "\n".join(agent_stats)

    return solara.Markdown(
        f""" 
### Estadísticas de la Simulación
                           
- {status}
- {time_info}

- **Porcentaje de celdas limpias:** `{clean_percent:.2f}%`

- **Cambios de celdas en promedio:** `{movements}`

- **Batería promedio:** `{avg_battery:.2f}%`

### Estadísticas por Agente:
{agent_stats_str}
""")

# Página de visualización del modelo
page = SolaraViz(
    model,
    components=[space_component, plot_component, stats_component],
    model_params=model_params,
    name="Simulación 2: Múltiples agentes Aspiradora (Jin Sik - A01026630)",
)
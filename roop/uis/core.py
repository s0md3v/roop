from typing import Dict
import gradio

from roop.uis.__layouts__ import default
from roop.uis.typing import Component, ComponentName

COMPONENTS: Dict[ComponentName, Component] = {}


def init() -> None:
    default.render().launch()


def get_theme() -> gradio.Theme:
    return gradio.themes.Soft(
        primary_hue=gradio.themes.colors.red,
        secondary_hue=gradio.themes.colors.gray,
        font=gradio.themes.GoogleFont('Open Sans')
    )


def get_component(name: ComponentName) -> Component:
    return COMPONENTS[name]


def register_component(name: ComponentName, component: Component) -> None:
    COMPONENTS[name] = component

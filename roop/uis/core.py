from typing import Dict
import gradio

from roop.uis import source, target, preview, settings, output
from roop.uis.typing import Component, ComponentName

COMPONENTS: Dict[ComponentName, Component] = {}


def init() -> None:
    with gradio.Blocks(theme=get_theme()) as ui:
        with gradio.Row():
            settings.render()
            with gradio.Row():
                source.render()
                target.render()
            preview.render()
        output.render()
    ui.launch()


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

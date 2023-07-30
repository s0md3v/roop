import gradio

from roop.uis.__components__ import settings, source, target, preview, output
import roop.uis.core as ui


def render() -> gradio.Blocks:
    with gradio.Blocks(theme=ui.get_theme()) as layout:
        with gradio.Row():
            with gradio.Column(scale=1):
                settings.render()
            with gradio.Column(scale=1):
                source.render()
                target.render()
            with gradio.Column(scale=2):
                preview.render()
        with gradio.Row():
            output.render()
    return layout

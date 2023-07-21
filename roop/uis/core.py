import gradio
from roop.uis import source, target, output


def init() -> None:
    with gradio.Blocks() as ui:
        source.render()
        target.render()
        output.render()
    ui.launch()

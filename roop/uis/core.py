import gradio
from roop.uis import source, target, preview, output


def init() -> None:
    with gradio.Blocks() as ui:
        source.render()
        target.render()
        preview.render()
        output.render()
    ui.launch()

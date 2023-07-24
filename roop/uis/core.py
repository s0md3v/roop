import gradio
from roop.uis import source, target, preview, output


def init() -> None:
    with gradio.Blocks(theme=get_theme()) as ui:
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
        font=[gradio.themes.GoogleFont('Open Sans'), 'Arial', 'sans-serif']
    )

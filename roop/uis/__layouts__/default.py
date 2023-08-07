import gradio

from roop.uis.__components__ import settings, source, target, preview, reference, output


def render() -> gradio.Blocks:
    with gradio.Blocks() as layout:
        with gradio.Row():
            with gradio.Column(scale=1):
                settings.render()
            with gradio.Column(scale=1):
                source.render()
                target.render()
            with gradio.Column(scale=2):
                preview.render()
                reference.render()
        with gradio.Row():
            output.render()
    return layout


def listen() -> None:
    settings.listen()
    source.listen()
    target.listen()
    preview.listen()
    reference.listen()
    output.listen()

"""Descargar las revisiones seleccionadas sin cargar los modelos en memoria."""
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
for version, revision in (
    ("v3.6.0", "4cfcb9b23190f7d2455f6dd3a99c034a9b22d090"),
):
    snapshot_download(
        "cs21004/robertuito-toxicidad-sv", revision=revision,
        local_dir=ROOT / "models" / version / "semilla_42" / "modelo",
        ignore_patterns=["*.bin", "*.h5", "*.msgpack"],
    )
snapshot_download(
    "caeher/mbert-toxicidad-sv-v2",
    revision="a774917a5546a7da25fa6f57d3563881337dc90a",
    local_dir=ROOT / "models" / "mbert-toxicidad-sv-v2",
    ignore_patterns=["*.bin", "*.h5", "*.msgpack"],
)
snapshot_download(
    "TheArbite/xlmr-large-hateval-hate-speech-sv",
    revision="9476aae3116cf3a2bde95b9a410284c5186a1f1f",
    ignore_patterns=["*.bin", "*.h5", "*.msgpack"],
)

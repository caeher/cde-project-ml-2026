#!/usr/bin/env python
"""Verificación reproducible del entorno Hugging Face (TFM-21)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import torch
import transformers
from datasets import __version__ as datasets_version
from accelerate import __version__ as accelerate_version
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
VERIFY_DIR = ROOT / ".hf-verify"
MODELS = {
    "mbert": {
        "repo_id": "google-bert/bert-base-multilingual-cased",
        "model_name": "bert-base-multilingual-cased",
        "expected_type": "bert",
    },
    "xlmr": {
        "repo_id": "FacebookAI/xlm-roberta-base",
        "model_name": "xlm-roberta-base",
        "expected_type": "xlm-roberta",
    },
}


def _run_hf(args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        ["hf", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output.strip()


def _check_hf_auth() -> None:
    code, output = _run_hf(["auth", "whoami"])
    if code != 0 or "user=" not in output:
        raise RuntimeError(
            "Sesión Hugging Face no activa. Ejecuta: hf auth login "
            "(o notebook_login() en Colab)."
        )
    print(f"[OK] Hugging Face auth: {output}")


def _download_config(key: str, cfg: dict) -> Path:
    target = VERIFY_DIR / key
    target.mkdir(parents=True, exist_ok=True)
    code, output = _run_hf(
        [
            "download",
            cfg["repo_id"],
            "config.json",
            "--local-dir",
            str(target),
        ]
    )
    if code != 0:
        raise RuntimeError(f"No se pudo descargar config de {cfg['repo_id']}: {output}")

    config_path = target / "config.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    model_type = data.get("model_type")
    if model_type != cfg["expected_type"]:
        raise RuntimeError(
            f"model_type inesperado para {key}: {model_type} (esperado {cfg['expected_type']})"
        )
    print(f"[OK] {key}: config.json descargado ({model_type})")
    return config_path


def _check_tokenizers() -> None:
    for key, cfg in MODELS.items():
        tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"])
        print(f"[OK] {key}: tokenizer cargado (vocab={tokenizer.vocab_size})")


def main() -> int:
    print("=== Verificación TFM-21: entorno Hugging Face ===")
    print(f"Python: {sys.version.split()[0]}")
    print(f"torch: {torch.__version__} | cuda: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"transformers: {transformers.__version__}")
    print(f"datasets: {datasets_version}")
    print(f"accelerate: {accelerate_version}")
    print()

    _check_hf_auth()
    for key, cfg in MODELS.items():
        _download_config(key, cfg)
    _check_tokenizers()

    print()
    print("Verificación TFM-21 completada correctamente.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

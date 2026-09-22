"""Pruebas del motor V3 (sin entrenar ni inferir en CPU)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import torch

from modeling_v3.constants import REFERENCE_SHA256
from modeling_v3.data import validar_contrato
from modeling_v3.device import require_cuda
from modeling_v3.normalization import normalizar
from modeling_v3.paths import default_data_dir


def test_import_modeling_v3():
    import modeling_v3  # noqa: F401

    assert modeling_v3.CLASES[0] == "No Tóxico"


def test_cli_parser_build_data():
    from modeling_v3.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["build-data", "--data-dir", str(default_data_dir())])
    assert args.command == "build-data"


def test_normalizacion_ejemplos():
    assert "@usuario" in normalizar("Hola @juan_perez")
    assert "http://url" in normalizar("Mira https://ejemplo.com/x")
    t = normalizar("sos un 🤡")
    assert "payaso" in t.lower() or ":payaso" in t.lower() or "cara" in t.lower()


def test_contrato_datos_hashes():
    res = validar_contrato(default_data_dir())
    assert res["ok"] is True
    for nombre, sha_ref in REFERENCE_SHA256.items():
        info = res["archivos"][nombre]
        assert info["coincide"] is True
        assert info["sha256"] == sha_ref


def test_reconstruir_sin_lexico():
    from modeling_v3.data import reconstruir

    with pytest.raises(FileNotFoundError, match="lexicon_salvadoreno"):
        reconstruir()


def test_require_cuda_sin_gpu():
    with patch.object(torch.cuda, "is_available", return_value=False):
        with pytest.raises(RuntimeError, match="CUDA"):
            require_cuda()

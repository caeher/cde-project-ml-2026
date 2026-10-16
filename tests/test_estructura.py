# -*- coding: utf-8 -*-
"""Pruebas rápidas, sin GPU ni modelos: python -m unittest discover tests"""
import hashlib, json, sys, unittest
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402


class Rutas(unittest.TestCase):
    def test_rutas_existen(self):
        for nombre in ["DATA", "DATASET", "HISTORY", "SOURCES", "X_THREADS", "THREADS", "THREAD_LABELS", "FROZEN_BANK", "HARD_CASES", "AFFECTIVE_PROBE", "REPORTS_IMPROVEMENT"]:
            self.assertTrue(getattr(P, nombre).exists(), nombre)

    def test_versiones_historicas(self):
        for v in ["1.1.0", "1.2.0", "1.3.0", "1.3.1", "1.4.0-a", "1.4.0", "1.5.0", "1.6.0", "1.7.0"]:
            self.assertTrue((P.history(v) / "train.csv").exists(), v)

    def test_sin_carpetas_viejas(self):
        for viejo in ["hilos_reales", "banco_congelado", "dataset_final", "hard_cases", "dataset_b2", "dataset_v3", "dataset_v4", "raw", "interim", "processed"]:
            self.assertFalse((P.DATA / viejo).exists(), viejo)


class BancoCongelado(unittest.TestCase):
    def test_sha256_igual_al_manifest(self):
        man = json.loads((P.FROZEN_BANK / "MANIFEST.json").read_text(encoding="utf-8"))
        for k, v in man.items():
            self.assertEqual(hashlib.sha256((RAIZ / v["archivo"]).read_bytes()).hexdigest(), v["sha256"], k)


class Dataset(unittest.TestCase):
    def test_version_y_sin_fugas(self):
        import pandas as pd
        from src.data.build_dataset_final import verificar
        meta = json.loads((P.DATASET / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta.get("version"), P.DATASET_VERSION)
        tr, va, te, adv = (pd.read_csv(P.DATASET / f) for f in ["train.csv", "val.csv", "test.csv", "test_adversarial.csv"])
        banco = {k: pd.read_csv(P.FROZEN_BANK / f"{k}.csv").rename(columns={"texto_original": "texto"}) for k in ["migrantes", "externo2", "militares", "xenofobia"]}
        verificar(tr, va, te, adv, banco)  # lanza AssertionError si hay fuga
        self.assertEqual(len(tr), meta["train_total"])

    def test_val_test_iguales_en_todas_las_versiones(self):
        import pandas as pd
        ref = {f: pd.read_csv(P.DATASET / f).set_index("ID")[["texto_original", "label"]] for f in ["val.csv", "test.csv"]}
        for v in ["1.1.0", "1.2.0", "1.3.1", "1.4.0", "1.5.0", "1.6.0", "1.7.0"]:
            for f, r in ref.items():
                d = pd.read_csv(P.history(v) / f).set_index("ID")[["texto_original", "label"]]
                self.assertTrue(d.reindex(r.index).equals(r), f"{v}/{f}")


class Metricas(unittest.TestCase):
    def test_f1m_y_mcnemar(self):
        from src.evaluation.metrics import f1m, mcnemar
        y = np.array([0, 1, 2, 3, 0, 1, 2, 3]); self.assertAlmostEqual(f1m(y, y), 1.0)
        self.assertAlmostEqual(f1m(y, np.array([0, 1, 2, 3, 1, 0, 3, 2])), 0.5)
        a = np.array([True] * 10 + [False] * 10); b = np.array([True] * 20)
        m = mcnemar(a, b); self.assertEqual((m["b"], m["c"]), (10, 0)); self.assertLess(m["p_exacta"], 0.01)

    def test_reexportaciones(self):
        import src.evaluation.comparar_v4 as v4, src.evaluation.comparar_modelos as cm, src.evaluation.metrics as me
        self.assertIs(v4.f1m, me.f1m); self.assertIs(v4.ic_delta, me.ic_delta); self.assertIs(cm.mcnemar, me.mcnemar)


class Normalizacion(unittest.TestCase):
    def test_v1_2_casos_fijos(self):
        from src.features.normalization import normalizar
        self.assertEqual(normalizar("@juanperez hola http://x.com/abc 😂"), "@usuario hola http://url :cara_llorando_de_risa:")
        for t in ["SOS UN IDIOTA!!!", "te voy a buscar"]:
            self.assertTrue(normalizar(t).strip())


if __name__ == "__main__":
    unittest.main()

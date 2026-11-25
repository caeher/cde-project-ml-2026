"""Pruebas de catálogo e inferencia sin descargar pesos."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch

from app.api import main


class Encoding(dict):
    def to(self, device):
        return self


class Modelo:
    def __init__(self, logits):
        self.logits = torch.tensor([logits], dtype=torch.float64)

    def __call__(self, **kwargs):
        return SimpleNamespace(logits=self.logits)


class TestModelos(unittest.TestCase):
    def test_catalogo_oficial(self):
        self.assertEqual(
            [item['id'] for item in main.CATALOGO],
            ['v3.6.0', 'mbert_v2', 'xlmr_hf', 'xlmr_local'],
        )

    def test_obtener_xlmr_local(self):
        state = {'id': 'xlmr_local'}
        with patch.object(main, '_cache', {}), patch.object(
            main, '_cargar_xlmr_local', return_value=state
        ) as cargar:
            self.assertIs(main._obtener('xlmr_local'), state)
            self.assertIs(main._obtener('xlmr_local'), state)
        cargar.assert_called_once_with()

    def test_mbert_promedia_tres_probabilidades(self):
        modelos = [Modelo(x) for x in ([2., 1., 0., 0.], [0., 3., 1., 0.], [1., 0., 2., 0.])]
        state = {
            'tipo': 'ensemble', 'id': 'mbert_v2', 'nombre': main.MBERT_HF_ID,
            'tok': lambda *args, **kwargs: Encoding(),
            'modelos': modelos, 'temperatura': 1.0,
        }
        with patch.object(main, 'normalizar', return_value='hola'):
            result = main._predecir_con_estado(state, 'hola')
        expected = np.mean([torch.softmax(m.logits, -1).numpy()[0] for m in modelos], axis=0)
        np.testing.assert_allclose(list(result['probabilidades'].values()), expected)
        self.assertEqual(result['n_modelos'], 3)
        self.assertEqual(result['modelo_id'], 'mbert_v2')


if __name__ == '__main__':
    unittest.main()

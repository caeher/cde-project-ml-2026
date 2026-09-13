# -*- coding: utf-8 -*-
"""
Inferencia de mBERT (bert-base-multilingual-cased) en NumPy puro.

Mismo enfoque que xlmr_numpy.py: se lee model.safetensors y se ejecuta el
forward pass a mano, sin PyTorch. El sandbox no admite torch (el índice de
descarga está bloqueado y la rueda de PyPI arrastra los paquetes CUDA, que no
caben en disco), así que auditar los pesos entregados exige reimplementar.

Diferencias frente a XLM-RoBERTa:
  · prefijo de pesos `bert.` en vez de `roberta.`
  · posiciones absolutas 0..T-1 (RoBERTa desplaza y salta el padding)
  · LayerNorm guardado como `gamma`/`beta` (nomenclatura antigua), eps 1e-12
  · cabeza = pooler (densa + tanh sobre [CLS]) y luego `classifier`,
    no la RobertaClassificationHead
"""
import json
from pathlib import Path

import numpy as np
from safetensors import safe_open
from tokenizers import Tokenizer

MODELO = Path("/tmp/mbw/mbert-sv")

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]


def layer_norm(x, w, b, eps):
    m = x.mean(-1, keepdims=True)
    v = x.var(-1, keepdims=True)
    return (x - m) / np.sqrt(v + eps) * w + b


def gelu(x):
    from scipy.special import erf
    return 0.5 * x * (1.0 + erf(x / np.sqrt(2.0)))


def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


class MBertNumpy:
    def __init__(self, modelo=MODELO):
        self.dir = Path(modelo)
        self.W = {}
        with safe_open(str(self.dir / "model.safetensors"), framework="np") as f:
            for k in f.keys():
                self.W[k] = f.get_tensor(k).astype(np.float32)
        self.cfg = json.load(open(self.dir / "config.json", encoding="utf-8"))
        self.tok = Tokenizer.from_file(str(self.dir / "tokenizer.json"))
        self.H = self.cfg["hidden_size"]
        self.L = self.cfg["num_hidden_layers"]
        self.A = self.cfg["num_attention_heads"]
        self.dh = self.H // self.A
        self.pad = self.cfg["pad_token_id"]
        self.eps = self.cfg["layer_norm_eps"]

    def _ln(self, x, prefijo):
        """LayerNorm tolerante a las dos nomenclaturas (gamma/beta o weight/bias)."""
        W = self.W
        g = W.get(prefijo + ".gamma", W.get(prefijo + ".weight"))
        b = W.get(prefijo + ".beta", W.get(prefijo + ".bias"))
        return layer_norm(x, g, b, self.eps)

    # ---------------------------------------------------------------- tokenizar
    def codificar(self, textos, max_length=128):
        encs = [self.tok.encode(t) for t in textos]
        ids = [e.ids[:max_length] for e in encs]
        n = max(len(i) for i in ids)
        X = np.full((len(ids), n), self.pad, dtype=np.int64)
        M = np.zeros((len(ids), n), dtype=np.float32)
        for i, seq in enumerate(ids):
            X[i, : len(seq)] = seq
            M[i, : len(seq)] = 1.0
        return X, M

    # ---------------------------------------------------------------- forward
    def forward(self, input_ids, mask):
        W, H, A, dh = self.W, self.H, self.A, self.dh
        B, T = input_ids.shape

        # --- Embeddings: BERT usa posiciones absolutas 0..T-1 ---
        pos = np.arange(T)[None, :].repeat(B, axis=0)
        x = (W["bert.embeddings.word_embeddings.weight"][input_ids]
             + W["bert.embeddings.position_embeddings.weight"][pos]
             + W["bert.embeddings.token_type_embeddings.weight"][0])
        x = self._ln(x, "bert.embeddings.LayerNorm")

        add_mask = (1.0 - mask)[:, None, None, :] * -1e9

        for l in range(self.L):
            p = f"bert.encoder.layer.{l}."
            q = x @ W[p + "attention.self.query.weight"].T + W[p + "attention.self.query.bias"]
            k = x @ W[p + "attention.self.key.weight"].T + W[p + "attention.self.key.bias"]
            v = x @ W[p + "attention.self.value.weight"].T + W[p + "attention.self.value.bias"]

            def split(t):
                return t.reshape(B, T, A, dh).transpose(0, 2, 1, 3)

            q, k, v = split(q), split(k), split(v)
            scores = q @ k.transpose(0, 1, 3, 2) / np.sqrt(dh) + add_mask
            ctx = softmax(scores) @ v
            ctx = ctx.transpose(0, 2, 1, 3).reshape(B, T, H)

            ao = ctx @ W[p + "attention.output.dense.weight"].T + W[p + "attention.output.dense.bias"]
            x = self._ln(ao + x, p + "attention.output.LayerNorm")

            inter = gelu(x @ W[p + "intermediate.dense.weight"].T + W[p + "intermediate.dense.bias"])
            out = inter @ W[p + "output.dense.weight"].T + W[p + "output.dense.bias"]
            x = self._ln(out + x, p + "output.LayerNorm")

        # --- Cabeza: pooler sobre [CLS] y clasificador lineal ---
        pooled = np.tanh(x[:, 0, :] @ W["bert.pooler.dense.weight"].T + W["bert.pooler.dense.bias"])
        return pooled @ W["classifier.weight"].T + W["classifier.bias"]

    # ---------------------------------------------------------------- API
    def predecir(self, textos, max_length=128, batch=16, con_probs=False):
        partes = []
        for i in range(0, len(textos), batch):
            X, M = self.codificar(textos[i:i + batch], max_length)
            partes.append(self.forward(X, M))
        L = np.concatenate(partes, axis=0)
        if con_probs:
            return L.argmax(-1), softmax(L)
        return L.argmax(-1)


if __name__ == "__main__":
    m = MBertNumpy()
    pruebas = ["Buenos días a todos, qué bonito día",
               "Sos un pendejo de mierda",
               "Esos indios de mierda no deberían estar aquí",
               "Te voy a matar hijo de puta"]
    pred, probs = m.predecir(pruebas, con_probs=True)
    for t, p, pr in zip(pruebas, pred, probs):
        print(f"{CLASES[p]:<20} conf={pr[p]:.3f}  :: {t}")

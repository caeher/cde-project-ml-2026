# -*- coding: utf-8 -*-
"""
Inferencia de XLM-RoBERTa en NumPy puro.

Se implementa el forward pass leyendo directamente model.safetensors, sin PyTorch.
Permite auditar el modelo entrenado del equipo en un entorno sin GPU ni torch.
"""
import json
from pathlib import Path

import numpy as np
from safetensors import safe_open
from tokenizers import Tokenizer

BASE = Path("/sessions/bold-practical-shannon/mnt/proyecto/Métricas de Evaluación/Para modelo XLMR")
MODELO = BASE / "02_modelo_prototipo/modelo_entrenado"
TOKJSON = BASE / "01_dataset_y_entrenamiento/results_xlmr/checkpoint-134/tokenizer.json"

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]


def cargar_pesos():
    W = {}
    with safe_open(str(MODELO / "model.safetensors"), framework="np") as f:
        for k in f.keys():
            W[k] = f.get_tensor(k).astype(np.float32)
    cfg = json.load(open(MODELO / "config.json"))
    return W, cfg


def layer_norm(x, w, b, eps=1e-5):
    m = x.mean(-1, keepdims=True)
    v = x.var(-1, keepdims=True)
    return (x - m) / np.sqrt(v + eps) * w + b


def gelu(x):
    # GELU exacta (la que usa HF para hidden_act="gelu")
    from scipy.special import erf
    return 0.5 * x * (1.0 + erf(x / np.sqrt(2.0)))


def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


class XLMRNumpy:
    def __init__(self):
        self.W, self.cfg = cargar_pesos()
        self.tok = Tokenizer.from_file(str(TOKJSON))
        self.H = self.cfg["hidden_size"]
        self.L = self.cfg["num_hidden_layers"]
        self.A = self.cfg["num_attention_heads"]
        self.dh = self.H // self.A
        self.pad = self.cfg["pad_token_id"]
        self.eps = self.cfg["layer_norm_eps"]

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
        W, H, A, dh, eps = self.W, self.H, self.A, self.dh, self.eps
        B, T = input_ids.shape

        # --- Embeddings ---
        # RoBERTa: las posiciones arrancan en pad_token_id + 1 y saltan el padding
        pos = (np.cumsum(mask.astype(np.int64), axis=1) * mask.astype(np.int64)) + self.pad
        emb = W["roberta.embeddings.word_embeddings.weight"][input_ids]
        emb = emb + W["roberta.embeddings.position_embeddings.weight"][pos]
        emb = emb + W["roberta.embeddings.token_type_embeddings.weight"][0]
        x = layer_norm(emb, W["roberta.embeddings.LayerNorm.weight"],
                       W["roberta.embeddings.LayerNorm.bias"], eps)

        # Máscara aditiva para la atención
        add_mask = (1.0 - mask)[:, None, None, :] * -1e9

        # --- 12 capas ---
        for l in range(self.L):
            p = f"roberta.encoder.layer.{l}."
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
            x = layer_norm(ao + x, W[p + "attention.output.LayerNorm.weight"],
                           W[p + "attention.output.LayerNorm.bias"], eps)

            inter = gelu(x @ W[p + "intermediate.dense.weight"].T + W[p + "intermediate.dense.bias"])
            out = inter @ W[p + "output.dense.weight"].T + W[p + "output.dense.bias"]
            x = layer_norm(out + x, W[p + "output.LayerNorm.weight"],
                           W[p + "output.LayerNorm.bias"], eps)

        # --- Cabeza de clasificación (RobertaClassificationHead: toma el token <s>) ---
        cls = x[:, 0, :]
        h = np.tanh(cls @ W["classifier.dense.weight"].T + W["classifier.dense.bias"])
        logits = h @ W["classifier.out_proj.weight"].T + W["classifier.out_proj.bias"]
        return logits

    # ---------------------------------------------------------------- API
    def predecir(self, textos, max_length=128, batch=16, con_probs=False):
        logits_all = []
        for i in range(0, len(textos), batch):
            X, M = self.codificar(textos[i:i + batch], max_length)
            logits_all.append(self.forward(X, M))
        # Se rellena a ancho común antes de concatenar
        L = np.concatenate(logits_all, axis=0)
        if con_probs:
            return L.argmax(-1), softmax(L)
        return L.argmax(-1)


if __name__ == "__main__":
    import sys
    m = XLMRNumpy()
    pruebas = ["Buenos días a todos, qué bonito día",
               "Sos un pendejo de mierda",
               "Esos indios de mierda no deberían estar aquí",
               "Te voy a matar hijo de puta"]
    pred, probs = m.predecir(pruebas, con_probs=True)
    for t, p, pr in zip(pruebas, pred, probs):
        print(f"{CLASES[p]:<20} conf={pr[p]:.3f}  :: {t}")

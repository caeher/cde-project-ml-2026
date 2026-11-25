"""Inferencia XLM-R; importar este módulo no carga ni ejecuta modelos."""
from functools import lru_cache

if __package__:
    from .inferenciav2 import LABELS, cargar_modelo, predecir_toxicidad
else:
    from inferenciav2 import LABELS, cargar_modelo, predecir_toxicidad


@lru_cache(maxsize=1)
def _recursos():
    return cargar_modelo()


def predecir_local(texto):
    tokenizer, model, device = _recursos()
    clase, confianza, probs = predecir_toxicidad(texto, tokenizer, model, device)
    print(f'\nTexto: "{texto}"')
    print(f"Predicción Principal: {clase} (Confianza: {confianza:.2%})")
    print("Distribución de Probabilidades:")
    for nombre, probabilidad in zip(LABELS, probs):
        print(f"  - {nombre:<20}: {probabilidad.item():.2%}")
    return clase, confianza, probs


def main():
    for texto in (
        "Pásame el reporte cuando tengás tiempo, porfa.",
        "Ese mae es bien bayunco para manejar.",
        "Te voy a ir a buscar a tu casa para desbaratarte a golpes.",
    ):
        predecir_local(texto)


if __name__ == "__main__":
    main()

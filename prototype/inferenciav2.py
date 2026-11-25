from pathlib import Path
import sys
import torch

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))
from src.features.normalization import normalizar
from src.models.xlmr import CLASES, cargar_xlmr

# Mapeo oficial de etiquetas del proyecto
LABELS = CLASES


def cargar_modelo(ruta=None):
    """Usa pesos locales completos o la revisión publicada que utiliza la API."""
    tokenizer, model, device, _ = cargar_xlmr(ruta)
    print(f"Dispositivo activo: {device.type.upper()}")

    return tokenizer, model, device


def predecir_toxicidad(texto: str, tokenizer, model, device):
    """Recibe una frase y retorna la clase predicha, confianza y probabilidades."""
    inputs = tokenizer(
        normalizar(texto),
        return_tensors="pt",
        truncation=True,
        max_length=128,
        padding=True
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

    pred_idx = torch.argmax(probs).item()
    clase_predicha = LABELS[pred_idx]
    confianza = probs[pred_idx].item()
    return clase_predicha, confianza, probs


def ejecutar_ejemplos(tokenizer, model, device):
    ejemplos = [
        "Hola a todos, feliz inicio de semana",
        "Ese maje no sabe lo que esta haciendo",
        "Ese mae es bien bayunco para manejar",
        "Te voy a ir a buscar a la salida para romperte la cara",
    ]

    print("\n=== RESULTADOS DE INFERENCIA DE PRUEBA ===")
    for texto in ejemplos:
        clase, conf, _ = predecir_toxicidad(texto, tokenizer, model, device)
        print(f"\nTexto: '{texto}'")
        print(f"Predicción: {clase} (Confianza: {conf:.2%})")


def main():
    tokenizer, model, device = cargar_modelo()
    ejecutar_ejemplos(tokenizer, model, device)

    print("\n" + "="*45)
    print("           MODO INTERACTIVO EN VIVO")
    print("="*45)
    print("Escribe un texto para evaluar (o 'salir' para terminar):")

    while True:
        entrada = input("\nTexto > ")
        if entrada.lower().strip() in ["salir", "exit", "quit"]:
            print("Saliendo del modo interactivo.")
            break
        if not entrada.strip():
            continue

        clase, conf, probs = predecir_toxicidad(entrada, tokenizer, model, device)
        print(f"-> Clasificación: {clase} ({conf:.2%})")
        print("   Desglose de probabilidades:")
        for idx, label in enumerate(LABELS):
            print(f"   - {label:<20}: {probs[idx].item():.2%}")


if __name__ == "__main__":
    main()

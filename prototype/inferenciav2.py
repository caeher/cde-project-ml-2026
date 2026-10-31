from pathlib import Path
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

BASE_DIR = Path(__file__).resolve().parent

# Configuración de rutas (Prioriza el nuevo modelo unificado)
NUEVO_MODELO_PATH = BASE_DIR / "xlm_roberta_hate_speech_sv"
LEGACY_MODEL_PATH = BASE_DIR / "mi_modelo_xlmr"

# Mapeo oficial de etiquetas del proyecto
LABELS = [
    "No Tóxico",
    "Lenguaje Ofensivo",
    "Discurso de Odio",
    "Amenazas/Violencia",
]


def cargar_modelo():
    """Carga el modelo entrenado y el tokenizador desde las rutas disponibles."""
    # Buscar en orden de prioridad
    if NUEVO_MODELO_PATH.exists():
        model_dir = NUEVO_MODELO_PATH
    elif LEGACY_MODEL_PATH.exists():
        model_dir = LEGACY_MODEL_PATH
    else:
        raise FileNotFoundError(
            f"No se encontró ninguna carpeta de modelo válida.\n"
            f"Se buscó en:\n"
            f" - {NUEVO_MODELO_PATH}\n"
            f" - {LEGACY_MODEL_PATH}"
        )

    print(f"Cargando tokenizador y modelo desde: {model_dir}")
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    print(f"Dispositivo activo: {device.type.upper()}")

    return tokenizer, model, device


def predecir_toxicidad(texto: str, tokenizer, model, device):
    """Recibe una frase y retorna la clase predicha, confianza y probabilidades."""
    inputs = tokenizer(
        texto,
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
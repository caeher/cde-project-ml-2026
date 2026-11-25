import torch
import torch.nn.functional as F
from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification

# Asegúrate de que la carpeta local no tenga el punto al inicio
model_path = r"C:\Users\Dresler\Documents\La U\MachineLearn\version3\xlm_roberta_hate_speech_sv"

print("Cargando modelo y tokenizador localmente...")
tokenizer = XLMRobertaTokenizer.from_pretrained(model_path)
model = XLMRobertaForSequenceClassification.from_pretrained(model_path)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()
print(f"✓ Modelo cargado exitosamente en dispositivo: {device.upper()}")

# Función de prueba de fuego local
def predecir_local(texto):
    inputs = tokenizer(texto, return_tensors="pt", truncation=True, max_length=128, padding=True).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1).cpu().numpy()[0]
        pred_idx = probs.argmax()
        
    clases = ['No Tóxico', 'Lenguaje Ofensivo', 'Discurso de Odio', 'Amenazas/Violencia']
    
    print(f"\nTexto: \"{texto}\"")
    print(f"Predicción Principal: {clases[pred_idx]} (Confianza: {probs[pred_idx]*100:.2f}%)")
    print("Distribución de Probabilidades:")
    for cls, p in zip(clases, probs):
        print(f"  - {cls:<20}: {p*100:6.2f}%")

# Prueba de fuego local
predecir_local("Pásame el reporte cuando tengás tiempo, porfa.")
predecir_local("Ese mae es bien bayunco para manejar.")
predecir_local("Te voy a ir a buscar a tu casa para desbaratarte a golpes.")
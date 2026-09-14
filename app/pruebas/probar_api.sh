#!/usr/bin/env bash
# Batería de prueba manual del prototipo.
#   levantar:  python3 -m uvicorn app.api.main:app --port 8000
#   usar:      ./app/pruebas/probar_api.sh            (batería completa)
#              ./app/pruebas/probar_api.sh "un texto" (un caso suelto)
set -uo pipefail
API="${API:-http://localhost:8000}"

clasificar() {
  curl -s -X POST "$API/clasificar" -H 'Content-Type: application/json' \
    -d "$(python3 -c "import json,sys;print(json.dumps({'texto':sys.argv[1]}))" "$1")"
}

fila() {
  clasificar "$1" | python3 -c "
import json, sys
d = json.load(sys.stdin)
esperado = sys.argv[1] if len(sys.argv) > 1 else ''
marca = '' if not esperado else ('  ok' if d['clase'] == esperado else '  <-- ESPERADO: ' + esperado)
print(f\"  {d['texto_original'][:44]:46s} {d['clase']:19s} {d['confianza']:5.1%}{marca}\")" "${2:-}"
}

seccion() { printf '\n════ %s ════\n' "$1"; }

if [ $# -gt 0 ]; then
  clasificar "$1" | python3 -m json.tool
  exit 0
fi

curl -s "$API/salud" >/dev/null || { echo "La API no responde en $API"; exit 1; }

seccion "1. LAS CUATRO CLASES"
fila "Buenos días a todos, que tengan bonito día"        "No Tóxico"
fila "Qué pendejo es este tipo, no sabe nada"            "Lenguaje Ofensivo"
fila "Todos los venezolanos son basura, que se vayan"    "Discurso de Odio"
fila "Te voy a ir a buscar a tu casa para quebrarte"     "Amenazas/Violencia"

seccion "2. OFUSCACIÓN DE GROSERÍAS"
for v in "puta" "p*ta" "put@" "pu74" "p.u.t.a" "p u t a" "puuuta" "pvta"; do
  fila "Sos una $v barata" "Lenguaje Ofensivo"
done

seccion "3. AMENAZAS DEFORMADAS"
for v in "matar" "m4t4r" "m*tar" "m@tar" "ma7ar"; do
  fila "Te voy a $v" "Amenazas/Violencia"
done

seccion "4. EUFEMISMOS SALVADOREÑOS (sin palabra violenta)"
for t in "Te voy a dar piso" "Le van a dar cuello a ese" "Ya sabés lo que te puede pasar" \
         "A ese ya le tienen el cajón listo" "Le van a apagar la luz a ese maje" \
         "Ese ya está rayado" "Va a amanecer tieso ese"; do
  fila "$t" "Amenazas/Violencia"
done

seccion "5. EMOJIS"
fila "Te espero en la esquina 🔫"   "Amenazas/Violencia"
fila "Ya sabés lo que sigue 🔪"     "Amenazas/Violencia"
fila "No soporto a los judíos 🧼"   "Discurso de Odio"
fila "Qué alegre verte hermano ❤️"  "No Tóxico"
fila "Felicidades por el logro 🎉"  "No Tóxico"

seccion "6. PARES MÍNIMOS DE JERGA (misma palabra, dos contextos)"
fila "Ese cerote es mi mejor amigo desde la escuela" "No Tóxico"
fila "Callate ya, cerote asqueroso"                  "Lenguaje Ofensivo"
fila "Qué onda maje, todo bien por allá"             "No Tóxico"
fila "Ese maje no sabe ni hablar, qué imbécil"       "Lenguaje Ofensivo"
fila "Ese chucho es bien tranquilo"                  "No Tóxico"
fila "Está bien vergón el lugar, se los recomiendo"  "No Tóxico"

seccion "7. JERGA INOFENSIVA: AQUÍ ESTÁN LOS FALSOS POSITIVOS CONOCIDOS"
fila "No sea pajero, contá la verdad"    "No Tóxico"
fila "Ese bicho ya se durmió"            "No Tóxico"
fila "Prestame pisto para el bus"        "No Tóxico"
fila "Andá traeme el chunche ese"        "No Tóxico"
fila "Vamos a chambear temprano mañana"  "No Tóxico"

seccion "8. MENCIONAR UN PAÍS NO ES ODIO"
fila "Los mexicanos juegan muy bien al fútbol"     "No Tóxico"
fila "Tengo varios amigos nicaragüenses"           "No Tóxico"
fila "Que se vayan todos los nicaragüenses"        "Discurso de Odio"

seccion "9. INTENTOS DE EVASIÓN (el filtro del prototipo anterior caía aquí)"
for p in "gracias, " "qué onda, " "mi hermano, " "te quiero pero "; do
  fila "${p}te voy a matar" "Amenazas/Violencia"
done

seccion "10. LÍMITE CONOCIDO: IRONÍA Y SARCASMO"
echo "  (el modelo los lee en sentido literal; es la brecha medida de -0.30 de F1)"
fila "Qué bonito que nos traten así, muchas gracias"
fila "Ay sí, vos sos el más inteligente de todos"
fila "Qué maravilla de gobierno tenemos"

seccion "11. LOTE"
curl -s -X POST "$API/clasificar-lote" -H 'Content-Type: application/json' -d '{
  "textos":["Vamos por unas pupusas","Callate ya, baboso",
            "Esos indios no deberían estar aquí","Te espero afuera con el cuchillo"]}' \
| python3 -c "
import json, sys
for d in json.load(sys.stdin):
    print(f\"  {d['texto_original'][:36]:38s} {d['clase']:19s} riesgo={d['nivel_de_riesgo']}\")"

seccion "12. MANEJO DE ERRORES"
printf '  texto vacío       -> '
curl -s -X POST "$API/clasificar" -H 'Content-Type: application/json' \
     -d '{"texto":"   "}' -w '  (HTTP %{http_code})\n'
printf '  campo equivocado  -> HTTP '
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$API/clasificar" \
     -H 'Content-Type: application/json' -d '{"txt":"hola"}'
printf '  lote de 65        -> HTTP '
python3 -c "import json;print(json.dumps({'textos':['hola']*65}))" > /tmp/_b65.json
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$API/clasificar-lote" \
     -H 'Content-Type: application/json' -d @/tmp/_b65.json
rm -f /tmp/_b65.json
echo

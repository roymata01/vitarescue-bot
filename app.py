from flask import Flask, request
import os
import requests
import anthropic

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "vitarescue2024")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
INSTAGRAM_TOKEN = os.environ.get("INSTAGRAM_TOKEN", "")

CONTEXTO = """Eres el asistente virtual de VITA RESCUE CAPACITACION, empresa mexicana de cursos de primeros auxilios y productos de seguridad.

IDENTIDAD:
- Telefono: +52 221 360 0094
- Correo: contacto@vitarescue.com.mx
- Sitio web: https://www.vitarescue.com.mx
- Tienda: https://www.vitarescue.com.mx/shop

TONO: Profesional, humano y cercano. Responde siempre en espanol. Usa frases como "Con gusto te ayudo", "Te explico".

NO DEBES: ofrecer ambulancias, dar diagnosticos medicos, prometer inventario. Si alguien esta en peligro, dile que llame al 911.

CURSOS:
- Primeros auxilios basicos en adultos - 5 horas
- Primeros auxilios en ninos y bebes - 5 horas
- Control de Hemorragias Stop The Bleed - 3 horas
- RCP - 3 horas
- RCP y DEA - 3 horas
- Primeros auxilios a motociclistas - 5 horas
- Primeros auxilios en lugares remotos - 8 horas
- Rescate acuatico - 4 horas
- Programa para colegios (primaria, secundaria, bachillerato, docentes)

MODALIDADES: Presencial (max 24 personas), En linea Zoom (max 50), E-learning VITAlearning, Colegios (max 35 alumnos).

ENTREGABLES: Constancia (1 ano vigencia), DC-3 para empresas, Constancia STOP THE BLEED internacional, Manuales, Reporte del curso.

PRODUCTOS (IVA incluido):
- Botiquin VITA Equipado: $1,799 MXN (personalizado +$200)
- Dispositivo antiatragantamiento: $580 MXN
- Mascarilla RCP Pocket: $200 MXN
- Torniquete CAT: $250 MXN
- Paquete 5 torniquetes CAT: $1,100 MXN
- Paquete 4 mascarillas RCP: $690 MXN
Precios de referencia, confirmar disponibilidad con asesor.

BOTIQUIN VITA EQUIPADO: Incluye mas de 40 articulos para emergencias cotidianas y guia interactiva con codigos QR a mas de 25 videos instructivos. Entrega 4-5 dias, personalizado 5 dias adicionales.

RECOMENDACIONES POR PERFIL:
- Familia: Botiquin + Primeros auxilios basicos
- Padres con bebes: Curso ninos y bebes + Botiquin + Dispositivo antiatragantamiento
- Empresa: Curso privado + DC-3 + botiquines por area + RCP + Control hemorragias
- Colegio: Programa Colegios VITA RESCUE + botiquines + capacitacion docente
- Gimnasio/deporte: RCP y DEA + Primeros auxilios + Botiquin + Torniquete CAT
- Motociclistas: Curso motociclistas + Control hemorragias + Botiquin

DATOS A RECOLECTAR para cotizaciones de cursos: nombre, empresa, telefono, correo, ciudad, curso de interes, numero de participantes, modalidad, fecha tentativa, si requiere DC-3 o factura.

Cuando tengas los datos, cierra con: "Un asesor de VITA RESCUE te contactara para confirmar disponibilidad y cotizacion."
"""

FILTRO = """Analiza este mensaje y decide si esta relacionado con VITA RESCUE (cursos de primeros auxilios, botiquines, RCP, hemorragias, capacitacion, productos de seguridad, precios, cotizaciones, informacion del negocio).

Responde UNICAMENTE con una sola palabra:
- SI: si el mensaje es sobre cursos, productos, precios, primeros auxilios, capacitacion, o interes en los servicios de VITA RESCUE
- NO: si es un saludo sin contexto, mensaje personal, tema no relacionado, spam, o cualquier otra cosa

Mensaje: """

def es_relevante(mensaje):
    cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    respuesta = cliente.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=5,
        messages=[{"role": "user", "content": FILTRO + mensaje}]
    )
    resultado = respuesta.content[0].text.strip().upper()
    print(f"Filtro para '{mensaje}': {resultado}")
    return resultado == "SI"

def preguntar_claude(mensaje):
    cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    respuesta = cliente.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=CONTEXTO,
        messages=[{"role": "user", "content": mensaje}]
    )
    return respuesta.content[0].text

def enviar_whatsapp(numero, texto):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": numero, "type": "text", "text": {"body": texto}}
    requests.post(url, headers=headers, json=data)

def enviar_instagram(recipient_id, texto):
    url = "https://graph.facebook.com/v18.0/me/messages"
    headers = {"Authorization": f"Bearer {INSTAGRAM_TOKEN}", "Content-Type": "application/json"}
    data = {"recipient": {"id": recipient_id}, "message": {"text": texto}}
    requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token invalido", 403

@app.route("/webhook", methods=["POST"])
def recibir_mensaje():
    data = request.get_json()
    try:
        entry = data["entry"][0]
        # Instagram
        if "messaging" in entry:
            mensaje = entry["messaging"][0]
            sender_id = mensaje["sender"]["id"]
            texto = mensaje["message"]["text"]
            print(f"Instagram de {sender_id}: {texto}")
            if es_relevante(texto):
                respuesta = preguntar_claude(texto)
                enviar_instagram(sender_id, respuesta)
        # WhatsApp
        elif "changes" in entry:
            cambio = entry["changes"][0]["value"]
            if "messages" in cambio:
                mensaje = cambio["messages"][0]
                numero = mensaje["from"]
                texto = mensaje["text"]["body"]
                print(f"WhatsApp de {numero}: {texto}")
                if es_relevante(texto):
                    respuesta = preguntar_claude(texto)
                    enviar_whatsapp(numero, respuesta)
    except Exception as e:
        print("Error:", e)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

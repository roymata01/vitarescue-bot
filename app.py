from flask import Flask, request
import os
import requests
import anthropic

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "vitarescue2024")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CONTEXTO = """Eres el asistente virtual de VITA RESCUE CAPACITACIÓN, empresa mexicana de cursos de primeros auxilios.
Tu trabajo es responder preguntas sobre los cursos, dar información, cotizar para empresas o escuelas, y mandar links de compra o registro.
Responde siempre en español, de forma amable y profesional.
Si no tienes información específica sobre algo, di que un asesor les contactará pronto."""

def preguntar_claude(mensaje):
    cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    respuesta = cliente.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=CONTEXTO,
        messages=[{"role": "user", "content": mensaje}]
    )
    return respuesta.content[0].text

def enviar_mensaje(numero, texto):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": numero, "type": "text", "text": {"body": texto}}
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
        mensaje = data["entry"][0]["changes"][0]["value"]["messages"][0]
        numero = mensaje["from"]
        texto = mensaje["text"]["body"]
        print(f"Mensaje de {numero}: {texto}")
        respuesta = preguntar_claude(texto)
        enviar_mensaje(numero, respuesta)
    except Exception as e:
        print("Error:", e)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

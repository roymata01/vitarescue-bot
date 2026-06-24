from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "vitarescue2024"

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
    print("Mensaje recibido:", data)
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)

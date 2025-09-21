from flask import Flask, jsonify, request, abort

app = Flask(__name__)

@app.get("/ping")
def health(): return jsonify({"status":"ok"}), 200

@app.get("/historial/<cliente_id>")
def get_historial(cliente_id):
    # Defensa en profundidad: debe venir del autorizador
    if request.headers.get("X-Auth-Validated","").lower() != "true":
        return jsonify({"error":"auth_not_validated"}), 403

    user_id = request.headers.get("X-User-Id","unknown")
    # Demo de payload protegido
    data = {
        "clienteId": cliente_id,
        "resumen": "Historial clínico simulado",
        "visiblePara": user_id
    }
    return jsonify(data), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","8080")))

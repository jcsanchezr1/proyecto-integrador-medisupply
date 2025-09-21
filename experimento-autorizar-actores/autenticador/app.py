from flask import Flask, request, jsonify, Response
import os, time, base64, json, logging
import jwt  # PyJWT
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# ===== Config común =====
JWT_ISS = os.getenv("JWT_ISS", "https://auth.local")
JWT_AUD = os.getenv("JWT_AUD", "medisupply")
JWT_KID = os.getenv("JWT_KID", "dev-kid-1")

# ===== Config Keycloak (fachada) =====
KEYCLOAK_TOKEN_URL = os.getenv("KEYCLOAK_TOKEN_URL", "").strip()
CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "").strip()
DEFAULT_SCOPE = os.getenv("DEFAULT_SCOPE", "openid profile email").strip()

USING_KEYCLOAK = bool(KEYCLOAK_TOKEN_URL)
TIMEOUT = (5, 10)  # (connect, read) seconds

# ===== Usuarios demo (solo modo local) =====
USERS = {
    "gerente@demo.com": {
        "password": "demo123",  # plaintext solo para demo
        "id": "u-1001",
        "role": "GerenteCuenta",
        "permissions": ["historial.read"]
    },
    "vendedor@demo.com": {
        "password": "demo123",
        "id": "u-2001",
        "role": "Vendedor",
        "permissions": []
    }
}

# ===== Llaves RSA (solo modo local) =====
def b64d(s): return base64.b64decode(s) if s else None

private_pem_b64 = os.getenv("JWT_PRIVATE_PEM_B64", "")
public_pem_b64  = os.getenv("JWT_PUBLIC_PEM_B64", "")

if not USING_KEYCLOAK:
    if private_pem_b64 and public_pem_b64:
        PRIVATE_PEM = b64d(private_pem_b64)
        PUBLIC_PEM  = b64d(public_pem_b64)
    else:
        if os.path.exists("keys/private.pem") and os.path.exists("keys/public.pem"):
            with open("keys/private.pem","rb") as f: PRIVATE_PEM = f.read()
            with open("keys/public.pem","rb") as f: PUBLIC_PEM  = f.read()
        else:
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            PRIVATE_PEM = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            PUBLIC_PEM = key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            app.logger.warning("Llaves RSA efímeras generadas (solo DEV).")

    def to_b64u(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

    def jwks_from_public_pem(pub_pem: bytes, kid: str):
        pub = serialization.load_pem_public_key(pub_pem)
        numbers = pub.public_numbers()
        n = numbers.n.to_bytes((numbers.n.bit_length()+7)//8, "big")
        e = numbers.e.to_bytes((numbers.e.bit_length()+7)//8, "big")
        return {"keys":[{"kty":"RSA","kid":kid,"use":"sig","alg":"RS256","n":to_b64u(n),"e":to_b64u(e)}]}

    JWKS = jwks_from_public_pem(PUBLIC_PEM, JWT_KID)

# ===== Helpers =====
def json_or_form(req):
    # Acepta JSON {username,password} o {email,password} y x-www-form-urlencoded
    data = {}
    if req.is_json:
        data = req.get_json(silent=True) or {}
    else:
        # form-encoded
        for k in req.form:
            data[k] = req.form.get(k)
        if not data:
            # intenta leer raw
            try:
                data = json.loads(req.data.decode("utf-8"))
            except Exception:
                data = {}
    # normaliza campos
    username = (data.get("username") or data.get("email") or "").strip().lower()
    password = (data.get("password") or data.get("pwd") or "").strip()
    scope    = data.get("scope") or DEFAULT_SCOPE
    return username, password, scope

def local_issue_token(email):
    user = USERS.get(email)
    if not user:
        return None, ("invalid_credentials", 401)
    now = int(time.time())
    payload = {
        "iss": JWT_ISS, "aud": JWT_AUD, "iat": now, "exp": now + 3600,
        "sub": user["id"], "role": user["role"], "permissions": user["permissions"]
    }
    token = jwt.encode(payload, PRIVATE_PEM, algorithm="RS256", headers={"kid": JWT_KID})
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600
    }, None

# ===== Rutas =====

@app.get("/ping")
def health():
    mode = "keycloak" if USING_KEYCLOAK else "local"
    return jsonify({"status":"ok","mode":mode}), 200

# JWKS solo tiene sentido en modo local
if not USING_KEYCLOAK:
    @app.get("/auth/jwks.json")
    def jwks():
        return jsonify(JWKS), 200

# --- Login local legado (DEV) ---
@app.post("/auth/login")
def login_local():
    if USING_KEYCLOAK:
        return jsonify({"error":"disabled_in_keycloak_mode"}), 400
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").lower().strip()
    pwd   = data.get("password","")
    user  = USERS.get(email)
    if not user or user["password"] != pwd:
        return jsonify({"error":"invalid_credentials"}), 401
    resp, err = local_issue_token(email)
    return (jsonify(resp), 200) if not err else (jsonify({"error": err[0]}), err[1])

# --- Fachada Keycloak Password Grant ---
def kc_token_request(grant_type, **kwargs):
    form = {
        "grant_type": grant_type,
        "client_id": CLIENT_ID
    }
    if CLIENT_SECRET:
        form["client_secret"] = CLIENT_SECRET
    if grant_type == "password":
        form["username"] = kwargs["username"]
        form["password"] = kwargs["password"]
        if kwargs.get("scope"):
            form["scope"] = kwargs["scope"]
    elif grant_type == "refresh_token":
        form["refresh_token"] = kwargs["refresh_token"]
    else:
        raise ValueError("grant_type no soportado")

    app.logger.info(f"Proxying to KC {KEYCLOAK_TOKEN_URL} grant={grant_type}")
    print("Proxying to KC:", KEYCLOAK_TOKEN_URL)
    r = requests.post(KEYCLOAK_TOKEN_URL, data=form, timeout=TIMEOUT)
    print("KC response status:", r.status_code)
    print("KC response body:", r.text)
    print("KC response headers:", r.headers)
    return Response(r.content, status=r.status_code, content_type=r.headers.get("Content-Type","application/json"))

# Atajos: soporta /token y /auth/token
@app.post("/token")
@app.post("/auth/token")
def token_password():
    if USING_KEYCLOAK:
        username, password, scope = json_or_form(request)
        if not username or not password:
            return jsonify({"error":"invalid_request","detail":"username/password requeridos"}), 400
        return kc_token_request("password", username=username, password=password, scope=scope)
    # modo local: acepta también /token como alias y emite token local
    username, password, _ = json_or_form(request)
    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error":"invalid_credentials"}), 401
    resp, err = local_issue_token(username)
    return (jsonify(resp), 200) if not err else (jsonify({"error": err[0]}), err[1])

# Refresh (opcional)
@app.post("/auth/refresh")
def token_refresh():
    if not USING_KEYCLOAK:
        return jsonify({"error":"unsupported_in_local_mode"}), 400
    _, _, _ = json_or_form(request)
    rt = (request.form.get("refresh_token")
          or (request.get_json(silent=True) or {}).get("refresh_token")
          or "")
    if not rt:
        return jsonify({"error":"invalid_request","detail":"refresh_token requerido"}), 400
    return kc_token_request("refresh_token", refresh_token=rt)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","8080")))

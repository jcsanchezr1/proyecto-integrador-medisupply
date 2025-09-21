# server.py
# Autorizador MediSupply
# - Valida JWT de Keycloak (issuer/audience/firma RS256 via JWKS)
# - Extrae permisos/roles y autoriza el acceso
# - Reenvía al micro de historial agregando cabeceras X-Auth-Validated y X-User-Id
# - (Opcional) Firma llamada saliente a Cloud Run privado con ID token de GCP
# Reqs: flask, pyjwt[crypto], requests, python-dotenv
# Opcional (si UPSTREAM_AUTH=gcp): google-auth

import os
import logging
import requests
from flask import Flask, request, jsonify, Response

import jwt
from jwt import PyJWKClient
from jwt.exceptions import (
    InvalidSignatureError, ExpiredSignatureError,
    InvalidAudienceError, InvalidIssuerError, PyJWKClientError,
)

# ------- (Opcional) Google Auth para llamar Cloud Run privado -------
google_auth_available = False
try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
    google_auth_available = True
except Exception:
    google_auth_available = False

# ---------------------- Configuración / Entorno ----------------------
from dotenv import load_dotenv
load_dotenv(".env.local")  # en local/dev

REALM_ISS       = os.getenv("JWT_ISS", "https://keycloak-czl6jx3zfa-uc.a.run.app/realms/medisupply")
JWKS_URL        = os.getenv("JWKS_URL", f"{REALM_ISS}/protocol/openid-connect/certs")
CLIENT_AUD      = os.getenv("JWT_AUD", "medisupply-client")

HISTORIAL_BASE  = os.getenv("HISTORIAL_BASE", "https://historial-service-159067324714.us-central1.run.app")
HTTP_TIMEOUT    = int(os.getenv("HTTP_TIMEOUT", "10"))
CLOCK_SKEW      = int(os.getenv("CLOCK_SKEW", "10"))  # tolerancia reloj (segundos)
REQUIRED_PERMISSION = os.getenv("REQUIRED_PERMISSION", "historial.read")

# Llamada a upstream (historial) con ID token de GCP (Cloud Run privado)
# UPSTREAM_AUTH = 'none' (por defecto) o 'gcp'
UPSTREAM_AUTH   = os.getenv("UPSTREAM_AUTH", "none").lower()
TARGET_AUDIENCE = os.getenv("TARGET_AUDIENCE", HISTORIAL_BASE)  # para ID token

# -------------------------- Logging ---------------------------------
log = logging.getLogger("authz")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(message)s")

# ---------------------- JWKS (cacheado por PyJWKClient) -------------
if not JWKS_URL:
    raise RuntimeError("JWKS_URL no configurado")
jwk_client = PyJWKClient(JWKS_URL, cache_keys=True)

# --------------------------- App Flask -------------------------------
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# --------------------------- Utilidades ------------------------------
def _bearer_token(req) -> str | None:
    """
    Si API Gateway/ESPv2 autenticó el backend con su propio ID token,
    mueve el Authorization original del cliente a X-Forwarded-Authorization.
    """
    xf = req.headers.get("X-Forwarded-Authorization", "")
    if xf.lower().startswith("bearer "):
        return xf[7:].strip()
    h = req.headers.get("Authorization", "")
    if h.lower().startswith("bearer "):
        return h[7:].strip()
    return None


def _jwks_kids_now():
    try:
        r = requests.get(JWKS_URL, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        return [k.get("kid") for k in (r.json() or {}).get("keys", [])]
    except Exception as e:
        log.warning(f"[authz] Error leyendo JWKS_URL={JWKS_URL}: {e}")
        return []


def _extract_roles_and_perms(claims: dict) -> set[str]:
    eff = set()
    # Keycloak realm roles
    for r in (claims.get("realm_access", {}) or {}).get("roles", []) or []:
        eff.add(str(r).strip())
    # Keycloak client roles
    for _, obj in (claims.get("resource_access", {}) or {}).items():
        for r in obj.get("roles", []) or []:
            eff.add(str(r).strip())
    # Atajos y otros esquemas
    if "role" in claims:
        eff.add(str(claims["role"]).strip())
    for p in claims.get("permissions", []) or []:
        eff.add(str(p).strip())
    return {x.lower() for x in eff}


def _pick_user_id(claims: dict) -> str:
    for k in ("sub", "preferred_username", "email", "client_id", "clientId"):
        v = claims.get(k)
        if v:
            return str(v)
    return "unknown"


def _get_gcp_id_token(audience: str) -> str | None:
    """
    Genera un ID token para invocar Cloud Run privado.
    Requiere google-auth y credenciales del SA (en Cloud Run viene por defecto).
    """
    if not google_auth_available:
        log.error("[authz] google-auth no está disponible pero UPSTREAM_AUTH=gcp")
        return None
    try:
        req = google_requests.Request()
        token = google_id_token.fetch_id_token(req, audience)
        return token
    except Exception as e:
        log.error(f"[authz] No se pudo obtener ID token para audience={audience}: {e}")
        return None


# --------------------------- Autorización ----------------------------
def _authorize(token: str):
    # 1) Header sin verificar
    try:
        header = jwt.get_unverified_header(token)
    except Exception as e:
        log.error(f"[authz] Token malformado: {e}")
        return None, 401, {"detail": f"malformed token: {e}"}

    kid = header.get("kid"); alg = header.get("alg")
    log.debug(f"[authz] Header -> kid={kid} alg={alg}")

    # 2) Cuerpo sin verificar (para log de iss/aud)
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        log.debug(f"[authz] Unverified iss={unverified.get('iss')} aud={unverified.get('aud')}")
    except Exception as e:
        log.debug(f"[authz] No se pudo leer payload no-verificado: {e}")

    # 3) Clave de firma (con intento de refresh)
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
    except PyJWKClientError:
        log.warning(f"[authz] KID {kid} no encontrado en cache. Refrescando JWKS...")
        _ = _jwks_kids_now()
        try:
            signing_key = jwk_client.get_signing_key_from_jwt(token)
        except PyJWKClientError as e2:
            msg = f"Unable to find signing key kid={kid} in JWKS."
            log.error(f"[authz] {msg} err={e2}")
            return None, 401, {"detail": msg, "error": "unauthorized"}

    log.debug(f"[authz] Using signing key kid={getattr(signing_key,'key_id',None)}")

    # 4) Verificación firma + issuer + audience
    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=CLIENT_AUD,    # PyJWT acepta lista o string en claim aud
            issuer=REALM_ISS,
            options={
                "require": ["exp", "iat"],
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
            },
            leeway=CLOCK_SKEW,
        )
        log.info(f"[authz] JWT OK sub={claims.get('sub')}")
    except ExpiredSignatureError:
        return None, 401, {"detail": "token expired", "error": "unauthorized"}
    except InvalidAudienceError:
        return None, 401, {"detail": f"rol invalido, need '{REQUIRED_PERMISSION}'", "error": "unauthorized"}
    except InvalidIssuerError:
        return None, 401, {"detail": f"issuer invalido, need '{REALM_ISS}'", "error": "unauthorized"}
    except InvalidSignatureError:
        return None, 401, {"detail": "firma invalida", "error": "unauthorized"}
    except Exception as e:
        return None, 401, {"detail": f"jwt decode error: {e}", "error": "unauthorized"}

    effective = _extract_roles_and_perms(claims)
    log.info(f"[authz] effective={sorted(effective)}")

    if REQUIRED_PERMISSION.lower() in effective or "gerentecuenta" in effective:
        return claims, 200, None

    return None, 403, {
        "detail": "forbidden: missing permission/role",
        "required": [REQUIRED_PERMISSION, "GerenteCuenta"]
    }


# ---------------------------- Endpoints ------------------------------
@app.get("/ping")
def ping():
    return jsonify(ok=True, iss=REALM_ISS, jwks=JWKS_URL, aud=CLIENT_AUD), 200


@app.get("/_debug/jwks")
def dbg_jwks():
    return jsonify(kids=_jwks_kids_now()), 200


@app.post("/_debug/decode")
def dbg_decode():
    token = _bearer_token(request) or (request.json or {}).get("token")
    if not token:
        return jsonify(error="missing token"), 400
    try:
        header = jwt.get_unverified_header(token)
        payload = jwt.decode(token, options={"verify_signature": False})
        return jsonify(header=header, payload=payload), 200
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.get("/historial/<cliente_id>")
def get_historial(cliente_id):
    # 1) Token del cliente (Keycloak)
    token = _bearer_token(request)
    if not token:
        return jsonify(detail="missing bearer token"), 401

    # 2) Autorizar
    claims, code, err = _authorize(token)
    if code != 200:
        return jsonify(err), code

    # 3) Headers requeridos por el micro de historial
    fwd_headers = {
        "X-Auth-Validated": "true",
        "X-User-Id": _pick_user_id(claims),
        # Trazabilidad opcional:
        "X-Auth-Iss": str(claims.get("iss", "")),
        "X-Auth-Subject": str(claims.get("sub", "")),
    }

    # 4) (Opcional) Cloud Run privado: adjuntar ID token de GCP
    if UPSTREAM_AUTH == "gcp":
        idt = _get_gcp_id_token(TARGET_AUDIENCE)
        if not idt:
            return jsonify(error="upstream_auth", detail="missing id_token for Cloud Run"), 502
        fwd_headers["Authorization"] = f"Bearer {idt}"

    # 5) Llamada a upstream (no reenviamos Authorization del cliente)
    try:
        url = f"{HISTORIAL_BASE}/historial/{cliente_id}"
        r = requests.get(url, headers=fwd_headers, timeout=HTTP_TIMEOUT)
        return Response(
            r.content,
            status=r.status_code,
            headers={"Content-Type": r.headers.get("Content-Type", "application/json")}
        )
    except Exception as e:
        log.exception("[authz] Error llamando a historial")
        return jsonify(error="upstream_error", detail=str(e)), 502


# -------------------------- Main (local) -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)

import os
import json
import hashlib
import logging
import requests
import functions_framework

# ===== Config =====
INVENTORY_BASE_URL = os.getenv(
    "INVENTORY_BASE_URL",
    "https://inventory-service-159067324714.us-central1.run.app"
).rstrip("/")
FORWARD_PATH    = os.getenv("FORWARD_PATH", "/inventory/products")
CHECKSUM_HEADER = os.getenv("CHECKSUM_HEADER", "X-Message-Integrity")
CHECKSUM_ALGO   = os.getenv("CHECKSUM_ALGO", "sha256").lower()
HTTP_TIMEOUT    = float(os.getenv("HTTP_TIMEOUT_SEC", "10"))

HOP_BY_HOP = {
    "connection","keep-alive","proxy-authenticate","proxy-authorization",
    "te","trailers","transfer-encoding","upgrade"
}
STRIP_HEADERS = {
    "host",
    "content-length", "accept-encoding",    
    "x-cloud-trace-context", "traceparent", "forwarded", "function-execution-id",
}

def _cors_headers() -> dict:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, X-Message-Integrity, X-Correlation-Id",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Max-Age": "3600",
    }

def _canonical_json_bytes(raw_body: bytes, content_type: str) -> bytes:
    """Si es JSON, serializa de forma canónica (keys ordenadas, sin espacios)."""
    if "application/json" in (content_type or "").lower():
        try:
            data = json.loads(raw_body.decode("utf-8"))
            canon = json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
            return canon.encode("utf-8")
        except Exception:
            return raw_body
    return raw_body

def _compute_checksum(raw: bytes) -> str:
    if CHECKSUM_ALGO != "sha256":
        raise ValueError("Unsupported algorithm; only sha256 is supported.")
    h = hashlib.sha256()
    h.update(raw)
    return h.hexdigest()

def _expected_from_header(v: str) -> str:
    # Acepta "sha256=<hex>" o "<hex>"
    return (v or "").split("=", 1)[-1].strip()

def _forward_headers(req, skip_header: str) -> dict:
    """Copia headers útiles, elimina hop-by-hop + problemáticos + header de integridad."""
    out = {}
    for k, v in req.headers.items():
        kl = k.lower()
        if kl in HOP_BY_HOP or kl in STRIP_HEADERS:
            continue
        if kl == skip_header.lower():
            continue
        out[k] = v
    
    out["X-Integrity-Validated"] = "true"
    
    out["Content-Type"] = "application/json"
    
    if req.headers.get("X-Correlation-Id"):
        out["X-Correlation-Id"] = req.headers["X-Correlation-Id"]
    return out

@functions_framework.http
def validador_mediador(request):
    
    if request.method == "OPTIONS":
        return ("", 204, _cors_headers())

    cors = {"Access-Control-Allow-Origin": "*"}

    # 1) Header de integridad
    header_val = request.headers.get(CHECKSUM_HEADER, "")
    if not header_val:
        body = {"error": f"Missing {CHECKSUM_HEADER}"}
        return (json.dumps(body), 400, {"Content-Type": "application/json", **cors})

    expected = _expected_from_header(header_val)

    # 2) Checksum del body canónico
    raw_body = request.get_data(cache=False, as_text=False)
    content_type = request.headers.get("Content-Type", "")
    actual = _compute_checksum(_canonical_json_bytes(raw_body, content_type))

    if actual != expected:
        body = {"error": "Integrity check failed", "expected": expected, "actual": actual}
        return (json.dumps(body), 400, {"Content-Type": "application/json", **cors})

    # 3) Reenviar al servicio de inventario
    if not INVENTORY_BASE_URL:
        body = {"status": "ok", "note": "Validated only (no proxy). Set INVENTORY_BASE_URL."}
        return (json.dumps(body), 200, {"Content-Type": "application/json", **cors})

    url = INVENTORY_BASE_URL + FORWARD_PATH
    headers = _forward_headers(request, CHECKSUM_HEADER)

    try:
        print(f"Forwarding to {url} with headers {headers} and body {raw_body!r}")
        resp = requests.post(url, data=raw_body, headers=headers, timeout=HTTP_TIMEOUT)
      
        out_headers = {"Content-Type": resp.headers.get("Content-Type", "application/json"), **cors}
        if "Location" in resp.headers:
            out_headers["Location"] = resp.headers["Location"]
        return (resp.content, resp.status_code, out_headers)

    except requests.RequestException as e:
        logging.exception("Proxy error")
        body = {"error": "Upstream error", "detail": str(e)}
        return (json.dumps(body), 502, {"Content-Type": "application/json", **cors})

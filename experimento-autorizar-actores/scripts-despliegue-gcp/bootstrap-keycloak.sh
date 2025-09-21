#!/usr/bin/env bash
set -euo pipefail

# ===== Inputs requeridos =====
: "${KEYCLOAK_URL=https://keycloak-czl6jx3zfa-uc.a.run.app}"
: "${KEYCLOAK_ADMIN:=admin}"
: "${KEYCLOAK_ADMIN_PASSWORD:=admin}"
: "${KC_REALM:=medisupply}"
: "${JWT_AUD:=medisupply-client}"

IMG="quay.io/keycloak/keycloak:23.0"
CONF_VOL="kcadm-conf"   # ~/.keycloak del usuario 'keycloak' (HOME=/opt/keycloak)

# ---- Git Bash en Windows: desactiva conversión de rutas para docker ----
DOCKER_ENV_PREFIX=()
if [[ "${MSYSTEM:-}" == MINGW* || "${OSTYPE:-}" == msys || "${OSTYPE:-}" == cygwin ]]; then
  DOCKER_ENV_PREFIX=(env MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*')
fi

# Crea volumen si no existe (para persistir la sesión/config del kcadm)
docker volume inspect "${CONF_VOL}" >/dev/null 2>&1 || docker volume create "${CONF_VOL}" >/dev/null

# Helper: ejecutar kcadm con entrypoint y volumen correctos
run_kc() {
  "${DOCKER_ENV_PREFIX[@]}" docker run --rm \
    --entrypoint /opt/keycloak/bin/kcadm.sh \
    -v "${CONF_VOL}:/opt/keycloak/.keycloak" \
    "${IMG}" "$@"
}

echo "→ Login kcadm contra ${KEYCLOAK_URL}"
# OJO: --server va con 'config credentials'
run_kc config credentials \
  --server "${KEYCLOAK_URL}" \
  --realm master \
  --user "${KEYCLOAK_ADMIN}" \
  --password "${KEYCLOAK_ADMIN_PASSWORD}"

echo "→ Crear realm ${KC_REALM} (idempotente)"
run_kc create realms -s realm="${KC_REALM}" -s enabled=true || true

echo "→ Crear client ${JWT_AUD} (public + direct access) (idempotente)"
run_kc create clients -r "${KC_REALM}" \
  -s clientId="${JWT_AUD}" \
  -s protocol=openid-connect \
  -s publicClient=true \
  -s directAccessGrantsEnabled=true \
  -s 'redirectUris=["*"]' \
  -s 'webOrigins=["*"]' || true

# Obtener ID interno del client
CID="$(run_kc get clients -r "${KC_REALM}" -q clientId="${JWT_AUD}" --fields id --format csv --noquotes | tail -n1)"

echo "→ Asegurar mapper 'audience' para incluir ${JWT_AUD}"
run_kc create "clients/${CID}/protocol-mappers/models" -r "${KC_REALM}" \
  -s name="aud-${JWT_AUD}" \
  -s protocol=openid-connect \
  -s protocolMapper=oidc-audience-mapper \
  -s 'config."included.client.audience"='"${JWT_AUD}" \
  -s 'config."id.token.claim"=true' \
  -s 'config."access.token.claim"=true' || true

echo "→ Crear roles (idempotente)"
run_kc create roles -r "${KC_REALM}" -s name=GerenteCuenta  || true
run_kc create roles -r "${KC_REALM}" -s name=historial.read || true
run_kc create roles -r "${KC_REALM}" -s name=Vendedor       || true

echo "→ Usuario gerente@demo.com"
run_kc create users -r "${KC_REALM}" \
  -s username="gerente@demo.com" -s email="gerente@demo.com" -s enabled=true || true
run_kc set-password -r "${KC_REALM}" --username "gerente@demo.com" --new-password "demo123" --temporary=false
run_kc add-roles -r "${KC_REALM}" --uusername "gerente@demo.com" --rolename GerenteCuenta
run_kc add-roles -r "${KC_REALM}" --uusername "gerente@demo.com" --rolename historial.read

echo "→ Usuario vendedor@demo.com"
run_kc create users -r "${KC_REALM}" \
  -s username="vendedor@demo.com" -s email="vendedor@demo.com" -s enabled=true || true
run_kc set-password -r "${KC_REALM}" --username "vendedor@demo.com" --new-password "demo123" --temporary=false
run_kc add-roles -r "${KC_REALM}" --uusername "vendedor@demo.com" --rolename Vendedor

echo
echo "✅ Bootstrap listo en ${KEYCLOAK_URL}"
echo "   Realm: ${KC_REALM}"
echo "   Client (aud): ${JWT_AUD}"
echo "   Usuarios: gerente@demo.com / demo123 | vendedor@demo.com / demo123"
echo
echo "→ Variables para el autorizador:"
echo "   JWT_ISS=${KEYCLOAK_URL}/realms/${KC_REALM}"
echo "   JWKS_URL=${KEYCLOAK_URL}/realms/${KC_REALM}/protocol/openid-connect/certs"
echo "   JWT_AUD=${JWT_AUD}"

"""
Validation controller for cf-validador component.
Handles validation and proxy logic.
"""
import os
import logging
import requests
from typing import Dict, Any, Tuple
from flask import request, make_response

from models.validation_model import ValidationModel


class ValidationController:
    """Controller for handling validation and proxy operations."""
    
    def __init__(self):
        self.validation_model = ValidationModel()
        self.inventory_base_url = os.getenv("INVENTORY_BASE_URL", "").rstrip("/")
        self.checksum_header = os.getenv("CHECKSUM_HEADER", "X-Message-Integrity")
        self.forward_path = os.getenv("FORWARD_PATH", "/inventory/products")
    
    def validate_and_proxy(self) -> Tuple[Dict[str, Any], int]:
        """
        Validate request integrity and optionally proxy to inventory service.
        
        Returns:
            Tuple of (response_data, status_code)
        """
        # Verifica que el header de integridad este presente
        header_value = request.headers.get(self.checksum_header, "")
        if not header_value:
            logging.warning("Missing integrity header: %s", self.checksum_header)
            return {"error": f"Missing {self.checksum_header}"}, 400
        
        # Extrae el checksum esperado
        expected_checksum = header_value.split("=", 1)[-1]  # supports "sha256=<hex>" or "<hex>"
        
        # Obtiene el raw body
        raw_body = request.get_data(cache=False, as_text=False)
        content_type = request.headers.get("Content-Type", "")
        
        # Valida la integridad
        is_valid, actual_checksum, error_message = self.validation_model.validate_integrity(
            raw_body, content_type, expected_checksum
        )
        
        if not is_valid:
            return {
                "error": error_message,
                "expected": expected_checksum,
                "actual": actual_checksum
            }, 400
        
        # Si no hay URL de inventario configurada, retorna solo la validación de éxito
        if not self.inventory_base_url:
            logging.error("INVENTORY_BASE_URL not configured")
            return {
                "status": "ok",
                "note": "Validated only (no proxy). Set INVENTORY_BASE_URL to enable forwarding."
            }, 200
        
        # Proxy (envia la petición a través del proxy al servicio de inventario)
        return self._proxy_to_inventory(raw_body)
    
    def _proxy_to_inventory(self, raw_body: bytes) -> Tuple[Dict[str, Any], int]:
        """
        Proxy validated request to inventory service.
        
        Args:
            raw_body: Raw request body to forward
            
        Returns:
            Tuple of (response_data, status_code)
        """
        forward_url = self.inventory_base_url + self.forward_path
        
        # Prepara headers (prepara los headers para la petición)
        fwd_headers = {
            k: v for k, v in request.headers.items() 
            if k.lower() != self.checksum_header.lower()
        }
        fwd_headers["X-Integrity-Validated"] = "true"
        
        try:
            resp = requests.post(forward_url, data=raw_body, headers=fwd_headers, timeout=10)
            
            # Crea la respuesta con los headers apropiados
            response_data = resp.content
            status_code = resp.status_code
            
            # Crea la respuesta con Flask
            flask_response = make_response(response_data, status_code)
            
            # Copia los headers importantes
            for k, v in resp.headers.items():
                if k.lower() in ["content-type", "location"]:
                    flask_response.headers[k] = v
            
            return flask_response.get_json() if resp.headers.get('content-type', '').startswith('application/json') else {"status": "ok"}, status_code
            
        except requests.RequestException as e:
            logging.exception("Proxy error")
            return {"error": "Upstream error", "detail": str(e)}, 502

"""
Validation model for cf-validador component.
Handles checksum computation and validation logic.
"""
import hashlib
import json
import logging
from typing import Tuple, Optional


class ValidationModel:
    
    def __init__(self, algorithm: str = "sha256"):
        self.algorithm = algorithm.lower()
        if self.algorithm != "sha256":
            raise ValueError("Unsupported algorithm. Only sha256 is supported in this sample.")
    
    def canonical_json_bytes(self, raw_body: bytes, content_type: str) -> bytes:
        """
        Convierte el raw body a bytes canónicos de JSON para el cálculo de checksum consistente.
        
        Args:
            raw_body: Raw request body bytes
            content_type: Content-Type header value
            
        Returns:
            Canonical JSON bytes
        """
        if "application/json" in (content_type or "").lower():
            try:
                data = json.loads(raw_body.decode("utf-8"))
                canon = json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
                return canon.encode("utf-8")
            except Exception:
                return raw_body
        return raw_body
    
    def compute_checksum(self, raw_body: bytes) -> str:
        """
        Calcula el checksum para el raw body dado.
        
        Args:
            raw_body: Raw bytes to compute checksum for
            
        Returns:
            Hex digest del checksum
        """
        h = hashlib.sha256()
        h.update(raw_body)
        return h.hexdigest()
    
    def validate_integrity(self, raw_body: bytes, content_type: str, expected_checksum: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida la integridad del body de la petición.
        
        Args:
            raw_body: Raw request body bytes
            content_type: Content-Type header value
            expected_checksum: Expected checksum from header
            
        Returns:
            Tuple de (is_valid, actual_checksum, error_message)
        """
        try:
            canonical_body = self.canonical_json_bytes(raw_body, content_type)
            actual_checksum = self.compute_checksum(canonical_body)
            
            if actual_checksum != expected_checksum:
                logging.warning("Integrity mismatch: expected=%s actual=%s", expected_checksum, actual_checksum)
                return False, actual_checksum, "Integrity check failed"
            
            return True, actual_checksum, None
            
        except Exception as e:
            logging.exception("Error during validation")
            return False, "", f"Validation error: {str(e)}"

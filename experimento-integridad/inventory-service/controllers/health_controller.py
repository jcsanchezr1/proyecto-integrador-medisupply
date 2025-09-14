"""
Controlador de salud para el componente inventory-service.
Gestiona las operaciones de verificación de salud y estado del sistema.
"""
from typing import Dict, Any, Tuple
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


class HealthController:
    """Gestiona las operaciones de verificación de salud."""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def health_check(self) -> Tuple[Dict[str, Any], int]:
        """
        Realiza la verificación de salud.
        
        Returns:
            Tuple de (response_data, status_code)
        """
        try:
            # Prueba la conexión a la base de datos
            self.db.session.execute(text("SELECT 1"))
            
            return {
                "status": "ok",
                "database": "connected",
                "service": "inventory-service"
            }, 200
            
        except Exception as e:
            return {
                "status": "error",
                "database": "disconnected",
                "service": "inventory-service",
                "error": str(e)
            }, 503

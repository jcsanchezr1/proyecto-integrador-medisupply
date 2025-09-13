"""
Health controller for inventory-service component.
Handles health check and system status operations.
"""
from typing import Dict, Any, Tuple
from flask_sqlalchemy import SQLAlchemy


class HealthController:
    """Controller for handling health check operations."""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def health_check(self) -> Tuple[Dict[str, Any], int]:
        """
        Perform health check.
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Test database connection
            self.db.session.execute('SELECT 1')
            
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

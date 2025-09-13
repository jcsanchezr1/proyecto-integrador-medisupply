"""
Response view for cf-validador component.
Handles response formatting and serialization.
"""
from typing import Dict, Any, Tuple
from flask import make_response


class ResponseView:
    """Vista para formatear y serializar respuestas."""
    
    @staticmethod
    def create_response(data: Dict[str, Any], status_code: int) -> Any:
        """
        Crea una respuesta Flask desde los datos y el código de estado.
        
        Args:
            data: Response data dictionary
            status_code: HTTP status code
            
        Returns:
            Objeto de respuesta Flask
        """
        return make_response(data, status_code)
    
    @staticmethod
    def format_error_response(error_message: str, **kwargs) -> Dict[str, Any]:
        """
        Formatea una respuesta de error.
        
        Args:
            error_message: Error message
            **kwargs: Additional error details
            
        Returns:
            Diccionario de respuesta de error formateado
        """
        response = {"error": error_message}
        response.update(kwargs)
        return response
    
    @staticmethod
    def format_success_response(message: str, **kwargs) -> Dict[str, Any]:
        """
        Formatea una respuesta de éxito.
        
        Args:
            message: Success message
            **kwargs: Additional response data
            
        Returns:
            Diccionario de respuesta de éxito formateado
        """
        response = {"status": "ok", "message": message}
        response.update(kwargs)
        return response

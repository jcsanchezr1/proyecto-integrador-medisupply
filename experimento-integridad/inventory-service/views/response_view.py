"""
Gestiona el formateo y serialización de respuestas.
"""
from typing import Dict, Any
from flask import jsonify, make_response


class ResponseView:
    """Vista para formatear y serializar respuestas."""
    
    @staticmethod
    def create_json_response(data: Dict[str, Any], status_code: int):
        """
        Crea una respuesta JSON desde los datos y el código de estado.
        
        Args:
            data: diccionario de datos de la respuesta
            status_code: HTTP status code
            
        Returns:
            Objeto de respuesta JSON Flask
        """
        return jsonify(data), status_code
    
    @staticmethod
    def create_response(data: Dict[str, Any], status_code: int):
        """
        Crea una respuesta Flask desde los datos y el código de estado.
        
        Args:
            data: diccionario de datos de la respuesta
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
            error_message: mensaje de error
            **kwargs: detalles adicionales del error
            
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
            message: mensaje de éxito
            **kwargs: datos adicionales de la respuesta
            
        Returns:
            Diccionario de respuesta de éxito formateado
        """
        response = {"status": "ok", "message": message}
        response.update(kwargs)
        return response

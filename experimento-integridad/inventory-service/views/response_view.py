"""
Response view for inventory-service component.
Handles response formatting and serialization.
"""
from typing import Dict, Any
from flask import jsonify, make_response


class ResponseView:
    """View for formatting and serializing responses."""
    
    @staticmethod
    def create_json_response(data: Dict[str, Any], status_code: int):
        """
        Create a JSON response from data and status code.
        
        Args:
            data: Response data dictionary
            status_code: HTTP status code
            
        Returns:
            Flask JSON response object
        """
        return jsonify(data), status_code
    
    @staticmethod
    def create_response(data: Dict[str, Any], status_code: int):
        """
        Create a Flask response from data and status code.
        
        Args:
            data: Response data dictionary
            status_code: HTTP status code
            
        Returns:
            Flask response object
        """
        return make_response(data, status_code)
    
    @staticmethod
    def format_error_response(error_message: str, **kwargs) -> Dict[str, Any]:
        """
        Format an error response.
        
        Args:
            error_message: Error message
            **kwargs: Additional error details
            
        Returns:
            Formatted error response dictionary
        """
        response = {"error": error_message}
        response.update(kwargs)
        return response
    
    @staticmethod
    def format_success_response(message: str, **kwargs) -> Dict[str, Any]:
        """
        Format a success response.
        
        Args:
            message: Success message
            **kwargs: Additional response data
            
        Returns:
            Formatted success response dictionary
        """
        response = {"status": "ok", "message": message}
        response.update(kwargs)
        return response

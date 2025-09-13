"""
Main application entry point for cf-validador component.
Uses MVC pattern with separate models, views, and controllers.
Compatible with Google Cloud Functions Framework.
"""
import os
import logging
from flask import Flask, request

from controllers.validation_controller import ValidationController
from views.response_view import ResponseView

# Cloud Function (Gen2) using functions_framework via Flask app "app" as entrypoint.
app = Flask(__name__)

# Initialize MVC components
validation_controller = ValidationController()
response_view = ResponseView()

@app.route("/", methods=["POST"])
def validate_and_proxy():
    """
    Main endpoint for validation and proxy functionality.
    Uses MVC pattern to separate concerns.
    """
    try:
        # Use controller to handle business logic
        response_data, status_code = validation_controller.validate_and_proxy()
        
        # Use view to format response
        return response_view.create_response(response_data, status_code)
        
    except Exception as e:
        logging.exception("Unexpected error in validate_and_proxy")
        error_response = response_view.format_error_response(
            "Internal server error", 
            detail=str(e)
        )
        return response_view.create_response(error_response, 500)

# Cloud Function entry point - simplified approach
def validate_and_proxy_function(request):
    """
    Cloud Function entry point for Google Cloud Functions.
    This function is called by the functions-framework.
    """
    try:
        # Use controller to handle business logic directly
        response_data, status_code = validation_controller.validate_and_proxy()
        
        # Use view to format response
        return response_view.create_response(response_data, status_code)
        
    except Exception as e:
        logging.exception("Unexpected error in validate_and_proxy_function")
        error_response = response_view.format_error_response(
            "Internal server error", 
            detail=str(e)
        )
        return response_view.create_response(error_response, 500)
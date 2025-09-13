"""
Main application entry point for inventory-service component.
Uses MVC pattern with separate models, views, and controllers.
"""
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from models.product_model import Product, db
from controllers.product_controller import ProductController
from controllers.health_controller import HealthController
from views.response_view import ResponseView

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///inventory.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Initialize MVC components
product_controller = ProductController()
health_controller = HealthController(db)
response_view = ResponseView()

@app.before_request
def ensure_db():
    """Create tables if missing (demo convenience)."""
    db.create_all()

@app.route("/healthz", methods=["GET"])
def health():
    """
    Health check endpoint.
    Uses MVC pattern to separate concerns.
    """
    try:
        response_data, status_code = health_controller.health_check()
        return response_view.create_json_response(response_data, status_code)
    except Exception as e:
        logging.exception("Unexpected error in health check")
        error_response = response_view.format_error_response(
            "Health check failed", 
            detail=str(e)
        )
        return response_view.create_json_response(error_response, 500)

@app.route("/inventory/products", methods=["POST"])
def create_product():
    """
    Create or update product endpoint.
    Uses MVC pattern to separate concerns.
    """
    try:
        response_data, status_code = product_controller.create_or_update_product()
        return response_view.create_json_response(response_data, status_code)
    except Exception as e:
        logging.exception("Unexpected error in create_product")
        error_response = response_view.format_error_response(
            "Internal server error", 
            detail=str(e)
        )
        return response_view.create_json_response(error_response, 500)

@app.route("/inventory/products/<sku>", methods=["GET"])
def get_product(sku):
    """
    Get product by SKU endpoint.
    Uses MVC pattern to separate concerns.
    """
    try:
        response_data, status_code = product_controller.get_product_by_sku(sku)
        return response_view.create_json_response(response_data, status_code)
    except Exception as e:
        logging.exception("Unexpected error in get_product")
        error_response = response_view.format_error_response(
            "Internal server error", 
            detail=str(e)
        )
        return response_view.create_json_response(error_response, 500)

@app.route("/inventory/products", methods=["GET"])
def get_all_products():
    """
    Get all products endpoint.
    Uses MVC pattern to separate concerns.
    """
    try:
        response_data, status_code = product_controller.get_all_products()
        return response_view.create_json_response(response_data, status_code)
    except Exception as e:
        logging.exception("Unexpected error in get_all_products")
        error_response = response_view.format_error_response(
            "Internal server error", 
            detail=str(e)
        )
        return response_view.create_json_response(error_response, 500)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
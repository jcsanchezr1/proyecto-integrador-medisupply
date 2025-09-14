"""
Punto de entrada principal de la aplicación para el componente inventory-service.
Usa el patrón MVC con modelos, vistas y controladores separados.
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

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///inventory.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializa la base de datos   
db.init_app(app)

# Inicializa los componentes MVC
product_controller = ProductController()
health_controller = HealthController(db)
response_view = ResponseView()

@app.before_request
def ensure_db():
    """Crea las tablas si faltan (conveniencia de demostración)."""
    db.create_all()

@app.route("/ping", methods=["GET"])
def health():
    """
    Punto de comprobación de salud.
    
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
    Punto de creación o actualización de producto.
    
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
    Punto de obtención de producto por SKU.

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
    Punto de obtención de todos los productos.    
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
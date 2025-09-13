"""
Controlador de productos para el componente inventory-service.
Gestiona la lógica y operaciones relacionadas con los productos.
"""
from datetime import date
from typing import Dict, Any, Tuple, Optional
from flask import request

from models.product_model import Product, db


class ProductController:
    """Gestiona las operaciones relacionadas con los productos."""
    
    def create_or_update_product(self) -> Tuple[Dict[str, Any], int]:
        """
        Crea un nuevo producto o actualiza uno existente.
        
        Returns:
            Tuple de (response_data, status_code)
        """
        # Verifica la integridad de la validación del header
        if request.headers.get("X-Integrity-Validated", "").lower() != "true":
            return {"error": "Integrity not validated"}, 403
        
        # Parsea los datos de la petición
        try:
            data = request.get_json(force=True)
        except Exception:
            return {"error": "Invalid JSON"}, 400
        
        # Valida los campos requeridos
        is_valid, error_message = Product.validate_required_fields(data)
        if not is_valid:
            return {"error": error_message}, 400
        
        sku = data.get("sku")
        name = data.get("name")
        lot_number = data.get("lot_number")
        expiration_str = data.get("expiration_date")
        
        # Valida la fecha de vencimiento
        exp_date, exp_error = Product.validate_expiration_date(expiration_str)
        if exp_error:
            return {"error": exp_error}, 400
        
        try:
            # Verifica si el producto existe
            existing_product = Product.find_by_sku(sku)
            
            if existing_product:
                # Actualiza el producto existente
                existing_product.update_product(name, lot_number, exp_date)
                db.session.commit()
                return {
                    "status": "updated",
                    "product": existing_product.to_dict()
                }, 200
            else:
                # Crea un nuevo producto
                new_product = Product.create_product(sku, name, lot_number, exp_date)
                db.session.commit()
                return {
                    "status": "created",
                    "product": new_product.to_dict()
                }, 201
                
        except Exception as e:
            db.session.rollback()
            return {"error": f"Database error: {str(e)}"}, 500
    
    def get_product_by_sku(self, sku: str) -> Tuple[Dict[str, Any], int]:
        """
        Obtiene un producto por SKU.
        
        Args:
            sku: Product SKU
            
        Returns:
            Tuple de (response_data, status_code)
        """
        try:
            product = Product.find_by_sku(sku)
            if not product:
                return {"error": "Product not found"}, 404
            
            return {"product": product.to_dict()}, 200
            
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}, 500
    
    def get_all_products(self) -> Tuple[Dict[str, Any], int]:
        """
        Obtiene todos los productos.
        
        Returns:
            Tuple de (response_data, status_code)
        """
        try:
            products = Product.query.all()
            return {
                "products": [product.to_dict() for product in products],
                "count": len(products)
            }, 200
            
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}, 500

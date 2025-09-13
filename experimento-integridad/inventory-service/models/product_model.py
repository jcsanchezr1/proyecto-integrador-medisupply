"""
Modelo de datos para el componente inventory-service.
Gestiona los datos y lógica de negocio relacionados con los productos.
"""
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from flask_sqlalchemy import SQLAlchemy

# Esto será inicializado en la aplicación principal
db = SQLAlchemy()


class Product(db.Model):
    """Modelo de datos para representar los productos del inventario."""
    
    __tablename__ = "products"
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    lot_number = db.Column(db.String(64), nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el producto a una representación de diccionario."""
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "lot_number": self.lot_number,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def find_by_sku(cls, sku: str) -> Optional['Product']:
        """Encuentra un producto por SKU."""
        return cls.query.filter_by(sku=sku).first()
    
    @classmethod
    def create_product(cls, sku: str, name: str, lot_number: str = None, 
                      expiration_date: date = None) -> 'Product':
        """Crea un nuevo producto."""
        product = cls(
            sku=sku,
            name=name,
            lot_number=lot_number,
            expiration_date=expiration_date
        )
        db.session.add(product)
        return product
    
    def update_product(self, name: str, lot_number: str = None, 
                      expiration_date: date = None) -> None:
        """Actualiza la información del producto."""
        self.name = name
        self.lot_number = lot_number
        self.expiration_date = expiration_date
    
    @staticmethod
    def validate_expiration_date(expiration_str: str) -> tuple[Optional[date], Optional[str]]:
        """
        Valida la fecha de vencimiento.
        
        Args:
            expiration_str: Date string in YYYY-MM-DD format
            
        Returns:
            Tuple de (date_object, error_message)
        """
        if not expiration_str:
            return None, None
            
        try:
            exp_date = date.fromisoformat(expiration_str)
            if exp_date < date.today():
                return None, "Expired lot is not allowed"
            return exp_date, None
        except ValueError:
            return None, "Invalid expiration_date format. Use YYYY-MM-DD"
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Valida los campos requeridos para la creación de un producto.
        
        Args:
            data: diccionario de datos del producto
            
        Returns:
            Tuple de (is_valid, error_message)
        """
        sku = data.get("sku")
        name = data.get("name")
        
        if not sku or not name:
            return False, "Faltan campos requeridos: sku, name"
        
        return True, None

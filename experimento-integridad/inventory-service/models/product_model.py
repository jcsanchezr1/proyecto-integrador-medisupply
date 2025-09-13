"""
Product model for inventory-service component.
Handles product data and business logic.
"""
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from flask_sqlalchemy import SQLAlchemy

# This will be initialized in the main app
db = SQLAlchemy()


class Product(db.Model):
    """Product model representing inventory items."""
    
    __tablename__ = "products"
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    lot_number = db.Column(db.String(64), nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary representation."""
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
        """Find product by SKU."""
        return cls.query.filter_by(sku=sku).first()
    
    @classmethod
    def create_product(cls, sku: str, name: str, lot_number: str = None, 
                      expiration_date: date = None) -> 'Product':
        """Create a new product."""
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
        """Update product information."""
        self.name = name
        self.lot_number = lot_number
        self.expiration_date = expiration_date
    
    @staticmethod
    def validate_expiration_date(expiration_str: str) -> tuple[Optional[date], Optional[str]]:
        """
        Validate expiration date string.
        
        Args:
            expiration_str: Date string in YYYY-MM-DD format
            
        Returns:
            Tuple of (date_object, error_message)
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
        Validate required fields for product creation.
        
        Args:
            data: Product data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        sku = data.get("sku")
        name = data.get("name")
        
        if not sku or not name:
            return False, "Missing required fields: sku, name"
        
        return True, None

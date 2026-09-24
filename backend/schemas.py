from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models import UserRole, MovementType

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    username: str
    name: str
    role: UserRole = UserRole.EMPLOYEE

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserResetPassword(BaseModel):
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str
    username: str

# --- PRODUCT SCHEMAS ---
class ProductBase(BaseModel):
    code: str
    name: str
    category: str = "Geral"
    unit: str = "un"
    items_per_box: int = Field(ge=1, default=1)
    cost_price: float = Field(ge=0.0, default=0.0)
    selling_price: float = Field(ge=0.0, default=0.0)
    box_selling_price: Optional[float] = Field(ge=0.0, default=0.0)
    quantity: int = Field(ge=0, default=0)
    min_quantity: int = Field(ge=0, default=5)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    items_per_box: Optional[int] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    box_selling_price: Optional[float] = None
    min_quantity: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    is_low_stock: bool = False

    class Config:
        from_attributes = True

class ProductStaffResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str
    unit: str
    items_per_box: int
    selling_price: float
    box_selling_price: Optional[float] = 0.0
    quantity: int
    min_quantity: int

    created_at: datetime
    is_low_stock: bool = False

    class Config:
        from_attributes = True

# --- MOVEMENT SCHEMAS ---
class MovementCreate(BaseModel):
    product_id: int
    type: MovementType
    quantity: int = Field(gt=0)
    unit_mode: str = "un" # "un" para unidades avulsas, "cx" para caixa fechada
    unit_price: Optional[float] = None
    notes: Optional[str] = None


class MovementResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    user_id: int
    user_name: str
    type: MovementType
    quantity: int
    unit_price: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- REPORT SCHEMAS ---
class StockValuation(BaseModel):
    total_products: int
    total_items: int
    total_cost_value: float
    total_selling_value: float
    potential_profit: float

class TopSellingProduct(BaseModel):
    product_id: int
    code: str
    name: str
    total_quantity_sold: int
    total_revenue: float

class IdleProduct(BaseModel):
    product_id: int
    code: str
    name: str
    quantity: int
    days_without_movement: int

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"

class MovementType(str, enum.Enum):
    IN = "IN"      # Entrada de mercadoria
    OUT = "OUT"    # Saída / Venda

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    movements = relationship("StockMovement", back_populates="user")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)  # SKU / Código de barras
    name = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False, default="Geral")
    unit = Column(String, nullable=False, default="un")
    items_per_box = Column(Integer, nullable=False, default=1)  # Qtd de itens dentro da caixa (ex: 12)
    cost_price = Column(Float, nullable=False, default=0.0)
    selling_price = Column(Float, nullable=False, default=0.0)      # Preço de Venda Avulso (Unidade)
    box_selling_price = Column(Float, nullable=True, default=0.0)   # Preço de Venda em Caixa Fechada (Desconto atacado)
    quantity = Column(Integer, nullable=False, default=0)
    min_quantity = Column(Integer, nullable=False, default=5)  # Alerta de estoque baixo
    created_at = Column(DateTime, default=datetime.utcnow)

    movements = relationship("StockMovement", back_populates="product")



class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(SQLEnum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=True) # Preço praticado no momento (custo na entrada, venda na saída)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="movements")
    user = relationship("User", back_populates="movements")

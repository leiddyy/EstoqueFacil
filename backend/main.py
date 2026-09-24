import sys
import os

# Garantir que a pasta backend esteja no path de busca de módulos do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from database import engine, Base, get_db
import models
import schemas
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    require_admin,
)

# Criar tabelas se não existirem
Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criar usuário admin padrão no startup se não existir
    db = next(get_db())
    admin_user = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin_user:
        hashed = get_password_hash("admin123")
        db_admin = models.User(
            username="admin",
            name="Administrador Principal",
            hashed_password=hashed,
            role=models.UserRole.ADMIN,
        )
        db.add(db_admin)
        
        # Criar também um funcionário padrão para testes simples
        hashed_emp = get_password_hash("123456")
        db_emp = models.User(
            username="funcionario",
            name="Funcionário Caixa",
            hashed_password=hashed_emp,
            role=models.UserRole.EMPLOYEE,
        )
        db.add(db_emp)
        db.commit()
    yield

app = FastAPI(
    title="Estoque Fácil API",
    description="Sistema de Controle de Estoque com RBAC para Pequenos Negócios",
    version="1.0.0",
    lifespan=lifespan,
)

# Permitir solicitações do frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.post("/api/auth/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos."
        )
    token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "name": user.name,
        "username": user.username,
    }

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ==================== ROTAS DE USUÁRIOS (ADMIN ONLY) ====================

@app.get("/api/users", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    return db.query(models.User).all()

@app.post("/api/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Nome de usuário já existe.")
    
    hashed = get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        name=user.name,
        hashed_password=hashed,
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.put("/api/users/{user_id}/reset-password")
def reset_user_password(user_id: int, payload: schemas.UserResetPassword, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"detail": f"Senha do usuário {user.username} redefinida com sucesso."}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir o seu próprio usuário logado.")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    db.delete(user)
    db.commit()
    return {"detail": "Usuário excluído com sucesso."}

# ==================== ROTAS DE PRODUTOS ====================

import urllib.request
import json

# Chave do token da API Bluesoft Cosmos
BLUESOFT_COSMOS_TOKEN = os.getenv("BLUESOFT_COSMOS_TOKEN", "IIkk0LgYkXZPGlJHRgtgdw")


@app.get("/api/products/lookup/{barcode}")
def lookup_barcode(barcode: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Verificar se já existe cadastrado no banco local
    existing = db.query(models.Product).filter(models.Product.code == barcode).first()
    if existing:
        return {
            "found": True,
            "source": "local",
            "code": existing.code,
            "name": existing.name,
            "category": existing.category,
            "unit": existing.unit,
            "cost_price": existing.cost_price if current_user.role == models.UserRole.ADMIN else None,
            "selling_price": existing.selling_price,
            "quantity": existing.quantity,
            "min_quantity": existing.min_quantity
        }

    # 2. Se a chave da Bluesoft Cosmos estiver configurada, consulta primeiro a Cosmos API
    if BLUESOFT_COSMOS_TOKEN:
        try:
            cosmos_url = f"https://api.cosmos.bluesoft.com.br/gtins/{barcode}.json"
            req = urllib.request.Request(cosmos_url, headers={
                'User-Agent': 'Cosmos-API-Request',
                'X-Cosmos-Token': BLUESOFT_COSMOS_TOKEN
            })
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                if "description" in data:
                    name = data.get("description", "")
                    category = data.get("category", {}).get("name", "Geral") if isinstance(data.get("category"), dict) else "Geral"
                    price = data.get("avg_price", 0.0) or 0.0
                    
                    return {
                        "found": True,
                        "source": "bluesoft_cosmos",
                        "code": barcode,
                        "name": name.title(),
                        "category": category.title() if category else "Geral",
                        "unit": "un",
                        "cost_price": 0.0,
                        "selling_price": round(float(price), 2) if price else 0.0,
                        "quantity": 0,
                        "min_quantity": 5
                    }
        except Exception as e:
            print(f"Erro ao consultar Bluesoft Cosmos API: {e}")

    # 3. Fallback: Consultar API pública Open Food Facts
    try:
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        req = urllib.request.Request(url, headers={'User-Agent': 'EstoqueFacilMercadinho - Version 1.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("status") == 1 and "product" in data:
                prod = data["product"]
                name = prod.get("product_name_pt") or prod.get("product_name") or ""
                categories = prod.get("categories") or "Geral"
                category = categories.split(",")[0].strip() if categories else "Geral"
                
                if name:
                    return {
                        "found": True,
                        "source": "openfoodfacts",
                        "code": barcode,
                        "name": name.title(),
                        "category": category.title(),
                        "unit": "un",
                        "cost_price": 0.0,
                        "selling_price": 0.0,
                        "quantity": 0,
                        "min_quantity": 5
                    }
    except Exception as e:
        pass

    return {
        "found": False,
        "code": barcode,
        "name": "",
        "category": "Geral",
        "unit": "un",
        "cost_price": 0.0,
        "selling_price": 0.0,
        "quantity": 0,
        "min_quantity": 5
    }


@app.get("/api/products")
def list_products(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    products = db.query(models.Product).order_by(models.Product.name.asc()).all()
    
    result = []
    for p in products:
        item = {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "category": p.category,
            "unit": p.unit,
            "items_per_box": p.items_per_box,
            "selling_price": p.selling_price,
            "box_selling_price": p.box_selling_price or 0.0,
            "quantity": p.quantity,
            "min_quantity": p.min_quantity,
            "created_at": p.created_at,
            "is_low_stock": p.quantity <= p.min_quantity
        }
        if current_user.role == models.UserRole.ADMIN:
            item["cost_price"] = p.cost_price
        result.append(item)
    return result

@app.post("/api/products", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    existing = db.query(models.Product).filter(models.Product.code == product.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Código de produto (SKU/Barra) já cadastrado.")
    
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.put("/api/products/{product_id}")
def update_product(product_id: int, product_data: schemas.ProductUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    prod = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    update_dict = product_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(prod, key, value)
        
    db.commit()
    db.refresh(prod)
    return prod

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    prod = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    db.delete(prod)
    db.commit()
    return {"detail": "Produto excluído com sucesso."}

# ==================== ROTAS DE MOVIMENTAÇÃO DE ESTOQUE ====================

@app.post("/api/movements", response_model=schemas.MovementResponse)
def record_movement(mov: schemas.MovementCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    prod = db.query(models.Product).filter(models.Product.id == mov.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    # Calcular o fator de conversão se movimentar por caixa (cx)
    items_per_box = prod.items_per_box or 1
    actual_units = mov.quantity * items_per_box if mov.unit_mode == "cx" else mov.quantity
    
    # Preparar nota explicativa se foi movimentado em caixa
    mode_text = f" ({mov.quantity} cx com {items_per_box} un cada)" if mov.unit_mode == "cx" else ""
    full_notes = (mov.notes or "") + mode_text if mode_text else mov.notes

    if mov.type == models.MovementType.OUT:
        if prod.quantity < actual_units:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente. Saldo atual: {prod.quantity} {prod.unit}. Tentou baixar: {actual_units} {prod.unit}."
            )
        prod.quantity -= actual_units
        
        # Se for venda em caixa e houver preço diferenciado de caixa, usa o preço da caixa; caso contrário calcula proporcional
        default_price = prod.box_selling_price if (mov.unit_mode == "cx" and prod.box_selling_price and prod.box_selling_price > 0) else prod.selling_price
        price_used = mov.unit_price if mov.unit_price is not None else default_price
    else: # IN
        prod.quantity += actual_units
        price_used = mov.unit_price if mov.unit_price is not None else prod.cost_price

    new_movement = models.StockMovement(
        product_id=prod.id,
        user_id=current_user.id,
        type=mov.type,
        quantity=actual_units,
        unit_price=price_used,
        notes=full_notes,
    )
    db.add(new_movement)
    db.commit()
    db.refresh(new_movement)


    return {
        "id": new_movement.id,
        "product_id": prod.id,
        "product_name": prod.name,
        "user_id": current_user.id,
        "user_name": current_user.name,
        "type": new_movement.type,
        "quantity": new_movement.quantity,
        "unit_price": new_movement.unit_price,
        "notes": new_movement.notes,
        "created_at": new_movement.created_at,
    }


@app.get("/api/movements")
def list_movements(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    movements = db.query(models.StockMovement).order_by(models.StockMovement.created_at.desc()).all()
    result = []
    for m in movements:
        item = {
            "id": m.id,
            "product_id": m.product_id,
            "product_name": m.product.name if m.product else "Desconhecido",
            "user_id": m.user_id,
            "user_name": m.user.name if m.user else "Desconhecido",
            "type": m.type.value,
            "quantity": m.quantity,
            "notes": m.notes,
            "created_at": m.created_at
        }
        if current_user.role == models.UserRole.ADMIN:
            item["unit_price"] = m.unit_price
        result.append(item)
    return result

# ==================== ROTAS DE RELATÓRIOS & INTEGRAÇÃO ====================

@app.get("/api/reports/low-stock")
def get_low_stock_report(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    products = db.query(models.Product).filter(models.Product.quantity <= models.Product.min_quantity).all()
    return products

@app.get("/api/reports/valuation", response_model=schemas.StockValuation)
def get_stock_valuation(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    products = db.query(models.Product).all()
    total_products = len(products)
    total_items = sum(p.quantity for p in products)
    total_cost = sum(p.quantity * p.cost_price for p in products)
    total_selling = sum(p.quantity * p.selling_price for p in products)
    
    return {
        "total_products": total_products,
        "total_items": total_items,
        "total_cost_value": round(total_cost, 2),
        "total_selling_value": round(total_selling, 2),
        "potential_profit": round(total_selling - total_cost, 2)
    }

@app.get("/api/reports/top-selling")
def get_top_selling(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Agrupar saídas por produto
    movements = db.query(models.StockMovement).filter(models.StockMovement.type == models.MovementType.OUT).all()
    summary = {}
    for m in movements:
        p_id = m.product_id
        if p_id not in summary:
            summary[p_id] = {
                "product_id": p_id,
                "code": m.product.code if m.product else "",
                "name": m.product.name if m.product else "Produto Excluído",
                "total_quantity_sold": 0,
                "total_revenue": 0.0
            }
        summary[p_id]["total_quantity_sold"] += m.quantity
        summary[p_id]["total_revenue"] += m.quantity * (m.unit_price or 0.0)

    top_list = sorted(summary.values(), key=lambda x: x["total_quantity_sold"], reverse=True)
    return top_list[:10]

@app.get("/api/reports/idle-products")
def get_idle_products(days: int = 30, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Produtos com movimentação recente
    recent_movement_pids = db.query(models.StockMovement.product_id).filter(
        models.StockMovement.created_at >= cutoff_date
    ).distinct().all()
    recent_pids = [r[0] for r in recent_movement_pids]

    # Produtos com estoque > 0 e sem movimentação recente
    idle = db.query(models.Product).filter(
        models.Product.quantity > 0,
        ~models.Product.id.in_(recent_pids)
    ).all()

    return idle

# Servir arquivos estáticos do Frontend se a pasta existir
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    def read_root():
        return FileResponse(os.path.join(frontend_path, "index.html"))

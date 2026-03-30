import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Base, User
from schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemListResponse, ItemStats,
    UserCreate, UserResponse, LoginRequest, TokenResponse,
)
from auth import create_access_token, get_current_user
import crud

load_dotenv()

# Buat semua tabel
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cloud App API",
    description="REST API untuk mata kuliah Komputasi Awan — SI ITK",
    version="0.5.0",
)

# ==================== CORS ====================
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
origins_list = [origin.strip() for origin in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HEALTH CHECK ====================

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.5.0"}


# ==================== AUTH ENDPOINTS (PUBLIC) ====================

@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registrasi user baru.
    
    - **email**: Format valid, unik
    - **name**: Nama lengkap (2-100 char)
    - **password**: Min 8 char, huruf besar, angka, special (@$!%*?&)
    """
    user = crud.create_user(db=db, user_data=user_data)
    if not user:
        raise HTTPException(
            status_code=400, 
            detail="Email sudah terdaftar. Gunakan email lain atau login."
        )
    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login dan dapatkan JWT token.
    """
    user = crud.authenticate_user(db=db, email=login_data.email, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Email atau password salah. Periksa kembali kredensial Anda."
        )

    token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Ambil profil user yang sedang login."""
    return current_user


# ==================== ITEM ENDPOINTS (PROTECTED) ====================

@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Buat item baru. Harga harus > 0, quantity >= 0."""
    return crud.create_item(db=db, item_data=item)


@app.get("/items", response_model=ItemListResponse)
def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil daftar items dengan pagination & search."""
    return crud.get_items(db=db, skip=skip, limit=limit, search=search)


@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil satu item."""
    item = crud.get_item(db=db, item_id=item_id)
    if not item:
        raise HTTPException(
            status_code=404, 
            detail=f"Item dengan ID {item_id} tidak ditemukan."
        )
    return item


@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update item (partial update OK)."""
    updated = crud.update_item(db=db, item_id=item_id, item_data=item)
    if not updated:
        raise HTTPException(
            status_code=404, 
            detail=f"Item dengan ID {item_id} tidak ditemukan atau tidak dapat diupdate."
        )
    return updated


@app.delete("/items/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hapus item."""
    success = crud.delete_item(db=db, item_id=item_id)
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Item dengan ID {item_id} tidak ditemukan."
        )
    return None


# ==================== NEW STATS ENDPOINT ====================

@app.get("/items/stats", response_model=ItemStats)
def get_items_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Statistik items: total, nilai total, rata-rata harga/quantity, low stock (<10).
    """
    return crud.get_items_stats(db=db)


# ==================== TEAM INFO ====================

@app.get("/team")
def team_info():
    return {
        "team": "cloud-team-nyawit",
        "members": [
            {"name": "Muchlis Wahyu Saputra", "nim": "10231054", "role": "Lead Backend"},
            {"name": "Ranaya Chintya Mahitsa", "nim": "10231078", "role": "Lead Frontend"},
            {"name": "Ahmad Baihaqi", "nim": "10221063", "role": "Lead DevOps"},
            {"name": "Az-Zahra Atikah Nurhaliza", "nim": "10231022", "role": "Lead QA & Docs"},
        ],
    }

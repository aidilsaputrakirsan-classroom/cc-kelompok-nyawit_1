from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models import Item, User
from schemas import ItemCreate, ItemUpdate, UserCreate, ItemResponse, ItemListResponse, ItemStats
from auth import hash_password, verify_password


# ==================== USER CRUD ====================

def create_user(db: Session, user_data: UserCreate) -> User:
    """Buat user baru dengan password yang di-hash."""
    # Cek apakah email sudah terdaftar
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        return None  # Email sudah dipakai

    db_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hash_password(user_data.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Autentikasi user: cek email & password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ==================== ITEM CRUD ====================

def get_items(db: Session, skip: int = 0, limit: int = 20, search: str = None) -> ItemListResponse:
    """Ambil daftar items dengan pagination dan optional search."""
    query = db.query(Item)
    
    if search:
        query = query.filter(
            or_(
                Item.name.ilike(f"%{{search}}%"),
                Item.description.ilike(f"%{{search}}%")
            )
        )
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return ItemListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


def create_item(db: Session, item_data: ItemCreate) -> Item:
    """Buat item baru."""
    db_item = Item(**item_data.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(db: Session, item_id: int) -> Item | None:
    """Ambil item berdasarkan ID."""
    return db.query(Item).filter(Item.id == item_id).first()


def update_item(db: Session, item_id: int, item_data: ItemUpdate) -> Item | None:
    """Update item jika ditemukan."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return None
    
    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int) -> bool:
    """Hapus item dan return True jika berhasil."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return False
    
    db.delete(item)
    db.commit()
    return True


# ==================== STATS ====================

def get_items_stats(db: Session) -> ItemStats:
    """Ambil statistik items."""
    total_items = db.query(func.count(Item.id)).scalar()
    total_value = db.query(func.sum(Item.price * Item.quantity)).scalar() or 0.0
    avg_price = db.query(func.avg(Item.price)).scalar() or 0.0
    avg_quantity = db.query(func.avg(Item.quantity)).scalar() or 0.0
    low_stock = db.query(func.count(Item.id)).filter(Item.quantity < 10).scalar()
    
    return ItemStats(
        total_items=total_items,
        total_value=float(total_value),
        avg_price=float(avg_price),
        avg_quantity=float(avg_quantity),
        low_stock=low_stock
    )

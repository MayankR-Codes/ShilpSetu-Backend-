"""SQLAlchemy async models for ShilpSetu."""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    artisan_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title_en: Mapped[str] = mapped_column(String(255), nullable=True)
    title_hi: Mapped[str] = mapped_column(String(255), nullable=True)
    description_en: Mapped[str] = mapped_column(Text, nullable=True)
    description_hi: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=True)
    sub_category: Mapped[str] = mapped_column(String(64), nullable=True)
    craft_type: Mapped[str] = mapped_column(String(64), nullable=True)
    original_image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    enhanced_image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    price_suggested: Mapped[float] = mapped_column(Float, nullable=True)
    price_min: Mapped[float] = mapped_column(Float, nullable=True)
    price_max: Mapped[float] = mapped_column(Float, nullable=True)
    raw_material_cost: Mapped[float] = mapped_column(Float, nullable=True)
    min_profit: Mapped[float] = mapped_column(Float, nullable=True)
    features: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    why_buy: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    tags: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    materials_breakdown: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

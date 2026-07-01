from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    telegram_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tracked = relationship("TrackedProduct", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    platform = Column(String, nullable=False)  # amazon, flipkart, myntra
    url = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    category = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    original_price = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    last_scraped = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    price_history = relationship("PriceHistory", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    buy_scores = relationship("BuyScore", back_populates="product")
    tracked_by = relationship("TrackedProduct", back_populates="product")


class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    platform = Column(String, nullable=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    product = relationship("Product", back_populates="price_history")


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    text = Column(Text, nullable=False)
    rating = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=True)   # -1 to 1
    is_suspicious = Column(Boolean, default=False)   # fake review flag
    fit_signal = Column(String, nullable=True)        # "runs small", "true to size", etc.
    reviewer_name = Column(String, nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    product = relationship("Product", back_populates="reviews")


class BuyScore(Base):
    __tablename__ = "buy_scores"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    score = Column(Float, nullable=False)             # 0-10
    price_score = Column(Float, nullable=True)
    review_score = Column(Float, nullable=True)
    timing_score = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)           # AI-generated explanation
    recommendation = Column(String, nullable=True)    # "buy", "wait", "avoid"
    predicted_low_price = Column(Float, nullable=True)
    predicted_low_date = Column(String, nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    product = relationship("Product", back_populates="buy_scores")


class TrackedProduct(Base):
    __tablename__ = "tracked_products"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    target_price = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="tracked")
    product = relationship("Product", back_populates="tracked_by")


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="chat_history")


class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    searched_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="search_history")


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    alert_type = Column(String, nullable=False)   # "price_drop", "buy_score", "festival"
    threshold = Column(Float, nullable=True)
    channel = Column(String, nullable=False)      # "email", "telegram", "browser"
    is_triggered = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="alerts")

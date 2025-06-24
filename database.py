import os
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Optional
import json

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error("Database URL not found. Please configure the database.")
    st.stop()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    daily_sugar_limit = Column(Float, default=25.0)  # WHO recommendation
    created_at = Column(DateTime, default=datetime.utcnow)

class FoodItem(Base):
    __tablename__ = "food_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    sugar_g = Column(Float)
    calories = Column(Float)
    carbs_g = Column(Float)
    protein_g = Column(Float)
    fat_g = Column(Float)
    fiber_g = Column(Float)
    sodium_mg = Column(Float)
    data_source = Column(String)  # "USDA" or "OpenFoodFacts"
    external_id = Column(String)  # FDC ID or barcode
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyTracker(Base):
    __tablename__ = "daily_tracker"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)  # Simple user system for now
    food_item_id = Column(Integer)
    food_name = Column(String)
    portion_g = Column(Float)
    sugar_g = Column(Float)
    calories = Column(Float)
    consumed_at = Column(DateTime, default=datetime.utcnow)
    date = Column(String)  # Format: YYYY-MM-DD

class FavoriteFood(Base):
    __tablename__ = "favorite_foods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)  # Simple user system for now
    food_item_id = Column(Integer)
    food_name = Column(String)
    sugar_g = Column(Float)
    calories = Column(Float)
    food_data = Column(Text)  # JSON string of complete food data
    added_at = Column(DateTime, default=datetime.utcnow)

class SugarInsight(Base):
    __tablename__ = "sugar_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    date = Column(String)  # Format: YYYY-MM-DD
    total_sugar_g = Column(Float)
    total_calories = Column(Float)
    food_count = Column(Integer)
    exceeded_limit = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create all tables
def init_database():
    """Initialize the database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")
        return False

# Database operations
def get_db_session():
    """Get database session"""
    return SessionLocal()

def save_food_item(food_data: Dict) -> Optional[int]:
    """Save a food item to the database"""
    try:
        db = get_db_session()
        
        # Check if food item already exists
        existing_food = db.query(FoodItem).filter(
            FoodItem.name == food_data['name'],
            FoodItem.external_id == food_data.get('fdc_id', '')
        ).first()
        
        if existing_food:
            db.close()
            return existing_food.id
        
        # Create new food item
        food_item = FoodItem(
            name=food_data['name'],
            description=food_data.get('description', ''),
            sugar_g=food_data.get('sugar_g', 0),
            calories=food_data.get('calories', 0),
            carbs_g=food_data.get('carbs_g', 0),
            protein_g=food_data.get('protein_g', 0),
            fat_g=food_data.get('fat_g', 0),
            fiber_g=food_data.get('fiber_g', 0),
            sodium_mg=food_data.get('sodium_mg', 0),
            data_source=food_data.get('data_type', 'Unknown'),
            external_id=str(food_data.get('fdc_id', ''))
        )
        
        db.add(food_item)
        db.commit()
        food_id = food_item.id
        db.close()
        return food_id
        
    except Exception as e:
        st.error(f"Error saving food item: {str(e)}")
        return None

def add_to_daily_tracker(food_data: Dict, portion_g: float, user_id: int = 1) -> bool:
    """Add food consumption to daily tracker"""
    try:
        db = get_db_session()
        
        # Save food item first
        food_id = save_food_item(food_data)
        
        # Calculate actual values based on portion
        actual_sugar = (food_data.get('sugar_g', 0) / 100) * portion_g
        actual_calories = (food_data.get('calories', 0) / 100) * portion_g
        
        # Create tracker entry
        tracker_entry = DailyTracker(
            user_id=user_id,
            food_item_id=food_id,
            food_name=food_data['name'],
            portion_g=portion_g,
            sugar_g=actual_sugar,
            calories=actual_calories,
            date=datetime.now().strftime('%Y-%m-%d')
        )
        
        db.add(tracker_entry)
        db.commit()
        db.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding to daily tracker: {str(e)}")
        return False

def get_daily_tracker(date: str = None, user_id: int = 1) -> List[Dict]:
    """Get daily tracker entries"""
    try:
        db = get_db_session()
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        entries = db.query(DailyTracker).filter(
            DailyTracker.user_id == user_id,
            DailyTracker.date == date
        ).all()
        
        result = []
        for entry in entries:
            result.append({
                'id': entry.id,
                'name': entry.food_name,
                'portion_g': entry.portion_g,
                'sugar_g': entry.sugar_g,
                'calories': entry.calories,
                'time': entry.consumed_at.strftime('%H:%M')
            })
        
        db.close()
        return result
        
    except Exception as e:
        st.error(f"Error getting daily tracker: {str(e)}")
        return []

def remove_from_daily_tracker(entry_id: int) -> bool:
    """Remove entry from daily tracker"""
    try:
        db = get_db_session()
        
        entry = db.query(DailyTracker).filter(DailyTracker.id == entry_id).first()
        if entry:
            db.delete(entry)
            db.commit()
            db.close()
            return True
        
        db.close()
        return False
        
    except Exception as e:
        st.error(f"Error removing from daily tracker: {str(e)}")
        return False

def clear_daily_tracker(date: str = None, user_id: int = 1) -> bool:
    """Clear all entries for a specific date"""
    try:
        db = get_db_session()
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        db.query(DailyTracker).filter(
            DailyTracker.user_id == user_id,
            DailyTracker.date == date
        ).delete()
        
        db.commit()
        db.close()
        return True
        
    except Exception as e:
        st.error(f"Error clearing daily tracker: {str(e)}")
        return False

def add_to_favorites(food_data: Dict, user_id: int = 1) -> bool:
    """Add food to favorites"""
    try:
        db = get_db_session()
        
        # Check if already in favorites
        existing = db.query(FavoriteFood).filter(
            FavoriteFood.user_id == user_id,
            FavoriteFood.food_name == food_data['name']
        ).first()
        
        if existing:
            db.close()
            return False  # Already in favorites
        
        # Save food item first
        food_id = save_food_item(food_data)
        
        # Create favorite entry
        favorite = FavoriteFood(
            user_id=user_id,
            food_item_id=food_id,
            food_name=food_data['name'],
            sugar_g=food_data.get('sugar_g', 0),
            calories=food_data.get('calories', 0),
            food_data=json.dumps(food_data)
        )
        
        db.add(favorite)
        db.commit()
        db.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding to favorites: {str(e)}")
        return False

def get_favorites(user_id: int = 1) -> List[Dict]:
    """Get user's favorite foods"""
    try:
        db = get_db_session()
        
        favorites = db.query(FavoriteFood).filter(
            FavoriteFood.user_id == user_id
        ).order_by(FavoriteFood.added_at.desc()).all()
        
        result = []
        for fav in favorites:
            try:
                food_data = json.loads(fav.food_data)
                food_data['favorite_id'] = fav.id
                result.append(food_data)
            except json.JSONDecodeError:
                # Fallback for corrupted data
                result.append({
                    'favorite_id': fav.id,
                    'name': fav.food_name,
                    'sugar_g': fav.sugar_g,
                    'calories': fav.calories
                })
        
        db.close()
        return result
        
    except Exception as e:
        st.error(f"Error getting favorites: {str(e)}")
        return []

def remove_from_favorites(favorite_id: int) -> bool:
    """Remove food from favorites"""
    try:
        db = get_db_session()
        
        favorite = db.query(FavoriteFood).filter(FavoriteFood.id == favorite_id).first()
        if favorite:
            db.delete(favorite)
            db.commit()
            db.close()
            return True
        
        db.close()
        return False
        
    except Exception as e:
        st.error(f"Error removing from favorites: {str(e)}")
        return False

def clear_favorites(user_id: int = 1) -> bool:
    """Clear all favorites for a user"""
    try:
        db = get_db_session()
        
        db.query(FavoriteFood).filter(FavoriteFood.user_id == user_id).delete()
        db.commit()
        db.close()
        return True
        
    except Exception as e:
        st.error(f"Error clearing favorites: {str(e)}")
        return False

def save_daily_insight(date: str = None, user_id: int = 1) -> bool:
    """Save daily sugar insight summary"""
    try:
        db = get_db_session()
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get daily tracker data
        entries = db.query(DailyTracker).filter(
            DailyTracker.user_id == user_id,
            DailyTracker.date == date
        ).all()
        
        if not entries:
            db.close()
            return False
        
        # Calculate totals
        total_sugar = sum(entry.sugar_g for entry in entries)
        total_calories = sum(entry.calories for entry in entries)
        food_count = len(entries)
        exceeded_limit = total_sugar > 25.0  # WHO recommendation
        
        # Check if insight already exists
        existing = db.query(SugarInsight).filter(
            SugarInsight.user_id == user_id,
            SugarInsight.date == date
        ).first()
        
        if existing:
            # Update existing
            existing.total_sugar_g = total_sugar
            existing.total_calories = total_calories
            existing.food_count = food_count
            existing.exceeded_limit = exceeded_limit
        else:
            # Create new
            insight = SugarInsight(
                user_id=user_id,
                date=date,
                total_sugar_g=total_sugar,
                total_calories=total_calories,
                food_count=food_count,
                exceeded_limit=exceeded_limit
            )
            db.add(insight)
        
        db.commit()
        db.close()
        return True
        
    except Exception as e:
        st.error(f"Error saving daily insight: {str(e)}")
        return False

def get_weekly_insights(user_id: int = 1, days: int = 7) -> List[Dict]:
    """Get insights for the past N days"""
    try:
        db = get_db_session()
        
        insights = db.query(SugarInsight).filter(
            SugarInsight.user_id == user_id
        ).order_by(SugarInsight.date.desc()).limit(days).all()
        
        result = []
        for insight in insights:
            result.append({
                'date': insight.date,
                'total_sugar_g': insight.total_sugar_g,
                'total_calories': insight.total_calories,
                'food_count': insight.food_count,
                'exceeded_limit': insight.exceeded_limit
            })
        
        db.close()
        return result
        
    except Exception as e:
        st.error(f"Error getting weekly insights: {str(e)}")
        return []

def search_food_history(query: str, user_id: int = 1, limit: int = 10) -> List[Dict]:
    """Search previously tracked foods"""
    try:
        db = get_db_session()
        
        foods = db.query(FoodItem).filter(
            FoodItem.name.ilike(f'%{query}%')
        ).limit(limit).all()
        
        result = []
        for food in foods:
            result.append({
                'id': food.id,
                'name': food.name,
                'description': food.description,
                'sugar_g': food.sugar_g,
                'calories': food.calories,
                'carbs_g': food.carbs_g,
                'protein_g': food.protein_g,
                'fat_g': food.fat_g,
                'fiber_g': food.fiber_g,
                'sodium_mg': food.sodium_mg,
                'data_type': food.data_source,
                'fdc_id': food.external_id
            })
        
        db.close()
        return result
        
    except Exception as e:
        st.error(f"Error searching food history: {str(e)}")
        return []
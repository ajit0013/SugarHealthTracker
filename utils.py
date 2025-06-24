from typing import Tuple
import math

def sugar_to_teaspoons(sugar_grams: float) -> float:
    """
    Convert sugar content from grams to teaspoons
    
    Args:
        sugar_grams (float): Sugar content in grams
        
    Returns:
        float: Sugar content in teaspoons (1 teaspoon ≈ 4g sugar)
    """
    return sugar_grams / 4.0

def teaspoons_to_sugar(teaspoons: float) -> float:
    """
    Convert teaspoons to sugar content in grams
    
    Args:
        teaspoons (float): Number of teaspoons
        
    Returns:
        float: Sugar content in grams
    """
    return teaspoons * 4.0

def get_health_warning_color(sugar_content: float) -> Tuple[str, str, str]:
    """
    Determine health warning level and color based on sugar content
    
    Args:
        sugar_content (float): Sugar content in grams per 100g
        
    Returns:
        Tuple[str, str, str]: (warning_level, warning_text, color)
    """
    if sugar_content <= 5.0:
        return (
            "LOW SUGAR",
            "This food is low in sugar and is a good choice for a healthy diet.",
            "green"
        )
    elif sugar_content <= 15.0:
        return (
            "MODERATE SUGAR",
            "This food contains moderate amounts of sugar. Consume in moderation.",
            "yellow"
        )
    else:
        return (
            "HIGH SUGAR",
            "This food is high in sugar. Consider limiting your consumption.",
            "red"
        )

def calculate_daily_sugar_percentage(sugar_content: float, daily_limit: float = 25.0) -> float:
    """
    Calculate what percentage of daily sugar intake this food represents
    
    Args:
        sugar_content (float): Sugar content in grams
        daily_limit (float): Daily sugar limit in grams (default: WHO recommendation of 25g)
        
    Returns:
        float: Percentage of daily sugar intake
    """
    return (sugar_content / daily_limit) * 100

def format_nutrition_info(nutrition_data: dict) -> dict:
    """
    Format nutrition information for display
    
    Args:
        nutrition_data (dict): Raw nutrition data
        
    Returns:
        dict: Formatted nutrition data
    """
    formatted_data = {}
    
    # Round values to appropriate decimal places
    for key, value in nutrition_data.items():
        if isinstance(value, (int, float)):
            if key in ['calories']:
                formatted_data[key] = round(value, 0)
            elif key.endswith('_mg'):
                formatted_data[key] = round(value, 1)
            else:
                formatted_data[key] = round(value, 1)
        else:
            formatted_data[key] = value
    
    return formatted_data

def get_sugar_health_tips(sugar_content: float) -> list:
    """
    Get health tips based on sugar content
    
    Args:
        sugar_content (float): Sugar content in grams
        
    Returns:
        list: List of health tips
    """
    tips = []
    
    if sugar_content <= 5.0:
        tips.extend([
            "Great choice! This food is naturally low in sugar.",
            "You can enjoy this as part of a balanced diet.",
            "Consider pairing with protein for sustained energy."
        ])
    elif sugar_content <= 15.0:
        tips.extend([
            "Moderate sugar content - enjoy in reasonable portions.",
            "Consider the timing of consumption (e.g., before exercise).",
            "Balance with low-sugar foods throughout the day."
        ])
    else:
        tips.extend([
            "High sugar content - consider limiting portion size.",
            "Try to consume with fiber-rich foods to slow absorption.",
            "Consider this as an occasional treat rather than daily food.",
            "Look for lower-sugar alternatives when possible."
        ])
    
    return tips

def calculate_sugar_impact_score(sugar_content: float, portion_size: float = 100.0) -> dict:
    """
    Calculate a comprehensive sugar impact score
    
    Args:
        sugar_content (float): Sugar content in grams per 100g
        portion_size (float): Typical portion size in grams
        
    Returns:
        dict: Impact score and related information
    """
    # Calculate actual sugar in typical portion
    actual_sugar = (sugar_content / 100) * portion_size
    
    # Calculate teaspoons
    teaspoons = sugar_to_teaspoons(actual_sugar)
    
    # Calculate percentage of daily intake
    who_percentage = calculate_daily_sugar_percentage(actual_sugar, 25.0)
    ada_male_percentage = calculate_daily_sugar_percentage(actual_sugar, 36.0)
    ada_female_percentage = calculate_daily_sugar_percentage(actual_sugar, 25.0)
    
    # Determine impact level
    if actual_sugar <= 5.0:
        impact_level = "Low Impact"
        impact_score = 1
    elif actual_sugar <= 10.0:
        impact_level = "Moderate Impact"
        impact_score = 2
    elif actual_sugar <= 20.0:
        impact_level = "High Impact"
        impact_score = 3
    else:
        impact_level = "Very High Impact"
        impact_score = 4
    
    return {
        "actual_sugar_g": actual_sugar,
        "teaspoons": teaspoons,
        "who_daily_percentage": who_percentage,
        "ada_male_percentage": ada_male_percentage,
        "ada_female_percentage": ada_female_percentage,
        "impact_level": impact_level,
        "impact_score": impact_score,
        "portion_size": portion_size
    }

def validate_food_search_input(input_value: str) -> Tuple[bool, str]:
    """
    Validate food search input
    
    Args:
        input_value (str): User input for food search
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not input_value or not input_value.strip():
        return False, "Please enter a food name or barcode."
    
    if len(input_value.strip()) < 2:
        return False, "Please enter at least 2 characters."
    
    if len(input_value.strip()) > 100:
        return False, "Search term is too long. Please use fewer than 100 characters."
    
    return True, ""

def validate_barcode_input(barcode: str) -> Tuple[bool, str]:
    """
    Validate barcode input
    
    Args:
        barcode (str): Barcode input
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not barcode or not barcode.strip():
        return False, "Please enter a barcode number."
    
    # Remove any spaces or dashes
    clean_barcode = barcode.replace(" ", "").replace("-", "")
    
    # Check if it's all digits
    if not clean_barcode.isdigit():
        return False, "Barcode should contain only numbers."
    
    # Check length (typical barcodes are 8, 12, or 13 digits)
    if len(clean_barcode) not in [8, 12, 13, 14]:
        return False, "Barcode should be 8, 12, 13, or 14 digits long."
    
    return True, ""

def format_nutrient_display(nutrient_name: str, amount: float, unit: str) -> str:
    """
    Format nutrient information for display
    
    Args:
        nutrient_name (str): Name of the nutrient
        amount (float): Amount of the nutrient
        unit (str): Unit of measurement
        
    Returns:
        str: Formatted nutrient string
    """
    if amount == 0:
        return f"{nutrient_name}: Not available"
    
    if unit == "g":
        return f"{nutrient_name}: {amount:.1f}g"
    elif unit == "mg":
        if amount >= 1000:
            return f"{nutrient_name}: {amount/1000:.1f}g"
        else:
            return f"{nutrient_name}: {amount:.0f}mg"
    elif unit == "kcal":
        return f"{nutrient_name}: {amount:.0f} kcal"
    else:
        return f"{nutrient_name}: {amount:.1f} {unit}"

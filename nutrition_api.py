import requests
import os
from typing import List, Dict, Optional
import streamlit as st

class NutritionAPI:
    """
    Handles nutrition data retrieval from USDA FoodData Central API
    """
    
    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY", "DEMO_KEY")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        
    def search_food_by_name(self, food_name: str) -> List[Dict]:
        """
        Search for food items by name using USDA FoodData Central API
        
        Args:
            food_name (str): Name of the food to search for
            
        Returns:
            List[Dict]: List of food items with nutritional information
        """
        try:
            # Search for foods
            search_url = f"{self.base_url}/foods/search"
            search_params = {
                "api_key": self.api_key,
                "query": food_name,
                "dataType": ["Foundation", "SR Legacy"],
                "pageSize": 5,
                "sortBy": "dataType.keyword",
                "sortOrder": "asc"
            }
            
            response = requests.get(search_url, params=search_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                foods = data.get("foods", [])
                
                if not foods:
                    return []
                
                # Process the foods and extract nutrition data
                processed_foods = []
                for food in foods[:3]:  # Limit to top 3 results
                    nutrition_info = self._extract_nutrition_data(food)
                    if nutrition_info:
                        processed_foods.append(nutrition_info)
                
                return processed_foods
            
            elif response.status_code == 403:
                st.error("API access denied. Please check your API key configuration.")
                return []
            else:
                st.error(f"API request failed with status code: {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
            return []
        except requests.exceptions.ConnectionError:
            st.error("Unable to connect to the nutrition database. Please check your internet connection.")
            return []
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            return []
    
    def search_food_by_barcode(self, barcode: str) -> List[Dict]:
        """
        Search for food items by barcode using OpenFoodFacts API
        
        Args:
            barcode (str): Barcode number
            
        Returns:
            List[Dict]: List of food items matching the barcode
        """
        try:
            # Clean barcode (remove spaces and dashes)
            clean_barcode = barcode.replace(" ", "").replace("-", "")
            
            # OpenFoodFacts API URL
            off_url = f"https://world.openfoodfacts.org/api/v0/product/{clean_barcode}.json"
            
            response = requests.get(off_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if product was found
                if data.get("status") == 1 and "product" in data:
                    product = data["product"]
                    
                    # Extract product information
                    nutrition_info = self._extract_openfoodfacts_data(product)
                    if nutrition_info:
                        return [nutrition_info]
                    else:
                        return []
                else:
                    # Product not found in OpenFoodFacts
                    return []
            else:
                st.error(f"Failed to fetch barcode data. Status code: {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            st.error("Request timed out while searching barcode. Please try again.")
            return []
        except requests.exceptions.ConnectionError:
            st.error("Unable to connect to barcode database. Please check your internet connection.")
            return []
        except Exception as e:
            st.error(f"An error occurred while searching barcode: {str(e)}")
            return []
    
    def _extract_openfoodfacts_data(self, product_data: Dict) -> Optional[Dict]:
        """
        Extract relevant nutrition data from OpenFoodFacts product data
        
        Args:
            product_data (Dict): Raw product data from OpenFoodFacts API
            
        Returns:
            Optional[Dict]: Processed nutrition information
        """
        try:
            # Extract basic information
            food_info = {
                "name": product_data.get("product_name", "Unknown Product"),
                "description": product_data.get("brands", ""),
                "fdc_id": product_data.get("code", ""),
                "data_type": "OpenFoodFacts",
                "sugar_g": 0,
                "calories": 0,
                "carbs_g": 0,
                "protein_g": 0,
                "fat_g": 0,
                "fiber_g": 0,
                "sodium_mg": 0
            }
            
            # Get nutrition data per 100g
            nutriments = product_data.get("nutriments", {})
            
            # Extract nutrition values (OpenFoodFacts uses different keys)
            food_info["sugar_g"] = nutriments.get("sugars_100g", 0) or 0
            food_info["calories"] = nutriments.get("energy-kcal_100g", 0) or 0
            food_info["carbs_g"] = nutriments.get("carbohydrates_100g", 0) or 0
            food_info["protein_g"] = nutriments.get("proteins_100g", 0) or 0
            food_info["fat_g"] = nutriments.get("fat_100g", 0) or 0
            food_info["fiber_g"] = nutriments.get("fiber_100g", 0) or 0
            food_info["sodium_mg"] = (nutriments.get("sodium_100g", 0) or 0) * 1000  # Convert from g to mg
            
            # Add additional product information
            if product_data.get("brands"):
                food_info["description"] = f"{product_data.get('brands')} - {product_data.get('categories', '').split(',')[0] if product_data.get('categories') else ''}"
            
            return food_info
            
        except Exception as e:
            st.error(f"Error processing OpenFoodFacts data: {str(e)}")
            return None
    
    def _extract_nutrition_data(self, food_data: Dict) -> Optional[Dict]:
        """
        Extract relevant nutrition data from USDA food data
        
        Args:
            food_data (Dict): Raw food data from USDA API
            
        Returns:
            Optional[Dict]: Processed nutrition information
        """
        try:
            # Extract basic information
            food_info = {
                "name": food_data.get("description", "Unknown Food"),
                "description": food_data.get("additionalDescriptions", ""),
                "fdc_id": food_data.get("fdcId"),
                "data_type": food_data.get("dataType", ""),
                "sugar_g": 0,
                "calories": 0,
                "carbs_g": 0,
                "protein_g": 0,
                "fat_g": 0,
                "fiber_g": 0,
                "sodium_mg": 0
            }
            
            # Extract nutrition data from foodNutrients
            nutrients = food_data.get("foodNutrients", [])
            
            for nutrient in nutrients:
                nutrient_id = nutrient.get("nutrientId")
                nutrient_name = nutrient.get("nutrientName", "").lower()
                amount = nutrient.get("value", 0)
                
                # Map nutrient IDs to our fields (USDA nutrient IDs)
                if nutrient_id == 2000:  # Total Sugars
                    food_info["sugar_g"] = amount
                elif nutrient_id == 1008:  # Energy (calories)
                    food_info["calories"] = amount
                elif nutrient_id == 1005:  # Total Carbohydrates
                    food_info["carbs_g"] = amount
                elif nutrient_id == 1003:  # Protein
                    food_info["protein_g"] = amount
                elif nutrient_id == 1004:  # Total Fat
                    food_info["fat_g"] = amount
                elif nutrient_id == 1079:  # Fiber
                    food_info["fiber_g"] = amount
                elif nutrient_id == 1093:  # Sodium
                    food_info["sodium_mg"] = amount
                
                # Alternative matching by name if ID doesn't work
                elif "sugar" in nutrient_name and "total" in nutrient_name:
                    if food_info["sugar_g"] == 0:  # Only if not already set
                        food_info["sugar_g"] = amount
                elif "energy" in nutrient_name or "calorie" in nutrient_name:
                    if food_info["calories"] == 0:
                        food_info["calories"] = amount
                elif "carbohydrate" in nutrient_name and "total" in nutrient_name:
                    if food_info["carbs_g"] == 0:
                        food_info["carbs_g"] = amount
                elif "protein" in nutrient_name:
                    if food_info["protein_g"] == 0:
                        food_info["protein_g"] = amount
                elif "fat" in nutrient_name and ("total" in nutrient_name or "lipid" in nutrient_name):
                    if food_info["fat_g"] == 0:
                        food_info["fat_g"] = amount
                elif "fiber" in nutrient_name:
                    if food_info["fiber_g"] == 0:
                        food_info["fiber_g"] = amount
                elif "sodium" in nutrient_name:
                    if food_info["sodium_mg"] == 0:
                        food_info["sodium_mg"] = amount
            
            return food_info
            
        except Exception as e:
            st.error(f"Error processing nutrition data: {str(e)}")
            return None
    
    def get_detailed_food_info(self, fdc_id: int) -> Optional[Dict]:
        """
        Get detailed information for a specific food item
        
        Args:
            fdc_id (int): FDC ID of the food item
            
        Returns:
            Optional[Dict]: Detailed food information
        """
        try:
            detail_url = f"{self.base_url}/food/{fdc_id}"
            params = {"api_key": self.api_key}
            
            response = requests.get(detail_url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            st.error(f"Error fetching detailed food info: {str(e)}")
            return None

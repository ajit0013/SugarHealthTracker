import streamlit as st
import pandas as pd
import numpy as np
from nutrition_api import NutritionAPI
from utils import (
    sugar_to_teaspoons, get_health_warning_color, format_nutrition_info,
    calculate_daily_sugar_percentage, get_sugar_health_tips, 
    calculate_sugar_impact_score
)
import time
import plotly.express as px
import plotly.graph_objects as go
from database import (
    init_database, add_to_daily_tracker, get_daily_tracker, 
    remove_from_daily_tracker, clear_daily_tracker,
    add_to_favorites, get_favorites, remove_from_favorites, clear_favorites,
    save_daily_insight, get_weekly_insights, search_food_history
)
from datetime import datetime, timedelta

# Initialize the nutrition API
nutrition_api = NutritionAPI()

# Initialize database
if 'db_initialized' not in st.session_state:
    if init_database():
        st.session_state.db_initialized = True
    else:
        st.error("Failed to initialize database. Some features may not work.")
        st.session_state.db_initialized = False

# Page configuration
st.set_page_config(
    page_title="Sugar Checker App",
    page_icon="🍬",
    layout="wide"
)

# Title and description
st.title("🍬 Sugar Checker App")
st.markdown("**Check the sugar content in your food and get health warnings**")

# Add navigation tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Food Search", "📊 Daily Tracker", "⭐ Favorites", "📈 Sugar Insights"])

with tab1:

    # Create two columns for the main interface
    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("Search for Food")
        
        # Search method selection
        search_method = st.radio(
            "Choose search method:",
            ["Food Name Search", "Barcode Scanner"]
        )
        
        if search_method == "Food Name Search":
            food_name = st.text_input(
                "Enter food name:",
                placeholder="e.g., apple, coca cola, chocolate chip cookies"
            )
            search_button = st.button("🔍 Search Food", type="primary")
            
        else:  # Barcode Scanner
            st.info("📱 Real Barcode Scanner (OpenFoodFacts)")
            barcode = st.text_input(
                "Enter barcode number:",
                placeholder="e.g., 3017620422003, 7622210951965"
            )
            search_button = st.button("📊 Scan Barcode", type="primary")
            food_name = None

    with col2:
        st.subheader("Sugar Content Results")
        
        # Initialize session state for results
        if 'search_results' not in st.session_state:
            st.session_state.search_results = None
        if 'error_message' not in st.session_state:
            st.session_state.error_message = None

    # Handle search button click
    if search_button:
        with st.spinner("Searching nutrition database..."):
            try:
                if search_method == "Food Name Search" and food_name:
                    # Search by food name
                    results = nutrition_api.search_food_by_name(food_name.strip())
                    if results:
                        st.session_state.search_results = results
                        st.session_state.error_message = None
                    else:
                        st.session_state.search_results = None
                        st.session_state.error_message = f"No results found for '{food_name}'. Please try a different food name or check spelling."
                        
                elif search_method == "Barcode Scanner" and barcode:
                    # Search by barcode
                    results = nutrition_api.search_food_by_barcode(barcode.strip())
                    if results:
                        st.session_state.search_results = results
                        st.session_state.error_message = None
                    else:
                        st.session_state.search_results = None
                        st.session_state.error_message = f"No product found for barcode '{barcode}'. This could be due to the barcode not being in our database."
                else:
                    st.session_state.error_message = "Please enter a food name or barcode to search."
                    st.session_state.search_results = None
                    
            except Exception as e:
                st.session_state.error_message = f"An error occurred while searching: {str(e)}"
                st.session_state.search_results = None

    # Display results or error messages
    with col2:
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
            st.info("💡 **Tips for better results:**\n- Try simpler food names (e.g., 'apple' instead of 'red delicious apple')\n- Check spelling\n- Use common food names\n- For packaged foods, try brand names")
            
        elif st.session_state.search_results:
            results = st.session_state.search_results
            
            # Display multiple results if available
            for idx, food_item in enumerate(results):
                if idx > 0:
                    st.markdown("---")
                    
                # Food name and description
                st.markdown(f"### {food_item['name']}")
                if food_item.get('description'):
                    st.markdown(f"*{food_item['description']}*")
                
                # Sugar content section
                sugar_content = food_item.get('sugar_g', 0)
                
                # Create columns for sugar display and action buttons
                sugar_col1, sugar_col2, sugar_col3, action_col = st.columns([2, 2, 3, 2])
                
                with sugar_col1:
                    st.metric(
                        label="Sugar Content",
                        value=f"{sugar_content:.1f}g",
                        help="Sugar content per 100g of food"
                    )
                
                with sugar_col2:
                    teaspoons = sugar_to_teaspoons(sugar_content)
                    st.metric(
                        label="Teaspoons",
                        value=f"{teaspoons:.1f} tsp",
                        help="Equivalent teaspoons of sugar (1 tsp ≈ 4g)"
                    )
                
                with sugar_col3:
                    # Health warning with color coding
                    warning_level, warning_text, warning_color = get_health_warning_color(sugar_content)
                    
                    if warning_color == "red":
                        st.error(f"🔴 {warning_level}: {warning_text}")
                    elif warning_color == "yellow":
                        st.warning(f"🟡 {warning_level}: {warning_text}")
                    else:
                        st.success(f"🟢 {warning_level}: {warning_text}")
                
                with action_col:
                    # Action buttons
                    if st.button(f"⭐ Save", key=f"fav_{idx}"):
                        if st.session_state.db_initialized and add_to_favorites(food_item):
                            st.success("Added to favorites!")
                        else:
                            st.error("Failed to add to favorites!")
                    
                    portion_size = st.number_input(
                        "Portion (g)", 
                        min_value=1, 
                        max_value=1000, 
                        value=100, 
                        key=f"portion_{idx}"
                    )
                    
                    if st.button(f"➕ Track", key=f"track_{idx}"):
                        if st.session_state.db_initialized and add_to_daily_tracker(food_item, portion_size):
                            actual_sugar = (sugar_content / 100) * portion_size
                            st.success(f"Added {actual_sugar:.1f}g sugar to daily tracker!")
                            # Save daily insight
                            save_daily_insight()
                        else:
                            st.error("Failed to add to daily tracker!")
                
                # Sugar visualization chart
                if sugar_content > 0:
                    st.markdown("#### 📊 Sugar Comparison Chart")
                    
                    # Create comparison data
                    comparison_data = {
                        'Item': ['This Food', 'WHO Daily Limit', 'Apple (avg)', 'Coca Cola (avg)'],
                        'Sugar (g)': [sugar_content, 25, 10, 10.6],
                        'Color': ['#FF6B6B' if sugar_content > 15 else '#FFA726' if sugar_content > 5 else '#66BB6A',
                                '#E0E0E0', '#81C784', '#FF5722']
                    }
                    
                    fig = px.bar(
                        comparison_data, 
                        x='Item', 
                        y='Sugar (g)',
                        color='Color',
                        color_discrete_map={color: color for color in comparison_data['Color']},
                        title="Sugar Content Comparison (per 100g)"
                    )
                    fig.update_layout(showlegend=False, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Additional nutritional information
                st.markdown("#### 📊 Nutritional Information (per 100g)")
                
                nutrition_data = {
                    "Nutrient": [],
                    "Amount": [],
                    "Unit": []
                }
                
                # Add available nutrition data
                nutrition_fields = [
                    ("Calories", food_item.get('calories', 0), "kcal"),
                    ("Total Carbohydrates", food_item.get('carbs_g', 0), "g"),
                    ("Sugars", food_item.get('sugar_g', 0), "g"),
                    ("Protein", food_item.get('protein_g', 0), "g"),
                    ("Total Fat", food_item.get('fat_g', 0), "g"),
                    ("Fiber", food_item.get('fiber_g', 0), "g"),
                    ("Sodium", food_item.get('sodium_mg', 0), "mg")
                ]
                
                for nutrient, amount, unit in nutrition_fields:
                    if amount > 0:  # Only show nutrients with values
                        nutrition_data["Nutrient"].append(nutrient)
                        nutrition_data["Amount"].append(f"{amount:.1f}")
                        nutrition_data["Unit"].append(unit)
                
                if nutrition_data["Nutrient"]:
                    df = pd.DataFrame(nutrition_data)
                    st.dataframe(df, hide_index=True, use_container_width=True)
                
                # Health tips based on sugar content
                tips = get_sugar_health_tips(sugar_content)
                if tips:
                    st.markdown("#### 💡 Health Tips")
                    for tip in tips[:3]:  # Show top 3 tips
                        st.info(tip)
                
                # Daily sugar intake context
                st.markdown("#### 📈 Daily Sugar Context")
                daily_limit_who = 25  # WHO recommendation: 25g per day
                daily_limit_ada = 36  # ADA recommendation for men: 36g per day
                
                percentage_who = (sugar_content / daily_limit_who) * 100
                percentage_ada = (sugar_content / daily_limit_ada) * 100
                
                context_col1, context_col2 = st.columns(2)
                
                with context_col1:
                    st.info(f"**WHO Daily Limit (25g):**\n{percentage_who:.1f}% of daily recommendation")
                
                with context_col2:
                    st.info(f"**ADA Daily Limit (36g for men):**\n{percentage_ada:.1f}% of daily recommendation")
                
                # Break after first result for cleaner display
                if idx == 0 and len(results) > 1:
                    st.markdown("---")
                    st.markdown(f"*Showing 1 of {len(results)} results. Search again for different options.*")
                    break
        
        else:
            # Default state - show instructions
            st.info("👆 Enter a food name or barcode above to check its sugar content!")
            
            st.markdown("#### 🎯 How to use this app:")
            st.markdown("""
            1. **Food Name Search**: Enter any food name (e.g., "apple", "coca cola", "cookies")
            2. **Barcode Scanner**: Enter a product barcode number (uses OpenFoodFacts database)
            3. Get instant results with:
               - Sugar content in grams and teaspoons
               - Color-coded health warnings
               - Complete nutritional information
               - Daily intake context
            """)
            
            st.markdown("#### 🚦 Health Warning System:")
            st.success("🟢 **LOW SUGAR** (0-5g per 100g): Good choice!")
            st.warning("🟡 **MODERATE SUGAR** (5-15g per 100g): Consume in moderation")
            st.error("🔴 **HIGH SUGAR** (15g+ per 100g): Limit consumption")

# Daily Tracker Tab
with tab2:
    st.subheader("📊 Daily Sugar Tracker")
    
    # Date selector
    selected_date = st.date_input("Select Date", datetime.now())
    date_str = selected_date.strftime('%Y-%m-%d')
    
    # Get daily tracker data from database
    if st.session_state.db_initialized:
        daily_tracker_data = get_daily_tracker(date_str)
    else:
        daily_tracker_data = []
    
    # Display current daily total
    if daily_tracker_data:
        total_sugar = sum(item['sugar_g'] for item in daily_tracker_data)
        total_calories = sum(item['calories'] for item in daily_tracker_data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sugar", f"{total_sugar:.1f}g")
        with col2:
            st.metric("Teaspoons", f"{sugar_to_teaspoons(total_sugar):.1f} tsp")
        with col3:
            who_percentage = (total_sugar / 25) * 100
            st.metric("WHO Daily %", f"{who_percentage:.0f}%")
        with col4:
            st.metric("Total Calories", f"{total_calories:.0f} kcal")
        
        # Progress bar
        progress = min(total_sugar / 25, 1.0)
        st.progress(progress)
        
        if total_sugar > 25:
            st.error("You've exceeded the WHO daily sugar recommendation!")
        elif total_sugar > 20:
            st.warning("You're approaching your daily sugar limit!")
        else:
            st.success("Good job staying within healthy limits!")
        
        # Display tracked items
        st.markdown("### Today's Sugar Intake")
        
        for idx, item in enumerate(daily_tracker_data):
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
            
            with col1:
                st.write(f"**{item['name']}**")
            with col2:
                st.write(f"{item['sugar_g']:.1f}g sugar")
            with col3:
                st.write(f"{item['portion_g']}g portion")
            with col4:
                st.write(f"{item['time']}")
            with col5:
                if st.button("🗑️", key=f"remove_{item['id']}"):
                    if remove_from_daily_tracker(item['id']):
                        st.success("Removed from tracker!")
                        st.rerun()
        
        # Clear all button
        if st.button("🗑️ Clear All Today", type="secondary"):
            if clear_daily_tracker(date_str):
                st.success("Cleared all entries for today!")
                st.rerun()
        
        # Daily sugar chart
        if len(daily_tracker_data) > 1:
            chart_data = pd.DataFrame(daily_tracker_data)
            
            fig = px.pie(
                chart_data, 
                values='sugar_g', 
                names='name',
                title=f"Sugar Distribution for {selected_date.strftime('%B %d, %Y')}"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No items tracked for this date. Start by searching for foods and clicking the 'Track' button!")
    
    # Weekly insights
    if st.session_state.db_initialized:
        st.markdown("### 📈 Weekly Sugar Trends")
        weekly_data = get_weekly_insights(days=7)
        
        if weekly_data:
            df = pd.DataFrame(weekly_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Sugar trend chart
            fig = px.line(
                df, 
                x='date', 
                y='total_sugar_g',
                title="Daily Sugar Intake - Last 7 Days",
                markers=True
            )
            fig.add_hline(y=25, line_dash="dash", line_color="red", 
                         annotation_text="WHO Daily Limit (25g)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary stats
            avg_sugar = df['total_sugar_g'].mean()
            days_exceeded = df['exceeded_limit'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Weekly Average", f"{avg_sugar:.1f}g")
            with col2:
                st.metric("Days Over Limit", f"{days_exceeded}")
            with col3:
                compliance = ((7 - days_exceeded) / 7) * 100
                st.metric("Compliance Rate", f"{compliance:.0f}%")

# Favorites Tab
with tab3:
    st.subheader("⭐ Favorite Foods")
    
    # Get favorites from database
    if st.session_state.db_initialized:
        favorite_foods = get_favorites()
    else:
        favorite_foods = []
    
    if favorite_foods:
        for food in favorite_foods:
            with st.expander(f"{food['name']} - {food.get('sugar_g', 0):.1f}g sugar"):
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.write(f"**Sugar:** {food.get('sugar_g', 0):.1f}g per 100g")
                    st.write(f"**Calories:** {food.get('calories', 0):.0f} kcal")
                    
                with col2:
                    teaspoons = sugar_to_teaspoons(food.get('sugar_g', 0))
                    st.write(f"**Teaspoons:** {teaspoons:.1f} tsp")
                    warning_level, _, warning_color = get_health_warning_color(food.get('sugar_g', 0))
                    
                    if warning_color == "red":
                        st.error(f"🔴 {warning_level}")
                    elif warning_color == "yellow":
                        st.warning(f"🟡 {warning_level}")
                    else:
                        st.success(f"🟢 {warning_level}")
                
                with col3:
                    if st.button("🗑️ Remove", key=f"remove_fav_{food['favorite_id']}"):
                        if remove_from_favorites(food['favorite_id']):
                            st.success("Removed from favorites!")
                            st.rerun()
                
                with col4:
                    if st.button("➕ Track", key=f"track_fav_{food['favorite_id']}"):
                        if add_to_daily_tracker(food, 100):  # Default 100g portion
                            st.success("Added to daily tracker!")
                            save_daily_insight()
        
        # Clear all favorites
        if st.button("🗑️ Clear All Favorites", type="secondary"):
            if clear_favorites():
                st.success("Cleared all favorites!")
                st.rerun()
    
    else:
        st.info("No favorite foods saved yet. Search for foods and click the 'Save' button to add them here!")
    
    # Quick search in food history
    st.markdown("### 🔍 Search Food History")
    history_search = st.text_input("Search previously tracked foods:", placeholder="e.g., apple, bread, chocolate")
    
    if history_search and st.session_state.db_initialized:
        history_results = search_food_history(history_search)
        
        if history_results:
            st.markdown("**Previously Tracked Foods:**")
            for food in history_results[:5]:  # Show top 5 results
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{food['name']}**")
                    st.write(f"Sugar: {food['sugar_g']:.1f}g | Calories: {food['calories']:.0f}")
                
                with col2:
                    warning_level, _, warning_color = get_health_warning_color(food['sugar_g'])
                    if warning_color == "red":
                        st.error(f"🔴 {warning_level}")
                    elif warning_color == "yellow":
                        st.warning(f"🟡 {warning_level}")
                    else:
                        st.success(f"🟢 {warning_level}")
                
                with col3:
                    if st.button("➕ Track", key=f"track_hist_{food['id']}"):
                        if add_to_daily_tracker(food, 100):
                            st.success("Added to tracker!")
                            save_daily_insight()
        else:
            st.info("No matching foods found in your history.")

# Sugar Insights Tab
with tab4:
    st.subheader("📈 Sugar Insights & Analytics")
    
    # Educational content
    st.markdown("### 🧠 Understanding Sugar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Types of Sugar:**
        - **Natural sugars**: Found in fruits, vegetables, and dairy
        - **Added sugars**: Added during processing or preparation
        - **Free sugars**: Both added sugars and natural sugars in honey, syrups, and fruit juices
        """)
        
        st.markdown("""
        **Health Impact Levels:**
        - **0-5g per 100g**: Low sugar - minimal impact
        - **5-15g per 100g**: Moderate - watch portions
        - **15g+ per 100g**: High sugar - limit consumption
        """)
    
    with col2:
        st.markdown("""
        **Daily Recommendations:**
        - **WHO**: Max 25g (6 tsp) for adults
        - **AHA Men**: Max 36g (9 tsp)
        - **AHA Women**: Max 25g (6 tsp)
        - **Children**: Max 19g (5 tsp)
        """)
        
        st.markdown("""
        **Hidden Sugar Sources:**
        - Condiments and sauces
        - Breakfast cereals
        - Yogurt and smoothies
        - Processed snacks
        - Soft drinks and juices
        """)
    
    # Interactive sugar calculator
    st.markdown("### 🧮 Sugar Calculator")
    
    calc_col1, calc_col2 = st.columns(2)
    
    with calc_col1:
        st.markdown("**Convert Sugar Units:**")
        grams_input = st.number_input("Sugar in grams:", min_value=0.0, max_value=200.0, value=10.0, step=0.1)
        
        teaspoons_result = sugar_to_teaspoons(grams_input)
        who_percent = (grams_input / 25) * 100
        
        st.write(f"**{grams_input}g** = **{teaspoons_result:.1f} teaspoons**")
        st.write(f"**{who_percent:.1f}%** of WHO daily limit")
    
    with calc_col2:
        st.markdown("**Daily Limit Comparison:**")
        
        limits_data = {
            'Group': ['WHO Adult', 'AHA Men', 'AHA Women', 'Children'],
            'Daily Limit (g)': [25, 36, 25, 19],
            'Teaspoons': [6.25, 9, 6.25, 4.75]
        }
        
        limits_df = pd.DataFrame(limits_data)
        fig = px.bar(
            limits_df, 
            x='Group', 
            y='Daily Limit (g)',
            title="Daily Sugar Limits by Group",
            color='Daily Limit (g)',
            color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Advanced analytics (if data available)
    if st.session_state.db_initialized:
        weekly_insights = get_weekly_insights(days=30)  # Last 30 days
        
        if weekly_insights:
            st.markdown("### 📊 Monthly Sugar Analysis")
            
            df = pd.DataFrame(weekly_insights)
            df['date'] = pd.to_datetime(df['date'])
            
            # Today's analysis
            today_data = get_daily_tracker()
            if today_data:
                total_daily_sugar = sum(item['sugar_g'] for item in today_data)
                
                # Create impact score visualization
                impact_data = calculate_sugar_impact_score(total_daily_sugar, 100)
                
                impact_col1, impact_col2 = st.columns(2)
                
                with impact_col1:
                    st.markdown("**Today's Impact Score:**")
                    
                    score_colors = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}
                    score_color = score_colors.get(impact_data['impact_score'], "🔴")
                    
                    st.markdown(f"## {score_color} {impact_data['impact_level']}")
                    st.write(f"**Total Sugar:** {total_daily_sugar:.1f}g")
                    st.write(f"**WHO Percentage:** {impact_data['who_daily_percentage']:.1f}%")
                
                with impact_col2:
                    st.markdown("**Recommendations:**")
                    tips = get_sugar_health_tips(total_daily_sugar)
                    for tip in tips[:2]:
                        st.info(tip)
            
            # Monthly trends
            st.markdown("### 📈 Monthly Trends")
            
            # Calculate statistics
            avg_sugar = df['total_sugar_g'].mean()
            max_sugar = df['total_sugar_g'].max()
            days_exceeded = df['exceeded_limit'].sum()
            total_days = len(df)
            
            trend_col1, trend_col2, trend_col3, trend_col4 = st.columns(4)
            
            with trend_col1:
                st.metric("Average Daily Sugar", f"{avg_sugar:.1f}g")
            with trend_col2:
                st.metric("Highest Day", f"{max_sugar:.1f}g")
            with trend_col3:
                st.metric("Days Over Limit", f"{days_exceeded}/{total_days}")
            with trend_col4:
                compliance = ((total_days - days_exceeded) / total_days) * 100
                st.metric("Compliance Rate", f"{compliance:.0f}%")
            
            # Monthly chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['total_sugar_g'],
                mode='lines+markers',
                name='Daily Sugar Intake',
                line=dict(color='blue')
            ))
            fig.add_hline(y=25, line_dash="dash", line_color="red", 
                         annotation_text="WHO Daily Limit (25g)")
            fig.update_layout(
                title="30-Day Sugar Intake Trend",
                xaxis_title="Date",
                yaxis_title="Sugar Intake (g)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

# Sidebar with additional information
with st.sidebar:
    st.markdown("## 📚 Sugar Facts")
    
    st.markdown("### 🥄 Sugar Conversion")
    st.markdown("- 1 teaspoon = ~4 grams of sugar")
    st.markdown("- 1 tablespoon = ~12 grams of sugar")
    st.markdown("- 1 cup = ~200 grams of sugar")
    
    st.markdown("### 🏥 Health Guidelines")
    st.markdown("**WHO Recommendation:**")
    st.markdown("- Adults: Maximum 25g (6 tsp) per day")
    st.markdown("- Children: Maximum 19g (5 tsp) per day")
    
    st.markdown("**American Heart Association:**")
    st.markdown("- Men: Maximum 36g (9 tsp) per day")
    st.markdown("- Women: Maximum 25g (6 tsp) per day")
    
    st.markdown("### ⚠️ Hidden Sugar Sources")
    st.markdown("""
    - Condiments and sauces
    - Breakfast cereals
    - Yogurt and smoothies
    - Processed snacks
    - Soft drinks and juices
    """)
    
    st.markdown("---")
    st.markdown("*Data sourced from USDA FoodData Central*")

# Footer with example barcodes
st.markdown("---")
st.markdown("#### 📊 Example Barcodes to Try:")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **Popular Products:**
    - `3017620422003` - Nutella
    - `7622210951965` - Toblerone
    - `3017624010701` - Smarties
    """)

with col2:
    st.markdown("""
    **Beverages:**
    - `5449000000996` - Coca-Cola
    - `4902102072453` - Kit Kat
    - `3228857000906` - Red Bull
    """)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "This app helps you make informed decisions about sugar consumption. "
    "Always consult healthcare professionals for personalized dietary advice."
    "</div>",
    unsafe_allow_html=True
)

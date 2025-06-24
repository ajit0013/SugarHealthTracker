# Sugar Checker App

## Overview

The Sugar Checker App is a Streamlit-based web application designed to help users check the sugar content in various foods and receive health warnings based on nutritional information. The app provides two primary search methods: searching by food name and barcode scanning (mock implementation). It integrates with the USDA FoodData Central API to retrieve accurate nutritional data and presents sugar content in an easy-to-understand format with visual health indicators.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for rapid web application development
- **UI Components**: Multi-tab interface with Food Search, Daily Tracker, Favorites, and Sugar Insights
- **Interactive Elements**: Radio buttons, text inputs, date selectors, charts, and action buttons
- **Visualization**: Health warning colors, Plotly charts, progress bars, and trend analysis

### Backend Architecture
- **API Integration**: USDA FoodData Central API and OpenFoodFacts API for nutritional data
- **Database Layer**: PostgreSQL with SQLAlchemy ORM for persistent data storage
- **Data Processing**: Custom utility functions for sugar content conversion and health assessment
- **Error Handling**: Built-in timeout, response validation, and database transaction management

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Primary Streamlit application entry point with multi-tab interface
- **Features**: 
  - Food search with real-time API integration
  - Daily sugar tracking with database persistence
  - Favorites management system
  - Advanced analytics and insights dashboard
- **Architecture Decision**: Tab-based UI for organized feature separation

### 2. Nutrition API Handler (`nutrition_api.py`)
- **Purpose**: Manages interactions with USDA FoodData Central and OpenFoodFacts APIs
- **Features**:
  - Food search by name functionality
  - Real barcode scanning via OpenFoodFacts
  - API response processing and data extraction
  - Error handling for API failures
- **Architecture Decision**: Separate API class for modularity and easier testing

### 3. Database Layer (`database.py`)
- **Purpose**: Complete database operations and data persistence
- **Features**:
  - SQLAlchemy models for all data entities
  - CRUD operations for tracking, favorites, and insights
  - Historical data analysis and search functionality
  - Automatic daily insight generation
- **Architecture Decision**: Separate database module for clean data layer separation

### 4. Utility Functions (`utils.py`)
- **Purpose**: Common helper functions for data processing and health analysis
- **Features**:
  - Sugar content conversion and health assessments
  - Impact scoring and recommendation generation
  - Data formatting and validation
- **Architecture Decision**: Utility module promotes code reusability and separation of concerns

### 5. Configuration Files
- **Streamlit Config**: Server configuration for headless deployment
- **Replit Config**: Deployment and workflow configuration
- **Dependencies**: Managed via pyproject.toml with uv lock file

## Data Flow

1. **User Input**: User enters food name or barcode through Streamlit interface
2. **API Request**: Application sends request to USDA FoodData Central API
3. **Data Processing**: Raw API response is processed to extract nutritional information
4. **Sugar Analysis**: Sugar content is converted to teaspoons and health warnings are generated
5. **Display**: Processed information is presented to user with visual indicators

## External Dependencies

### Primary Dependencies
- **Streamlit**: Web application framework for user interface
- **Requests**: HTTP library for API communication
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing support
- **Plotly**: Interactive data visualization and charts
- **Matplotlib**: Static plotting and visualization
- **Seaborn**: Statistical data visualization
- **SQLAlchemy**: Database ORM for PostgreSQL integration
- **psycopg2-binary**: PostgreSQL database adapter

### External APIs
- **USDA FoodData Central API**: Primary source for nutritional data
  - API Key: Configurable via environment variable (defaults to DEMO_KEY)
  - Rate Limits: Handled through result limiting and timeout implementation
  - Fallback: Error handling for API unavailability
- **OpenFoodFacts API**: Real barcode scanning and product database
  - Public API with no authentication required
  - Global product database with nutritional information
  - Used for barcode-to-product lookup functionality

## Deployment Strategy

### Replit Deployment
- **Target**: Autoscale deployment on Replit platform
- **Runtime**: Python 3.11 environment
- **Port Configuration**: Application runs on port 5000
- **Process Management**: Streamlit server with headless configuration

### Environment Configuration
- **Nix Channel**: Stable 24.05 for consistent environment
- **Module System**: Python 3.11 module for runtime
- **Server Settings**: Configured for headless operation with specific address binding

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- June 22, 2025: Initial setup with basic food search and barcode functionality
- June 22, 2025: Upgraded barcode scanner to use real OpenFoodFacts API instead of mock data
- June 22, 2025: Added comprehensive feature enhancements:
  - Multi-tab interface with Food Search, Daily Tracker, Favorites, and Sugar Insights
  - Interactive daily sugar tracking with progress visualization
  - Favorites system for saving frequently checked foods
  - Enhanced sugar comparison charts using Plotly
  - Personalized health tips based on sugar content
  - Educational content and sugar calculator
  - Portion size tracking and adjustment
  - Real-time daily sugar limit monitoring
- June 22, 2025: Integrated PostgreSQL database for persistent data storage:
  - Database models for users, food items, daily tracking, favorites, and insights
  - Persistent daily sugar tracking across sessions
  - Historical data analysis with weekly and monthly trends
  - Food history search functionality
  - Automatic daily insight generation and storage

## Technical Notes

### Architecture Decisions Rationale

1. **Streamlit Selection**: Chosen for rapid development and built-in web interface capabilities, eliminating need for separate frontend framework
2. **USDA API Integration**: Selected for reliable, government-maintained nutritional data with comprehensive food database
3. **Modular Structure**: Separate modules for API handling and utilities to improve maintainability and testing
4. **Sugar-to-Teaspoons Conversion**: Implemented to provide intuitive understanding of sugar content for average users
5. **Health Warning System**: Color-coded system based on established nutritional guidelines for immediate visual feedback

### Potential Enhancements
- Database integration for caching frequently searched foods
- User authentication for personalized tracking
- Enhanced barcode scanning with actual camera integration
- Nutritional goal setting and tracking features
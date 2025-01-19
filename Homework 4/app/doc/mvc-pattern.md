Model-View-Controller (MVC) Pattern

Overview
MVC is an architectural pattern that separates an application into three main logical components:
- Model (Data handling)
- View (User interface)
- Controller (Business logic)

Implementation Details

Model (`data_model.py`)
class DataModel:
    def __init__(self):
        self.db = DatabaseFactory.get_database("sqlite", "updated_stocks_database.db")
    
    def fetch_stock_data_from_db(self, issuer, from_date, to_date):
        # Data access logic
        pass

    def calculate_rsi_signals(self, data):
        # Business calculations
        pass
```

View (`frontend-graph.html`)
- Handles the presentation layer
- Displays stock data and RSI signals
- Provides user interface for data interaction

Controller (`controller.py`)
```python
class DataController:
    def __init__(self):
        self.model = DataModel()

    def get_rsi_signals(self, request):
        # Request handling and response formatting
        pass

    def get_stock_data(self, request):
        # Coordinate model and view interactions
        pass
```

Benefits of MVC
1. Separation of Concerns
   - Clear distinction between data, presentation, and logic
   - Each component can be modified independently
   - Easier to maintain and test

2. Code Organization
   - Structured project layout
   - Clear responsibilities for each component
   - Reduced code duplication

3. **Maintainability**
   - Changes to one component don't affect others
   - Easier to identify and fix bugs
   - Simpler to add new features


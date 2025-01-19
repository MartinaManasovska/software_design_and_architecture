from abc import ABC, abstractmethod
import sqlite3
import pandas as pd

class DatabaseConnection(ABC):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def disconnect(self):
        pass

class SQLiteConnection(DatabaseConnection):
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None
    
    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.connection.row_factory = sqlite3.Row
            return self.connection
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def disconnect(self):
        if self.connection:
            self.connection.close()

class DatabaseFactory:
    @staticmethod
    def get_database(db_type, db_name):
        if db_type.lower() == "sqlite":
            return SQLiteConnection(db_name)
        raise ValueError(f"Unsupported database type: {db_type}")

"""
Simplified Database Module for Standalone Chatbot

This provides mock database functionality for testing without requiring a real database.
"""

from typing import Generator
from sqlalchemy.orm import Session

# Mock database session
class MockDatabaseSession:
    def __init__(self):
        self.chats = {}
        self.messages = {}
        self._counter = 0
    
    def add(self, obj):
        """Mock add method"""
        pass
    
    def commit(self):
        """Mock commit method"""
        pass
    
    def refresh(self, obj):
        """Mock refresh method"""
        pass
    
    def query(self, model_class):
        """Mock query method"""
        return MockQuery(self)
    
    def delete(self, obj):
        """Mock delete method"""
        pass

class MockQuery:
    def __init__(self, session):
        self.session = session
        self._filters = []
    
    def filter(self, *args):
        """Mock filter method"""
        self._filters.extend(args)
        return self
    
    def first(self):
        """Mock first method"""
        return None
    
    def all(self):
        """Mock all method"""
        return []

def get_mock_db() -> Generator[Session, None, None]:
    """Dependency to get mock database session"""
    db = MockDatabaseSession()
    try:
        yield db
    finally:
        pass

# For compatibility with original code
get_patient_db = get_mock_db 
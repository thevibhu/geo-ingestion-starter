import sys
import os
sys.path.append('/app')

import uuid
from unittest.mock import Mock
import service

def test_create_feature_returns_uuid():
    """Test that create_feature returns a valid UUID"""
    mock_db = Mock()
    
    result = service.create_feature(mock_db, "Test Site", 45.5, -73.6)
    
    assert isinstance(result, uuid.UUID)
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

def test_invalid_uuid_returns_false():
    """Test that invalid UUID returns False"""
    mock_db = Mock()
    
    result = service.process_feature(mock_db, "not-a-uuid")
    
    assert result is False
    mock_db.execute.assert_not_called()
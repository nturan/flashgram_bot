"""Simplified tests for bulk processing tools."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.tools.bulk_processing import (
    process_bulk_text_for_flashcards_impl,
    check_bulk_processing_status_impl
)


class TestBulkProcessingSimple:
    """Simplified test cases for bulk text processing functionality."""

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_success(self, mock_bulk_processor):
        """Test successful bulk text processing initiation."""
        mock_job_id = "job_12345"
        mock_job_status = {
            "job_id": mock_job_id,
            "status": "pending",
            "total_words": 50,
            "processed_words": 0
        }
        
        mock_bulk_processor.start_bulk_processing.return_value = mock_job_id
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = process_bulk_text_for_flashcards_impl(
            "Это большой текст для обработки",
            user_id=123
        )
        
        assert result["success"] is True
        assert result["job_id"] == "job_12345"
        assert result["total_words"] == 50

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_error(self, mock_bulk_processor):
        """Test error handling in bulk text processing."""
        mock_bulk_processor.start_bulk_processing.side_effect = Exception("Processing start failed")
        
        result = process_bulk_text_for_flashcards_impl("test text", user_id=123)
        
        assert result["success"] is False
        assert "error" in result

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_success(self, mock_bulk_processor):
        """Test successful bulk processing status check."""
        mock_job_status = {
            "job_id": "job_12345",
            "status": "processing",
            "total_words": 100,
            "processed_words": 45
        }
        
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = check_bulk_processing_status_impl(job_id="job_12345")
        
        assert result["success"] is True
        assert result["job"]["status"] == "processing"
        assert result["job"]["processed_words"] == 45

    def test_check_bulk_processing_status_no_parameters(self):
        """Test status check without providing parameters."""
        result = check_bulk_processing_status_impl()
        
        assert result["success"] is False
        assert "Please provide either job_id or user_id" in result["error"]

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_error(self, mock_bulk_processor):
        """Test error handling in status checking."""
        mock_bulk_processor.get_job_status.side_effect = Exception("Database connection failed")
        
        result = check_bulk_processing_status_impl(job_id="test_job")
        
        assert result["success"] is False
        assert "error" in result
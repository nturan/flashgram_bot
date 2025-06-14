"""Tests for bulk processing tools."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.tools.bulk_processing import (
    process_bulk_text_for_flashcards_impl,
    check_bulk_processing_status_impl
)


class TestBulkProcessing:
    """Test cases for bulk text processing functionality."""

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_for_flashcards_success(self, mock_bulk_processor):
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
            "Это большой текст для обработки с множеством русских слов.",
            user_id=123
        )
        
        assert result["success"] is True
        assert result["job_id"] == mock_job_id
        assert result["status"] == "started"
        assert result["total_words"] == 50
        assert "Started processing text with 50 Russian words" in result["message"]
        
        mock_bulk_processor.start_bulk_processing.assert_called_once_with(
            "Это большой текст для обработки с множеством русских слов.", 123
        )
        mock_bulk_processor.get_job_status.assert_called_once_with(mock_job_id)

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_for_flashcards_default_user_id(self, mock_bulk_processor):
        """Test bulk processing with default user_id when none provided."""
        mock_job_id = "job_67890"
        mock_job_status = {"job_id": mock_job_id, "total_words": 25}
        
        mock_bulk_processor.start_bulk_processing.return_value = mock_job_id
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = process_bulk_text_for_flashcards_impl(
            "Текст без user_id"
        )
        
        assert result["success"] is True
        assert result["job_id"] == mock_job_id
        
        # Should use default user_id of 0
        mock_bulk_processor.start_bulk_processing.assert_called_once_with(
            "Текст без user_id", 0
        )

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_for_flashcards_no_job_status(self, mock_bulk_processor):
        """Test bulk processing when job status is not available."""
        mock_job_id = "job_11111"
        
        mock_bulk_processor.start_bulk_processing.return_value = mock_job_id
        mock_bulk_processor.get_job_status.return_value = None
        
        result = process_bulk_text_for_flashcards_impl(
            "Текст для обработки",
            user_id=456
        )
        
        assert result["success"] is True
        assert result["job_id"] == mock_job_id
        assert result["total_words"] == 0
        assert "Started processing text with 0 Russian words" in result["message"]

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_for_flashcards_start_processing_error(self, mock_bulk_processor):
        """Test error handling when starting bulk processing fails."""
        mock_bulk_processor.start_bulk_processing.side_effect = Exception("Processing start failed")
        
        result = process_bulk_text_for_flashcards_impl(
            "Текст для тестирования ошибки",
            user_id=789
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "Processing start failed" in result["error"]

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_for_flashcards_empty_text(self, mock_bulk_processor):
        """Test bulk processing with empty text."""
        mock_job_id = "job_empty"
        mock_job_status = {"job_id": mock_job_id, "total_words": 0}
        
        mock_bulk_processor.start_bulk_processing.return_value = mock_job_id
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = process_bulk_text_for_flashcards_impl("", user_id=100)
        
        assert result["success"] is True
        assert result["total_words"] == 0

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_by_job_id(self, mock_bulk_processor):
        """Test checking bulk processing status by job ID."""
        mock_job_id = "job_status_test"
        mock_job_status = {
            "job_id": mock_job_id,
            "status": "processing",
            "total_words": 100,
            "processed_words": 45,
            "generated_flashcards": 120
        }
        
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = check_bulk_processing_status_impl(job_id=mock_job_id)
        
        assert result["success"] is True
        assert result["job"] == mock_job_status
        assert result["job"]["status"] == "processing"
        assert result["job"]["processed_words"] == 45
        
        mock_bulk_processor.get_job_status.assert_called_once_with(mock_job_id)

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_job_not_found(self, mock_bulk_processor):
        """Test checking status for non-existent job ID."""
        mock_job_id = "nonexistent_job"
        
        mock_bulk_processor.get_job_status.return_value = None
        
        result = check_bulk_processing_status_impl(job_id=mock_job_id)
        
        assert result["success"] is False
        assert "error" in result
        assert f"Job {mock_job_id} not found" in result["error"]

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_by_user_id(self, mock_bulk_processor):
        """Test checking bulk processing status by user ID."""
        user_id = 456
        mock_user_jobs = [
            {
                "job_id": "job1",
                "status": "completed",
                "total_words": 50,
                "generated_flashcards": 75
            },
            {
                "job_id": "job2",
                "status": "processing", 
                "total_words": 30,
                "processed_words": 15
            }
        ]
        
        mock_bulk_processor.get_user_jobs.return_value = mock_user_jobs
        
        result = check_bulk_processing_status_impl(user_id=user_id)
        
        assert result["success"] is True
        assert result["jobs"] == mock_user_jobs
        assert result["total_jobs"] == 2
        assert len(result["jobs"]) == 2
        
        mock_bulk_processor.get_user_jobs.assert_called_once_with(user_id)

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_user_no_jobs(self, mock_bulk_processor):
        """Test checking status for user with no jobs."""
        user_id = 999
        
        mock_bulk_processor.get_user_jobs.return_value = []
        
        result = check_bulk_processing_status_impl(user_id=user_id)
        
        assert result["success"] is True
        assert result["jobs"] == []
        assert result["total_jobs"] == 0

    def test_check_bulk_processing_status_no_parameters(self):
        """Test checking status without providing job_id or user_id."""
        result = check_bulk_processing_status_impl()
        
        assert result["success"] is False
        assert "error" in result
        assert "Please provide either job_id or user_id" in result["error"]

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_exception(self, mock_bulk_processor):
        """Test error handling in status checking."""
        mock_bulk_processor.get_job_status.side_effect = Exception("Database connection failed")
        
        result = check_bulk_processing_status_impl(job_id="test_job")
        
        assert result["success"] is False
        assert "error" in result
        assert "Database connection failed" in result["error"]

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_user_jobs_exception(self, mock_bulk_processor):
        """Test error handling when getting user jobs fails."""
        mock_bulk_processor.get_user_jobs.side_effect = Exception("User lookup failed")
        
        result = check_bulk_processing_status_impl(user_id=123)
        
        assert result["success"] is False
        assert "error" in result
        assert "User lookup failed" in result["error"]

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_very_long_text(self, mock_bulk_processor):
        """Test bulk processing with very long text."""
        long_text = "Это очень длинный текст для обработки. " * 1000
        mock_job_id = "job_long_text"
        mock_job_status = {"job_id": mock_job_id, "total_words": 4000}
        
        mock_bulk_processor.start_bulk_processing.return_value = mock_job_id
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = process_bulk_text_for_flashcards_impl(long_text, user_id=200)
        
        assert result["success"] is True
        assert result["total_words"] == 4000
        assert "4000 Russian words" in result["message"]

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_special_characters(self, mock_bulk_processor):
        """Test bulk processing with text containing special characters."""
        text_with_special = "Текст с символами: №1, 50%, email@example.com, https://site.ru"
        mock_job_id = "job_special"
        mock_job_status = {"job_id": mock_job_id, "total_words": 5}
        
        mock_bulk_processor.start_bulk_processing.return_value = mock_job_id
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = process_bulk_text_for_flashcards_impl(text_with_special, user_id=300)
        
        assert result["success"] is True
        assert result["job_id"] == mock_job_id

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_completed_job(self, mock_bulk_processor):
        """Test checking status of a completed job."""
        mock_job_status = {
            "job_id": "completed_job",
            "status": "completed",
            "total_words": 80,
            "processed_words": 80,
            "generated_flashcards": 200,
            "completion_time": "2024-01-15T10:30:00Z"
        }
        
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = check_bulk_processing_status_impl(job_id="completed_job")
        
        assert result["success"] is True
        assert result["job"]["status"] == "completed"
        assert result["job"]["processed_words"] == 80
        assert result["job"]["generated_flashcards"] == 200

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_failed_job(self, mock_bulk_processor):
        """Test checking status of a failed job."""
        mock_job_status = {
            "job_id": "failed_job",
            "status": "failed",
            "total_words": 60,
            "processed_words": 25,
            "error_message": "LLM API rate limit exceeded"
        }
        
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = check_bulk_processing_status_impl(job_id="failed_job")
        
        assert result["success"] is True
        assert result["job"]["status"] == "failed"
        assert result["job"]["error_message"] == "LLM API rate limit exceeded"

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_process_bulk_text_unicode_text(self, mock_bulk_processor):
        """Test bulk processing with Unicode text including emojis."""
        unicode_text = "Привет! 👋 Как дела? 😊 Изучаем русский язык! 📚"
        mock_job_id = "job_unicode"
        mock_job_status = {"job_id": mock_job_id, "total_words": 6}
        
        mock_bulk_processor.start_bulk_processing.return_value = mock_job_id
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = process_bulk_text_for_flashcards_impl(unicode_text, user_id=400)
        
        assert result["success"] is True
        assert result["job_id"] == mock_job_id
        assert result["total_words"] == 6

    @patch('app.my_graph.bulk_text_processor.bulk_processor')
    def test_check_bulk_processing_status_both_parameters(self, mock_bulk_processor):
        """Test checking status when both job_id and user_id are provided (should prioritize job_id)."""
        mock_job_status = {
            "job_id": "priority_job",
            "status": "processing",
            "total_words": 40
        }
        
        mock_bulk_processor.get_job_status.return_value = mock_job_status
        
        result = check_bulk_processing_status_impl(job_id="priority_job", user_id=500)
        
        assert result["success"] is True
        assert result["job"]["job_id"] == "priority_job"
        
        # Should have called get_job_status but not get_user_jobs
        mock_bulk_processor.get_job_status.assert_called_once_with("priority_job")
        mock_bulk_processor.get_user_jobs.assert_not_called()
"""Bulk text processing tool implementations."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def process_bulk_text_for_flashcards_impl(
    text: str, user_id: Optional[int] = None
) -> Dict[str, Any]:
    """Implementation for bulk text processing tool."""
    try:
        # Import here to avoid circular import
        from app.my_graph.bulk_text_processor import bulk_processor

        # Use a default user_id if not provided (for testing)
        if user_id is None:
            user_id = 0

        # Start bulk processing
        job_id = bulk_processor.start_bulk_processing(text, user_id)

        # Get initial job status
        job_status = bulk_processor.get_job_status(job_id)

        return {
            "job_id": job_id,
            "status": "started",
            "total_words": job_status["total_words"] if job_status else 0,
            "message": f"Started processing text with {job_status['total_words'] if job_status else 0} Russian words. This will run in the background.",
            "success": True,
        }

    except Exception as e:
        logger.error(f"Error starting bulk text processing: {e}")
        return {"error": str(e), "success": False}


def check_bulk_processing_status_impl(
    job_id: Optional[str] = None, user_id: Optional[int] = None
) -> Dict[str, Any]:
    """Implementation for bulk processing status check tool."""
    try:
        # Import here to avoid circular import
        from app.my_graph.bulk_text_processor import bulk_processor

        if job_id:
            # Check specific job
            job_status = bulk_processor.get_job_status(job_id)
            if not job_status:
                return {"error": f"Job {job_id} not found", "success": False}
            return {"job": job_status, "success": True}

        elif user_id:
            # Get all jobs for user
            user_jobs = bulk_processor.get_user_jobs(user_id)
            return {"jobs": user_jobs, "total_jobs": len(user_jobs), "success": True}

        else:
            return {
                "error": "Please provide either job_id or user_id",
                "success": False,
            }

    except Exception as e:
        logger.error(f"Error checking bulk processing status: {e}")
        return {"error": str(e), "success": False}
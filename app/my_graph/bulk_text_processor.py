"""Asynchronous bulk text processing for generating flashcards from large texts."""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.config import settings
from app.my_graph.tools import (
    analyze_russian_grammar_impl,
    generate_flashcards_from_analysis_impl,
)

logger = logging.getLogger(__name__)


class BulkProcessingJob:
    """Represents a bulk processing job with status tracking."""

    def __init__(self, job_id: str, text: str, user_id: int, total_words: int = 0):
        self.job_id = job_id
        self.text = text
        self.user_id = user_id
        self.total_words = total_words
        self.processed_words = 0
        self.generated_flashcards = 0
        self.status = "pending"  # pending, processing, completed, failed
        self.error_message = None
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.failed_words = []
        self.processed_word_types = {}


class BulkTextProcessor:
    """Handles asynchronous bulk processing of Russian text for flashcard generation."""

    def __init__(self):
        self.active_jobs: Dict[str, BulkProcessingJob] = {}
        self.completed_jobs: Dict[str, BulkProcessingJob] = {}

    def extract_russian_words(self, text: str) -> List[str]:
        """Extract Russian words from text, filtering out common words and non-Russian text."""
        # Define Russian alphabet pattern
        russian_pattern = r"[а-яё]+[а-яёъь-]*[а-яё]|[а-яё]"

        # Extract Russian words
        russian_words = re.findall(russian_pattern, text.lower())

        # Filter out common words and very short words
        filtered_words = []
        seen_words = set()

        for word in russian_words:
            if len(word) >= 3 and word not in seen_words:
                filtered_words.append(word)
                seen_words.add(word)

        return filtered_words

    def start_bulk_processing(self, text: str, user_id: int) -> str:
        """Start a bulk processing job and return the job ID."""
        job_id = str(uuid.uuid4())

        # Extract Russian words
        russian_words = self.extract_russian_words(text)

        # Create job
        job = BulkProcessingJob(
            job_id=job_id, text=text, user_id=user_id, total_words=len(russian_words)
        )

        self.active_jobs[job_id] = job

        # Start processing asynchronously
        asyncio.create_task(self._process_job_async(job, russian_words))

        logger.info(
            f"Started bulk processing job {job_id} for user {user_id} with {len(russian_words)} words"
        )

        return job_id

    async def _process_job_async(self, job: BulkProcessingJob, words: List[str]):
        """Process a job asynchronously."""
        try:
            job.status = "processing"
            total_flashcards = 0

            # Process words in small batches to avoid overwhelming the system
            batch_size = 3
            for i in range(0, len(words), batch_size):
                batch = words[i : i + batch_size]

                # Process batch
                for word in batch:
                    try:
                        # Analyze grammar
                        analysis_result = analyze_russian_grammar_impl(word)

                        if analysis_result.get("success"):
                            # Generate flashcards
                            flashcard_result = generate_flashcards_from_analysis_impl(
                                analysis_data=analysis_result
                            )

                            if flashcard_result.get("success"):
                                cards_generated = flashcard_result.get(
                                    "flashcards_generated", 0
                                )
                                total_flashcards += cards_generated

                                # Track word types
                                word_type = flashcard_result.get("word_type")
                                if word_type:
                                    job.processed_word_types[word_type] = (
                                        job.processed_word_types.get(word_type, 0) + 1
                                    )

                                logger.info(
                                    f"Job {job.job_id}: Generated {cards_generated} flashcards for word '{word}'"
                                )
                            else:
                                logger.warning(
                                    f"Job {job.job_id}: Failed to generate flashcards for word '{word}': {flashcard_result.get('error')}"
                                )
                                job.failed_words.append(
                                    {
                                        "word": word,
                                        "error": "flashcard_generation_failed",
                                    }
                                )
                        else:
                            logger.warning(
                                f"Job {job.job_id}: Failed to analyze word '{word}': {analysis_result.get('error')}"
                            )
                            job.failed_words.append(
                                {"word": word, "error": "analysis_failed"}
                            )

                    except Exception as e:
                        logger.error(
                            f"Job {job.job_id}: Error processing word '{word}': {e}"
                        )
                        job.failed_words.append({"word": word, "error": str(e)})

                    job.processed_words += 1

                # Small delay between batches to prevent overwhelming the system
                await asyncio.sleep(1)

            # Mark job as completed
            job.status = "completed"
            job.generated_flashcards = total_flashcards
            job.completed_at = datetime.utcnow()

            # Move to completed jobs
            self.completed_jobs[job.job_id] = job
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]

            logger.info(
                f"Completed bulk processing job {job.job_id}: {total_flashcards} flashcards generated from {job.processed_words} words"
            )

        except Exception as e:
            logger.error(f"Error in bulk processing job {job.job_id}: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

            # Move to completed jobs even if failed
            self.completed_jobs[job.job_id] = job
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a processing job."""
        job = self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)

        if not job:
            return None

        progress_pct = 0
        if job.total_words > 0:
            progress_pct = (job.processed_words / job.total_words) * 100

        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress_percentage": round(progress_pct, 1),
            "processed_words": job.processed_words,
            "total_words": job.total_words,
            "generated_flashcards": job.generated_flashcards,
            "failed_words_count": len(job.failed_words),
            "processed_word_types": job.processed_word_types,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }

    def get_user_jobs(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all jobs for a specific user."""
        user_jobs = []

        # Check active jobs
        for job in self.active_jobs.values():
            if job.user_id == user_id:
                status = self.get_job_status(job.job_id)
                if status:
                    user_jobs.append(status)

        # Check completed jobs
        for job in self.completed_jobs.values():
            if job.user_id == user_id:
                status = self.get_job_status(job.job_id)
                if status:
                    user_jobs.append(status)

        # Sort by creation time, newest first
        user_jobs.sort(key=lambda x: x["created_at"], reverse=True)

        return user_jobs

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs to prevent memory issues."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        jobs_to_remove = []
        for job_id, job in self.completed_jobs.items():
            if job.completed_at and job.completed_at.timestamp() < cutoff_time:
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.completed_jobs[job_id]
            logger.info(f"Cleaned up old job {job_id}")


# Global instance
bulk_processor = BulkTextProcessor()

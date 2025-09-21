"""
Batch Processing Service
========================

Handles large-scale batch processing of heat exposure predictions
with optimized performance and resource management.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path

from ..models.model_loader import model_loader
from ..utils.validators import InputValidator, ValidationError
from ..utils.data_preprocessor import DataPreprocessor
from ..utils.logger import get_logger
from ..config.settings import settings
from .compliance_service import ComplianceService

logger = get_logger(__name__)


class BatchJob:
    """Represents a batch processing job."""

    def __init__(self, job_id: str, data: List[Dict[str, Any]], options: Dict[str, Any]):
        self.job_id = job_id
        self.data = data
        self.options = options
        self.status = 'pending'
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0.0
        self.results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.total_items = len(data)
        self.processed_items = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary representation."""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'success_count': len([r for r in self.results if 'error' not in r]),
            'error_count': len([r for r in self.results if 'error' in r]),
            'errors': self.errors,
            'options': self.options
        }


class BatchService:
    """Service for handling large-scale batch processing."""

    def __init__(self):
        self.validator = InputValidator()
        self.preprocessor = DataPreprocessor()
        self.compliance_service = ComplianceService()
        self.active_jobs: Dict[str, BatchJob] = {}
        self.completed_jobs: Dict[str, BatchJob] = {}
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_PREDICTIONS)
        self.job_cleanup_interval = 3600  # 1 hour
        self.max_completed_jobs = 100

        # Start cleanup task
        asyncio.create_task(self._cleanup_completed_jobs())

    async def submit_batch_job(self,
                              data: List[Dict[str, Any]],
                              use_conservative: bool = True,
                              log_compliance: bool = True,
                              chunk_size: int = 100,
                              priority: str = 'normal') -> str:
        """
        Submit a new batch processing job.

        Args:
            data: List of worker data dictionaries
            use_conservative: Apply conservative bias for safety
            log_compliance: Whether to log predictions for OSHA compliance
            chunk_size: Size of processing chunks for large batches
            priority: Job priority ('low', 'normal', 'high')

        Returns:
            Job ID for tracking

        Raises:
            ValidationError: If input validation fails
            RuntimeError: If job submission fails
        """
        try:
            # Validate batch size
            if len(data) > settings.BATCH_SIZE_LIMIT:
                raise ValidationError(f"Batch size {len(data)} exceeds limit of {settings.BATCH_SIZE_LIMIT}")

            # Create job ID
            job_id = f"batch_{uuid.uuid4().hex[:8]}_{int(time.time())}"

            # Job options
            options = {
                'use_conservative': use_conservative,
                'log_compliance': log_compliance,
                'chunk_size': min(chunk_size, 1000),  # Cap chunk size
                'priority': priority,
                'submitted_by': 'api',
                'submission_time': datetime.now().isoformat()
            }

            # Create and store job
            job = BatchJob(job_id, data, options)
            self.active_jobs[job_id] = job

            # Start processing asynchronously
            asyncio.create_task(self._process_batch_job(job))

            logger.info(f"Batch job {job_id} submitted with {len(data)} items",
                       job_id=job_id, batch_size=len(data))

            return job_id

        except ValidationError as e:
            logger.error(f"Batch job validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Batch job submission failed: {e}")
            raise RuntimeError(f"Failed to submit batch job: {e}") from e

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a batch job.

        Args:
            job_id: Job identifier

        Returns:
            Job status dictionary or None if not found
        """
        # Check active jobs
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].to_dict()

        # Check completed jobs
        if job_id in self.completed_jobs:
            return self.completed_jobs[job_id].to_dict()

        return None

    async def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results of a completed batch job.

        Args:
            job_id: Job identifier

        Returns:
            Job results dictionary or None if not found
        """
        job = self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)

        if not job:
            return None

        if job.status != 'completed':
            return {
                'job_id': job_id,
                'status': job.status,
                'message': 'Job not completed yet',
                'progress': job.progress
            }

        return {
            'job_id': job_id,
            'status': job.status,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'total_items': job.total_items,
            'processed_items': job.processed_items,
            'success_count': len([r for r in job.results if 'error' not in r]),
            'error_count': len([r for r in job.results if 'error' in r]),
            'results': job.results,
            'processing_summary': self._generate_processing_summary(job)
        }

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel an active batch job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was cancelled, False otherwise
        """
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in ['pending', 'running']:
                job.status = 'cancelled'
                logger.info(f"Batch job {job_id} cancelled", job_id=job_id)
                return True

        return False

    async def list_jobs(self, status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List batch jobs with optional filtering.

        Args:
            status_filter: Filter by job status
            limit: Maximum number of jobs to return

        Returns:
            List of job status dictionaries
        """
        all_jobs = list(self.active_jobs.values()) + list(self.completed_jobs.values())

        # Filter by status if specified
        if status_filter:
            all_jobs = [job for job in all_jobs if job.status == status_filter]

        # Sort by creation time (newest first)
        all_jobs.sort(key=lambda x: x.created_at, reverse=True)

        # Apply limit
        all_jobs = all_jobs[:limit]

        return [job.to_dict() for job in all_jobs]

    async def _process_batch_job(self, job: BatchJob) -> None:
        """Process a batch job asynchronously."""
        try:
            job.status = 'running'
            job.started_at = datetime.now()

            logger.info(f"Starting batch job processing", job_id=job.job_id)

            # Validate input data
            try:
                validated_data, warnings = self.validator.validate_batch_prediction(job.data)
                if warnings:
                    job.errors.extend(warnings)
            except ValidationError as e:
                job.status = 'failed'
                job.errors.append(f"Validation failed: {e}")
                job.completed_at = datetime.now()
                return

            # Process data in chunks
            chunk_size = job.options.get('chunk_size', 100)
            use_conservative = job.options.get('use_conservative', True)
            log_compliance = job.options.get('log_compliance', True)

            total_chunks = (len(validated_data) + chunk_size - 1) // chunk_size

            for i in range(0, len(validated_data), chunk_size):
                # Check if job was cancelled
                if job.status == 'cancelled':
                    break

                chunk_data = validated_data[i:i + chunk_size]
                chunk_number = i // chunk_size + 1

                logger.debug(f"Processing chunk {chunk_number}/{total_chunks}",
                           job_id=job.job_id, chunk_size=len(chunk_data))

                # Process chunk
                chunk_results = await self._process_chunk(
                    chunk_data, use_conservative, job.job_id
                )

                # Update job progress
                job.results.extend(chunk_results)
                job.processed_items += len(chunk_data)
                job.progress = job.processed_items / job.total_items

                # Log compliance if enabled
                if log_compliance:
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            self.executor,
                            self.compliance_service.log_batch_predictions,
                            chunk_results
                        )
                    except Exception as e:
                        job.errors.append(f"Compliance logging error: {e}")

            # Complete job
            if job.status != 'cancelled':
                job.status = 'completed'

            job.completed_at = datetime.now()
            processing_time = (job.completed_at - job.started_at).total_seconds()

            logger.info(
                f"Batch job completed",
                job_id=job.job_id,
                status=job.status,
                processed_items=job.processed_items,
                processing_time_seconds=processing_time
            )

            # Move to completed jobs
            self.completed_jobs[job.job_id] = job
            del self.active_jobs[job.job_id]

        except Exception as e:
            job.status = 'failed'
            job.errors.append(f"Processing error: {e}")
            job.completed_at = datetime.now()
            logger.error(f"Batch job failed", job_id=job.job_id, error=str(e))

    async def _process_chunk(self,
                           chunk_data: List[Dict[str, Any]],
                           use_conservative: bool,
                           job_id: str) -> List[Dict[str, Any]]:
        """Process a chunk of data."""
        try:
            # Preprocess chunk
            processed_data = self.preprocessor.preprocess_batch(chunk_data)

            # Get model
            model = model_loader.load_model()

            # Process predictions in parallel for the chunk
            chunk_results = []
            futures = []

            with ThreadPoolExecutor(max_workers=min(10, len(processed_data))) as chunk_executor:
                for i, data in enumerate(processed_data):
                    future = chunk_executor.submit(
                        self._predict_single_safe, model, data, use_conservative, i
                    )
                    futures.append(future)

                # Collect results
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=settings.PREDICTION_TIMEOUT)
                        if result:
                            chunk_results.append(result)
                    except Exception as e:
                        logger.error(f"Chunk prediction failed", job_id=job_id, error=str(e))

            return chunk_results

        except Exception as e:
            logger.error(f"Chunk processing failed", job_id=job_id, error=str(e))
            return []

    def _predict_single_safe(self,
                           model,
                           data: Dict[str, Any],
                           use_conservative: bool,
                           index: int) -> Optional[Dict[str, Any]]:
        """Safely predict single sample with error handling."""
        try:
            result = model.predict_single(data, use_conservative)
            result['batch_index'] = index
            return result
        except Exception as e:
            logger.error(f"Single prediction failed for batch item {index}: {e}")
            return {
                'batch_index': index,
                'worker_id': data.get('worker_id', f'worker_{index}'),
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'prediction_successful': False
            }

    def _generate_processing_summary(self, job: BatchJob) -> Dict[str, Any]:
        """Generate processing summary for completed job."""
        successful_results = [r for r in job.results if 'error' not in r]
        failed_results = [r for r in job.results if 'error' in r]

        if not successful_results:
            return {'error': 'No successful predictions'}

        # Calculate risk statistics
        risk_scores = [r.get('heat_exposure_risk_score', 0) for r in successful_results]
        risk_levels = [r.get('risk_level', 'Unknown') for r in successful_results]

        processing_time = (job.completed_at - job.started_at).total_seconds() if job.completed_at and job.started_at else 0

        return {
            'performance_metrics': {
                'total_processing_time_seconds': processing_time,
                'average_prediction_time_ms': (processing_time * 1000) / len(successful_results) if successful_results else 0,
                'throughput_predictions_per_second': len(successful_results) / processing_time if processing_time > 0 else 0
            },
            'prediction_statistics': {
                'successful_predictions': len(successful_results),
                'failed_predictions': len(failed_results),
                'success_rate_percent': (len(successful_results) / job.total_items) * 100
            },
            'risk_analysis': {
                'average_risk_score': round(sum(risk_scores) / len(risk_scores), 3),
                'max_risk_score': round(max(risk_scores), 3),
                'min_risk_score': round(min(risk_scores), 3),
                'high_risk_workers': sum(1 for score in risk_scores if score > 0.75),
                'medium_risk_workers': sum(1 for score in risk_scores if 0.5 <= score <= 0.75),
                'low_risk_workers': sum(1 for score in risk_scores if score < 0.5)
            },
            'risk_level_distribution': {
                'Safe': sum(1 for level in risk_levels if level == 'Safe'),
                'Caution': sum(1 for level in risk_levels if level == 'Caution'),
                'Warning': sum(1 for level in risk_levels if level == 'Warning'),
                'Danger': sum(1 for level in risk_levels if level == 'Danger')
            }
        }

    async def _cleanup_completed_jobs(self) -> None:
        """Periodically clean up old completed jobs."""
        while True:
            try:
                await asyncio.sleep(self.job_cleanup_interval)

                current_time = datetime.now()
                jobs_to_remove = []

                # Remove jobs older than 24 hours
                for job_id, job in self.completed_jobs.items():
                    if job.completed_at and (current_time - job.completed_at).total_seconds() > 86400:  # 24 hours
                        jobs_to_remove.append(job_id)

                # Keep only the most recent jobs if we exceed the limit
                if len(self.completed_jobs) > self.max_completed_jobs:
                    sorted_jobs = sorted(
                        self.completed_jobs.items(),
                        key=lambda x: x[1].completed_at or datetime.min,
                        reverse=True
                    )
                    # Keep the most recent jobs
                    jobs_to_keep = dict(sorted_jobs[:self.max_completed_jobs])
                    jobs_to_remove.extend([job_id for job_id in self.completed_jobs if job_id not in jobs_to_keep])

                # Remove old jobs
                for job_id in jobs_to_remove:
                    if job_id in self.completed_jobs:
                        del self.completed_jobs[job_id]

                if jobs_to_remove:
                    logger.info(f"Cleaned up {len(jobs_to_remove)} old batch jobs")

            except Exception as e:
                logger.error(f"Error during job cleanup: {e}")

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get batch service statistics."""
        active_count = len(self.active_jobs)
        completed_count = len(self.completed_jobs)

        # Calculate statistics for active jobs
        active_stats = {
            'total_active_jobs': active_count,
            'pending_jobs': sum(1 for job in self.active_jobs.values() if job.status == 'pending'),
            'running_jobs': sum(1 for job in self.active_jobs.values() if job.status == 'running'),
            'cancelled_jobs': sum(1 for job in self.active_jobs.values() if job.status == 'cancelled')
        }

        # Calculate statistics for completed jobs
        completed_stats = {
            'total_completed_jobs': completed_count,
            'successful_jobs': sum(1 for job in self.completed_jobs.values() if job.status == 'completed'),
            'failed_jobs': sum(1 for job in self.completed_jobs.values() if job.status == 'failed')
        }

        return {
            'service_name': 'BatchService',
            'active_jobs': active_stats,
            'completed_jobs': completed_stats,
            'executor_status': {
                'max_workers': self.executor._max_workers,
                'active_threads': len([t for t in self.executor._threads if t.is_alive()])
            },
            'configuration': {
                'max_batch_size': settings.BATCH_SIZE_LIMIT,
                'max_concurrent_predictions': settings.MAX_CONCURRENT_PREDICTIONS,
                'cleanup_interval_seconds': self.job_cleanup_interval
            },
            'timestamp': datetime.now().isoformat()
        }
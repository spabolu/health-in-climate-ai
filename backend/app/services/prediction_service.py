"""
Prediction Service
==================

Core business logic for heat exposure predictions and risk assessments.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.model_loader import model_loader
from ..utils.validators import InputValidator, ValidationError
from ..utils.data_preprocessor import DataPreprocessor
from ..utils.logger import get_logger, log_prediction
from ..config.settings import settings
from .compliance_service import ComplianceService

logger = get_logger(__name__)


class PredictionService:
    """Main service for handling heat exposure predictions."""

    def __init__(self):
        self.validator = InputValidator()
        self.preprocessor = DataPreprocessor()
        self.compliance_service = ComplianceService()
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_PREDICTIONS)

    async def predict_single_worker(self,
                                   input_data: Dict[str, Any],
                                   use_conservative: bool = True,
                                   log_compliance: bool = True) -> Dict[str, Any]:
        """
        Predict heat exposure risk for a single worker.

        Args:
            input_data: Worker data including biometrics and environmental conditions
            use_conservative: Apply conservative bias for safety
            log_compliance: Whether to log prediction for OSHA compliance

        Returns:
            Heat exposure prediction result

        Raises:
            ValidationError: If input validation fails
            RuntimeError: If prediction fails
        """
        start_time = time.time()
        request_id = f"single_{int(time.time() * 1000)}"

        try:
            logger.info(f"Starting single worker prediction", request_id=request_id)

            # Input validation
            validated_data, warnings = self.validator.validate_single_prediction(input_data)
            if warnings:
                logger.warning(f"Validation warnings: {warnings}", request_id=request_id)

            # Data preprocessing
            processed_data = self.preprocessor.preprocess_single(validated_data)

            # Get model and make prediction
            model = model_loader.load_model()
            prediction_result = model.predict_single(processed_data, use_conservative)

            # Add service metadata
            prediction_result.update({
                'request_id': request_id,
                'processing_time_ms': round((time.time() - start_time) * 1000, 2),
                'validation_warnings': warnings,
                'data_quality_score': self._calculate_data_quality_score(processed_data),
                'service_version': '1.0.0'
            })

            # OSHA compliance logging
            if log_compliance:
                await self._log_compliance_async(prediction_result)

            # Log successful prediction
            logger.info(
                f"Single prediction completed successfully",
                request_id=request_id,
                worker_id=prediction_result.get('worker_id'),
                risk_level=prediction_result.get('risk_level'),
                risk_score=prediction_result.get('heat_exposure_risk_score'),
                processing_time=prediction_result.get('processing_time_ms')
            )

            return prediction_result

        except ValidationError as e:
            logger.error(f"Validation failed for single prediction: {e}", request_id=request_id)
            raise
        except Exception as e:
            logger.error(f"Single prediction failed: {e}", request_id=request_id)
            raise RuntimeError(f"Prediction service error: {e}") from e

    async def predict_multiple_workers(self,
                                     input_data: List[Dict[str, Any]],
                                     use_conservative: bool = True,
                                     log_compliance: bool = True,
                                     parallel: bool = True) -> Dict[str, Any]:
        """
        Predict heat exposure risk for multiple workers.

        Args:
            input_data: List of worker data dictionaries
            use_conservative: Apply conservative bias for safety
            log_compliance: Whether to log predictions for OSHA compliance
            parallel: Whether to process predictions in parallel

        Returns:
            Batch prediction results

        Raises:
            ValidationError: If input validation fails
            RuntimeError: If prediction fails
        """
        start_time = time.time()
        request_id = f"batch_{int(time.time() * 1000)}"
        total_workers = len(input_data)

        try:
            logger.info(f"Starting batch prediction for {total_workers} workers",
                       request_id=request_id)

            # Input validation
            validated_data, warnings = self.validator.validate_batch_prediction(input_data)
            if warnings:
                logger.warning(f"Batch validation warnings: {warnings}", request_id=request_id)

            # Data preprocessing
            processed_data = self.preprocessor.preprocess_batch(validated_data)

            # Make predictions
            if parallel and len(processed_data) > 1:
                prediction_results = await self._predict_batch_parallel(
                    processed_data, use_conservative, request_id
                )
            else:
                prediction_results = await self._predict_batch_sequential(
                    processed_data, use_conservative, request_id
                )

            # Calculate batch statistics
            batch_stats = self._calculate_batch_statistics(prediction_results)

            # OSHA compliance logging
            if log_compliance:
                await self._log_batch_compliance_async(prediction_results)

            # Prepare batch response
            batch_result = {
                'request_id': request_id,
                'batch_size': total_workers,
                'successful_predictions': len(prediction_results),
                'failed_predictions': total_workers - len(prediction_results),
                'processing_time_ms': round((time.time() - start_time) * 1000, 2),
                'validation_warnings': warnings,
                'batch_statistics': batch_stats,
                'predictions': prediction_results,
                'service_version': '1.0.0'
            }

            logger.info(
                f"Batch prediction completed",
                request_id=request_id,
                total_workers=total_workers,
                successful=len(prediction_results),
                processing_time=batch_result['processing_time_ms']
            )

            return batch_result

        except ValidationError as e:
            logger.error(f"Batch validation failed: {e}", request_id=request_id)
            raise
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}", request_id=request_id)
            raise RuntimeError(f"Batch prediction service error: {e}") from e

    async def predict_dataframe(self,
                               df: pd.DataFrame,
                               use_conservative: bool = True,
                               log_compliance: bool = True) -> Dict[str, Any]:
        """
        Predict heat exposure risk for workers from DataFrame.

        Args:
            df: DataFrame with worker data
            use_conservative: Apply conservative bias for safety
            log_compliance: Whether to log predictions for OSHA compliance

        Returns:
            DataFrame prediction results
        """
        start_time = time.time()
        request_id = f"dataframe_{int(time.time() * 1000)}"

        try:
            logger.info(f"Starting DataFrame prediction for {len(df)} workers",
                       request_id=request_id)

            # Input validation
            validated_df, warnings = self.validator.validate_dataframe(df)
            if warnings:
                logger.warning(f"DataFrame validation warnings: {warnings}", request_id=request_id)

            # Data preprocessing
            processed_df = self.preprocessor.preprocess_dataframe(validated_df)

            # Get model and make batch prediction
            model = model_loader.load_model()
            prediction_results = model.predict_batch(processed_df, use_conservative)

            # Calculate batch statistics
            batch_stats = self._calculate_batch_statistics(prediction_results)

            # OSHA compliance logging
            if log_compliance:
                await self._log_batch_compliance_async(prediction_results)

            # Prepare response
            result = {
                'request_id': request_id,
                'batch_size': len(df),
                'successful_predictions': len(prediction_results),
                'processing_time_ms': round((time.time() - start_time) * 1000, 2),
                'validation_warnings': warnings,
                'batch_statistics': batch_stats,
                'predictions': prediction_results,
                'service_version': '1.0.0'
            }

            logger.info(
                f"DataFrame prediction completed",
                request_id=request_id,
                total_workers=len(df),
                successful=len(prediction_results),
                processing_time=result['processing_time_ms']
            )

            return result

        except Exception as e:
            logger.error(f"DataFrame prediction failed: {e}", request_id=request_id)
            raise RuntimeError(f"DataFrame prediction service error: {e}") from e

    async def _predict_batch_parallel(self,
                                     processed_data: List[Dict[str, Any]],
                                     use_conservative: bool,
                                     request_id: str) -> List[Dict[str, Any]]:
        """Process batch predictions in parallel."""
        logger.info(f"Processing {len(processed_data)} predictions in parallel",
                   request_id=request_id)

        # Get model once for all predictions
        model = model_loader.load_model()

        # Create futures for parallel processing
        futures = []
        with ThreadPoolExecutor(max_workers=min(settings.MAX_CONCURRENT_PREDICTIONS, len(processed_data))) as executor:
            for i, data in enumerate(processed_data):
                future = executor.submit(self._predict_single_safe, model, data, use_conservative, i)
                futures.append(future)

            # Collect results as they complete
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=settings.PREDICTION_TIMEOUT)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Parallel prediction failed: {e}", request_id=request_id)

        return results

    async def _predict_batch_sequential(self,
                                      processed_data: List[Dict[str, Any]],
                                      use_conservative: bool,
                                      request_id: str) -> List[Dict[str, Any]]:
        """Process batch predictions sequentially."""
        logger.info(f"Processing {len(processed_data)} predictions sequentially",
                   request_id=request_id)

        model = model_loader.load_model()
        results = []

        for i, data in enumerate(processed_data):
            try:
                result = self._predict_single_safe(model, data, use_conservative, i)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Sequential prediction {i} failed: {e}", request_id=request_id)

        return results

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
            logger.error(f"Prediction failed for batch item {index}: {e}")
            return {
                'batch_index': index,
                'worker_id': data.get('worker_id', f'worker_{index}'),
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'prediction_successful': False
            }

    def _calculate_data_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score based on feature completeness and validity."""
        total_features = len(self.validator.all_features)
        available_features = sum(1 for f in self.validator.all_features
                               if f in data and data[f] is not None and data[f] != 0)

        # Base score from completeness
        completeness_score = available_features / total_features

        # Bonus for having key features
        key_features = ['Temperature', 'Humidity', 'hrv_mean_hr', 'Age']
        key_features_present = sum(1 for f in key_features if f in data and data[f] != 0)
        key_features_bonus = (key_features_present / len(key_features)) * 0.2

        return min(1.0, completeness_score + key_features_bonus)

    def _calculate_batch_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for batch prediction results."""
        if not results:
            return {'error': 'No successful predictions'}

        # Filter successful predictions
        successful_results = [r for r in results if 'error' not in r]

        if not successful_results:
            return {'error': 'No successful predictions'}

        # Extract risk scores and levels
        risk_scores = [r.get('heat_exposure_risk_score', 0) for r in successful_results]
        risk_levels = [r.get('risk_level', 'Unknown') for r in successful_results]

        # Calculate statistics
        stats = {
            'total_predictions': len(results),
            'successful_predictions': len(successful_results),
            'failed_predictions': len(results) - len(successful_results),
            'risk_score_statistics': {
                'mean': round(sum(risk_scores) / len(risk_scores), 3),
                'min': round(min(risk_scores), 3),
                'max': round(max(risk_scores), 3),
                'median': round(sorted(risk_scores)[len(risk_scores)//2], 3)
            },
            'risk_level_distribution': {
                'Safe': sum(1 for level in risk_levels if level == 'Safe'),
                'Caution': sum(1 for level in risk_levels if level == 'Caution'),
                'Warning': sum(1 for level in risk_levels if level == 'Warning'),
                'Danger': sum(1 for level in risk_levels if level == 'Danger')
            }
        }

        # Calculate risk alert counts
        high_risk_count = sum(1 for score in risk_scores if score > 0.75)
        medium_risk_count = sum(1 for score in risk_scores if 0.5 <= score <= 0.75)

        stats['alerts'] = {
            'high_risk_workers': high_risk_count,
            'medium_risk_workers': medium_risk_count,
            'requires_immediate_attention': high_risk_count
        }

        return stats

    async def _log_compliance_async(self, prediction_result: Dict[str, Any]) -> None:
        """Log single prediction for compliance asynchronously."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.compliance_service.log_prediction,
                prediction_result
            )
        except Exception as e:
            logger.error(f"Compliance logging failed: {e}")

    async def _log_batch_compliance_async(self, prediction_results: List[Dict[str, Any]]) -> None:
        """Log batch predictions for compliance asynchronously."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.compliance_service.log_batch_predictions,
                prediction_results
            )
        except Exception as e:
            logger.error(f"Batch compliance logging failed: {e}")

    def get_service_health(self) -> Dict[str, Any]:
        """Get service health status."""
        try:
            model_health = model_loader.health_check()

            return {
                'service_name': 'PredictionService',
                'status': 'healthy' if model_health['status'] == 'healthy' else 'unhealthy',
                'model_status': model_health,
                'executor_status': {
                    'max_workers': self.executor._max_workers,
                    'active_threads': len([t for t in self.executor._threads if t.is_alive()])
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'service_name': 'PredictionService',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
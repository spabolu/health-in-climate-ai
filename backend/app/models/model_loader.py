"""
Model Loader
============

Handles model loading, caching, and management for the HeatGuard system.
"""

import os
import time
import threading
from typing import Dict, Optional, Any
import logging
from datetime import datetime, timedelta

from ..config.settings import settings
from ..utils.logger import get_logger
from .heat_predictor import HeatExposurePredictor

logger = get_logger(__name__)


class ModelLoader:
    """
    Manages model loading, caching, and lifecycle for heat exposure prediction.
    Implements singleton pattern with thread-safe operations.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._models: Dict[str, HeatExposurePredictor] = {}
        self._model_metadata: Dict[str, Dict[str, Any]] = {}
        self._load_times: Dict[str, datetime] = {}
        self._access_times: Dict[str, datetime] = {}
        self._load_lock = threading.Lock()
        self._initialized = True

        logger.info("ModelLoader initialized")

    def load_model(self, model_name: str = "default",
                   model_dir: Optional[str] = None,
                   force_reload: bool = False) -> HeatExposurePredictor:
        """
        Load or retrieve a cached heat exposure prediction model.

        Args:
            model_name: Unique identifier for the model
            model_dir: Directory containing model files (uses default if None)
            force_reload: Force reload even if model is cached

        Returns:
            Loaded HeatExposurePredictor instance

        Raises:
            FileNotFoundError: If model files are not found
            RuntimeError: If model loading fails
        """
        with self._load_lock:
            # Check if model is already loaded and not expired
            if (model_name in self._models and
                not force_reload and
                self._is_model_valid(model_name)):

                # Update access time
                self._access_times[model_name] = datetime.now()
                logger.debug(f"Retrieved cached model: {model_name}")
                return self._models[model_name]

            # Load new model
            logger.info(f"Loading heat exposure model: {model_name}")
            start_time = time.time()

            try:
                # Create new predictor instance
                predictor = HeatExposurePredictor(model_dir=model_dir)

                # Cache the model
                self._models[model_name] = predictor
                self._load_times[model_name] = datetime.now()
                self._access_times[model_name] = datetime.now()

                # Store metadata
                load_duration = time.time() - start_time
                self._model_metadata[model_name] = {
                    'model_dir': model_dir or settings.MODEL_DIR,
                    'load_duration': load_duration,
                    'feature_count': len(predictor.feature_columns),
                    'target_classes': list(predictor.label_encoder.classes_),
                    'version': '1.0.0'
                }

                logger.info(f"Model {model_name} loaded successfully in {load_duration:.2f}s")

                # Clean up old models if cache is full
                self._cleanup_cache()

                return predictor

            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise RuntimeError(f"Model loading failed: {e}") from e

    def get_model(self, model_name: str = "default") -> Optional[HeatExposurePredictor]:
        """
        Get a cached model without loading if not present.

        Args:
            model_name: Model identifier

        Returns:
            Model instance if cached, None otherwise
        """
        if model_name in self._models and self._is_model_valid(model_name):
            self._access_times[model_name] = datetime.now()
            return self._models[model_name]
        return None

    def is_model_loaded(self, model_name: str = "default") -> bool:
        """
        Check if a model is currently loaded and valid.

        Args:
            model_name: Model identifier

        Returns:
            True if model is loaded and valid
        """
        return (model_name in self._models and
                self._is_model_valid(model_name))

    def unload_model(self, model_name: str) -> bool:
        """
        Unload a specific model from cache.

        Args:
            model_name: Model identifier

        Returns:
            True if model was unloaded, False if not found
        """
        with self._load_lock:
            if model_name in self._models:
                del self._models[model_name]
                del self._model_metadata[model_name]
                del self._load_times[model_name]
                del self._access_times[model_name]

                logger.info(f"Model {model_name} unloaded from cache")
                return True
            return False

    def reload_model(self, model_name: str = "default",
                     model_dir: Optional[str] = None) -> HeatExposurePredictor:
        """
        Force reload a model, replacing any cached version.

        Args:
            model_name: Model identifier
            model_dir: Model directory path

        Returns:
            Reloaded model instance
        """
        logger.info(f"Force reloading model: {model_name}")
        return self.load_model(model_name, model_dir, force_reload=True)

    def get_model_info(self, model_name: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get metadata about a loaded model.

        Args:
            model_name: Model identifier

        Returns:
            Model metadata dictionary or None if not loaded
        """
        if model_name not in self._model_metadata:
            return None

        metadata = self._model_metadata[model_name].copy()
        metadata.update({
            'model_name': model_name,
            'is_loaded': self.is_model_loaded(model_name),
            'load_time': self._load_times[model_name].isoformat(),
            'last_access': self._access_times[model_name].isoformat(),
            'age_minutes': (datetime.now() - self._load_times[model_name]).total_seconds() / 60
        })

        return metadata

    def get_all_models_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all loaded models.

        Returns:
            Dictionary mapping model names to their metadata
        """
        return {
            model_name: self.get_model_info(model_name)
            for model_name in self._models.keys()
        }

    def clear_cache(self) -> int:
        """
        Clear all cached models.

        Returns:
            Number of models that were cleared
        """
        with self._load_lock:
            count = len(self._models)
            self._models.clear()
            self._model_metadata.clear()
            self._load_times.clear()
            self._access_times.clear()

            logger.info(f"Cleared {count} models from cache")
            return count

    def _is_model_valid(self, model_name: str) -> bool:
        """
        Check if a cached model is still valid (not expired).

        Args:
            model_name: Model identifier

        Returns:
            True if model is valid
        """
        if model_name not in self._load_times:
            return False

        # Check if model has expired (optional TTL)
        load_time = self._load_times[model_name]
        max_age = timedelta(hours=24)  # Models expire after 24 hours

        if datetime.now() - load_time > max_age:
            logger.info(f"Model {model_name} has expired and will be reloaded")
            return False

        # Check if model instance is still functional
        model = self._models.get(model_name)
        return model is not None and model.is_loaded

    def _cleanup_cache(self) -> None:
        """
        Clean up cache by removing least recently used models if cache is full.
        """
        if len(self._models) <= settings.MODEL_CACHE_SIZE:
            return

        # Sort models by last access time
        models_by_access = sorted(
            self._access_times.items(),
            key=lambda x: x[1]
        )

        # Remove oldest models
        models_to_remove = len(self._models) - settings.MODEL_CACHE_SIZE
        for model_name, _ in models_by_access[:models_to_remove]:
            logger.info(f"Removing {model_name} from cache (LRU cleanup)")
            del self._models[model_name]
            del self._model_metadata[model_name]
            del self._load_times[model_name]
            del self._access_times[model_name]

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on model loader and cached models.

        Returns:
            Health check results
        """
        try:
            total_models = len(self._models)
            valid_models = sum(1 for name in self._models.keys() if self._is_model_valid(name))

            # Try to load default model if not present
            default_model_loaded = self.is_model_loaded("default")
            if not default_model_loaded:
                try:
                    self.load_model("default")
                    default_model_loaded = True
                except Exception as e:
                    logger.warning(f"Could not load default model during health check: {e}")

            return {
                'status': 'healthy' if valid_models > 0 else 'unhealthy',
                'total_models_cached': total_models,
                'valid_models': valid_models,
                'default_model_loaded': default_model_loaded,
                'cache_size_limit': settings.MODEL_CACHE_SIZE,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Global model loader instance
model_loader = ModelLoader()
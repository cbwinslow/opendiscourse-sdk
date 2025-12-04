"""
================================================================================
File: feature_flags.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Feature flags system for runtime feature toggling. Enables/disables
    features dynamically without code changes, supports environment-based
    configuration, and provides decorator for wrapping feature-gated code.

Dependencies:
    - typing: Type hints
    - enum: Flag enumeration
    - functools: Decorator utilities
    - pydantic: Configuration validation

Classes:
    - FeatureFlag: Enum of available features
    - FeatureFlagManager: Centralized flag management
    - @feature_flag: Decorator for feature-gated functions

Usage:
    from scripts.core.feature_flags import FeatureFlag, feature_flag, flags

    # Check if feature enabled
    if flags.is_enabled(FeatureFlag.DEDUPLICATION):
        # Use deduplication
        ...

    # Decorator usage
    @feature_flag(FeatureFlag.ADVANCED_CACHING)
    def cache_response(data):
        # Only runs if caching enabled
        ...

    # Toggle features
    flags.enable(FeatureFlag.EXPERIMENTAL_EXPORT)
    flags.disable(FeatureFlag.BETA_FEATURES)

Changelog:
    2025-12-04: Initial creation

Notes:
    - Features can be toggled at runtime
    - Environment variable override support
    - Decorator safely skips disabled features

================================================================================
"""

import logging
import os
from enum import Enum
from typing import Callable, Optional, Dict, Any
from functools import wraps


# ============================================================================
# Feature Flag Enumeration
# ============================================================================

class FeatureFlag(str, Enum):
    """
    Available feature flags.

    Add new features here as they're developed. Each flag can be
    toggled independently to control feature availability.

    Categories:
        - Core: Essential features
        - Advanced: Optional advanced features
        - Experimental: Features in testing
        - Beta: Features in beta testing
    """

    # Core Features
    DEDUPLICATION = "deduplication"
    WORKER_POOL = "worker_pool"
    MULTI_DATABASE = "multi_database"

    # Advanced Features
    ADVANCED_CACHING = "advanced_caching"
    RESPONSE_VALIDATION = "response_validation"
    PARAMETER_VALIDATION = "parameter_validation"

    # Export Features
    CSV_EXPORT = "csv_export"
    PARQUET_EXPORT = "parquet_export"
    SQLITE_EXPORT = "sqlite_export"
    STREAMING_EXPORT = "streaming_export"

    # Experimental Features
    AUTO_RETRY = "auto_retry"
    DYNAMIC_WORKER_SCALING = "dynamic_worker_scaling"
    GRAPHQL_ENDPOINT = "graphql_endpoint"

    # Beta Features
    PERFORMANCE_PROFILING = "performance_profiling"
    METRICS_DASHBOARD = "metrics_dashboard"
    DISTRIBUTED_PROCESSING = "distributed_processing"


# ============================================================================
# Feature Flag Manager
# ============================================================================

class FeatureFlagManager:
    """
    Centralized feature flag management.

    Manages feature flags with support for environment variable
    overrides, enabling/disabling at runtime, and querying status.

    Attributes:
        flags: Dictionary of flag states
        logger: Logger instance

    Methods:
        is_enabled: Check if feature is enabled
        enable: Enable a feature
        disable: Disable a feature
        toggle: Toggle a feature
        get_all: Get all flag states
    """

    def __init__(self):
        """Initialize feature flag manager."""
        self.logger = logging.getLogger("FeatureFlags")

        # Default flag states (can be overridden by environment)
        self._default_states = {
            # Core features (enabled by default)
            FeatureFlag.DEDUPLICATION: True,
            FeatureFlag.WORKER_POOL: True,
            FeatureFlag.MULTI_DATABASE: True,

            # Advanced features (enabled by default)
            FeatureFlag.ADVANCED_CACHING: True,
            FeatureFlag.RESPONSE_VALIDATION: True,
            FeatureFlag.PARAMETER_VALIDATION: True,

            # Export features (enabled by default)
            FeatureFlag.CSV_EXPORT: True,
            FeatureFlag.PARQUET_EXPORT: True,
            FeatureFlag.SQLITE_EXPORT: True,
            FeatureFlag.STREAMING_EXPORT: False,  # Experimental

            # Experimental features (disabled by default)
            FeatureFlag.AUTO_RETRY: True,
            FeatureFlag.DYNAMIC_WORKER_SCALING: False,
            FeatureFlag.GRAPHQL_ENDPOINT: False,

            # Beta features (disabled by default)
            FeatureFlag.PERFORMANCE_PROFILING: False,
            FeatureFlag.METRICS_DASHBOARD: False,
            FeatureFlag.DISTRIBUTED_PROCESSING: False,
        }

        # Load flags from environment variables
        self.flags = self._load_from_environment()

        self.logger.info(f"Feature flags initialized: {sum(self.flags.values())} enabled")

    def _load_from_environment(self) -> Dict[FeatureFlag, bool]:
        """
        Load feature flags from environment variables.

        Environment variables: FEATURE_<FLAG_NAME>=true/false
        Example: FEATURE_DEDUPLICATION=true

        Returns:
            Dictionary of flag states
        """
        flags = self._default_states.copy()

        # Check for environment variable overrides
        for flag in FeatureFlag:
            env_var = f"FEATURE_{flag.value.upper()}"
            env_value = os.getenv(env_var)

            if env_value is not None:
                # Parse boolean from environment
                enabled = env_value.lower() in ('true', '1', 'yes', 'on')
                flags[flag] = enabled
                self.logger.debug(f"Override from env: {flag.value} = {enabled}")

        return flags

    # ========================================================================
    # Query Methods
    # ========================================================================

    def is_enabled(self, flag: FeatureFlag) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag: Feature flag to check

        Returns:
            True if feature is enabled

        Example:
            >>> if flags.is_enabled(FeatureFlag.DEDUPLICATION):
            >>>     # Use deduplication
        """
        return self.flags.get(flag, False)

    def is_disabled(self, flag: FeatureFlag) -> bool:
        """
        Check if a feature flag is disabled.

        Args:
            flag: Feature flag to check

        Returns:
            True if feature is disabled
        """
        return not self.is_enabled(flag)

    def get_all(self) -> Dict[str, bool]:
        """
        Get all feature flag states.

        Returns:
            Dictionary mapping flag names to states

        Example:
            >>> all_flags = flags.get_all()
            >>> for name, enabled in all_flags.items():
            >>>     print(f"{name}: {'✓' if enabled else '✗'}")
        """
        return {flag.value: enabled for flag, enabled in self.flags.items()}

    def get_enabled(self) -> list[str]:
        """Get list of enabled feature names."""
        return [flag.value for flag, enabled in self.flags.items() if enabled]

    def get_disabled(self) -> list[str]:
        """Get list of disabled feature names."""
        return [flag.value for flag, enabled in self.flags.items() if not enabled]

    # ========================================================================
    # Modification Methods
    # ========================================================================

    def enable(self, flag: FeatureFlag):
        """
        Enable a feature flag.

        Args:
            flag: Feature flag to enable

        Example:
            >>> flags.enable(FeatureFlag.ADVANCED_CACHING)
        """
        self.flags[flag] = True
        self.logger.info(f"Feature enabled: {flag.value}")

    def disable(self, flag: FeatureFlag):
        """
        Disable a feature flag.

        Args:
            flag: Feature flag to disable

        Example:
            >>> flags.disable(FeatureFlag.EXPERIMENTAL_EXPORT)
        """
        self.flags[flag] = False
        self.logger.info(f"Feature disabled: {flag.value}")

    def toggle(self, flag: FeatureFlag):
        """
        Toggle a feature flag.

        Args:
            flag: Feature flag to toggle

        Example:
            >>> flags.toggle(FeatureFlag.PERFORMANCE_PROFILING)
        """
        self.flags[flag] = not self.flags[flag]
        state = "enabled" if self.flags[flag] else "disabled"
        self.logger.info(f"Feature toggled: {flag.value} -> {state}")

    def set(self, flag: FeatureFlag, enabled: bool):
        """
        Set a feature flag to a specific state.

        Args:
            flag: Feature flag to set
            enabled: New state
        """
        self.flags[flag] = enabled
        state = "enabled" if enabled else "disabled"
        self.logger.info(f"Feature set: {flag.value} -> {state}")

    # ========================================================================
    # Batch Operations
    # ========================================================================

    def enable_all(self):
        """Enable all feature flags."""
        for flag in FeatureFlag:
            self.flags[flag] = True
        self.logger.info("All features enabled")

    def disable_all(self):
        """Disable all feature flags."""
        for flag in FeatureFlag:
            self.flags[flag] = False
        self.logger.warning("All features disabled")

    def reset_to_defaults(self):
        """Reset all flags to default states."""
        self.flags = self._default_states.copy()
        self.logger.info("Feature flags reset to defaults")

    # ========================================================================
    # Display
    # ========================================================================

    def print_status(self):
        """Print formatted feature flag status."""
        print("\n" + "=" * 70)
        print("FEATURE FLAGS STATUS")
        print("=" * 70)

        # Group by category
        categories = {
            "Core Features": [
                FeatureFlag.DEDUPLICATION,
                FeatureFlag.WORKER_POOL,
                FeatureFlag.MULTI_DATABASE,
            ],
            "Advanced Features": [
                FeatureFlag.ADVANCED_CACHING,
                FeatureFlag.RESPONSE_VALIDATION,
                FeatureFlag.PARAMETER_VALIDATION,
            ],
            "Export Features": [
                FeatureFlag.CSV_EXPORT,
                FeatureFlag.PARQUET_EXPORT,
                FeatureFlag.SQLITE_EXPORT,
                FeatureFlag.STREAMING_EXPORT,
            ],
            "Experimental": [
                FeatureFlag.AUTO_RETRY,
                FeatureFlag.DYNAMIC_WORKER_SCALING,
                FeatureFlag.GRAPHQL_ENDPOINT,
            ],
            "Beta": [
                FeatureFlag.PERFORMANCE_PROFILING,
                FeatureFlag.METRICS_DASHBOARD,
                FeatureFlag.DISTRIBUTED_PROCESSING,
            ],
        }

        for category, feature_list in categories.items():
            print(f"\n{category}:")
            for flag in feature_list:
                status = "✓" if self.is_enabled(flag) else "✗"
                print(f"  {status} {flag.value}")

        # Summary
        enabled_count = sum(self.flags.values())
        total_count = len(self.flags)
        print(f"\nTotal: {enabled_count}/{total_count} enabled")
        print("=" * 70 + "\n")


# ============================================================================
# Global Instance
# ============================================================================

# Singleton instance for global access
flags = FeatureFlagManager()


# ============================================================================
# Decorator
# ============================================================================

def feature_flag(flag: FeatureFlag, fallback_return: Any = None):
    """
    Decorator to gate functions behind feature flags.

    If the feature is disabled, the function is skipped and
    fallback_return is returned instead.

    Args:
        flag: Feature flag to check
        fallback_return: Value to return if feature disabled

    Returns:
        Decorator function

    Usage:
        @feature_flag(FeatureFlag.ADVANCED_CACHING)
        def cache_data(data):
            # Only runs if caching enabled
            return cached_data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if flags.is_enabled(flag):
                # Feature enabled, execute function
                return func(*args, **kwargs)
            else:
                # Feature disabled, return fallback
                logger = logging.getLogger(func.__module__)
                logger.debug(
                    f"Feature {flag.value} disabled, skipping {func.__name__}"
                )
                return fallback_return

        return wrapper
    return decorator


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'FeatureFlag',
    'FeatureFlagManager',
    'flags',
    'feature_flag',
]

"""
================================================================================
File: test_feature_flags.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Version: 1.0.0

Description:
    Tests for feature flags system including flag toggling, environment
    overrides, and decorator functionality.

================================================================================
"""

import pytest
import os
from scripts.core.feature_flags import (
    FeatureFlag,
    FeatureFlagManager,
    feature_flag
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def flag_manager():
    """Create fresh flag manager for each test."""
    return FeatureFlagManager()


# ============================================================================
# Basic Functionality Tests
# ============================================================================

def test_flag_manager_creation(flag_manager):
    """Test creating flag manager."""
    assert flag_manager is not None
    assert len(flag_manager.flags) > 0


def test_core_features_enabled_by_default(flag_manager):
    """Test that core features are enabled by default."""
    assert flag_manager.is_enabled(FeatureFlag.DEDUPLICATION)
    assert flag_manager.is_enabled(FeatureFlag.WORKER_POOL)
    assert flag_manager.is_enabled(FeatureFlag.MULTI_DATABASE)


def test_experimental_features_disabled_by_default(flag_manager):
    """Test that experimental features are disabled by default."""
    assert not flag_manager.is_enabled(FeatureFlag.DYNAMIC_WORKER_SCALING)
    assert not flag_manager.is_enabled(FeatureFlag.GRAPHQL_ENDPOINT)


# ============================================================================
# Query Methods Tests
# ============================================================================

def test_is_enabled(flag_manager):
    """Test checking if feature is enabled."""
    # Enable a feature
    flag_manager.enable(FeatureFlag.PERFORMANCE_PROFILING)

    assert flag_manager.is_enabled(FeatureFlag.PERFORMANCE_PROFILING)


def test_is_disabled(flag_manager):
    """Test checking if feature is disabled."""
    # Disable a feature
    flag_manager.disable(FeatureFlag.DEDUPLICATION)

    assert flag_manager.is_disabled(FeatureFlag.DEDUPLICATION)


def test_get_all_flags(flag_manager):
    """Test getting all flag states."""
    all_flags = flag_manager.get_all()

    assert isinstance(all_flags, dict)
    assert len(all_flags) > 0
    assert "deduplication" in all_flags


def test_get_enabled_list(flag_manager):
    """Test getting list of enabled features."""
    enabled = flag_manager.get_enabled()

    assert isinstance(enabled, list)
    assert "deduplication" in enabled  # Core feature


def test_get_disabled_list(flag_manager):
    """Test getting list of disabled features."""
    disabled = flag_manager.get_disabled()

    assert isinstance(disabled, list)
    # Some experimental features should be disabled
    assert len(disabled) > 0


# ============================================================================
# Modification Methods Tests
# ============================================================================

def test_enable_feature(flag_manager):
    """Test enabling a feature."""
    flag_manager.disable(FeatureFlag.ADVANCED_CACHING)
    assert not flag_manager.is_enabled(FeatureFlag.ADVANCED_CACHING)

    flag_manager.enable(FeatureFlag.ADVANCED_CACHING)
    assert flag_manager.is_enabled(FeatureFlag.ADVANCED_CACHING)


def test_disable_feature(flag_manager):
    """Test disabling a feature."""
    flag_manager.enable(FeatureFlag.DEDUPLICATION)
    assert flag_manager.is_enabled(FeatureFlag.DEDUPLICATION)

    flag_manager.disable(FeatureFlag.DEDUPLICATION)
    assert not flag_manager.is_enabled(FeatureFlag.DEDUPLICATION)


def test_toggle_feature(flag_manager):
    """Test toggling a feature."""
    initial_state = flag_manager.is_enabled(FeatureFlag.CSV_EXPORT)

    flag_manager.toggle(FeatureFlag.CSV_EXPORT)
    assert flag_manager.is_enabled(FeatureFlag.CSV_EXPORT) != initial_state

    flag_manager.toggle(FeatureFlag.CSV_EXPORT)
    assert flag_manager.is_enabled(FeatureFlag.CSV_EXPORT) == initial_state


def test_set_feature(flag_manager):
    """Test setting feature to specific state."""
    flag_manager.set(FeatureFlag.PARQUET_EXPORT, True)
    assert flag_manager.is_enabled(FeatureFlag.PARQUET_EXPORT)

    flag_manager.set(FeatureFlag.PARQUET_EXPORT, False)
    assert not flag_manager.is_enabled(FeatureFlag.PARQUET_EXPORT)


# ============================================================================
# Batch Operations Tests
# ============================================================================

def test_enable_all(flag_manager):
    """Test enabling all features."""
    flag_manager.enable_all()

    for flag in FeatureFlag:
        assert flag_manager.is_enabled(flag)


def test_disable_all(flag_manager):
    """Test disabling all features."""
    flag_manager.disable_all()

    for flag in FeatureFlag:
        assert not flag_manager.is_enabled(flag)


def test_reset_to_defaults(flag_manager):
    """Test resetting to default states."""
    # Change some flags
    flag_manager.disable(FeatureFlag.DEDUPLICATION)
    flag_manager.enable(FeatureFlag.GRAPHQL_ENDPOINT)

    # Reset
    flag_manager.reset_to_defaults()

    # Core feature should be enabled
    assert flag_manager.is_enabled(FeatureFlag.DEDUPLICATION)
    # Experimental should be disabled
    assert not flag_manager.is_enabled(FeatureFlag.GRAPHQL_ENDPOINT)


# ============================================================================
# Decorator Tests
# ============================================================================

def test_feature_flag_decorator_enabled():
    """Test decorator when feature is enabled."""
    # Create manager with feature enabled
    manager = FeatureFlagManager()
    manager.enable(FeatureFlag.ADVANCED_CACHING)

    # Override global flags temporarily
    from scripts.core import feature_flags
    original = feature_flags.flags
    feature_flags.flags = manager

    try:
        @feature_flag(FeatureFlag.ADVANCED_CACHING)
        def cached_function():
            return "executed"

        result = cached_function()
        assert result == "executed"
    finally:
        feature_flags.flags = original


def test_feature_flag_decorator_disabled():
    """Test decorator when feature is disabled."""
    manager = FeatureFlagManager()
    manager.disable(FeatureFlag.ADVANCED_CACHING)

    from scripts.core import feature_flags
    original = feature_flags.flags
    feature_flags.flags = manager

    try:
        @feature_flag(FeatureFlag.ADVANCED_CACHING, fallback_return="skipped")
        def cached_function():
            return "should not execute"

        result = cached_function()
        assert result == "skipped"
    finally:
        feature_flags.flags = original


def test_feature_flag_decorator_with_args():
    """Test decorator with function arguments."""
    manager = FeatureFlagManager()
    manager.enable(FeatureFlag.RESPONSE_VALIDATION)

    from scripts.core import feature_flags
    original = feature_flags.flags
    feature_flags.flags = manager

    try:
        @feature_flag(FeatureFlag.RESPONSE_VALIDATION)
        def validate_data(data, strict=False):
            return f"validated: {data}, strict={strict}"

        result = validate_data("test", strict=True)
        assert "validated: test" in result
        assert "strict=True" in result
    finally:
        feature_flags.flags = original


# ============================================================================
# Environment Variable Tests
# ============================================================================

def test_environment_variable_override(monkeypatch):
    """Test that environment variables override defaults."""
    # Set environment variable
    monkeypatch.setenv("FEATURE_GRAPHQL_ENDPOINT", "true")

    # Create new manager (will load from env)
    manager = FeatureFlagManager()

    # Should be enabled due to env var
    assert manager.is_enabled(FeatureFlag.GRAPHQL_ENDPOINT)


def test_environment_variable_disable(monkeypatch):
    """Test disabling via environment variable."""
    # Disable a normally-enabled feature
    monkeypatch.setenv("FEATURE_DEDUPLICATION", "false")

    manager = FeatureFlagManager()

    assert not manager.is_enabled(FeatureFlag.DEDUPLICATION)


# ============================================================================
# Display Tests
# ============================================================================

def test_print_status(flag_manager, capsys):
    """Test printing status."""
    flag_manager.print_status()

    captured = capsys.readouterr()
    assert "FEATURE FLAGS STATUS" in captured.out
    assert "Core Features" in captured.out
    assert "deduplication" in captured.out

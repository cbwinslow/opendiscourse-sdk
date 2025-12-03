"""Basic import tests to verify the package structure is correct."""

import pytest


def test_main_package_import():
    """Test that the main package can be imported."""
    import opendiscourse
    assert opendiscourse is not None


def test_config_import():
    """Test that configuration can be imported."""
    from opendiscourse.core.config import settings
    assert settings is not None


def test_api_routes_import():
    """Test that API routes can be imported."""
    from opendiscourse.api.v1.routes import api_router
    assert api_router is not None


def test_main_app_import():
    """Test that the main FastAPI app can be imported."""
    from opendiscourse.main import app
    assert app is not None


def test_entity_utils_import():
    """Test that entity utilities can be imported."""
    import opendiscourse.entity_utils
    assert opendiscourse.entity_utils is not None


def test_models_import():
    """Test that database models can be imported."""
    from opendiscourse.db.models import Entity, EntityType
    assert Entity is not None
    assert EntityType is not None


if __name__ == "__main__":
    pytest.main([__file__])
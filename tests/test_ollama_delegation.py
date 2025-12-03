from unittest.mock import Mock, patch

import pytest

from scripts.ollama_delegator import OllamaDelegationError, OllamaDelegator


class TestOllamaDelegation:
    @pytest.fixture
    def delegator(self):
        return OllamaDelegator()

    @patch('scripts.ollama_delegator.OllamaClient')
    def test_successful_delegation(self, mock_client):
        mock_instance = mock_client.return_value
        mock_instance.generate.return_value = "Bonjour"
        response = OllamaDelegator().delegate("Translate 'hello' to French")
        assert "bonjour" in response.lower()
        mock_instance.generate.assert_called_once_with(
            prompt="Translate 'hello' to French",
            model="llama2",
            timeout=300
        )

    @patch('scripts.ollama_delegator.OllamaClient')
    def test_retry_mechanism(self, mock_client):
        mock_instance = mock_client.return_value
        mock_instance.generate.side_effect = Exception("Timeout")

        with pytest.raises(OllamaDelegationError):
            OllamaDelegator().delegate("test", max_retries=3)

        assert mock_instance.generate.call_count == 3

    @patch('scripts.ollama_delegator.OllamaClient')
    def test_model_validation(self, mock_client):
        mock_instance = mock_client.return_value
        mock_instance.list_models.return_value = ["llama2", "codellama"]
        delegator = OllamaDelegator()
        assert delegator.validate_model("codellama") is True
        assert delegator.validate_model("invalid") is False

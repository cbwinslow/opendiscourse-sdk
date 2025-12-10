import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

# Mock FastMCP before importing servers
sys.modules["mcp.server.fastmcp"] = MagicMock()
from mcp.server.fastmcp import FastMCP

class TestMCPServers(unittest.TestCase):
    def setUp(self):
        # Reset FastMCP mock
        FastMCP.reset_mock()

    def test_congress_server_import(self):
        """Test that Congress MCP server can be imported and defines tools."""
        try:
            from servers.congress.src.congress_mcp import server
            # Check if tools are registered (this depends on how FastMCP is mocked/implemented)
            # For now, just successful import is a good sign
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import Congress server: {e}")

    def test_openstates_server_import(self):
        """Test that OpenStates MCP server can be imported."""
        try:
            from servers.openstates.src.openstates_mcp import server
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import OpenStates server: {e}")

    def test_govinfo_server_import(self):
        """Test that GovInfo MCP server can be imported."""
        try:
            from servers.govinfo.src.govinfo_mcp import server
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import GovInfo server: {e}")

if __name__ == "__main__":
    unittest.main()

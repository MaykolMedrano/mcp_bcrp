"""
Basic tests for mcp-bcrp
"""
import pytest
from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata
from mcp_bcrp.search_engine import SearchEngine
import pandas as pd
import json
import mcp_bcrp


class TestSearchEngine:
    """Test the deterministic search engine."""
    
    def test_normalize(self):
        """Test text normalization."""
        # Create a dummy dataframe
        df = pd.DataFrame({
            "Código de serie": ["TEST001"],
            "Nombre de serie": ["Precio del Cobre (USD)"]
        })
        engine = SearchEngine(df)
        
        result = engine._normalize("Precio del COBRE")
        assert "precio" in result
        assert "cobre" in result
        assert "del" not in result  # Stopword removed
    
    def test_attribute_extraction_currency(self):
        """Test currency attribute extraction."""
        df = pd.DataFrame({
            "Código de serie": ["TEST001"],
            "Nombre de serie": ["Test USD Series"]
        })
        engine = SearchEngine(df)
        
        attrs = engine._extract_attributes("reservas usd")
        assert attrs["currency"] == "usd"
        
        attrs = engine._extract_attributes("credito soles")
        assert attrs["currency"] == "pen"


class TestBCRPMetadata:
    """Test metadata loading and search."""
    
    @pytest.mark.asyncio
    async def test_load_creates_cache(self, tmp_path, monkeypatch):
        """Test that loading reads a valid local cache without HTTP."""
        frame = pd.DataFrame({
            "Código de serie": ["TEST001"],
            "Nombre de serie": ["Precio del Cobre"],
        })
        cache_path = tmp_path / "bcrp_metadata.json"
        frame.to_json(cache_path, orient="records")

        metadata = BCRPMetadata()
        metadata._cache_path = cache_path
        await metadata.load()

        assert metadata._loaded is True
        assert metadata.df.to_dict(orient="records") == frame.to_dict(orient="records")


class TestServerResources:
    """Regression tests for synchronous MCP resources."""

    def test_metadata_resource_reports_loaded_dataframe(self, monkeypatch):
        """The metadata resource must use BCRPMetadata.df, not a missing .data."""
        import mcp_bcrp.server as server

        frame = pd.DataFrame({
            "Código de serie": ["TEST001"],
            "Nombre de serie": ["Precio del Cobre"],
        })
        monkeypatch.setattr(server.metadata_client, "df", frame)
        monkeypatch.setattr(server.metadata_client, "_loaded", True)

        payload = json.loads(server.get_metadata())
        assert payload["total_series"] == 1
        assert "Código de serie" in payload["columns"]

    def test_metadata_resource_reports_unloaded_state(self, monkeypatch):
        import mcp_bcrp.server as server

        monkeypatch.setattr(server.metadata_client, "df", pd.DataFrame())
        monkeypatch.setattr(server.metadata_client, "_loaded", False)

        payload = json.loads(server.get_metadata())
        assert payload["status"].startswith("Metadata not loaded")


class TestAsyncBCRPClient:
    """Test async API client."""
    
    def test_date_formatting(self):
        """Test date format conversion."""
        client = AsyncBCRPClient()
        
        assert client._format_date_for_api("2024-01") == "2024-1"
        assert client._format_date_for_api("2024-12") == "2024-12"
        assert client._format_date_for_api(None) is None

    def test_timeout_from_environment(self, monkeypatch):
        """BCRP_TIMEOUT should configure clients created without an explicit timeout."""
        monkeypatch.setenv("BCRP_TIMEOUT", "7.5")
        client = AsyncBCRPClient()

        assert client.timeout == 7.5

    def test_package_version_is_generated(self):
        """The package exposes a version (generated when a distribution is built)."""
        assert isinstance(mcp_bcrp.__version__, str)
        assert mcp_bcrp.__version__

"""
Basic tests for mcp-bcrp
"""
import pytest
from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata
from mcp_bcrp.search_engine import SearchEngine
import pandas as pd


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
        """Test that loading creates a cache file."""
        # This is a placeholder - would need mocking for full test
        metadata = BCRPMetadata()
        # Actual test would mock httpx and verify cache creation
        pass


class TestAsyncBCRPClient:
    """Test async API client."""
    
    def test_date_formatting(self):
        """Test date format conversion."""
        client = AsyncBCRPClient()
        
        assert client._format_date_for_api("2024-01") == "2024-1"
        assert client._format_date_for_api("2024-12") == "2024-12"
        assert client._format_date_for_api(None) is None

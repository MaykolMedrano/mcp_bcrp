import io
import os
import re
from pathlib import Path
import httpx
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
import asyncio

logger = logging.getLogger("mcp_bcrp")

class BCRPMetadata:
    """
    Handles fetching and searching BCRP metadata.
    
    The metadata file (~17MB) is cached locally for fast searches.
    On first use, it downloads from BCRP and caches for future use.
    
    Cache location priority:
    1. BCRP_CACHE_DIR environment variable
    2. User's cache directory (~/.cache/mcp_bcrp or AppData/Local/mcp_bcrp)
    3. Package directory (fallback)
    """
    METADATA_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
    CACHE_FILENAME = "bcrp_metadata.json"

    def __init__(self):
        self.df = pd.DataFrame()
        self._loaded = False
        self._cache_path = self._get_cache_path()

    def _get_cache_path(self) -> Path:
        """Determine the best cache location for metadata."""
        # Priority 1: Environment variable
        if cache_dir := os.environ.get("BCRP_CACHE_DIR"):
            path = Path(cache_dir)
            path.mkdir(parents=True, exist_ok=True)
            return path / self.CACHE_FILENAME
        
        # Priority 2: User cache directory
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        else:  # Unix
            base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        
        cache_dir = base / "mcp_bcrp"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / self.CACHE_FILENAME

    async def load(self):
        """
        Load metadata from cache or download from BCRP.
        
        First checks for local cache. If not found, downloads from
        BCRP API and saves to cache for future use.
        """
        if self._loaded and not self.df.empty:
            return

        if self._cache_path.exists():
            logger.info(f"Loading metadata from cache: {self._cache_path}")
            try:
                self.df = pd.read_json(self._cache_path, orient="records")
                self._loaded = True
                return
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

        await self.refresh()

    async def refresh(self):
        """
        Fetch fresh metadata from BCRP API.
        
        Downloads the complete metadata catalog (~17MB) and saves
        to local cache as JSON for fast future searches.
        """
        logger.info("Fetching fresh metadata from BCRP (this may take a moment)...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=120.0) as client:
            resp = await client.get(self.METADATA_URL)
            resp.raise_for_status()
            
            content = resp.content
            self.df = pd.read_csv(io.BytesIO(content), delimiter=";", encoding="latin-1")
            
            # Save to cache
            self.df.to_json(self._cache_path, orient="records", date_format="iso", force_ascii=False)
            self._loaded = True
            logger.info(f"Metadata cached: {len(self.df)} series at {self._cache_path}")

    def search(self, query: str, limit: int = 20) -> pd.DataFrame:
        """
        Fuzzy search using RapidFuzz (Token Sort Ratio).
        Returns DataFrame of matching series.
        For deterministic single-match resolution, use `solve()`.
        """
        if self.df.empty:
            return pd.DataFrame()

        try:
            from rapidfuzz import process, fuzz
        except ImportError:
            logger.error("rapidfuzz not installed. Falling back to simple search.")
            return self._simple_search(query, limit)

        names = self.df["Nombre de serie"].astype(str).fillna("").tolist()
        
        results = process.extract(
            query, 
            names, 
            scorer=fuzz.token_sort_ratio, 
            limit=limit,
            score_cutoff=40
        )
        
        indices = [res[2] for res in results]
        
        return self.df.iloc[indices]

    def solve(self, query: str) -> dict:
        """
        Deterministic resolution using SearchEngine pipeline.
        Returns: { codigo_serie, confidence } | { error, ... }
        """
        if self.df.empty:
            return {"error": "no_match", "reason": "metadata_not_loaded"}
        
        try:
            from mcp_bcrp.search_engine import SearchEngine
        except ImportError as e:
            logger.error(f"SearchEngine import failed: {e}")
            return {"error": "internal", "reason": str(e)}
        
        engine = SearchEngine(self.df)
        return engine.solve(query)

    def _simple_search(self, query: str, limit: int = 20) -> pd.DataFrame:
        """Fallback simple search"""
        # ... (Previous implementation moved here if needed, or just keep minimal)
        keywords = query.lower().split()
        search_cols = ["Nombre de serie", "Código de serie"]
        valid_cols = [c for c in search_cols if c in self.df.columns]
        if not valid_cols: return pd.DataFrame()
        
        mask = pd.Series(True, index=self.df.index)
        for kw in keywords:
            kw_mask = pd.Series(False, index=self.df.index)
            for col in valid_cols:
                kw_mask |= self.df[col].fillna("").astype(str).str.contains(kw, case=False, regex=False)
            mask &= kw_mask
        return self.df[mask].head(limit)

class AsyncBCRPClient:
    """
    Async client for BCRP (Banco Central de Reserva del Perú) Statistical API.
    Replaces the synchronous 'usebcrp' library for MCP usage.
    """
    BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }

        self.semaphore = asyncio.Semaphore(1)

    async def _fetch(self, url: str) -> Dict[str, Any]:
        """Internal helper to perform async GET request with concurrency limit."""
        async with self.semaphore:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                logger.info(f"Fetching URL: {url} with headers: {self.headers}")
                # Add delay to be nice to the server and avoid rate limit trigger even with sequential
                await asyncio.sleep(0.5) 
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

    def _detect_frequency(self, codes: List[str]) -> str:
        """
        Detect frequency from series code suffix.
        BCRP convention: 
          - 'D' suffix = Daily (PD04638PD)
          - 'M' suffix = Monthly (PN01271PM)
          - 'Q' suffix = Quarterly
          - 'A' suffix = Annual
        """
        if not codes:
            return "monthly"
        # Check first code's suffix
        code = codes[0].upper()
        if len(code) >= 2:
            suffix = code[-1]  # Last char is usually D/M/Q/A
            if suffix == 'D':
                return "daily"
            elif suffix == 'Q':
                return "quarterly"
            elif suffix == 'A':
                return "annual"
        return "monthly"

    def _format_date_for_api(self, date_str: str, frequency: str = "monthly") -> str:
        """
        Format date based on frequency.
        - Daily: YYYY-M-D (e.g., 2024-12-1)
        - Monthly: YYYY-M (e.g., 2024-12)
        """
        if not date_str:
            return date_str
        parts = date_str.split('-')
        
        if frequency == "daily":
            # For daily: need YYYY-M-D format
            if len(parts) == 2:
                # YYYY-MM -> YYYY-M-1 (first day of month)
                return f"{parts[0]}-{int(parts[1])}-1"
            elif len(parts) == 3:
                # YYYY-MM-DD -> YYYY-M-D
                return f"{parts[0]}-{int(parts[1])}-{int(parts[2])}"
        else:
            # Monthly/Quarterly/Annual: YYYY-M
            if len(parts) >= 2:
                return f"{parts[0]}-{int(parts[1])}"
        return date_str

    async def get_series(
        self, 
        codes: List[str], 
        start_date: str = None, 
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Fetch statistical series data from BCRP API.
        
        Automatically detects frequency from series code suffix and formats
        dates accordingly (daily, monthly, quarterly, annual).
        
        Args:
            codes: List of BCRP series codes (e.g., ["PN01652XM", "PD04638PD"])
            start_date: Start date in 'YYYY-MM' or 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM' or 'YYYY-MM-DD' format
        
        Returns:
            pd.DataFrame with columns 'time' and one column per series code.
            Empty DataFrame if series not found or no data available.
        
        Raises:
            httpx.HTTPStatusError: If API returns error (except 404).
        """
        code_str = "-".join(codes)
        url = f"{self.BASE_URL}/{code_str}/json"
        
        # Detect frequency and format dates accordingly
        frequency = self._detect_frequency(codes)
        logger.info(f"Detected frequency: {frequency} for codes: {codes}")
        
        s_date = self._format_date_for_api(start_date, frequency)
        e_date = self._format_date_for_api(end_date, frequency)
        
        # For daily: if only YYYY-MM provided, expand to full month range
        if frequency == "daily" and start_date and end_date:
            # Adjust end_date to last day of month if needed
            e_parts = end_date.split('-')
            if len(e_parts) == 2:
                import calendar
                year, month = int(e_parts[0]), int(e_parts[1])
                last_day = calendar.monthrange(year, month)[1]
                e_date = f"{year}-{month}-{last_day}"
        
        if s_date and e_date:
             url += f"/{s_date}/{e_date}"
        elif s_date:
             url += f"/{s_date}/{s_date}"

        try:
            data = await self._fetch(url)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Series not found: {codes}")
                return pd.DataFrame()
            raise
            
        if "periods" not in data:
            return pd.DataFrame()

        records = []
        for p in data["periods"]:
            row = {"time": p["name"]}
            # 'values' list corresponds to the order of requested codes (mostly)
            # but sometimes BCRP returns "n.d."
            for i, val in enumerate(p["values"]):
                col_name = codes[i] if i < len(codes) else f"series_{i}"
                try:
                    # Handle "n.d." or other non-numeric
                    if isinstance(val, str) and "nir" in val.lower(): # sometimes they return 'No Informado' etc
                         row[col_name] = None
                    elif val == "n.d.":
                         row[col_name] = None
                    else:
                        row[col_name] = float(val)
                except (ValueError, TypeError):
                    row[col_name] = None
            records.append(row)

        df = pd.DataFrame(records)
        return df


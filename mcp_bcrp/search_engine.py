"""
Deterministic Search Engine for BCRP Series.

Pipeline:
1. Canonical Normalization (lowercase, remove accents, stopwords)
2. Attribute Extraction (currency, horizon, component)
3. Hard Filters
4. Fuzzy Scoring with RapidFuzz
5. Ambiguity Detection
"""

import pandas as pd
import logging
import unicodedata
import re
from typing import List, Dict, Any, Set, Optional

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

logger = logging.getLogger("mcp_bcrp")


class SearchEngine:
    """
    Deterministic Search Engine for BCRP Series.
    
    Implements a pipeline for univocal series resolution:
    1. Canonical Normalization
    2. Hard Filters (Currency, Horizon, Component)
    3. Fuzzy Scoring
    4. Ambiguity Detection
    """
    
    STOPWORDS = {'de', 'del', 'el', 'la', 'los', 'las', 'y', 'en', 'al', 'con', 'por'}

    def __init__(self, metadata_df: pd.DataFrame):
        """
        Initialize search engine with BCRP metadata.
        
        Args:
            metadata_df: DataFrame with BCRP series metadata.
        """
        self.df = metadata_df
        self._preprocess_metadata()

    def _normalize(self, text: str) -> str:
        """
        Canonical normalization of text.
        
        Applies: lowercase, accent removal, punctuation removal,
        stopword filtering, and space collapsing.
        
        Args:
            text: Raw input text.
            
        Returns:
            Normalized string with clean tokens.
        """
        if not isinstance(text, str):
            return ""
        
        text = text.lower()
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        clean_tokens = [t for t in tokens if t not in self.STOPWORDS]
        
        return " ".join(clean_tokens)

    def _extract_attributes(self, text_norm: str) -> Dict[str, Any]:
        """
        Extract structured attributes from normalized text.
        
        Args:
            text_norm: Normalized text string.
            
        Returns:
            Dictionary with currency, horizon, component, and scale.
        """
        attrs = {
            "currency": None,
            "horizon": None,
            "component": None,
            "scale": None
        }
        
        tokens = set(text_norm.split())
        
        # Currency detection
        if any(t in tokens for t in ['us', 'usd', 'dolares']):
            attrs['currency'] = 'usd'
        elif any(t in tokens for t in ['s', 'pen', 'soles']):
            attrs['currency'] = 'pen'
            
        # Horizon detection
        if "corto" in text_norm:
            attrs['horizon'] = 'corto'
        elif "largo" in text_norm:
            attrs['horizon'] = 'largo'
            
        # Component detection
        if "activos" in text_norm:
            attrs['component'] = 'activos'
        elif "pasivos" in text_norm:
            attrs['component'] = 'pasivos'
        
        # Scale detection
        if "millones" in text_norm:
            attrs['scale'] = 'millones'
        elif "miles" in text_norm:
            attrs['scale'] = 'miles'
            
        return attrs

    def _preprocess_metadata(self):
        """Pre-calculate normalized tokens and attributes for all series."""
        if self.df.empty:
            self.search_corpus = []
            return

        processed = []
        for idx, row in self.df.iterrows():
            raw_name = str(row.get('Nombre de serie', ''))
            name_norm = self._normalize(raw_name)
            attrs = self._extract_attributes(name_norm)
            
            item = {
                "idx": idx,
                "codigo_serie": row.get("Código de serie") or row.get("Codigo de serie"),
                "name_original": raw_name,
                "name_norm": name_norm,
                "tokens": set(name_norm.split()),
                "currency": attrs['currency'],
                "horizon": attrs['horizon'],
                "component": attrs['component'],
                "scale": attrs['scale']
            }
            processed.append(item)
            
        self.search_corpus = processed

    def solve(self, query: str) -> Dict[str, Any]:
        """
        Resolve query to a single series deterministically.
        
        Args:
            query: Search query (e.g., "tipo de cambio USD")
            
        Returns:
            Dict with 'codigo_serie' and 'confidence' on success,
            or 'error' and 'reason' on failure/ambiguity.
        """
        if not self.search_corpus:
            return {"error": "no_match", "reason": "empty_corpus"}

        # Parse and normalize query
        q_norm = self._normalize(query)
        q_attrs = self._extract_attributes(q_norm)
        q_tokens = set(q_norm.split())
        
        if not q_tokens:
            return {"error": "no_match", "reason": "empty_query"}

        candidates = self.search_corpus
        
        # Apply hard filters (currency, horizon, component)
        if q_attrs['currency']:
            candidates = [c for c in candidates if c['currency'] == q_attrs['currency']]
            
        if q_attrs['horizon']:
            candidates = [c for c in candidates if c['horizon'] == q_attrs['horizon']]
            
        if q_attrs['component']:
            candidates = [c for c in candidates if c['component'] == q_attrs['component']]
             
        if not candidates:
            return {"error": "no_match", "reason": "filters_eliminated_all"}

        # Score candidates using fuzzy matching
        scored_candidates = []
        for c in candidates:
            score = 0
            if fuzz:
                score = fuzz.token_sort_ratio(q_norm, c['name_norm'])
            
            # Penalize missing query tokens
            q_extras = len(q_tokens - c['tokens'])
            final_score = score - (5 * q_extras)
            
            if final_score >= 80:
                scored_candidates.append({
                    "series": c,
                    "score": final_score,
                    "original_score": score,
                    "missing_query_tokens": q_tokens - c['tokens']
                })

        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        if not scored_candidates:
            return {"error": "no_match", "reason": "low_score"}

        top = scored_candidates[0]
        
        # Single match: return directly
        if len(scored_candidates) == 1:
            return {
                "codigo_serie": top['series']['codigo_serie'],
                "confidence": round(top['score'] / 100.0, 2),
                "name": top['series']['name_original']
            }
            
        # Multiple matches: check for ambiguity
        candidates_top_tier = [
            x for x in scored_candidates 
            if x['score'] >= (top['score'] - 5)
        ]
        
        currencies = set(x['series']['currency'] for x in candidates_top_tier)
        components = set(x['series']['component'] for x in candidates_top_tier)
        
        if len(currencies) > 1 or len(components) > 1:
            return {
                "error": "ambiguedad",
                "candidates": [x['series']['codigo_serie'] for x in candidates_top_tier[:5]],
                "reason": "mixed_attributes_in_top_results"
            }
             
        # Deterministic winner
        return {
            "codigo_serie": top['series']['codigo_serie'],
            "confidence": round(top['score'] / 100.0, 2),
            "name": top['series']['name_original']
        }

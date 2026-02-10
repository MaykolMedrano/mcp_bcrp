"""
Deterministic Search Engine for BCRP Series.

Pipeline:
1. Canonical Normalization (lowercase, remove accents, synonyms)
2. Attribute Extraction (currency, horizon, component, side)
3. Hard Filters
4. Fuzzy Scoring with RapidFuzz (Token Set Ratio)
5. Interactive Candidate Resolution
"""

import pandas as pd
import logging
import unicodedata
import re
from typing import Dict, Any

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

logger = logging.getLogger("mcp_bcrp")


class SearchEngine:
    """
    Interactive Search Engine for BCRP Series.
    
    Implements a pipeline for robust series resolution:
    1. Canonical Normalization with Synonym Support
    2. Attribute Filtering (Currency, Side)
    3. Fuzzy Set Scoring
    4. Multi-candidate Result Generation
    """
    
    STOPWORDS = {'de', 'del', 'el', 'la', 'los', 'las', 'y', 'en', 'al', 'con', 'por', 'precio', 'valor', 'indicador'}
    
    # Synonym map for common abbreviations
    SYNONYMS = {
        "tc": "tipo cambio",
        "t.c.": "tipo cambio",
        "pbi": "producto bruto interno",
        "internacional": "lme londres Chicago nymex",
    }

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
        synonym expansion, stopword filtering.
        """
        if not isinstance(text, str):
            return ""
        
        text = text.lower()
        # Remove accents
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        # Replace punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Apply synonyms (simple replacement)
        for syn, target in self.SYNONYMS.items():
            if syn in text.split():
                text = text.replace(syn, target)
        
        tokens = text.split()
        clean_tokens = [t for t in tokens if t not in self.STOPWORDS]
        
        return " ".join(clean_tokens)

    def _extract_attributes(self, text_norm: str) -> Dict[str, Any]:
        """Extract structured attributes to help disambiguate."""
        attrs = {
            "currency": None,
            "side": None,  # compra / venta
            "horizon": None,
            "component": None
        }
        
        tokens = set(text_norm.split())
        
        # Currency
        if any(t in tokens for t in ['us', 'usd', 'dolares']):
            attrs['currency'] = 'usd'
        elif any(t in tokens for t in ['s', 'pen', 'soles']):
            attrs['currency'] = 'pen'
            
        # Side (Critical for FX)
        if "compra" in tokens:
            attrs['side'] = 'compra'
        elif "venta" in tokens:
            attrs['side'] = 'venta'
            
        # Horizon
        if "corto" in tokens:
            attrs['horizon'] = 'corto'
        elif "largo" in tokens:
            attrs['horizon'] = 'largo'
            
        return attrs

    def _preprocess_metadata(self):
        """Pre-calculate normalized search corpus."""
        if self.df.empty:
            self.search_corpus = []
            return

        processed = []
        for idx, row in self.df.iterrows():
            raw_name = str(row.get('Nombre de serie', ''))
            name_norm = self._normalize(raw_name)
            attrs = self._extract_attributes(name_norm)
            
            # Use original code column names if possible
            code = row.get("Código de serie") or row.get("Codigo de serie")
            
            item = {
                "idx": idx,
                "codigo_serie": code,
                "name_original": raw_name,
                "name_norm": name_norm,
                "tokens": set(name_norm.split()),
                "currency": attrs['currency'],
                "side": attrs['side'],
                "horizon": attrs['horizon']
            }
            processed.append(item)
            
        self.search_corpus = processed

    def solve(self, query: str) -> Dict[str, Any]:
        """
        Resolve query with interactive candidate logic.
        """
        if not self.search_corpus:
            return {"error": "no_match", "reason": "empty_corpus"}

        q_norm = self._normalize(query)
        q_attrs = self._extract_attributes(q_norm)
        q_tokens = set(q_norm.split())
        
        if not q_tokens:
            return {"error": "no_match", "reason": "empty_query"}

        # Scoring
        scored = []
        for c in self.search_corpus:
            if not fuzz:
                # Basic token overlap fallback
                intersection = len(q_tokens & c['tokens'])
                score = (intersection / len(q_tokens)) * 100 if q_tokens else 0
            else:
                # Token Set Ratio is perfect for finding "query" inside "long technical title"
                score = fuzz.token_set_ratio(q_norm, c['name_norm'])
            
            # Boost if specific side (compra/venta) matches
            if q_attrs['side'] and c['side'] == q_attrs['side']:
                score += 5
            elif q_attrs['side'] and c['side'] and c['side'] != q_attrs['side']:
                score -= 10
            
            if score >= 65:
                scored.append({
                    "codigo_serie": c['codigo_serie'],
                    "name": c['name_original'],
                    "score": score
                })

        scored.sort(key=lambda x: x['score'], reverse=True)
        
        if not scored:
            return {"error": "no_match", "reason": "low_confidence"}

        # Logic for result type
        top_score = scored[0]['score']
        
        # 1. Check for ties or very close matches at the top
        # If multiple series have top_score, or are very close (within 2 pts), return candidates.
        high_tier = [s for s in scored if s['score'] >= (top_score - 2)]
        
        if len(high_tier) > 1 and top_score < 100:
             # Ambiguity if multiple high matches, unless one is perfect 100 and there are no other 100s
             pass # fall through to candidates logic
        elif len(high_tier) == 1 and top_score >= 85:
            # Single clear winner with good score
            return {
                "codigo_serie": high_tier[0]['codigo_serie'],
                "confidence": round(high_tier[0]['score'] / 100.0, 2),
                "name": high_tier[0]['name']
            }
        
        # If top_score is 100, but there are multiple 100s, it's ambiguous
        top_tier_100 = [s for s in scored if s['score'] == 100]
        if len(top_tier_100) == 1:
             return {
                "codigo_serie": top_tier_100[0]['codigo_serie'],
                "confidence": 1.0,
                "name": top_tier_100[0]['name']
            }

        # 2. Interactive Candidates
        # Return top 5 matches if confidence is mixed or tied
        candidates = []
        seen_codes = set()
        for s in scored[:5]:
            if s['codigo_serie'] not in seen_codes:
                candidates.append({
                    "codigo": s['codigo_serie'],
                    "nombre": s['name']
                })
                seen_codes.add(s['codigo_serie'])
        
        return {
            "error": "ambiguedad",
            "reason": "multiple_candidates",
            "candidates": candidates
        }

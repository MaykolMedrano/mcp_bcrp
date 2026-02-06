from fastmcp import FastMCP
from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata
import pandas as pd
import json
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tempfile
import os

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_bcrp")

# Initialize FastMCP
mcp = FastMCP("bcrp-agent")

# Initialize Clients
bcrp_client = AsyncBCRPClient()
metadata_client = BCRPMetadata()

# --- Internal Logic ---

async def _search_series(query: str) -> str:
    """
    Uses robust local metadata search.
    Now returns deterministic result via SearchEngine.solve().
    """
    try:
        await metadata_client.load()
        
        logger.info(f"Searching for: {query}")
        
        # First try deterministic solve
        result = metadata_client.solve(query)
        
        if "error" not in result:
            # Success - return JSON with the match
            return json.dumps(result, ensure_ascii=False)
        
        if result.get("error") == "ambiguedad":
            # Return ambiguity info for user to refine
            return json.dumps(result, ensure_ascii=False)
        
        # Fallback to fuzzy search for exploratory queries
        df = metadata_client.search(query)
        
        if df.empty:
            return "No series found matching that query."
        return df.to_json(orient='records')
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Search failed: {str(e)}"

async def _get_data(series_codes: list[str], period: str = None) -> str:
    try:
        logger.info(f"Fetching data for: {series_codes} range: {period}")
        
        # Parse period if needed, but client handles basic string appending
        # We might need to handle the specific format "start_date/end_date" if provided as one string
        start = None
        end = None
        start = None
        end = None
        if period:
            parts = period.split('/')
            if len(parts) == 2:
                start, end = parts
            elif len(parts) == 1:
                 # Check if it looks like a year "YYYY"
                 if len(period) == 4 and period.isdigit():
                     start = f"{period}-01"
                     end = f"{period}-12"
                 else:
                     start = period # fallback
                     # If only start is provided, client won't append it currently.
                     # We should probably set end to 'now' or similar if start is provided?
                     # Or rely on client update. But client needs start AND end.
                     # If only start provided, let's duplicate it? or leave end=None?
                     # If I set end=start, it fetches one month.
                     pass
        
        df = await bcrp_client.get_series(series_codes, start_date=start, end_date=end)
        
        if df.empty:
            return "No data found for the specified parameters."
            
        return df.to_json(orient='records', date_format='iso')
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return f"Error fetching data: {str(e)}"

# --- MCP Tools ---

@mcp.tool()
async def search_series(query: str) -> str:
    """
    Search for BCRP economic indicators by keyword.
    
    Uses deterministic search with fuzzy matching. Returns the best match
    or an ambiguity error if multiple matches are equally scored.
    
    Args:
        query: Search term (e.g., "tipo de cambio", "inflacion", "PBI")
    
    Returns:
        JSON string with match result containing codigo_serie and confidence,
        or error details if ambiguous or not found.
    """
    return await _search_series(query)

@mcp.tool()
async def get_data(series_codes: list[str], period: str = None) -> str:
    """
    Fetch time series data for specific BCRP series codes.
    
    Args:
        series_codes: List of BCRP series codes (e.g., ["PN01652XM", "PD04638PD"])
        period: Date range in format 'YYYY-MM/YYYY-MM' or single 'YYYY-MM'.
                If None, returns all available data.
    
    Returns:
        JSON string with array of records containing 'time' and values.
    """
    return await _get_data(series_codes, period)

@mcp.tool()
async def get_table(
    series_codes: list[str], 
    names: list[str] = None, 
    period: str = None
) -> str:
    """
    Get a formatted table with custom column names.
    
    Args:
        series_codes: List of BCRP series codes to retrieve
        names: Optional custom names for columns (must match series_codes length)
        period: Date range in format 'YYYY-MM/YYYY-MM' or 'YYYY'
    
    Returns:
        JSON string with formatted table data.
    """
    try:
        # 1. Fetch Data
        data_json = await _get_data(series_codes, period)
        if data_json.startswith("Error") or data_json.startswith("No data"):
            return data_json
            
        df = pd.read_json(data_json, orient='records')
        if df.empty:
            return "No data found."
            
        # 2. Resolve Names if not provided
        if not names:
            await metadata_client.load()
            names = metadata_client.get_series_names(series_codes)
            
        # 3. Rename columns
        mapping = {code: name for code, name in zip(series_codes, names)}
        df.rename(columns=mapping, inplace=True)
            
        return df.to_json(orient='records', date_format='iso', indent=2)
        

    except Exception as e:
        return f"Table generation failed: {str(e)}"

@mcp.tool()
async def plot_chart(
    series_codes: list[str], 
    period: str = None, 
    title: str = None,
    names: list[str] = None,
    output_path: str = None
) -> str:
    """
    Generate a professional chart for BCRP series data.
    Returns the path to the saved PNG file.
    
    Args:
        series_codes: List of BCRP series codes to plot
        period: Date range in format 'YYYY-MM/YYYY-MM' (optional)
        title: Custom chart title (optional, uses series name if not provided)
        names: Custom names for each series in legend (optional)
        output_path: Custom output path for the chart (optional)
    """
    try:
        # 1. Fetch Data
        data_json = await _get_data(series_codes, period)
        if data_json.startswith("Error") or data_json.startswith("No data"):
            return data_json
            
        df = pd.read_json(data_json, orient='records')
        if df.empty:
            return "No data found to plot."
        
        # 2. Setup plot style
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 6), dpi=120)
        
        # 3. Parse time column (BCRP uses Spanish month abbreviations)
        if 'time' in df.columns:
            # Spanish month mapping
            spanish_months = {
                'Ene': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Abr': 'Apr',
                'May': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Ago': 'Aug',
                'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dic': 'Dec'
            }
            
            def parse_spanish_date(date_str):
                """Convert BCRP Spanish date format to datetime."""
                try:
                    for es, en in spanish_months.items():
                        date_str = date_str.replace(es, en)
                    return pd.to_datetime(date_str, format='%b.%Y')
                except Exception:
                    return pd.to_datetime(date_str)
            
            df['time'] = df['time'].apply(parse_spanish_date)
            df = df.set_index('time')
        
        # 4. Resolve Names if not provided
        if not names:
            await metadata_client.load()
            names = metadata_client.get_series_names(series_codes)

        # 5. Plot each series
        colors = ['#1a5fb4', '#e01b24', '#33d17a', '#ff7800', '#9141ac']
        for idx, code in enumerate(series_codes):
            col_name = code if code in df.columns else (names[idx] if names and names[idx] in df.columns else None)
            if col_name:
                series = df[col_name].dropna()
                label = names[idx] if names and idx < len(names) else col_name
                color = colors[idx % len(colors)]
                ax.plot(series.index, series.values, linewidth=2.5, 
                       label=label, color=color)
                
                # Fill area for first series
                if idx == 0:
                    ax.fill_between(series.index, series.values, 
                                   alpha=0.15, color=color)
        
        # 5. Format chart
        chart_title = title or f'Serie BCRP: {series_codes[0]}'
        ax.set_title(chart_title, fontsize=14, fontweight='bold', 
                    pad=15, color='#2c3e50')
        ax.set_xlabel('Periodo', fontsize=11, labelpad=10, color='#34495e')
        ax.set_ylabel('Valor', fontsize=11, labelpad=10, color='#34495e')
        
        # Date formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.xticks(rotation=45, ha='right')
        
        # Grid and legend
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper left', frameon=True, framealpha=0.95)
        
        # Source annotation
        codes_str = ', '.join(series_codes)
        fig.text(0.99, 0.01, 
                f'Fuente: BCRP | Series: {codes_str}',
                ha='right', va='bottom', fontsize=8, 
                color='#7f8c8d', style='italic')
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.18)
        
        # 6. Save chart
        if output_path:
            save_path = output_path
        else:
            save_path = os.path.join(tempfile.gettempdir(), 
                                    f'bcrp_chart_{series_codes[0]}.png')
        
        fig.savefig(save_path, dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        
        logger.info(f"Chart saved to: {save_path}")
        return json.dumps({
            "status": "success",
            "chart_path": save_path,
            "series": series_codes,
            "message": f"Chart saved to {save_path}"
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return f"Chart generation failed: {str(e)}"

@mcp.prompt()
def economista_peruano(topic: str = "economía peruana"):
    """
    Prompt para actuar como un experto economista peruano (BCRP).
    Usa este prompt para analizar datos con rigor técnico y contexto local.
    """
    return f"""
    Actúa como un Economista Senior del Banco Central de Reserva del Perú (BCRP).
    
    Tu objetivo es analizar: {topic}
    
    PERFIL:
    - Eres riguroso, técnico pero claro.
    - Usas terminología precisa (ej: "Tipo de Cambio Interbancario", "Inflación subyacente").
    - Siempre citas el código de la serie (ej: PN01234PM) como fuente de verdad.
    - Conoces el contexto económico reciente del Perú (inflación controlada, volatilidad cambiaria, impacto minero).
    - Evitas especulaciones políticas; te centras en los fundamentos macroeconómicos.

    FORMATO DE RESPUESTA:
    1. **Resumen Ejecutivo**: 2-3 líneas con la conclusión principal.
    2. **Análisis de Datos**: Presenta la tabla de datos y destaca tendencias (crecimiento, caída, estabilidad).
    3. **Contexto**: Explica por qué ocurre esto (ej: "por el alza del precio del cobre" o "efecto base").
    4. **Fuente**: Cita siempre "Fuente: BCRP (Serie [CODIGO])".

    Si te faltan datos, usa las herramientas disponibles para buscarlos antes de responder.
    """

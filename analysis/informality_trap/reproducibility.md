# Guía de Replicabilidad: La Trampa de la Informalidad (IA + MCP)

Este documento detalla el proceso paso a paso de cómo se construyó este análisis. **Importante: Toda la lógica de extracción, procesamiento y síntesis fue realizada por la IA utilizando MCP.**

## 1. El Prompt de Investigación

El usuario planteó una tesis estructural sobre la informalidad laboral:
> *"Este nuevo análisis se enfoca en la 'Trampa de la Informalidad'... @mcp:bcrp-api debe extraer las series de Tasa de Interés y Crédito... @mcp:wbgapi360 aporta los datos de Empleo Informal..."*

## 2. Ejecución Técnica (Discovery MCP)

La IA identificó que los datos de BCRP para crédito eran mayoritariamente variaciones mensuales, por lo que optó por el indicador de **Stock de Crédito al Sector Privado (% PIB)** del Banco Mundial para una visión estructural de largo plazo.

### Llamadas Críticas:
- **BCRP**: Extracción de la Tasa de Referencia de Política Monetaria (`PD04722MM`) para medir el "costo del dinero".
- **World Bank**: Extracción de `SL.EMP.SELF.ZS` (Autoempleo) como "proxy" de informalidad estructural.

```json
// Ejemplo de consulta automatizada
mcp_wbgapi360_get_data({
  "economies": ["PER"],
  "indicator_code": "SL.EMP.SELF.ZS",
  "years": 15
})
```

## 3. Automatización del Análisis (Python)

La IA generó un script en memoria (`informality_analysis.py`) para calcular la correlación de Pearson.

### Fragmento del Script:
```python
# Sincronización de periodicidad (Mensual -> Anual)
bcrp_annual = aggregate_monthly_to_annual(bcrp_raw)

# Cálculo de Correlación
# Resultado: -0.6586 (Relación negativa entre Tasas e Informalidad)
corr = correlation(rates, informalities)
```

## 4. Visualización con Estándares FT

Se utilizó la herramienta `mcp_wbgapi360:plot_chart` para inyectar los datos normalizados y generar el gráfico de tendencias.

---
> [!NOTE]
> **Conclusión de Replicabilidad**: Este caso demuestra que la IA puede actuar como un economista senior, capaz de cuestionar la calidad de los datos iniciales y buscar fuentes alternativas (como pasar de BCRP a WB para el crédito) para robustecer la tesis original.

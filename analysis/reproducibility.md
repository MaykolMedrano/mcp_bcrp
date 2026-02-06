# Guía de Replicabilidad: Sinergia IA + MCP

Este documento detalla el protocolo para replicar el análisis de impacto de los shocks del precio del oro en la deforestación de Perú. Este proceso es un ejemplo de **Analítica Aumentada**, combinando el razonamiento de la IA con datos en tiempo real de fuentes oficiales.

## 1. El Rol de las Herramientas

### IA (Cerebro y Automatización)
- **Superación del Corte de Conocimiento**: Aunque el entrenamiento base de la IA (como este modelo Gemini) tiene un límite temporal (cutoff), el acceso a los MCP permite "ver el presente". 
- **Scripting Automático**: El script de procesamiento (`process_data.py`) fue generado automáticamente por la IA "al vuelo" para resolver el problema de alineación de frecuencias (mensual vs anual).
- **Razonamiento Estadístico**: La IA identifica las correlaciones y propone las métricas de normalización.

### MCP (Fuente de Verdad y Validación)
- **Datos Validados**: Los indicadores no son "alucinados". Son consultados directamente a las APIs del BCRP y el Banco Mundial a través de servidores MCP.
- **Acceso Reciente**: Gracias al MCP, pudimos analizar precios del oro de **enero de 2026**, algo imposible con el entrenamiento estático de cualquier IA.

## 2. Estrategia de Prompting

Para replicar con éxito, el usuario debe proporcionar un prompt que defina el **objetivo analítico** y las **fuentes**:
> *Prompt Ejemplo*: "@mcp:bcrp-api necesito el precio del oro de los últimos 20 años y @mcp:wbgapi360 indicadores de deforestación para Perú. Analiza el impacto de los shocks de precio en la pérdida forestal y genera un gráfico comparativo."

## 3. Requisitos del Entorno

- **MCP Servers**: `bcrp-api` y `wbgapi360`.
- **Python 3.x**: Para ejecutar el script de procesamiento generado.

## 4. Protocolo de Ejecución

### Fase A: Extracción de Datos
1. **Oro**: Serie `PN01654XM` via `bcrp-api:get_data`.
2. **Deforestación**: `AG.LND.FRST.K2` via `wbgapi360:get_data`.

### Fase B: Procesamiento (IA-Generated Script)
El procesamiento lógico se encuentra encapsulado en el script `process_data.py`, el cual automatiza la limpieza y genera el JSON necesario para la visualización final.
1. **Alineación**: Agrega datos mensuales a promedios anuales.
2. **Normalización**: Escala [0, 100] para visualización de tendencias.
3. **Validación**: Cálculo de Correlación de Pearson.

### Fase C: Visualización (MCP-Enhanced)
Inyección del JSON procesado en `wbgapi360:plot_chart` para generar visualizaciones con estilo profesional (FT-style).

---
> [!IMPORTANT]
> **Conclusión**: Este workflow demuestra que la IA no es solo una base de datos estática, sino un motor de ejecución que utiliza los MCP como sus "ojos y manos" en el mundo real.

---
> [!IMPORTANT]
> **Nota de Transparencia**: Este análisis utiliza datos oficiales reportados por el gobierno peruano y el Banco Mundial. Cualquier discrepancia en versiones futuras de los datos puede alterar levemente el coeficiente de correlación.

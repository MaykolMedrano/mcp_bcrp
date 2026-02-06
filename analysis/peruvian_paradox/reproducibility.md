# Guía de Replicabilidad: La Paradoja Peruana (IA + MCP)

Este documento explica paso a paso cómo se generó esta investigación. Es fundamental entender que **este análisis fue concebido, ejecutado y procesado íntegramente por la Inteligencia Artificial (IA) utilizando herramientas de MCP**, sin intervención manual del usuario en el cálculo o búsqueda de datos.

## 1. El Prompt Original (La Intención)

Todo comenzó con un prompt de alta complejidad conceptual enviado por el usuario:
> *"La aparente paradoja de la economía peruana sugiere que la estabilidad monetaria gestionada por el BCRP actúa como una armadura... Requiero que @mcp:bcrp-api provea el Tipo de Cambio Real Multilateral y @mcp:wbgapi360 la Productividad Total..."*

### Por qué funciona:
La IA no solo leyó el texto, sino que identificó las **hipótesis económicas** subyacentes y seleccionó automáticamente los indicadores que podían probarlas o refutarlas.

## 2. Descubrimiento y Validación (MCP)

La IA utilizó el protocolo **MCP** para superar el límite de su entrenamiento estático.

### Snippets de herramientas:
1.  **Búsqueda Semántica**: Se usó `bcrp_api:search_series` para encontrar códigos como `PN01259PM` (TCR Multilateral) y `PN00120MM` (Tasa Interbancaria).
2.  **Consulta de Verdades**: Se usó `wbgapi360:get_data` para extraer indicadores de pobreza del Banco Mundial actualizados a 2024.

```json
// Ejemplo de llamada interna MCP realizada por la IA
mcp_bcrp-api_get_data({
  "series_codes": ["PN01271PM", "PN00120MM", "PN01259PM"],
  "period": "2015-01/2026-02"
})
```

## 3. Procesamiento y Automatización (Scripting IA)

Dado que los datos del BCRP son mensuales y los del Banco Mundial son anuales, la IA generó automáticamente un script de Python para sincronizarlos. **El usuario no escribió ni una línea de este código.**

### Lógica del Script (`paradox_analysis.py`):
```python
# Snippet del código generado por la IA
def correlation(x, y):
    n = len(x)
    mu_x = sum(x)/n
    mu_y = sum(y)/n
    # Cálculo de Pearson automático
    num = sum((xi - mu_x) * (yi - mu_y) for xi, yi in zip(x, y))
    den = (sum((xi - mu_x)**2 for xi in x) * sum((yi - mu_y)**2 for yi in y))**0.5
    return num/den
```

## 4. Visualizaciones Profesional (MCP-Plot)

Finalmente, la IA no usó librerías genéricas, sino la herramienta `plot_chart` del MCP de World Bank para asegurar que el gráfico siguiera estándares de publicación (Financial Times style).

## Conclusión: El Modelo de Analítica Aumentada

| Componente | Rol en esta Investigación |
| :--- | :--- |
| **Usuario** | Define la tesis y el contexto narrativo. |
| **IA (Gemini)** | Actúa como el científico de datos, genera código y redacta conclusiones. |
| **MCP** | Provee la infraestructura de datos en tiempo real y herramientas de visualización validadas. |

> [!IMPORTANT]
> **Nada de lo aquí expuesto es manual.** Es el resultado de una orquestación automatizada donde la IA utiliza el MCP como su interfaz táctica con el mundo financiero real.

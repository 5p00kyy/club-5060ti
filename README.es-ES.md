# club-5060ti

Recetas prácticas de LLM locales, comprobantes de benchmarks y notas de configuración para sistemas con RTX 5060 Ti 16GB.

El enfoque del proyecto es sencillo: hacer que la inferencia local en la RTX 5060 Ti sea más reproducible ya sea con una tarjeta, dos tarjetas o configuraciones comunitarias más grandes. Algunas notas de llama.cpp/GGUF también son útiles en otras tarjetas NVIDIA, pero los resultados de GPUs que no sean 5060 Ti o configuraciones mixtas deben reportarse como canales de hardware separados. Cada resultado útil debe venir acompañado de la forma de lanzamiento, el contexto de hardware, los detalles del modelo, el método de benchmark y las advertencias necesarias para que otra persona pueda reproducirlo o mejorarlo.

## Historial de Estrellas

<p align="center">
  <a href="https://www.star-history.com/?repos=5p00kyy%2Fclub-5060ti&type=date&legend=top-left">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=5p00kyy/club-5060ti&type=date&theme=dark&legend=top-left" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=5p00kyy/club-5060ti&type=date&legend=top-left" />
      <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=5p00kyy/club-5060ti&type=date&legend=top-left" />
    </picture>
  </a>
</p>

## Empieza Aquí

| Ruta | Usa esto cuando | Punto de entrada |
| --- | --- | --- |
| Canales de hardware | Quieras entender cómo se separan los resultados de 1x, 2x, 4x/múltiples y otras GPUs CUDA. | docs/hardware-lanes.md |
| 1x RTX 5060 Ti | Busques los mejores ajustes para una sola tarjeta y configuraciones iniciales conservadoras. | docs/single-5060ti.md |
| 2x RTX 5060 Ti | Busques recetas de doble 16GB para modelos de clase 27B y de contexto largo. | docs/llamacpp-qwen36.md |
| Otras GPUs CUDA | Quieras adaptar las recetas a configuraciones NVIDIA que no sean 5060 Ti o de arquitectura mixta. | docs/gpu-compatibility.md |
| Explorador de resultados | Quieras comparar comprobantes de benchmark, filtrar por nivel e inspeccionar configuraciones de servicio. | https://5p00kyy.github.io/club-5060ti/ |
| Protocolo de benchmark | Quieras enviar o comparar un resultado sin mezclar métodos. | docs/benchmark-protocol.md |
| Enviar un resultado | Busques una ruta de contribución estructurada y rápida. | docs/community-result-template.md |

## Dirección Actual

club-5060ti recopila recetas y comprobantes de benchmark probados para la RTX 5060 Ti. Es primeramente un proyecto de 5060 Ti, no específicamente un proyecto de dual-5060 Ti: las configuraciones de una sola tarjeta, doble tarjeta y configuraciones de 5060 Ti más grandes son útiles siempre que estén etiquetadas claramente. No pretende afirmar que solo las tarjetas Blackwell puedan usar estos flujos de trabajo; mantiene los canales de la 5060 Ti claros para que los resultados comunitarios de otras tarjetas sigan siendo comparables en lugar de mezclarse. El explorador de resultados se construye a partir de archivos JSON guardados en `data/results/`, por lo que la documentación, los scripts y el sitio estático describen la misma evidencia.

Las filas importadas de `llm-bench` son datos históricos archivados hasta que se vuelvan a ejecutar bajo el protocolo de benchmark. Son una procedencia útil, no evidencia principal.

## Sistema de Niveles (Tiers)

A cada resultado de benchmark se le asigna un nivel para ayudar a los visitantes a encontrar rápidamente configuraciones útiles:

- **Recommended (Recomendado)** - La mejor configuración conocida de velocidad/ajuste para el canal de GPU. No es un respaldo de calidad; significa que esta es la configuración que se debe probar primero para ese modelo y hardware.
- **Capable (Capaz)** - Funciona bien como una opción sólida. Incluye quants alternativos, variantes de experimentos de caché KV y fusiones de fine-tune como Qwopus.
- **Experimental** - Ajustes forzados, configuraciones inusuales e importaciones heredadas obsoletas. Interesantes pero no para uso diario.

Los niveles se pueden filtrar directamente en el explorador de resultados.

## Base Probada

Hardware semilla:

- GPUs: 2x NVIDIA GeForce RTX 5060 Ti 16GB
- Driver: 595.58.03
- VRAM Total: 32GB entre dos tarjetas
- Sistema: Dell Precision Tower 7810, placa Dell 0GWHMW
- CPU: 2x Intel Xeon E5-2680 v4
- Memoria del host: 128GB DDR4-2133
- Entorno de inferencia: Proxmox LXC con 16 vCPU y 60GB de RAM asignados
- Ancho de enlace PCIe: ambas tarjetas RTX 5060 Ti funcionan a x8 en este host

Consulta `docs/hardware.md` para ver la base completa y las notas de hardware.

## Índice de Recetas

| Canal | Modelo | Evidencia | Notas |
| --- | --- | --- | --- |
| upstream llama.cpp | Qwen3.6 27B GGUF | Receta semilla | Ruta densa recomendada para doble tarjeta. Q6_K a 131K ctx con f16 KV y MTP n=3 ofrece 45-55 tok/s de decode. La referencia de contexto largo sostenido (87K prompt, 742 tokens generados, 21.7 tok/s decode) usó Q6_K_XL a 184K ctx. Q3_K_XL en una sola tarjeta es el ajuste económico recomendado a 204K ctx. |
| upstream llama.cpp | Qwen3.5 9B GGUF | Receta semilla | Ruta de contexto largo pequeña; canal de cordura útil para tarjetas 1x y 2x. Modelo inicial recomendado en una sola tarjeta. |
| upstream llama.cpp | Qwen3.6 35B-A3B GGUF | Receta semilla | Ruta MoE fuerte. Recomendado tanto en canales 1x (IQ3_XXS) como 2x (Q5_K_S). El modelo práctico más rápido del conjunto de datos. |
| upstream llama.cpp | Qwen3.5 122B-A10B GGUF | Receta semilla | MoE grande/forzado. IQ4_XS en 2 tarjetas con MTP n=4. Recomendado para el máximo conteo de parámetros. |
| upstream llama.cpp | Qwopus3.6 27B / 35B-A3B | Receta semilla | Resultados de fusión de fine-tune. Nivel "Capable"; alternativa interesante pero no recomendación principal. |
| BeeLlama | Qwen3.6 27B / 35B-A3B DFlash | Filas semilla exploratorias | El 27B Q3_K_XL 8K DFlash en una sola tarjeta funciona; el 35B-A3B DFlash en una sola tarjeta mejora la salida con formato de código. Motor alternativo, nivel "Capable". |
| ik_llama.cpp | Qwen3.6 27B IQ4/IQ5 | Verificación de ajuste exploratoria | El ajuste de forma 105k q4-KV en una sola tarjeta encaja; las filas de benchmark limpias necesitan limpieza de chat-template/no-thinking. |
| vLLM | Qwen3.6 27B NVFP4/MTP | Objetivo de comparación | Existen notas históricas, pero esto necesita un JSON de benchmark actual antes de ser promovido. |

## Resultados y Datos

Los archivos de resultados canónicos residen en `data/results/` y siguen el esquema `data/schema/benchmark-result.schema.json`.

Construir los datos del sitio estático:

~~~bash
python3 scripts/build_site_data.py
~~~

Validar el JSON de resultados:

~~~bash
python3 scripts/validate_results.py data/results
~~~

Ejecutar un benchmark compatible con OpenAI siguiendo el protocolo:

~~~bash
python3 scripts/run_openai_bench.py \
  --base-url http://127.0.0.1:8080/v1 \
  --model Qwen3.6-27B \
  --prompt-set short-chat \
  --prompt-set code-generate \
  --prompt-set agent-tool \
  --runs 1 \
  --no-thinking \
  --output data/results/my-run.json
~~~

Las antiguas filas de resumen de `llm-bench` han sido importadas en `data/results/llm-bench-legacy-import.json` como datos históricos archivados (nivel experimental). Vuelve a ejecutarlas bajo el protocolo de benchmark antes de usarlas para comparaciones.

El explorador alojado muestra tarjetas de modelos agrupadas por modelo y configuración, con filtrado por nivel, sparklines a través de tipos de prompt y la configuración de servicio en la sublínea de la tarjeta. `Generation tok/s` es la velocidad de tokens de salida; `prompt eval tok/s` es la velocidad de procesamiento de prompt/prefill. El modo MTP/especulación y modo thinking se muestran en cada tarjeta y se pueden filtrar. Activa "raw runs" en el explorador para inspeccionar mediciones repetidas.

Para la configuración de doble tarjeta Qwen3.6 27B Q6_K (131K ctx, f16 KV, MTP n=3), las filas de prompt de benchmark muestran 45-55 tok/s de decode. Una ejecución anterior de Q6_K_XL a 184K ctx sostuvo 21.7 tok/s de decode en un prompt de 87K tokens (`87293/742`, `420.14 tok/s` prompt eval), confirmando que el modelo maneja contextos profundos mucho más allá de la ventana de benchmark estándar.

Se espera que los resultados crezcan con el tiempo. Los nuevos reportes comunitarios pueden agregarse como notas archivadas, evidencia de recetas, filas de benchmark o reproducciones verificadas, dependiendo de qué tan completos y comparables sean.

## Próximos Datos Útiles

Las nuevas contribuciones más útiles son:

- Resultados de 3x/4x+ RTX 5060 Ti con topología PCIe completa.
- Filas comparativas de 2x RTX 5060 Ti con y sin MTP para el mismo modelo 27B, quant, contexto y caché KV.
- Filas de Qwen3.6 35B A3B de diferentes sistemas 5060 Ti, especialmente configuraciones de doble tarjeta y de mayor número de tarjetas.
- Benchmarks de RTX 5060 Ti de una sola tarjeta (el canal 1x está creciendo pero necesita más cobertura).
- Resultados de adaptación CUDA etiquetados claramente como GPUs mixtas o no 5060 Ti.
- Notas de energía, térmica y enlace PCIe cuando expliquen diferencias de rendimiento.

## Enviar un Resultado

La ruta preferida es a través de un issue de GitHub utilizando la plantilla de reporte de resultados.

- Ruta rápida: abre un issue y pega la [plantilla de resultado comunitario para copiar y pegar](docs/community-result-template.md).
- Los reportes de issues simples también son aceptables; incluye lo que puedas y los mantenedores normalizarán los campos faltantes.

Como mínimo, incluye el canal de hardware, conteo exacto de GPUs, topología PCIe, runtime, modelo, quant, contexto, caché KV, conteo de tokens generados, prompt eval tok/s, decode tok/s y advertencias.

Si deseas un archivo de resultado estructurado, genera el JSON con `scripts/run_openai_bench.py`, valídalo con `scripts/validate_results.py` y adjunta o envía el JSON. Consulta `docs/reporting-results.md`.

## Mapa del Repositorio

- docs/benchmark-protocol.md - reglas para resultados comparables, conjuntos de prompts, niveles de contexto y niveles de promoción
- docs/FAQ.md - respuestas cortas a preguntas comunes de configuración
- docs/community-goals.md - objetivos del proyecto y prioridades de contribución
- docs/client-examples.md - ejemplos de clientes compatibles con OpenAI
- docs/reporting-results.md - cómo capturar un reporte de resultado útil
- docs/hardware-lanes.md - cómo se separan los resultados de 1x, 2x, multi-5060 Ti y otras GPUs CUDA
- docs/gpu-compatibility.md - base de Blackwell, GPUs mixtas y otras notas de arquitectura CUDA
- docs/single-5060ti.md - configuraciones iniciales conservadoras para una sola tarjeta
- docs/vllm-qwen36.md - notas de vLLM NVFP4/MTP
- docs/beellama-dflash.md - resultados iniciales y notas de fallos de BeeLlama DFlash
- docs/ik-llama-cpp.md - notas iniciales de ajuste y protocolo de ik_llama.cpp
- docs/llamacpp-qwen36.md - ruta de llama.cpp Qwen3.6 27B MTP GGUF
- docs/llamacpp-qwen35-9b-mtp.md - ruta de contexto máximo nativo de Qwen3.5 9B
- docs/qwen36-35b-a3b.md - verificaciones de Qwen3.6 35B A3B
- docs/qwen36-kv-quality-20260605.md - comparación de calidad de caché KV de Qwen3.6 27B
- docs/benchmarks.md - notas de resultados actuales legibles para humanos
- docs/troubleshooting.md - fallos observados y correcciones
- data/ - datos de resultados canónicos y esquemas
- examples/ - fragmentos de lanzamiento/configuración saneados
- scripts/ - ayudantes de validación, reporte, smoke, importación y benchmark
- site/ - explorador de resultados estático generado desde data/

## Descargas de Modelos

El ayudante de descarga envuelve la CLI de Hugging Face y acepta un autor u organización de Hugging Face, el nombre del repo del modelo, un selector opcional de quant/archivo y un directorio de descarga opcional:

~~~bash
scripts/download-models.sh unsloth Qwen3.6-27B-MTP-GGUF Q4_K_XL ~/models/Qwen3.6-27B-MTP-GGUF
scripts/download-models.sh unsloth Qwen3.6-27B-MTP-GGUF Qwen3.6-27B-UD-Q6_K_XL.gguf ~/models/Qwen3.6-27B-MTP-GGUF
scripts/download-models.sh RedHatAI Qwen3.6-35B-A3B-NVFP4 '' ~/models/Qwen3.6-35B-A3B-NVFP4
~~~

Cuando el selector termina en `.gguf`, se trata como un archivo exacto. De lo contrario, se convierte en un patrón de inclusión GGUF, por lo que `Q4_K_XL` descarga archivos que coincidan con `*Q4_K_XL*.gguf`. Deja el selector vacío para descargar el repositorio completo.

Instala la CLI `hf` o `huggingface-cli` antes de ejecutarlo, e inicia sesión primero al descargar modelos restringidos (gated). Configura `MODEL_DIR` si deseas una raíz predeterminada diferente.

## Ayudante de Construcción de llama.cpp

~~~bash
scripts/update-llama.sh
~~~

Esto construye el árbol de llama.cpp upstream utilizado por los ejemplos de Qwen3.6 GGUF. El ayudante es una ruta de construcción pública reproducible, no un administrador de servicios para un despliegue específico.

El objetivo de arquitectura CUDA predeterminado es `120a` para RTX 5060 Ti / Blackwell. Para otras GPUs CUDA o construcciones de arquitectura mixta, pasa las arquitecturas explícitamente:

~~~bash
CUDA_ARCHITECTURES="86;89;120a" scripts/update-llama.sh
~~~

Usa la lista de arquitecturas soportadas por tu toolchain de CUDA/CMake instalado y registra el valor exacto en tu resultado. Consulta `docs/gpu-compatibility.md` antes de tratar los resultados de tarjetas mixtas como comparables con la base de 2x RTX 5060 Ti.

## Estándar de Contribución

Las contribuciones son más útiles cuando incluyen el modelo exacto de GPU, diseño de placa base/PCIe, ancho de enlace/generación negociado, versiones de driver/runtime, comandos de lanzamiento, longitud de contexto, configuración de caché KV, forma del prompt, conteo de tokens generados, tokens/seg, y advertencias relevantes.

Comienza con `CONTRIBUTING.md` y `docs/benchmark-protocol.md`.

## Verificación

~~~bash
python3 -m py_compile scripts/*.py
bash -n scripts/*.sh examples/*.sh
python3 scripts/validate_results.py data/results
python3 scripts/build_site_data.py
./scripts/check_repo.sh
~~~

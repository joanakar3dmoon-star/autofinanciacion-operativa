# Inventario de recuperación — autofinanciación operativa (cuarentena)

Fuente: `joanakar3dmoon-star/autofinanciacion-operativa`, rama `main`, SHA `0f3c7b2de993a9e00a076c374ffa65419b04bac4`. Destino eventual: carpeta `operaciones/autofinanciacion/` dentro del monorepo único R3DM/TITAN, pero con aislamiento estricto.

## Código identificado

- `src/autofinanciacion_operativa/agents/portfolio_strategy_agent.py`
- `research_agent.py`
- `risk_monitoring_agent.py`
- `trade_execution_agent.py`
- `broker/alpaca_client.py`
- `journal/reflective_journal.py`
- `config.py`, `runner.py`, `cli.py`
- `titan-operativa/bots_reinversion.py`
- `catalog_worker.py`, `product_pipeline.py`
- `stripe_readonly.py`
- `wallet.py`, `tienda/catalog.json`, `tienda/tasks.json`

## Clasificación de riesgo

El repositorio contiene ejecución de operaciones de mercado a través de Alpaca, estrategia de cartera y lógica de reinversión. El usuario ha indicado que no quiere trading ni cripto. Por ello:

- No ejecutar `trade_execution_agent`, `alpaca_client`, `bots_reinversion` ni `runner`.
- No configurar broker, API keys, cuentas ni permisos de órdenes.
- No habilitar transferencias, retiros ni movimientos de dinero.
- No importar secretos, logs, datos locales, archivos de wallet ni bases reales.
- No conectar estos módulos a los workers de QUASAR, Colmena, PULPOS, Aurora o tienda.
- Mantener la carpeta en cuarentena, con feature flags desactivados y sin workflows programados.

La utilidad de lectura/catálogo que no mueve fondos puede revisarse separadamente, pero no se debe asumir que es segura por llamarse wallet o read-only: auditar todas las dependencias y operaciones antes de cualquier reutilización.

## Pruebas identificadas

- `tests/test_agents.py`
- `tests/test_package_import.py`
- `titan-operativa/test_bots_reinversion.py`
- `test_catalog_worker.py`
- `test_product_pipeline.py`
- `test_wallet.py`
- Workflows `.github/workflows/titan-operativa-tests.yml`, `titan-hourly-marketing.yml`, `titan-organic-worker.yml`

Los workflows con tareas horarias o de marketing no deben habilitarse al integrar. Primero hay que auditar triggers, secrets, permisos y efectos externos.

## Criterio de aceptación para el monorepo

1. Importar únicamente después de confirmar que no se activan workflows automáticamente.
2. Colocar el código bajo `operaciones/autofinanciacion/` y aplicar reglas CI que impidan ejecución de brokers/órdenes.
3. Excluir `.env`, datos, logs y cualquier secreto.
4. Añadir pruebas de que el módulo está deshabilitado por defecto y que los workers comerciales no pueden invocarlo.
5. Mantener separado el ciclo de pedidos/ventas del ciclo financiero.
6. No reactivar sin una solicitud nueva y autorización expresa.

Este inventario no ejecuta operaciones ni mueve dinero. La carpeta queda clasificada como cuarentena, no como empleado operativo.

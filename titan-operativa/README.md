# r3dm/titan · Autofinanciación operativa (sin trading)

Este módulo es **tesorería para un negocio digital**, NO inversión financiera.

- Nunca utiliza brokers, acciones, criptomonedas, préstamos ni productos especulativos.
- No contiene órdenes de compra de activos ni operaciones de trading.
- Una «wallet» de TITAN es un **panel contable**: los fondos siguen custodiados por Stripe, Wise o la entidad bancaria. El panel no emite dinero electrónico.
- Las cifras disponibles proceden exclusivamente de consultas autenticadas a proveedores reales; nunca de valores introducidos por un formulario ni de ingresos proyectados.
- La lectura de saldos y el cálculo de presupuesto no implican pagar, transferir o retirar dinero.
- Toda salida de fondos requiere cuenta de destino verificada, permisos técnicos específicos, idempotencia, límites, registro y aprobación expresa de la orden. No hay ejecución automática de gastos en esta versión.
- Antes de poder vender, cobrar y facturar comercialmente, revisar el alta y obligaciones fiscales españolas.

## Primera entrega

`wallet.py` calcula cuánto beneficio **realmente disponible** puede proponerse para reinvertir en bots, producción de contenidos, SEO, infraestructura y captación orgánica. Resta reservas fiscales, devoluciones, costes comprometidos, saldo mínimo y movimientos pendientes. No cuenta ventas futuras como dinero.

`stripe_readonly.py` consulta **GET /v1/balance** con clave Stripe LIVE restringida, guardada fuera del código. No acepta el modo de pruebas como saldo real ni puede ordenar retiradas. Los saldos Wise y bancarios solo podrán añadirse cuando exista integración autorizada con evidencia verificable.

`test_wallet.py` contiene pruebas unitarias sin pagos reales y sin depender de créditos externos.

## Integración futura en TITAN

1. Conservar `r3dmtitan.com` y sus servicios mientras se migra el backend.
2. Conectar la tienda TITAN a Checkout LIVE y webhooks firmados, persistentes, idempotentes.
3. Registrar órdenes cobradas, comisiones, reservas y obligaciones en un libro mayor trazable.
4. Reconciliar con Stripe, Wise y banco sin duplicar transferencias entre ellos.
5. Crear una orden de retirada o gasto solo tras autorización concreta y verificación de cuenta y fondos; consultar su estado de ejecución real y registrar el resultado.
6. Mantener TITAN independiente de QUASAR y de cualquier módulo de trading antiguo del repositorio.

**Estado:** implementación inicial de lectura y planificación, no un servicio desplegado de retiradas ni una wallet custodial.

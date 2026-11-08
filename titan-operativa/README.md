# r3dm/titan · Autoinversión y autofinanciación operativa

**Este módulo sirve para rentabilizar el propio negocio de servicios digitales TITAN. No es trading, inversión bursátil ni criptomonedas.** No utiliza brokers y no compra activos financieros.

## Reglas del propietario

- **Gastos operativos:** cubrir primero los gastos reales y autorizados de dominio, alojamiento, herramientas, mantenimiento y producción, siempre con ingresos disponibles, sin crear deudas.
- **Autoinversión:** reinvertir **solo el porcentaje que el propietario decida** del importe que queda tras gastos y reservas. Por defecto es **0 %**, no el 100 %.
- **Reservas y retiradas personales:** mantener el resto sin comprometer; reservar impuestos, devoluciones, gastos pendientes y un colchón mínimo.
- **Sin dinero ficticio:** solo saldos LIVE recientes obtenidos por conexión autenticada; nunca son suficientes las ventas previstas, cifras introducidas en el panel o pantallas de simulación.
- **Sin gastar de otras empresas:** cuando Stripe se comparta entre TITAN y QUASAR, el dinero utilizable queda limitado por el saldo **conciliado y atribuido a TITAN**, incluso si Stripe muestra una cifra global superior.
- **Sin movimiento sin aprobación:** la lectura y planificación NO autorizan cargos, transferencias ni retiradas. Para mover dinero se requiere una orden individual del titular, fondos y destino verificables, clave con permisos mínimos, límites, idempotencia y registro; fuera del alcance de este módulo.
- **Wallet no custodial:** es un panel contable. El dinero sigue en Stripe, Wise y el banco, sin emisión de dinero electrónico.
- **Cumplimiento:** revisar situación fiscal española antes de ofrecer nuevas ventas, facturar o cobrar profesionalmente.

## Motor de tesorería implementado (código, NO desplegado)

- `wallet.py`: verifica frescura y origen LIVE de saldos de proveedores y calcula importes disponibles. Prioriza cubrir gastos nuevos propuestos y después reinvertir un porcentaje de **lo restante**. Respeta reservas, tope por operación y límite diario; nunca mueve fondos.
- `stripe_readonly.py`: adaptador de solo lectura `GET /v1/balance` con clave LIVE restringida en el servidor, nunca en GitHub ni navegador.
- `bots_reinversion.py`: preserva los ocho bots originales **Analista, Presupuesto, SEO, Campañas, Conversión, Fideliza, Control y Escala** y ejecuta trabajo determinista sobre datos aportados por integraciones autorizadas:
  - Analista: calcula márgenes a partir de ingresos efectivamente cobrados y costes registrados.
  - Presupuesto: separa gastos del negocio, autoinversión elegida y dinero no asignado.
  - SEO: genera títulos y metadescripciones para los servicios existentes, como borradores reales.
  - Campañas: calcula el presupuesto máximo propuesto y bloquea la ejecución hasta aprobación.
  - Conversión: genera borradores comerciales desde el catálogo real, precio y enlace de TITAN.
  - Fideliza: prepara una plantilla de seguimiento, sin contactar a nadie sin autorización.
  - Control: identifica gastos no aprobados y servicios con margen negativo.
  - Escala: propone priorizar servicios con al menos dos pedidos pagados, margen positivo y financiación disponible. No contrata servicios.
- `test_wallet.py` y `test_bots_reinversion.py`: pruebas unitarias offline sin pagos ni APIs bancarias.

Las propuestas no son ventas, los borradores no son publicaciones y los resultados calculados no se presentarán como transferencias ejecutadas. No hay promesas de rentabilidad.

## Integración pendiente con la aplicación original

1. Conservar `r3dmtitan.com` y base de datos; migrar backend sólo con exportación y credenciales seguras verificadas.
2. Unir pedidos y ventas reales mediante Checkout LIVE y webhooks firmados, idempotentes, con entrega solo después de pago real confirmado y revisión.
3. Crear libro mayor por **negocio**, conciliar transferencias internas y evitar sumar dos veces fondos Stripe→banco.
4. Configurar políticas de aprobación por gasto y un porcentaje editable sólo por el titular.
5. Aportar datos de órdenes y gastos conciliados a estos ocho bots; persistir trabajos y ejecución. Publicar únicamente con conexiones y permisos apropiados.
6. Integrar retirada a cuenta bancaria verificada mediante el proveedor. No retirar automáticamente ni registrar ingresos ficticios.
7. Ejecutar pruebas, comprobar seguridad y desplegar sin servicios que cobren mientras no haya fondos operativos.

**Estado real:** se han escrito y versionado módulos de lectura, planificación y generación de activos internos; todavía no están desplegados en TITAN ni se han autorizado transferencias. El antiguo código bursátil del repositorio no se importa ni se utiliza por TITAN.

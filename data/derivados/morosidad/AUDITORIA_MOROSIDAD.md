# Auditoría del tab Morosidad

Fecha de corte editorial: 21/08/2026. Último dato bancario: mayo de 2026. Último dato PNFC: febrero de 2026.

## 1. Definiciones y universos

- **Bancos · hogares:** cartera irregular dividida por las financiaciones a familias. Es porcentaje de **saldo**, no de personas. El archivo oficial también publica `Familias · Personales + TC` como agregado; no separa esas dos líneas ni publica allí una serie mensual compatible para hipotecarios y prendarios.
- **PNFC total, personales, tarjetas y grupo Fintech:** cartera con mora **mayor a 90 días** dividida por la cartera de la categoría. Es porcentaje de **saldo**.
- **Personas PNFC:** porcentaje de clientes en situación regular de pago según el Informe de Inclusión Financiera. Se presenta como snapshot anual; no se mezcla con los porcentajes de saldo.
- **Stock no es flujo:** ninguna variación se llama “nuevos morosos”. Puede cambiar por originaciones, pagos, refinanciaciones, castigos, ventas o reclasificaciones.

## 2. Períodos y frecuencia

- Bancos: mensual, mayo de 2016 a mayo de 2026.
- PNFC: mensual, enero de 2018 a febrero de 2026.
- Personas: snapshots de diciembre de 2024 y diciembre de 2025. Los valores 2024 se derivan de los niveles 2025 y de las caídas en regularidad informadas para 2025.
- No se interpoló ninguna observación.

## 3. Promedio histórico y pp-mes

Para cada universo se usa el promedio de todas las observaciones disponibles hasta noviembre de 2023:

`exceso_t = mora_t - promedio_pre_shock`

`saldo_ventana = suma(exceso_t)`

Unidad: **pp-mes**. Positivo significa más morosidad que la norma; negativo, menos.

- Promedio bancario pre-shock: **3,38%**.
- Promedio PNFC pre-shock: **18,17%**.

## 4. Ventana espejo

- Bancos: 30 meses espejo (jun-2021 a nov-2023) y 30 meses post-shock (dic-2023 a may-2026).
- PNFC: 27 meses espejo (sep-2021 a nov-2023) y 27 meses post-shock (dic-2023 a feb-2026).
- Diferencial: `saldo_post - saldo_espejo`.
- Diferencial positivo = **empeoró** la morosidad; negativo = mejoró.

Resultados:

- Bancos: antes **5,33 pp-mes**, después **59,04 pp-mes**, diferencial **+53,71 pp-mes**.
- PNFC: antes **-153,68 pp-mes**, después **-147,08 pp-mes**, diferencial **+6,60 pp-mes**.

## 5. Bancos vs PNFC

Los niveles no se tratan como idénticos. Comparten la idea general de irregularidad sobre saldo, pero PNFC explicita mora >90 días y responde a otro universo de proveedores y clientes. La comparación principal entre ambos se normaliza a nov-2023=100 para observar tendencia.

## 6. Personas y severidad

El informe oficial indica que en diciembre de 2025 estaba regular el 79% de los deudores fintech y el 71% de los deudores PNFC tradicionales. La caída durante 2025 fue de 7 y 14 p.p.; por eso se reconstruyen los snapshots de diciembre de 2024 como 86% y 85%, respectivamente. No se dispone en estas fuentes de una serie histórica mensual comparable de personas en situaciones 1 a 6. La composición mensual PNFC por mora <30, 30–90 y >90 días corresponde a saldos y se conserva separada.

## 7. Cambios regulatorios y cautelas

- El gráfico bancario marca el período de alivio de medidas financieras por COVID-19 que el propio BCRA sombrea en el Informe sobre Bancos.
- Desde julio de 2024, la Central de Deudores elevó el umbral mínimo informado de $1.000 a $25.000. Ese quiebre afecta conteos de personas; por eso no se construyó una serie mensual espuria a partir de esos conteos.
- Hipotecarios y prendarios no se incorporan como series porque el workbook mensual vigente no expone aperturas compatibles y continuas. El informe narrativo los menciona como impulsores en algunos meses, pero eso no alcanza para fabricar una serie.

## 8. Tasas reales y correlación

Se explora `corr(tasa_real_personales[t-k], mora_personales_más_tarjetas[t])` para k=0…6. La mayor correlación absoluta es **r=0.488** con **6 meses** de rezago. Es sincronía temporal, no prueba causal.

## 9. Resultado principal

La mora bancaria de hogares alcanzó **12,8%** en mayo de 2026, **+9,42 p.p.** sobre su promedio pre-shock y **+10,10 p.p.** frente a noviembre de 2023. La ventana post-shock resultó **53,71 pp-mes más desfavorable** que su espejo. PNFC también empeoró frente a noviembre de 2023, aunque su saldo acumulado en ambas ventanas sigue debajo de un promedio histórico elevado por años de mora muy alta.

## 10. Controles automáticos

Estado: **PASS**. Controles aprobados: 11/11.

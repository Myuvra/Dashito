# Auditoría de la pinza financiera

## 1. Convención anterior encontrada

El dashboard calculaba correctamente la desviación técnica de cada tasa, pero combinaba dos orientaciones: el costo bancario se mostraba positivo y el plazo fijo se invertía en algunos gráficos para mostrar la magnitud de la pérdida como barra positiva.

## 2. Problema de signos

La expresión anterior `banco_neto - pf_neto` no tenía una semántica universal desde el hogar. En particular, el **+$8,71 B** del plazo fijo espejo era `−pf_neto`: una magnitud de costo con el signo visual invertido, no un rendimiento favorable.

## 3. Convención nueva

En todo agregado de impacto hogar:

```text
+ = favorable para el hogar
− = desfavorable para el hogar
```

## 4. Fórmula banco

```text
brecha_técnica_banco = tasa_real_banco − promedio_histórico_banco
impacto_costo_banco = monto_personales × brecha_técnica_banco / 100
impacto_hogar_banco = −impacto_costo_banco
```

## 5. Fórmula plazo fijo

```text
brecha_pf = tasa_real_pf − promedio_histórico_pf
impacto_hogar_pf = monto_pf × brecha_pf / 100
```

## 6. Fórmula Fintech y balances

```text
balance_conjunto = impacto_hogar_banco + impacto_hogar_pf
impacto_hogar_fintech = −(stock_real_fintech × brecha_real_fintech / 100)
balance_ampliado = balance_conjunto + impacto_hogar_fintech
diferencial = saldo_post − saldo_espejo
```

El balance conjunto reúne crédito bancario y ahorro minorista. El balance ampliado suma Fintech como carga mensual estimada sobre stock. No representa a un “hogar promedio”: deudores y ahorristas son universos distintos.

La TNA Fintech es mensual y está ponderada por saldos. El stock real se interpola linealmente entre cortes oficiales; para marzo–julio de 2026 se conservan la última TNA y el último stock publicados en febrero. Esos cinco meses se muestran como estimación, no como observación.

Cada flujo mensual se llevó a pesos de **julio de 2026** con `IPC_ref / IPC_t` antes de acumular.

## 7. Resultados espejo

- Banco: **+$ 0,29 B**.
- Fintech: **+$ 0,50 B**.
- Plazo fijo: **−$ 8,71 B**.
- Balance conjunto: **−$ 8,43 B**.
- Balance ampliado: **−$ 7,93 B**.

## 8. Resultados post-shock

- Banco: **−$ 0,75 B**.
- Fintech: **−$ 1,34 B** (27 meses con TNA observada y 5 estimados).
- Plazo fijo: **−$ 3,76 B**.
- Balance conjunto: **−$ 4,51 B**.
- Balance ampliado: **−$ 5,85 B**.

En plazo fijo post-shock, la pérdida bruta de meses desfavorables fue **−$ 12,96 B** y la compensación de meses favorables fue **+$ 9,21 B**; su suma da el saldo neto **−$ 3,76 B**.

## 9. Diferencial

El **diferencial post-shock vs espejo** es **+$ 3,92 B**. Ambos saldos fueron negativos contra sus normas históricas, pero el balance conjunto post-shock fue menos desfavorable en **+$ 3,92 B**.

Por componente: el crédito bancario cambió **−$ 1,04 B**, Fintech cambió **−$ 1,85 B**, el plazo fijo cambió **+$ 4,96 B**, el balance conjunto cambió **+$ 3,92 B** y el balance ampliado cambió **+$ 2,07 B**.

Hay dos preguntas distintas: en un saldo, positivo significa favorable y negativo desfavorable contra la norma histórica; en un diferencial entre ventanas, positivo significa mejora y negativo empeoramiento. Por eso “sigue siendo negativo” no equivale a “empeoró”.

La pista preliminar cercana a −$13,5 B no se reprodujo. La diferencia se explica porque trataba el **+$8,71 B** del PF espejo mostrado en pantalla como beneficio, cuando el dato subyacente era un impacto hogar de **−$8,71 B** y la interfaz lo había invertido para expresar “costo”.

## 10. Tests de consistencia

- **test_1_signo_banco:** OK · 64/64 meses
- **test_2_total_mensual:** OK · 64/64 meses
- **test_2b_total_ampliado_mensual:** OK · 64/64 meses
- **test_3_suma_post_kpi:** OK
- **test_4_suma_espejo_kpi:** OK
- **test_5_diferencial:** OK
- **test_5b_diferencial_ampliado:** OK
- **test_6_componentes_grafico:** OK
- **test_7_bruto_compensacion_saldo_pf:** OK

## Tabla final

| Concepto | Espejo | Post-shock | Diferencial |
|---|---:|---:|---:|
| Banco | +$ 0,29 B | −$ 0,75 B | −$ 1,04 B |
| Fintech · estimación sobre stock | +$ 0,50 B | −$ 1,34 B | −$ 1,85 B |
| PF | −$ 8,71 B | −$ 3,76 B | +$ 4,96 B |
| Balance conjunto de crédito y ahorro minorista | −$ 8,43 B | −$ 4,51 B | +$ 3,92 B |
| Balance ampliado banco + Fintech + PF | −$ 7,93 B | −$ 5,85 B | +$ 2,07 B |

## Fuentes archivadas

- `data/fuentes/tasas/bcra/tas2_ser.txt`
- `data/fuentes/tasas/bcra/tas1_ser.txt`
- `data/fuentes/tasas/indec/serie_ipc_divisiones.csv`
- `data/fuentes/tasas/pnfc/series-informe-proveedores-no-financieros-credito-junio-2026.xlsx`

No se descargaron fuentes nuevas ni se modificaron originales.

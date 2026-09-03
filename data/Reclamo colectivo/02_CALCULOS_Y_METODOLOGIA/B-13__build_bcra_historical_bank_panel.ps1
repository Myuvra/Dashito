[CmdletBinding()]
param(
    [string]$HistoricalRoot = (Join-Path $PSScriptRoot '..\..\fuentes\credito_consumo\bcra_entidades\historico_2023_2026\extract'),
    [string]$CurrentRoot = (Join-Path $PSScriptRoot '..\..\fuentes\credito_consumo\bcra_entidades\2026-05\extract\Entfin\Tec_Cont'),
    [string]$OutputPath = (Join-Path $PSScriptRoot 'bcra_panel_bancos_2023_2026.csv'),
    [string]$SummaryPath = (Join-Path $PSScriptRoot 'bcra_panel_bancos_resumen_2023_2026.csv'),
    [string]$SystemPath = (Join-Path $PSScriptRoot 'bcra_sistema_financiero_2023_2026.csv')
)

$ErrorActionPreference = 'Stop'
$invariant = [System.Globalization.CultureInfo]::InvariantCulture

function Convert-ToNumber {
    param([AllowNull()][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    return [double]::Parse($Value.Replace(',', '.'), $invariant)
}

function Import-TabRows {
    param(
        [string]$Path,
        [string[]]$Header
    )

    return Get-Content -LiteralPath $Path | ConvertFrom-Csv -Delimiter "`t" -Header $Header
}

function Get-LatestValue {
    param(
        [object[]]$Rows,
        [string]$Code
    )

    $row = $Rows | Where-Object codigo_linea -eq $Code | Select-Object -First 1
    if ($null -eq $row -or [string]::IsNullOrWhiteSpace($row.fecha5)) {
        return $null
    }

    return Convert-ToNumber $row.fecha5
}

function Get-Percentage {
    param(
        [AllowNull()][double]$Numerator,
        [AllowNull()][double]$Denominator
    )

    if ($null -eq $Numerator -or $null -eq $Denominator -or $Denominator -eq 0) {
        return $null
    }

    return [math]::Round(100 * $Numerator / $Denominator, 6)
}

function Get-DetailedValue {
    param(
        [object[]]$Rows,
        [string]$Code,
        [ValidateSet('debe', 'haber')][string]$Side
    )

    $row = $Rows | Where-Object codigo_cuenta -eq $Code | Select-Object -First 1
    if ($null -eq $row -or [string]::IsNullOrWhiteSpace($row.$Side)) {
        return $null
    }

    return Convert-ToNumber $row.$Side
}

function Get-SumPresent {
    param([AllowEmptyCollection()][object[]]$Values)

    $present = @($Values | Where-Object { $null -ne $_ })
    if ($present.Count -eq 0) {
        return $null
    }

    return ($present | Measure-Object -Sum).Sum
}

$indicatorHeader = @(
    'codigo', 'entidad', 'fecha_archivo', 'codigo_linea', 'descripcion',
    'fecha1', 'fecha2', 'fecha3', 'fecha4', 'fecha5',
    'grupo_homogeneo', 'top10_privados', 'sistema', 'formato'
)
$balanceHeader = @(
    'codigo', 'entidad', 'fecha_archivo', 'codigo_linea', 'descripcion',
    'fecha1', 'fecha2', 'fecha3', 'fecha4', 'fecha5'
)
$detailedHeader = @(
    'codigo', 'entidad', 'fecha_archivo', 'codigo_cuenta', 'descripcion',
    'debe', 'haber'
)

$snapshots = [ordered]@{}
Get-ChildItem -LiteralPath $HistoricalRoot -Directory | Sort-Object Name | ForEach-Object {
    $snapshots[$_.Name] = Join-Path $_.FullName 'Entfin\Tec_Cont'
}
$snapshots['2026-05'] = $CurrentRoot

$panel = foreach ($snapshot in $snapshots.Keys) {
    $root = $snapshots[$snapshot]
    $entityDirectory = Join-Path $root 'entidad'

    Get-ChildItem -LiteralPath $entityDirectory -Filter '*.txt' -File |
        Where-Object BaseName -Match '^\d{5}$' |
        ForEach-Object {
            $code = $_.BaseName
            $indicatorPath = Join-Path $root "indicad\$code.txt"
            $balancePath = Join-Path $root "balres\$code.txt"
            $detailedPath = Join-Path $root "baldet\$code.txt"

            if (-not (Test-Path -LiteralPath $indicatorPath) -or
                -not (Test-Path -LiteralPath $balancePath) -or
                -not (Test-Path -LiteralPath $detailedPath)) {
                Write-Warning "Falta balance, detalle o indicadores para $snapshot / $code."
                return
            }

            $entityFields = (Get-Content -LiteralPath $_.FullName -TotalCount 1) -split "`t"
            $balances = @(Import-TabRows -Path $balancePath -Header $balanceHeader)
            $indicators = @(Import-TabRows -Path $indicatorPath -Header $indicatorHeader)
            $details = @(Import-TabRows -Path $detailedPath -Header $detailedHeader)

            $integralResult = Get-LatestValue -Rows $balances -Code '100040000000'
            $otherComprehensiveIncome = Get-LatestValue -Rows $balances -Code '100041500000'
            $netResult = if ($null -ne $integralResult) {
                $integralResult - $(if ($null -ne $otherComprehensiveIncome) { $otherComprehensiveIncome } else { 0 })
            } else {
                $null
            }
            $personalLoans = Get-LatestValue -Rows $balances -Code '100010303020'
            $assets = Get-LatestValue -Rows $balances -Code '100010000000'
            $provisions = Get-LatestValue -Rows $balances -Code '100010304000'
            $personalInterestPesos = Get-DetailedValue -Rows $details -Code '511107' -Side haber
            $personalInterestForeignCurrency = Get-DetailedValue -Rows $details -Code '515107' -Side haber
            $personalInterest = Get-SumPresent -Values @($personalInterestPesos, $personalInterestForeignCurrency)
            $financialIncome = Get-DetailedValue -Rows $details -Code '510000' -Side haber
            $financialExpenses = Get-DetailedValue -Rows $details -Code '520000' -Side debe
            $badDebtCharges = Get-DetailedValue -Rows $details -Code '530000' -Side debe
            $serviceIncome = Get-DetailedValue -Rows $details -Code '540000' -Side haber
            $administrativeExpenses = Get-DetailedValue -Rows $details -Code '560000' -Side debe

            [pscustomobject][ordered]@{
                corte_publicacion = $snapshot
                codigo_entidad = [int]$code
                entidad = $entityFields[1].Trim('"')
                grupo_institucional = $entityFields[40].Trim('"')
                codigo_grupo_institucional = $entityFields[41].Trim('"')
                periodo_balance_resultados = $entityFields[11].Trim('"')
                periodo_indicadores = $entityFields[21].Trim('"')
                resultado_integral_acumulado_miles_pesos = $integralResult
                otro_resultado_integral_acumulado_miles_pesos = $otherComprehensiveIncome
                resultado_neto_estimado_sin_ori_miles_pesos = $netResult
                intereses_por_prestamos_personales_miles_pesos = $personalInterest
                intereses_personales_pesos_cuenta_511107_miles_pesos = $personalInterestPesos
                intereses_personales_moneda_extranjera_cuenta_515107_miles_pesos = $personalInterestForeignCurrency
                ingresos_financieros_totales_miles_pesos = $financialIncome
                egresos_financieros_totales_miles_pesos = $financialExpenses
                cargo_por_incobrabilidad_total_miles_pesos = $badDebtCharges
                ingresos_por_servicios_totales_miles_pesos = $serviceIncome
                gastos_administracion_totales_miles_pesos = $administrativeExpenses
                intereses_personales_sobre_ingresos_financieros_pct = Get-Percentage -Numerator $personalInterest -Denominator $financialIncome
                prestamos_personales_miles_pesos = $personalLoans
                activo_total_miles_pesos = $assets
                previsiones_miles_pesos = $provisions
                prestamos_personales_sobre_activo_pct = Get-Percentage -Numerator $personalLoans -Denominator $assets
                previsiones_sobre_prestamos_personales_pct = Get-Percentage -Numerator $provisions -Denominator $personalLoans
                resultado_neto_sobre_activo_pct_no_anualizado = Get-Percentage -Numerator $netResult -Denominator $assets
                roe_pct = Get-LatestValue -Rows $indicators -Code '800010400010'
                roa_pct = Get-LatestValue -Rows $indicators -Code '800010401010'
                tasa_implicita_prestamos_totales_pct = Get-LatestValue -Rows $indicators -Code '800010400080'
                margen_financiero_sobre_activo_pct = Get-LatestValue -Rows $indicators -Code '800010401020'
                cargos_incobrabilidad_sobre_activo_pct = Get-LatestValue -Rows $indicators -Code '800010401030'
                cartera_irregular_consumo_pct = Get-LatestValue -Rows $indicators -Code '800010200160'
                unidad_balance = 'miles de pesos corrientes'
                nota_comparabilidad = 'Los saldos son nominales. Resultados e intereses son acumulados al mes informado. La cuenta 511107+515107 mide ingreso bruto por intereses personales, no ganancia neta del producto.'
            }
        }
}

$panel |
    Sort-Object corte_publicacion, codigo_entidad |
    Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8

$summary = $panel |
    Group-Object corte_publicacion |
    ForEach-Object {
        $rows = @($_.Group)
        $positive = @($rows | Where-Object { $null -ne $_.resultado_neto_estimado_sin_ori_miles_pesos -and $_.resultado_neto_estimado_sin_ori_miles_pesos -gt 0 })
        $negative = @($rows | Where-Object { $null -ne $_.resultado_neto_estimado_sin_ori_miles_pesos -and $_.resultado_neto_estimado_sin_ori_miles_pesos -lt 0 })
        $zero = @($rows | Where-Object { $null -ne $_.resultado_neto_estimado_sin_ori_miles_pesos -and $_.resultado_neto_estimado_sin_ori_miles_pesos -eq 0 })
        $personalLoanRows = @($rows | Where-Object { $null -ne $_.prestamos_personales_miles_pesos })
        $personalInterest = ($rows.intereses_por_prestamos_personales_miles_pesos | Measure-Object -Sum).Sum
        $financialIncome = ($rows.ingresos_financieros_totales_miles_pesos | Measure-Object -Sum).Sum

        [pscustomobject][ordered]@{
            corte_publicacion = $_.Name
            entidades = $rows.Count
            resultado_estimado_positivo = $positive.Count
            resultado_estimado_negativo = $negative.Count
            resultado_estimado_cero = $zero.Count
            entidades_con_prestamos_personales = $personalLoanRows.Count
            suma_intereses_prestamos_personales_miles_pesos_no_consolidada = $personalInterest
            suma_ingresos_financieros_miles_pesos_no_consolidada = $financialIncome
            intereses_personales_sobre_ingresos_financieros_pct_no_consolidado = Get-Percentage -Numerator $personalInterest -Denominator $financialIncome
            suma_egresos_financieros_miles_pesos_no_consolidada = ($rows.egresos_financieros_totales_miles_pesos | Measure-Object -Sum).Sum
            suma_cargo_incobrabilidad_miles_pesos_no_consolidada = ($rows.cargo_por_incobrabilidad_total_miles_pesos | Measure-Object -Sum).Sum
            suma_gastos_administracion_miles_pesos_no_consolidada = ($rows.gastos_administracion_totales_miles_pesos | Measure-Object -Sum).Sum
            suma_prestamos_personales_miles_pesos_no_consolidada = ($personalLoanRows.prestamos_personales_miles_pesos | Measure-Object -Sum).Sum
            suma_activo_miles_pesos_no_consolidada = ($rows.activo_total_miles_pesos | Measure-Object -Sum).Sum
            advertencia = 'Sumas entre entidades no consolidadas y nominales; usar sólo como control. Para el total del sistema corresponde el agregado oficial AA000.'
        }
    }

$summary |
    Sort-Object corte_publicacion |
    Export-Csv -LiteralPath $SummaryPath -NoTypeInformation -Encoding utf8

$system = foreach ($snapshot in $snapshots.Keys) {
    $root = $snapshots[$snapshot]
    $balancePath = Join-Path $root 'balres\AA000.txt'
    $indicatorPath = Join-Path $root 'indicad\AA000.txt'
    $entityPath = Join-Path $root 'entidad\AA000.txt'

    $balances = @(Import-TabRows -Path $balancePath -Header $balanceHeader)
    $indicators = @(Import-TabRows -Path $indicatorPath -Header $indicatorHeader)
    $entityFields = (Get-Content -LiteralPath $entityPath -TotalCount 1) -split "`t"
    $integralResult = Get-LatestValue -Rows $balances -Code '100040000000'
    $otherComprehensiveIncome = Get-LatestValue -Rows $balances -Code '100041500000'
    $netResult = if ($null -ne $integralResult) {
        $integralResult - $(if ($null -ne $otherComprehensiveIncome) { $otherComprehensiveIncome } else { 0 })
    } else {
        $null
    }
    $personalLoans = Get-LatestValue -Rows $balances -Code '100010303020'
    $assets = Get-LatestValue -Rows $balances -Code '100010000000'

    [pscustomobject][ordered]@{
        corte_publicacion = $snapshot
        agregado = 'AA000 - Total del sistema financiero'
        periodo_balance_resultados = $entityFields[11].Trim('"')
        periodo_indicadores = $entityFields[21].Trim('"')
        resultado_integral_acumulado_miles_pesos = $integralResult
        otro_resultado_integral_acumulado_miles_pesos = $otherComprehensiveIncome
        resultado_neto_estimado_sin_ori_miles_pesos = $netResult
        prestamos_personales_miles_pesos = $personalLoans
        activo_total_miles_pesos = $assets
        previsiones_miles_pesos = Get-LatestValue -Rows $balances -Code '100010304000'
        prestamos_personales_sobre_activo_pct = Get-Percentage -Numerator $personalLoans -Denominator $assets
        resultado_neto_sobre_activo_pct_no_anualizado = Get-Percentage -Numerator $netResult -Denominator $assets
        roe_pct = Get-LatestValue -Rows $indicators -Code '800010400010'
        roa_pct = Get-LatestValue -Rows $indicators -Code '800010401010'
        tasa_implicita_prestamos_totales_pct = Get-LatestValue -Rows $indicators -Code '800010400080'
        margen_financiero_sobre_activo_pct = Get-LatestValue -Rows $indicators -Code '800010401020'
        cargos_incobrabilidad_sobre_activo_pct = Get-LatestValue -Rows $indicators -Code '800010401030'
        cartera_irregular_consumo_pct = Get-LatestValue -Rows $indicators -Code '800010200160'
        unidad_balance = 'miles de pesos corrientes'
        nota_comparabilidad = 'Agregado oficial AA000. Saldos nominales; resultados acumulados al mes informado; no identifica margen ni resultado de préstamos personales.'
    }
}

$system |
    Sort-Object corte_publicacion |
    Export-Csv -LiteralPath $SystemPath -NoTypeInformation -Encoding utf8

Write-Host "Generado: $OutputPath"
Write-Host "Generado: $SummaryPath"
Write-Host "Generado: $SystemPath"
Write-Host "Filas panel: $($panel.Count)"

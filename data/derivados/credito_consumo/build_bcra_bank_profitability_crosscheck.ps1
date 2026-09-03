[CmdletBinding()]
param(
    [string]$OffersPath = (Join-Path $PSScriptRoot 'bcra_transparencia_bancos_prestamos_personales_2026-08-30.csv'),
    [string]$AccountingRoot = (Join-Path $PSScriptRoot '..\..\fuentes\credito_consumo\bcra_entidades\2026-05\extract\Entfin\Tec_Cont'),
    [string]$OutputPath = (Join-Path $PSScriptRoot 'bcra_bancos_ofertas_y_resultados_2026-08-30.csv')
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

function Get-Median {
    param([double[]]$Values)

    $ordered = @($Values | Sort-Object)
    if ($ordered.Count -eq 0) {
        return $null
    }
    if ($ordered.Count % 2 -eq 1) {
        return $ordered[[int][math]::Floor($ordered.Count / 2)]
    }

    $upper = $ordered.Count / 2
    return ($ordered[$upper - 1] + $ordered[$upper]) / 2
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

$indicatorHeader = @(
    'codigo', 'entidad', 'fecha_archivo', 'codigo_linea', 'descripcion',
    'fecha1', 'fecha2', 'fecha3', 'fecha4', 'fecha5',
    'grupo_homogeneo', 'top10_privados', 'sistema', 'formato'
)
$balanceHeader = @(
    'codigo', 'entidad', 'fecha_archivo', 'codigo_linea', 'descripcion',
    'fecha1', 'fecha2', 'fecha3', 'fecha4', 'fecha5'
)

$offers = Import-Csv -LiteralPath $OffersPath
$result = foreach ($group in ($offers | Group-Object codigo_entidad)) {
    $code = '{0:D5}' -f [int]$group.Name
    $indicatorPath = Join-Path $AccountingRoot "indicad\$code.txt"
    $balancePath = Join-Path $AccountingRoot "balres\$code.txt"
    $entityPath = Join-Path $AccountingRoot "entidad\$code.txt"

    if (-not (Test-Path -LiteralPath $indicatorPath) -or
        -not (Test-Path -LiteralPath $balancePath) -or
        -not (Test-Path -LiteralPath $entityPath)) {
        Write-Warning "No se encontraron los tres archivos contables para $code."
        continue
    }

    $indicators = @(Import-TabRows -Path $indicatorPath -Header $indicatorHeader)
    $balances = @(Import-TabRows -Path $balancePath -Header $balanceHeader)
    $entityFields = (Get-Content -LiteralPath $entityPath -TotalCount 1) -split "`t"
    $balancePeriod = $entityFields[11].Trim('"')
    $indicatorPeriod = $entityFields[21].Trim('"')

    $cftea = @($group.Group | ForEach-Object { Convert-ToNumber $_.cftea_max_pct })
    $tea = @($group.Group | ForEach-Object { Convert-ToNumber $_.tea_max_pct })
    $integralResult = Get-LatestValue -Rows $balances -Code '100040000000'
    $otherComprehensiveIncome = Get-LatestValue -Rows $balances -Code '100041500000'
    $otherComprehensiveIncomeReported = $null -ne $otherComprehensiveIncome
    $otherComprehensiveIncomeForCalculation = if ($otherComprehensiveIncomeReported) {
        $otherComprehensiveIncome
    } else {
        0
    }
    $estimatedNetResult = if ($null -ne $integralResult) {
        $integralResult - $otherComprehensiveIncomeForCalculation
    } else {
        $null
    }

    [pscustomobject][ordered]@{
        codigo_entidad = [int]$group.Name
        entidad = $group.Group[0].entidad
        fecha_oferta_mas_reciente = ($group.Group.fecha_informacion | Sort-Object | Select-Object -Last 1)
        filas_oferta = $group.Count
        cftea_max_pct = [math]::Round(($cftea | Measure-Object -Maximum).Maximum, 6)
        cftea_mediana_no_ponderada_pct = [math]::Round((Get-Median -Values $cftea), 6)
        tea_max_pct = [math]::Round(($tea | Measure-Object -Maximum).Maximum, 6)
        periodo_balance_resultados = $balancePeriod
        periodo_indicadores = $indicatorPeriod
        resultado_integral_acumulado_miles_pesos = $integralResult
        otro_resultado_integral_acumulado_miles_pesos = $otherComprehensiveIncome
        otro_resultado_integral_informado = $otherComprehensiveIncomeReported
        resultado_neto_estimado_sin_ori_miles_pesos = $estimatedNetResult
        prestamos_personales_miles_pesos = Get-LatestValue -Rows $balances -Code '100010303020'
        activo_total_miles_pesos = Get-LatestValue -Rows $balances -Code '100010000000'
        previsiones_miles_pesos = Get-LatestValue -Rows $balances -Code '100010304000'
        roe_pct = Get-LatestValue -Rows $indicators -Code '800010400010'
        roa_pct = Get-LatestValue -Rows $indicators -Code '800010401010'
        tasa_implicita_prestamos_totales_pct = Get-LatestValue -Rows $indicators -Code '800010400080'
        margen_financiero_sobre_activo_pct = Get-LatestValue -Rows $indicators -Code '800010401020'
        cargos_incobrabilidad_sobre_activo_pct = Get-LatestValue -Rows $indicators -Code '800010401030'
        cartera_irregular_consumo_pct = Get-LatestValue -Rows $indicators -Code '800010200160'
        alcance = 'Oferta maxima declarada, no ponderada por monto ni contratos; contabilidad total de la entidad, no del producto.'
    }
}

$result |
    Sort-Object @{ Expression = 'cftea_max_pct'; Descending = $true } |
    Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8

Write-Host "Generado: $OutputPath"
Write-Host "Entidades: $($result.Count)"

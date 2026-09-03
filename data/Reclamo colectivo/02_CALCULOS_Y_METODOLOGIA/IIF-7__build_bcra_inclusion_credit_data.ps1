[CmdletBinding()]
param(
    [string]$SourceRoot = (Join-Path $PSScriptRoot '..\..\fuentes\credito_consumo\bcra_inclusion\2026-08-30'),
    [string]$PersonalLoansOutput = (Join-Path $PSScriptRoot 'bcra_inclusion_prestamos_personales_2023_2025.csv'),
    [string]$ProvidersOutput = (Join-Path $PSScriptRoot 'bcra_inclusion_proveedores_2023_2025.csv'),
    [string]$AgeOutput = (Join-Path $PSScriptRoot 'bcra_inclusion_prestamos_personales_edad_cortes_2023_2025.csv')
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

function Get-Methodology {
    param([int]$Period)

    if ($Period -le 202406) {
        return [pscustomobject]@{
            tramo = 'A_2023-01_a_2024-06'
            umbral = 1000
            nota = 'CENDEU informaba personas con saldo de deuda desde $1.000.'
        }
    }

    return [pscustomobject]@{
        tramo = 'B_2024-07_a_2025-12'
        umbral = 25000
        nota = 'Desde julio de 2024 CENDEU informa personas con saldo de deuda desde $25.000 (Com. BCRA A 8001).'
    }
}

$assistancePath = Join-Path $SourceRoot 'inclusion-financiera-deudores-sistema-financiero-ampliado-tipo-asistencia.txt'
$providerPath = Join-Path $SourceRoot 'inclusion-financiera-deudores-sistema-financiero-ampliado-grupo-institucional.txt'
$agePath = Join-Path $SourceRoot 'inclusion-financiera-deudores-sistema-financiero-ampliado-asistencia-rango-etario.txt'

$personalSource = Import-Csv -LiteralPath $assistancePath |
    Where-Object { [int]$_.cd_periodo -ge 202301 -and $_.tx_asistencia -match '^Personales\s*/' } |
    Sort-Object { [int]$_.cd_periodo }

$firstBySegment = @{}
$previous = $null
$personal = foreach ($row in $personalSource) {
    $period = [int]$row.cd_periodo
    $method = Get-Methodology -Period $period
    $value = Convert-ToNumber $row.nu_valor

    if (-not $firstBySegment.ContainsKey($method.tramo)) {
        $firstBySegment[$method.tramo] = $value
    }

    $monthlyChange = if ($null -ne $previous -and $previous.tramo -eq $method.tramo) {
        [math]::Round($value - $previous.valor, 6)
    } else {
        $null
    }

    [pscustomobject][ordered]@{
        periodo = '{0:0000}-{1:00}' -f [math]::Floor($period / 100), ($period % 100)
        cobertura_personales_pct_poblacion_adulta = [math]::Round($value, 6)
        variacion_mensual_pp_dentro_tramo = $monthlyChange
        variacion_desde_inicio_tramo_pp = [math]::Round($value - $firstBySegment[$method.tramo], 6)
        tramo_metodologico = $method.tramo
        umbral_saldo_deuda_reportable_pesos = $method.umbral
        comparable_con_mes_anterior = $null -ne $monthlyChange
        fuente = 'BCRA, Indicadores de Inclusión Financiera, CENDEU'
        nota_metodologica = $method.nota
    }

    $previous = [pscustomobject]@{ tramo = $method.tramo; valor = $value }
}

$personal | Export-Csv -LiteralPath $PersonalLoansOutput -NoTypeInformation -Encoding utf8

$providers = Import-Csv -LiteralPath $providerPath |
    Where-Object { [int]$_.cd_periodo -ge 202301 } |
    ForEach-Object {
        $period = [int]$_.cd_periodo
        $method = Get-Methodology -Period $period

        [pscustomobject][ordered]@{
            periodo = '{0:0000}-{1:00}' -f [math]::Floor($period / 100), ($period % 100)
            grupo_institucional = $_.tx_grupo
            cobertura_pct_poblacion_adulta = [math]::Round((Convert-ToNumber $_.nu_valor), 6)
            tramo_metodologico = $method.tramo
            umbral_saldo_deuda_reportable_pesos = $method.umbral
            fuente = 'BCRA, Indicadores de Inclusión Financiera, CENDEU'
            nota = 'Cobertura por grupo; una persona puede tener deuda con más de un grupo. No sumar porcentajes.'
        }
    }

$providers |
    Sort-Object periodo, grupo_institucional |
    Export-Csv -LiteralPath $ProvidersOutput -NoTypeInformation -Encoding utf8

$selectedPeriods = @(202312, 202406, 202407, 202412, 202506, 202512)
$age = Import-Csv -LiteralPath $agePath |
    Where-Object {
        [int]$_.cd_periodo -in $selectedPeriods -and $_.tx_asistencia -match '^Personales\s*/'
    } |
    ForEach-Object {
        $period = [int]$_.cd_periodo
        $method = Get-Methodology -Period $period

        [pscustomobject][ordered]@{
            periodo = '{0:0000}-{1:00}' -f [math]::Floor($period / 100), ($period % 100)
            rango_etario = $_.tx_edad
            cobertura_personales_pct_poblacion_del_rango = [math]::Round((Convert-ToNumber $_.nu_valor), 6)
            tramo_metodologico = $method.tramo
            umbral_saldo_deuda_reportable_pesos = $method.umbral
            fuente = 'BCRA, Indicadores de Inclusión Financiera, CENDEU'
            nota = 'Denominador: población del rango etario; no es participación del rango dentro del total de deudores.'
        }
    }

$age |
    Sort-Object periodo, rango_etario |
    Export-Csv -LiteralPath $AgeOutput -NoTypeInformation -Encoding utf8

Write-Host "Generado: $PersonalLoansOutput"
Write-Host "Generado: $ProvidersOutput"
Write-Host "Generado: $AgeOutput"

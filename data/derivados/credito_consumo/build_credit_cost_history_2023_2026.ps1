$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$inputPath = Join-Path $repoRoot 'data\derivados\tasas\brecha_costo_credito_vs_cftea_referencia_2019_2026.csv'
$monthlyOutput = Join-Path $PSScriptRoot 'costo_credito_personal_historia_2023_2026.csv'
$annualOutput = Join-Path $PSScriptRoot 'costo_credito_personal_resumen_anual_2023_2026.csv'
$culture = [Globalization.CultureInfo]::InvariantCulture

function Parse-Number([string]$value) {
    return [double]::Parse($value, $culture)
}

function Format-Number([double]$value) {
    return $value.ToString('0.000000', $culture)
}

$monthlyNumeric = Import-Csv -LiteralPath $inputPath |
    Where-Object { $_.fecha -ge '2023-01' -and $_.fecha -le '2026-07' } |
    ForEach-Object {
        $inflation = Parse-Number $_.inflacion_12m_pct
        $tna = Parse-Number $_.banco_tna_pct
        $tea = ([math]::Pow(1 + $tna / 1200, 12) - 1) * 100
        $realTea = ((1 + $tea / 100) / (1 + $inflation / 100) - 1) * 100
        $cfteaProxy = Parse-Number $_.banco_cftea_estandarizado_pct
        $realCfteaProxy = ((1 + $cfteaProxy / 100) / (1 + $inflation / 100) - 1) * 100

        [pscustomobject]@{
            fecha = $_.fecha
            year = $_.fecha.Substring(0, 4)
            inflacion_12m_pct = $inflation
            banco_tna_pct = $tna
            banco_tea_calc_pct = $tea
            banco_tasa_real_tea_pct = $realTea
            banco_cftea_proxy_pct = $cfteaProxy
            banco_tasa_real_cftea_proxy_pct = $realCfteaProxy
            volumen_banco_nominal = $_.volumen_banco_nominal
            ventana = $_.ventana
        }
    }

if ($monthlyNumeric.Count -ne 43) {
    throw "Expected 43 monthly observations from 2023-01 through 2026-07; found $($monthlyNumeric.Count)."
}

$monthlyExport = $monthlyNumeric | ForEach-Object {
    [pscustomobject]@{
        fecha = $_.fecha
        inflacion_12m_pct = Format-Number $_.inflacion_12m_pct
        banco_tna_pct = Format-Number $_.banco_tna_pct
        banco_tea_calc_pct = Format-Number $_.banco_tea_calc_pct
        banco_tasa_real_tea_pct = Format-Number $_.banco_tasa_real_tea_pct
        banco_cftea_proxy_pct = Format-Number $_.banco_cftea_proxy_pct
        banco_tasa_real_cftea_proxy_pct = Format-Number $_.banco_tasa_real_cftea_proxy_pct
        volumen_banco_nominal = $_.volumen_banco_nominal
        ventana = $_.ventana
    }
}

$annualExport = $monthlyNumeric |
    Group-Object -Property year |
    ForEach-Object {
        $group = $_.Group
        [pscustomobject]@{
            year = $_.Name
            meses_observados = $group.Count
            promedio_inflacion_12m_pct = Format-Number (($group | Measure-Object -Property inflacion_12m_pct -Average).Average)
            promedio_tna_pct = Format-Number (($group | Measure-Object -Property banco_tna_pct -Average).Average)
            promedio_tea_calc_pct = Format-Number (($group | Measure-Object -Property banco_tea_calc_pct -Average).Average)
            promedio_tasa_real_tea_pct = Format-Number (($group | Measure-Object -Property banco_tasa_real_tea_pct -Average).Average)
            minimo_tasa_real_tea_pct = Format-Number (($group | Measure-Object -Property banco_tasa_real_tea_pct -Minimum).Minimum)
            maximo_tasa_real_tea_pct = Format-Number (($group | Measure-Object -Property banco_tasa_real_tea_pct -Maximum).Maximum)
            promedio_cftea_proxy_pct = Format-Number (($group | Measure-Object -Property banco_cftea_proxy_pct -Average).Average)
            promedio_tasa_real_cftea_proxy_pct = Format-Number (($group | Measure-Object -Property banco_tasa_real_cftea_proxy_pct -Average).Average)
        }
    }

$monthlyExport | Export-Csv -LiteralPath $monthlyOutput -NoTypeInformation -Encoding utf8
$annualExport | Export-Csv -LiteralPath $annualOutput -NoTypeInformation -Encoding utf8

Write-Output "monthly_rows=$($monthlyExport.Count)"
Write-Output "annual_rows=$($annualExport.Count)"
Write-Output "monthly_output=$monthlyOutput"
Write-Output "annual_output=$annualOutput"

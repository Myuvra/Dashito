param(
  [string]$SourceDir = "data/fuentes/pendulo_distributivo/indec",
  [string]$OutputPath = "data/derivados/pendulo_distributivo/cgi_raw.json"
)

$ErrorActionPreference = "Stop"

function Get-QuarterNumber([object]$value) {
  if ($null -eq $value) { return $null }
  $text = [string]$value
  if ($text -match '^\s*([1-4])') { return [int]$Matches[1] }
  return $null
}

function Read-ModernCgi($excel, [string]$path) {
  $book = $excel.Workbooks.Open($path, 0, $true)
  try {
    $sheets = [ordered]@{
      vab = "VAB_pb"
      rta = "RTA"
      imb = "IBM"
      taxes_net = "T-S"
      eeb = "EEB"
    }
    $rows = [ordered]@{
      total = 7
      private = 9
    }
    $periods = [ordered]@{}

    foreach ($metric in $sheets.Keys) {
      $sheet = $book.Worksheets.Item($sheets[$metric])
      $values = $sheet.UsedRange.Value2
      $year = $null
      for ($col = 3; $col -le $sheet.UsedRange.Columns.Count; $col++) {
        $yearCandidate = $values[3, $col]
        if ($yearCandidate -is [double] -or $yearCandidate -is [int]) {
          $year = [int]$yearCandidate
        } elseif ($yearCandidate -and ([string]$yearCandidate -match '^\s*(20\d{2})')) {
          $year = [int]$Matches[1]
        }
        $quarter = Get-QuarterNumber $values[4, $col]
        if ($null -eq $year -or $null -eq $quarter) { continue }
        $period = "{0}-Q{1}" -f $year, $quarter
        if (-not $periods.Contains($period)) {
          $periods[$period] = [ordered]@{
            period = $period
            year = $year
            quarter = $quarter
            total = [ordered]@{}
            private = [ordered]@{}
          }
        }
        foreach ($universe in $rows.Keys) {
          $raw = $values[$rows[$universe], $col]
          if ($raw -is [double] -or $raw -is [int] -or $raw -is [decimal]) {
            $periods[$period][$universe][$metric] = [double]$raw
          } else {
            $periods[$period][$universe][$metric] = $null
          }
        }
      }
    }
    return @($periods.Values)
  } finally {
    $book.Close($false)
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($book) | Out-Null
  }
}

function Read-HistoricalCgi($excel, [string]$path, [string]$universe) {
  $book = $excel.Workbooks.Open($path, 0, $true)
  try {
    $sheet = $book.Worksheets.Item(1)
    $values = $sheet.UsedRange.Value2
    $out = @()
    for ($col = 2; $col -le 16; $col++) {
      $yearText = [string]$values[5, $col]
      if ($yearText -notmatch '(19|20)\d{2}') { continue }
      $year = [int]$Matches[0]
      $out += [ordered]@{
        period = [string]$year
        year = $year
        universe = $universe
        vab = [double]$values[15, $col]
        rta = [double]$values[17, $col]
        imb = [double]$values[18, $col]
        eeb = [double]$values[19, $col]
        taxes_net = $null
      }
    }
    return $out
  } finally {
    $book.Close($false)
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($book) | Out-Null
  }
}

$excel = New-Object -ComObject Excel.Application
try {
  $excel.Visible = $false
  $excel.DisplayAlerts = $false
  $resolvedSource = (Resolve-Path -LiteralPath $SourceDir).Path
  $modern = Read-ModernCgi $excel (Join-Path $resolvedSource "serie_cgi_07_26.xls")
  $historicalTotal = Read-HistoricalCgi $excel (Join-Path $resolvedSource "cgi_cuadro1_total_1993_2007.xls") "total"
  $historicalPrivate = Read-HistoricalCgi $excel (Join-Path $resolvedSource "cgi_apendice4_privado_1993_2007.xls") "private"
  $payload = [ordered]@{
    extracted_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    modern = $modern
    historical = @($historicalTotal + $historicalPrivate)
  }
  $resolvedOutput = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputPath))
  [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($resolvedOutput)) | Out-Null
  $json = $payload | ConvertTo-Json -Depth 8
  [System.IO.File]::WriteAllText($resolvedOutput, $json, [System.Text.UTF8Encoding]::new($false))
  Write-Output "Extracted $($modern.Count) modern periods and $($payload.historical.Count) historical rows to $resolvedOutput"
} finally {
  if ($excel) {
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
  }
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}

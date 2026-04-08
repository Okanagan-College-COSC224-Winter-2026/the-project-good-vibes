param(
    [string]$BaseUrl = "http://localhost:5000",
    [string]$AdminEmail = "admin@example.com",
    [string]$AdminPassword = "123456",
    [string]$CsvPath = "docs/test-data/staff-seed.csv"
)

$ErrorActionPreference = "Stop"

function Get-ErrorBody {
    param([System.Management.Automation.ErrorRecord]$Err)

    try {
        $response = $Err.Exception.Response
        if ($null -eq $response) { return $Err.Exception.Message }

        $stream = $response.GetResponseStream()
        if ($null -eq $stream) { return $Err.Exception.Message }

        $reader = New-Object System.IO.StreamReader($stream)
        return $reader.ReadToEnd()
    } catch {
        return $Err.Exception.Message
    }
}

if (-not (Test-Path $CsvPath)) {
    throw "CSV file not found: $CsvPath"
}

Write-Host "Logging in as admin..."
$loginBody = @{ email = $AdminEmail; password = $AdminPassword } | ConvertTo-Json
Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/auth/login" -Method Post -Body $loginBody -ContentType "application/json" -SessionVariable Session | Out-Null

$rows = Import-Csv $CsvPath
if (-not $rows -or $rows.Count -eq 0) {
    throw "No rows found in $CsvPath"
}

$created = 0
$skipped = 0
$failed = 0

foreach ($row in $rows) {
    $role = "$($row.role)".Trim().ToLower()
    if ($role -notin @("student", "teacher", "admin")) {
        Write-Host "[SKIP] Invalid role '$role' for $($row.email)"
        $skipped++
        continue
    }

    $mustChange = $false
    if ("$($row.must_change_password)".Trim().ToLower() -in @("true", "1", "yes", "y")) {
        $mustChange = $true
    }

    $payload = @{
        name = "$($row.name)".Trim()
        email = "$($row.email)".Trim()
        password = "$($row.password)"
        role = $role
        must_change_password = $mustChange
    } | ConvertTo-Json

    try {
        $resp = Invoke-RestMethod -Uri "$BaseUrl/admin/users/create" -Method Post -Body $payload -ContentType "application/json" -WebSession $Session
        Write-Host "[OK] $($resp.msg)"
        $created++
    } catch {
        $body = Get-ErrorBody $_
        if ($body -match "already registered") {
            Write-Host "[SKIP] User already exists: $($row.email)"
            $skipped++
        } else {
            Write-Host "[FAIL] $($row.email): $body"
            $failed++
        }
    }
}

Write-Host "Done. Created=$created, Skipped=$skipped, Failed=$failed"

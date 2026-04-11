param(
    [string]$BaseUrl = "http://localhost:5000",
    [string]$TeacherEmail = "teacher@example.com",
    [string]$TeacherPassword = "123456",
    [int]$ClassId,
    [string]$CsvPath = "docs/test-data/students-21-seed.csv"
)

$ErrorActionPreference = "Stop"

if (-not $ClassId) {
    throw "ClassId is required. Example: -ClassId 1"
}

if (-not (Test-Path $CsvPath)) {
    throw "CSV file not found: $CsvPath"
}

Write-Host "Logging in as teacher..."
$loginBody = @{ email = $TeacherEmail; password = $TeacherPassword } | ConvertTo-Json
Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/auth/login" -Method Post -Body $loginBody -ContentType "application/json" -SessionVariable Session | Out-Null

$csvText = Get-Content -Path $CsvPath -Raw

$escapedCsv = $csvText `
    -replace '\\', '\\\\' `
    -replace '"', '\\"' `
    -replace "`r`n", '\n' `
    -replace "`n", '\n'

$payload = "{`"class_id`":$ClassId,`"students`":`"$escapedCsv`"}"

Write-Host "Enrolling students from $CsvPath into class $ClassId..."
$response = Invoke-RestMethod -Uri "$BaseUrl/class/enroll_students" -Method Post -Body $payload -ContentType "application/json" -WebSession $Session
Write-Host "Result: $($response.msg)"
Write-Host "Note: newly created roster users receive default password 'password123' in current backend implementation."

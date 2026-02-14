param(
    [Parameter(Mandatory = $true)]
    [string]$StageName
)

$ErrorActionPreference = "Stop"

git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Current directory is not a git repository."
}

git add -A
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Output "No changes to upload."
    exit 0
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$message = "stage: $StageName ($timestamp)"
git commit -m $message | Out-Host

$branch = (git branch --show-current).Trim()
$remote = (git remote).Split([Environment]::NewLine, [System.StringSplitOptions]::RemoveEmptyEntries) | Select-Object -First 1

if (-not $remote) {
    Write-Output "Committed locally, but no git remote is configured."
    exit 0
}

git push $remote $branch | Out-Host
Write-Output "Uploaded: $remote/$branch -> $message"

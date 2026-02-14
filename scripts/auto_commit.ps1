param(
    [string]$MessagePrefix = "chore: auto snapshot"
)

$ErrorActionPreference = "Stop"

git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Current directory is not a git repository."
}

git add -A

$hasChanges = git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Output "No staged changes to commit."
    exit 0
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$message = "$MessagePrefix ($timestamp)"

git commit -m $message
Write-Output "Committed: $message"

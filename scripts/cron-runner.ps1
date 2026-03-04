# CodeGeass CRON Runner for Windows Task Scheduler
# CRITICAL: Use subscription, not API
$env:ANTHROPIC_API_KEY = $null

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

# Change to project directory
Set-Location $ProjectDir

# Run scheduler
& codegeass scheduler run-due

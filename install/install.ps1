# install.ps1 - workstation setup for AI courses (generic, safe to re-run)
# Installs Claude Desktop, uv and Git with winget, fetches the skills repo,
# links the skills for Claude Code, and creates the work layout:
#   ai\private\in         originals (never connect this folder to Claude)
#   ai\private\restored   restored results
#   ai\work\masked        masked copies: the folder you give to Claude
#   ai\tools, hints       masking tools and the hint files to paste
# Run:  powershell -ExecutionPolicy Bypass -File install.ps1 [-Source <git url or folder>] [-WithCli]
# Windows PowerShell 5.1 compatible; plain ASCII on purpose.
param(
    [string]$Source  = 'https://github.com/mariolpantunes/ai-skills',
    [string]$RepoDir = (Join-Path $env:USERPROFILE 'ai-skills'),
    [string]$AiHome  = (Join-Path $env:USERPROFILE 'ai'),  # not Documents: OneDrive may sync it
    [switch]$WithCli,
    [switch]$SkipApps
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ok = 0; $todo = @()

function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Done($m) { Write-Host "  [ok]   $m" -ForegroundColor Green; $script:ok++ }
function Todo($m) { Write-Host "  [todo] $m" -ForegroundColor Yellow; $script:todo += $m }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}
function Winget-Install($id, $label) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'winget not found: install App Installer from the Microsoft Store.' }
    winget install -e --id $id --accept-source-agreements --accept-package-agreements --silent
    # 0 = installed, -1978335189 = already installed / no update
    if ($LASTEXITCODE -notin 0, -1978335189) { throw "winget install $id failed ($LASTEXITCODE)" }
    Refresh-Path
}

# 1. Applications
Step 'Applications'
if (-not $SkipApps) {
    $claudeExe = Join-Path $env:LOCALAPPDATA 'AnthropicClaude\claude.exe'
    if (Test-Path $claudeExe) { Done 'Claude Desktop already installed (version left alone: it updates itself)' }
    else { Winget-Install 'Anthropic.Claude' 'Claude Desktop'; Done 'Claude Desktop installed' }
    if (Get-Command uv -ErrorAction SilentlyContinue) { Done 'uv already installed' }
    else { Winget-Install 'astral-sh.uv' 'uv'; Done 'uv installed' }
    if (Get-Command git -ErrorAction SilentlyContinue) { Done 'Git already installed' }
    else { Winget-Install 'Git.Git' 'Git'; Done 'Git installed' }
    if ($WithCli) {
        if (Get-Command claude -ErrorAction SilentlyContinue) { Done 'Claude Code already installed' }
        else { Winget-Install 'Anthropic.ClaudeCode' 'Claude Code'; Done 'Claude Code installed' }
    }
} else { Done 'Applications skipped (-SkipApps)' }

# 2. Skills repo (git clone or pull; a folder as -Source is copied)
Step "Skills repo ($Source)"
$git = Get-Command git -ErrorAction SilentlyContinue
if (Test-Path -LiteralPath $Source -PathType Container) {
    if (Test-Path $RepoDir) { Move-Item $RepoDir ("$RepoDir.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss')) }
    Copy-Item -LiteralPath $Source -Destination $RepoDir -Recurse
    Done "Copied from folder to $RepoDir"
} elseif ($git -and (Test-Path (Join-Path $RepoDir '.git'))) {
    git -C $RepoDir pull --ff-only
    if ($LASTEXITCODE -ne 0) { Todo 'git pull failed; the copy that is there is kept' } else { Done "Updated $RepoDir" }
} elseif ($git) {
    if (Test-Path $RepoDir) { Move-Item $RepoDir ("$RepoDir.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss')) }  # a copy that is not a git clone
    git clone $Source $RepoDir
    if ($LASTEXITCODE -ne 0) { throw 'git clone failed' }
    Done "Cloned to $RepoDir"
} else { throw 'Git is not available; re-run after installing it.' }
$skills = @(Get-ChildItem -Path (Join-Path $RepoDir 'plugins') -Recurse -Filter SKILL.md | ForEach-Object { $_.Directory })
if ($skills.Count -lt 1) { throw "no skills found in $RepoDir" }
Done "$($skills.Count) skills on disk"

# 3. Link the skills for Claude Code (directory junctions, no admin needed)
Step 'Link skills into ~\.claude\skills (Claude Code)'
$dst = Join-Path $env:USERPROFILE '.claude\skills'
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$linked = 0
foreach ($s in $skills) {
    $link = Join-Path $dst $s.Name
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { [IO.Directory]::Delete($link) } else { Todo "$($s.Name): a real folder is in the way, left alone"; continue }
    }
    New-Item -ItemType Junction -Path $link -Target $s.FullName | Out-Null
    $linked++
}
Done "$linked skill links (they follow git pull)"

# 4. Work layout, tools, hints
Step "Work folders under $AiHome"
foreach ($d in 'private\in', 'private\restored', 'work\masked', 'tools', 'hints') {
    New-Item -ItemType Directory -Force -Path (Join-Path $AiHome $d) | Out-Null
}
Copy-Item (Join-Path $RepoDir 'plugins\privacy\skills\mask-sensitive\scripts\sensitive.py') (Join-Path $AiHome 'tools') -Force
Copy-Item (Join-Path $RepoDir 'install\tools\*.cmd') (Join-Path $AiHome 'tools') -Force
Copy-Item (Join-Path $RepoDir 'hints\*') (Join-Path $AiHome 'hints') -Force
$terms = Join-Path $AiHome 'private\terms.txt'
if (-not (Test-Path $terms)) {
    "# One name per line (people, companies, products). Optional type: ORG: Acme Lda`r`n# Lines that start with # are ignored." | Set-Content -Path $terms -Encoding Ascii
}
Done 'tools, hints and terms.txt in place'

# 5. Check
Step 'Check'
Refresh-Path
foreach ($c in 'uv', 'git') { if (Get-Command $c -ErrorAction SilentlyContinue) { Done "$c on PATH" } else { Todo "$c not on PATH yet: open a new PowerShell" } }
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $env:AI_HOME = $AiHome
    uv run (Join-Path $AiHome 'tools\sensitive.py') scan (Join-Path $AiHome 'work') | Out-Host
    if ($LASTEXITCODE -eq 0) { Done 'masking tool runs (scan: CLEAN)' } else { Todo 'masking tool did not run clean' }
}

Write-Host "`n$ok ok, $($todo.Count) todo" -ForegroundColor Cyan
Write-Host @"

Next, by hand in Claude Desktop:
  1. Sign in with your Claude account.
  2. Customize > Plugins > Add marketplace: mariolpantunes/ai-skills  (then add core, office, data, privacy)
  3. Settings > Instructions: paste $AiHome\hints\global-instructions.md
  4. Connect only the folder $AiHome\work (never the folder private).
  5. Connectors > Microsoft 365 > Connect.
Put documents in $AiHome\private\in, double-click tools\mask.cmd, then work on work\masked.
"@
if ($todo.Count) { exit 1 }

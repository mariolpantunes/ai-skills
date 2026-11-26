# install.ps1 - workstation setup for AI courses (generic, safe to re-run)
# Installs the agent app (Claude Desktop or goose Desktop), uv and Git with winget, fetches the skills repo,
# links the skills for the agent, and creates the work layout:
#   ai\private\in         originals (never connect this folder to Claude)
#   ai\private\restored   restored results
#   ai\work\masked        masked copies: the folder you give to Claude
#   ai\tools, hints       masking tools and the hint files to paste
# Run:  powershell -ExecutionPolicy Bypass -File install.ps1 [-Agent claude|goose|both] [-Source <git url or folder>] [-WithCli]
# Windows PowerShell 5.1 compatible; plain ASCII on purpose.
param(
    [string]$Source  = 'https://github.com/mariolpantunes/ai-skills',
    [string]$RepoDir = (Join-Path $env:USERPROFILE 'ai-skills'),
    [string]$AiHome  = (Join-Path $env:USERPROFILE 'ai'),  # not Documents: OneDrive may sync it
    [ValidateSet('claude','goose','both')][string]$Agent = 'claude',   # which agent app to set up
    [switch]$WithCli,
    [switch]$RegisterMcp,   # add the masked-reader MCP server to the agent config (backs it up first)
    [switch]$SkipApps
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ok = 0; $todo = @()
$useClaude = $Agent -in 'claude','both'
$useGoose  = $Agent -in 'goose','both'

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
    if ($useClaude) {
        $claudeExe = Join-Path $env:LOCALAPPDATA 'AnthropicClaude\claude.exe'
        if (Test-Path $claudeExe) { Done 'Claude Desktop already installed (version left alone: it updates itself)' }
        else { Winget-Install 'Anthropic.Claude' 'Claude Desktop'; Done 'Claude Desktop installed' }
    }
    if ($useGoose) {
        Winget-Install 'AgenticAIFoundation.gooseDesktop' 'goose Desktop'; Done 'goose Desktop installed (or already there)'
    }
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

# 3. Link the skills (directory junctions, no admin needed): Claude Code reads ~\.claude\skills, goose reads ~\.agents\skills (flat)
function Link-Skills($dst) {
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
    Done "$linked skill links in $dst (they follow git pull)"
}
if ($useClaude) { Step 'Link skills into ~\.claude\skills (Claude Code)'; Link-Skills (Join-Path $env:USERPROFILE '.claude\skills') }
if ($useGoose)  { Step 'Link skills into ~\.agents\skills (goose)';       Link-Skills (Join-Path $env:USERPROFILE '.agents\skills') }

# 4. Work layout, tools, hints
Step "Work folders under $AiHome"
foreach ($d in 'private\in', 'private\restored', 'work\masked', 'tools', 'hints') {
    New-Item -ItemType Directory -Force -Path (Join-Path $AiHome $d) | Out-Null
}
Copy-Item (Join-Path $RepoDir 'plugins\privacy\skills\mask-sensitive\scripts\*.py') (Join-Path $AiHome 'tools') -Force
Copy-Item (Join-Path $RepoDir 'plugins\privacy\mcp\masked_reader.py') (Join-Path $AiHome 'tools') -Force
Copy-Item (Join-Path $RepoDir 'install\tools\*.cmd') (Join-Path $AiHome 'tools') -Force
Copy-Item (Join-Path $RepoDir 'hints\*') (Join-Path $AiHome 'hints') -Force
$terms = Join-Path $AiHome 'private\terms.txt'
if (-not (Test-Path $terms)) {
    "# One name per line (people, companies, products). Optional type: ORG: Acme Lda`r`n# Lines that start with # are ignored." | Set-Content -Path $terms -Encoding Ascii
}
Done 'tools, hints and terms.txt in place'

# 4a. goose: global hints = the course instructions (an existing different file is kept as a .bak copy)
$gooseCfgDir = Join-Path $env:APPDATA 'Block\goose\config'
if ($useGoose) {
    Step 'goose: global hints'
    New-Item -ItemType Directory -Force -Path $gooseCfgDir | Out-Null
    $hintsDst = Join-Path $gooseCfgDir '.goosehints'
    $hintsSrc = Join-Path $RepoDir 'hints\global-instructions.md'
    if ((Test-Path $hintsDst) -and ((Get-FileHash $hintsDst).Hash -ne (Get-FileHash $hintsSrc).Hash)) {
        Copy-Item $hintsDst ("$hintsDst.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    }
    Copy-Item $hintsSrc $hintsDst -Force
    Done "global hints in $hintsDst (open a new chat to load them)"
}

# 4b. masked-reader MCP server (opt-in): the agent reads documents only through masked text
if ($RegisterMcp -and $useGoose) {
    Step 'Registering the masked-reader extension in goose'
    $uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
    $cfg = Join-Path $gooseCfgDir 'config.yaml'
    if (-not $uv) { Todo 'uv not found: cannot register the extension' }
    elseif (-not (Test-Path $cfg)) { Todo 'goose has no config yet: start goose once, pick the provider, then run this again with -RegisterMcp' }
    else {
        $lines = [IO.File]::ReadAllLines($cfg)
        if ($lines -match '^\s{2}masked-reader:') { Done 'masked-reader already in the goose config' }
        else {
            Copy-Item $cfg ("$cfg.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
            $reader = Join-Path $AiHome 'tools\masked_reader.py'
            $block = @('  masked-reader:', '    name: Masked reader', "    cmd: '$uv'", "    args: [run, --script, '$reader']",
                       '    enabled: true', '    type: stdio', '    timeout: 300', "    envs: {AI_HOME: '$AiHome'}")
            $out = New-Object System.Collections.Generic.List[string]
            $placed = $false
            foreach ($l in $lines) {
                $out.Add($l)
                if (-not $placed -and $l -match '^extensions:\s*$') { foreach ($b in $block) { $out.Add($b) }; $placed = $true }
            }
            if (-not $placed) { $out.Add('extensions:'); foreach ($b in $block) { $out.Add($b) } }
            [IO.File]::WriteAllLines($cfg, $out, (New-Object Text.UTF8Encoding($false)))
            Done "masked-reader registered in $cfg (open a new chat)"
        }
    }
}
if ($RegisterMcp -and $useClaude) {
    Step 'Registering the masked-reader MCP server in Claude Desktop'
    $uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
    if (-not $uv) { Todo 'uv not found: cannot register the MCP server' } else {
        $cfgDir = Join-Path $env:APPDATA 'Claude'
        New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
        $cfg = Join-Path $cfgDir 'claude_desktop_config.json'
        $obj = [ordered]@{}
        if (Test-Path $cfg) {
            Copy-Item $cfg ("$cfg.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
            $raw = [IO.File]::ReadAllText($cfg).TrimStart([char]0xFEFF)
            if ($raw.Trim()) { $parsed = $raw | ConvertFrom-Json; foreach ($p in $parsed.PSObject.Properties) { $obj[$p.Name] = $p.Value } }
        }
        $servers = [ordered]@{}
        if ($obj.Contains('mcpServers') -and $obj['mcpServers']) { foreach ($p in $obj['mcpServers'].PSObject.Properties) { $servers[$p.Name] = $p.Value } }
        $servers['masked-reader'] = [ordered]@{
            command = $uv
            args    = @('run', '--script', (Join-Path $AiHome 'tools\masked_reader.py'))
            env     = [ordered]@{ AI_HOME = $AiHome }
        }
        $obj['mcpServers'] = $servers
        [IO.File]::WriteAllText($cfg, ($obj | ConvertTo-Json -Depth 10), (New-Object Text.UTF8Encoding($false)))
        Done "masked-reader registered in $cfg (restart Claude Desktop)"
    }
}

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
if ($useClaude) { Write-Host @"

Next, by hand in Claude Desktop:
  1. Sign in with your Claude account.
  2. Customize > Plugins > Add marketplace: mariolpantunes/ai-skills  (then add core, office, data, privacy)
  3. Settings > Instructions: paste $AiHome\hints\global-instructions.md
  4. Connect only the folder $AiHome\work (never the folder private).
  5. Connectors > Microsoft 365 > Connect.
  6. Optional: run install.ps1 -RegisterMcp, restart Claude Desktop: Claude then reads your documents only through the masked-reader tools.
Put documents in $AiHome\private\in, double-click tools\mask.cmd, then work on work\masked.
"@ }
if ($useGoose) { Write-Host @"

Next, by hand in goose:
  1. Start goose, choose the model provider, paste the key you were given.
  2. Settings > Chat > Default mode: Manual approval (the default is Autonomous).
  3. Open the folder $AiHome\work\masked as the working folder; start a new chat.
  4. Ask: "which skills do you have?" and "what rules do you follow?"
  5. Optional: run install.ps1 -Agent goose -RegisterMcp once goose has been started: goose then reads your documents only through the masked-reader extension.
goose has no folder fence: never work in the folder private.
Put documents in $AiHome\private\in, double-click tools\mask.cmd, then work on work\masked.
"@ }
if ($todo.Count) { exit 1 }

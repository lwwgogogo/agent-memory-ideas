param(
    [string]$IdentityFile = "$env:USERPROFILE/.ssh/liaoweiwen_imds_ed25519",
    [string]$Server = "liaoweiwen@222.20.98.121",
    [string]$RemoteDirectory = "/home/liaoweiwen/projects/agent-memory-ideas",
    [switch]$RunSmoke,
    [switch]$Ipv4Only
)
$ErrorActionPreference = 'Stop'
if ($RemoteDirectory -notmatch '^/home/liaoweiwen/projects/[a-zA-Z0-9_-]+$') { throw 'Unexpected remote project path' }
$projectRoot = Split-Path $PSScriptRoot -Parent
$archive = Join-Path ([System.IO.Path]::GetTempPath()) ('agent-memory-' + [guid]::NewGuid() + '.tar.gz')
$sshArgs = @('-i', $IdentityFile, '-p', '22', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15')
Push-Location $projectRoot
try {
    & tar --exclude=__pycache__ --exclude='*.pyc' -czf $archive README.md requirements.txt .gitignore configs src scripts tests docs experiments data
    if ($LASTEXITCODE -ne 0) { throw 'Archive creation failed' }
    & ssh @sshArgs $Server "mkdir -p '$RemoteDirectory'"
    if ($LASTEXITCODE -ne 0) { throw 'Remote directory creation failed' }
    & scp -i $IdentityFile -P 22 -o BatchMode=yes $archive "${Server}:$RemoteDirectory/source.tar.gz"
    if ($LASTEXITCODE -ne 0) { throw 'Upload failed' }
    & ssh @sshArgs $Server "cd '$RemoteDirectory' && tar -xzf source.tar.gz"
    if ($LASTEXITCODE -ne 0) { throw 'Extraction failed' }
    if ($RunSmoke) {
        $networkFlag = if ($Ipv4Only) { '1' } else { '0' }
        & ssh @sshArgs $Server "cd '$RemoteDirectory' && PIP_IPV4_ONLY=$networkFlag bash scripts/server_smoke.sh"
        if ($LASTEXITCODE -ne 0) { throw 'Remote smoke failed' }
    }
} finally {
    Pop-Location
    Remove-Item -LiteralPath $archive -ErrorAction SilentlyContinue
}

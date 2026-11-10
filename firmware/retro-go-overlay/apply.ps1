<#
.SYNOPSIS
  Накладає наш таргет на чистий клон Retro-Go.

.DESCRIPTION
  Копіює файли оверлея поверх клону (шляхи дзеркалять upstream) і реєструє
  таргет у components/retro-go/config.h. Ідемпотентний — можна запускати
  скільки завгодно разів, зокрема після `git pull` в клоні.

.EXAMPLE
  .\apply.ps1 -RetroGo ..\..\retro-go
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$RetroGo
)

$ErrorActionPreference = 'Stop'
$overlay = $PSScriptRoot

if (-not (Test-Path (Join-Path $RetroGo 'rg_tool.py'))) {
    throw "Не схоже на клон Retro-Go: у '$RetroGo' немає rg_tool.py"
}

# --- 1. копіюємо файли оверлея -------------------------------------------
# Копіюємо ВСІ теки оверлея (шляхи дзеркалять upstream), а не лише components:
# у retro-core/main/ лежать патчені main_snes.c (Type D) і main_nes.c (турбо).
Write-Host "Копіюю оверлей у $RetroGo ..."
foreach ($dir in Get-ChildItem -Path $overlay -Directory) {
    Copy-Item -Path $dir.FullName -Destination $RetroGo -Recurse -Force
    Write-Host "  $($dir.Name)/ - ok"
}

# --- 2. реєструємо таргет ------------------------------------------------
$cfg = Join-Path $RetroGo 'components\retro-go\config.h'
$text = Get-Content $cfg -Raw

if ($text -match 'RG_TARGET_RETRO_CONSOLE') {
    Write-Host "  таргет уже зареєстрований у config.h - пропускаю"
}
else {
    $anchor = '#else' + "`n" + '#warning "No target defined'
    if ($text -notmatch [regex]::Escape('#warning "No target defined')) {
        throw "Не знайшов місце вставки в $cfg - структура upstream змінилась, вставити вручну"
    }
    $insert = '#elif defined(RG_TARGET_RETRO_CONSOLE)' + "`n" +
              '#include "targets/retro-console/config.h"' + "`n"
    $idx = $text.IndexOf('#else')
    $text = $text.Substring(0, $idx) + $insert + $text.Substring($idx)
    Set-Content -Path $cfg -Value $text -Encoding utf8 -NoNewline
    Write-Host "  таргет зареєстрований у components/retro-go/config.h - ok"
}

Write-Host ""
Write-Host "Готово. Збірка:" -ForegroundColor Green
Write-Host "  `$env:IDF_TOOLS_PATH='C:\Espressif\tools'"
Write-Host "  . C:\esp\v5.3.5\esp-idf\export.ps1"
Write-Host "  cd $RetroGo"
Write-Host "  python rg_tool.py build-fw launcher retro-core --target=retro-console"

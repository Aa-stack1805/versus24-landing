#!/usr/bin/env bash
# Re-fetch the self-hosted woff2 files in assets/fonts/.
#
# Only needed when Google ships a new version of either family (the URLs carry
# a version segment, /v25/ and /v24/ below) or when the site starts needing a
# subset beyond latin and latin-ext. Day to day the committed files are fine.
#
# To find current URLs: request the CSS with a modern browser User-Agent so
# Google serves woff2 rather than ttf, and read the src: lines.
#
#   curl -A "$UA" 'https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=JetBrains+Mono:wght@100..800&display=swap'
#
# Then update the URLs here and the matching unicode-range blocks at the top of
# assets/style.css, which must stay identical to Google's.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p assets/fonts

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
BASE='https://fonts.gstatic.com/s'

fetch() {
  echo "  assets/fonts/$1"
  curl -sSf -A "$UA" "$BASE/$2" -o "assets/fonts/$1"
}

fetch archivo-latin.woff2            'archivo/v25/k3kQo8UDI-1M0wlSfdnoLg.woff2'
fetch archivo-latin-ext.woff2        'archivo/v25/k3kQo8UDI-1M0wlSfdfoLnnA.woff2'
fetch jetbrains-mono-latin.woff2     'jetbrainsmono/v24/tDbV2o-flEEny0FZhsfKu5WU4xD7OwE.woff2'
fetch jetbrains-mono-latin-ext.woff2 'jetbrainsmono/v24/tDbV2o-flEEny0FZhsfKu5WU4xD1OwG_TA.woff2'

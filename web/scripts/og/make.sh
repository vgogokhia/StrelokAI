#!/bin/sh
# Renders the Open Graph images (1200x630) with headless Chromium. Output: web/public/brand/og-{en,ka}.png
cd "$(dirname "$0")"
CHROME=${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}
render() { # lang heading subtitle elevLabel windLabel
  sed -e "s|__H__|$2|" -e "s|__S__|$3|" -e "s|__EL__|$4|" -e "s|__WL__|$5|" og.html > og-$1.tmp.html
  "$CHROME" --headless=new --no-sandbox --hide-scrollbars --allow-file-access-from-files --force-device-scale-factor=1 \
    --window-size=1200,800 --screenshot="$PWD/../../public/brand/og-$1.png" "file://$PWD/og-$1.tmp.html" 2>/dev/null
  rm -f og-$1.tmp.html
  # headless Chromium's viewport is shorter than the window: render tall, keep the top 1200x630
  python3 -c "from PIL import Image; p='../../public/brand/og-$1.png'; Image.open(p).crop((0,0,1200,630)).convert('RGB').save(p, optimize=True)"
}
render en 'Free <b>ballistic calculator</b> that works offline' 'Elevation and wind in MIL or MOA, drop charts and DOPE cards for .308, 6.5 CM, .223 and .22 LR' 'ELEVATION' 'WIND'
render ka 'უფასო <b>ბალისტიკური კალკულატორი</b>' 'ვერტიკალი და ქარი MIL-სა და MOA-ში, ცხრილები და DOPE. მუშაობს ინტერნეტის გარეშე.' 'ვერტიკალი' 'ქარი'

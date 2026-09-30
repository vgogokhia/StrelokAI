export default ({ F, n, table, dropTable }) => {
  const at = (k, yd) => F.tables[k].find((r) => r.yd === yd);
  const [a3, a5, a10] = [300, 500, 1000].map((y) => at("308", y));
  const [c5, c10] = [500, 1000].map((y) => at("65cm", y));
  const [r1, r2] = [100, 200].map((y) => at("22lr", y));
  const z100 = F.tables["308"], z200 = F.zero200;
  return [
{
  slug: "bullet-drop-chart", cat: "Ballistic charts", term: "Bullet drop chart",
  h1: "Bullet drop chart: .308, 6.5 Creedmoor, .223 and .22 LR",
  title: "Bullet Drop Chart: .308, 6.5 Creedmoor, .223 and .22 LR",
  description: "Bullet drop charts in inches, MOA and MIL for .308, 6.5 Creedmoor, .223 and .22 LR, with wind drift, velocity and energy, and how to read them.",
  short: "drop, come-ups and wind drift for four popular cartridges, and how to read them.",
  answer: "<b>Bullet drop</b> is how far the bullet falls below your line of sight at a given distance. With a 100-yard zero, a .308 175 gr load drops about " + n(-a5.dropIn, 0) + " inches at 500 yards (" + n(-a5.mil) + " MIL), a 6.5 Creedmoor 140 gr about " + n(-c5.dropIn, 0) + " inches, and a .22 LR with a 50-yard zero about " + n(-r1.dropIn, 0) + " inches at 100 yards.",
  sections: [
    { h: "How to read these charts", html: `<p><b>Drop</b> is measured from the line of sight, so it is zero at the zero distance and slightly positive just before it. <b>Up</b> is the elevation to dial or hold, in MOA and MIL. <b>Wind</b> is the drift for a full-value 10 mph crosswind; halve it for 5 mph, double it for 20. These are reference numbers: your rifle's velocity and your altitude will change them, so use the <a href="/">calculator</a> for your own load.</p>` },
    { h: ".308 Winchester, 175 gr", html: dropTable("308") + `<p>Explained in detail: <a href="/glossary/308-ballistics-chart/">.308 trajectory</a>. All .308 loads: <a href="/ballistics/308-win/">.308 Win charts</a>.</p>` },
    { h: "6.5 Creedmoor, 140 gr", html: dropTable("65cm") + `<p>Compared with .308: <a href="/glossary/6-5-creedmoor-ballistics-chart/">6.5 Creedmoor vs .308</a>. All loads: <a href="/ballistics/6-5-creedmoor/">6.5 Creedmoor charts</a>.</p>` },
    { h: ".223 Remington, 55 gr", html: dropTable("223") + `<p>The light 55 gr bullet starts fast but loses speed quickly; it has more wind drift at 500 yards than the .308 despite starting 640 fps faster. The 2.6" sight height is typical of an AR-15.</p>` },
    { h: ".22 LR, 40 gr standard velocity", html: dropTable("22lr") + `<p>More in <a href="/glossary/22lr-bullet-drop/">.22 LR bullet drop</a>.</p>` },
  ],
  faq: [
    { q: "How much does a .308 drop at 1000 yards?", a: `With a 175 gr bullet at 2600 fps and a 100-yard zero, about ${n(-a10.dropIn, 0)} inches, or ${n(-a10.mil)} MIL / ${n(-a10.moa)} MOA of come-up, at sea level.` },
    { q: "How much does a bullet drop at 100 yards?", a: "If you are zeroed at 100 yards, zero. Drop is measured from the line of sight, which crosses the bullet's path at the zero distance." },
    { q: "Do heavier bullets drop more?", a: "At the same velocity, a heavier bullet of the same caliber usually drops less at long range because it has a higher ballistic coefficient. In practice heavier bullets are loaded slower, which offsets some of that." },
    { q: "Why are my real drops different from the chart?", a: "Your muzzle velocity, altitude, temperature and zero are different. Enter your own values in the calculator and true it at a known distance." },
  ],
  related: ["308-ballistics-chart", "6-5-creedmoor-ballistics-chart", "22lr-bullet-drop", "zero-distance", "wind-drift"],
  cta: "Make a drop chart for your own load",
},
{
  slug: "308-ballistics-chart", cat: "Ballistic charts", term: ".308 trajectory",
  h1: ".308 trajectory explained: drop, wind and the transonic limit",
  title: ".308 Trajectory Explained: Drop, Wind and Effective Range",
  description: "How a .308 Winchester bullet flies to 1000 yards: drop and come-ups, wind drift, when it goes transonic, and what that means for effective range.",
  short: "how a .308 bullet drops, drifts and slows out to 1000 yards.",
  answer: "A .308 Winchester 175 gr Sierra MatchKing at 2600 fps with a 100-yard zero needs about <b>" + n(-a5.mil) + " MIL (" + n(-a5.moa) + " MOA) at 500 yards</b> and <b>" + n(-a10.mil) + " MIL (" + n(-a10.moa) + " MOA) at 1000 yards</b> at sea level. A 10 mph crosswind moves it about " + n(a5.windIn, 0) + " inches at 500 and " + n(a10.windIn, 0) + " inches at 1000 yards.",
  sections: [
    { h: "Worked example: 175 gr SMK to 1000 yards", html: dropTable("308") + `<p>Drop and wind tables for every other .308 load in our library are on the <a href="/ballistics/308-win/">.308 Win ballistics charts</a> page.</p>` },
    { h: "What the numbers tell you", html: `<ul><li><b>Out to 300 yards</b> the .308 is easy: ${n(-a3.mil)} MIL up and under 7 inches of drift in a 10 mph wind.</li>
<li><b>500–700 yards</b> is where wind calls start to dominate. An error of 3 mph in your wind estimate at 700 yards is about ${n(at("308", 700).windIn * 0.3, 0)} inches.</li>
<li><b>Past 800 yards</b> the 175 gr bullet approaches the speed of sound (Mach 1.2 at about ${Math.round(F.trans["308"].m12)} yards, Mach 1.0 at ${Math.round(F.trans["308"].m10)} yards at sea level). Accuracy and prediction quality drop. See <a href="/glossary/transonic/">transonic</a>.</li>
<li><b>At altitude</b> things improve. At 5000 ft and 90 °F the 1000-yard come-up drops from ${n(-F.da.sea.mil)} to ${n(-F.da.high.mil)} MIL and the bullet stays supersonic. See <a href="/glossary/density-altitude/">density altitude</a>.</li></ul>` },
    { h: "Other popular .308 loads", html: `<p>168 gr match loads (G7 BC about 0.218) start around 2650–2700 fps but go transonic sooner than the 175 gr. Heavy, high-BC bullets like 185–200 gr hybrids retain energy best but need a 1:10 or faster <a href="/glossary/twist-rate/">twist</a>. 147–150 gr FMJ military ball is flat to 400 yards but drifts much more in wind. Our bullet library includes the common factory loads, including those sold in Georgia. See the charts for <a href="/ballistics/308-win/">every .308 Win load in the library</a>, or generate one for exactly what you shoot.</p>` },
  ],
  faq: [
    { q: "What is the effective range of a .308?", a: "For target shooting, about 800–1000 yards with good match ammunition, limited by the bullet going transonic. For ethical hunting, most shooters limit themselves to much shorter distances where they can guarantee a precise hit and adequate energy." },
    { q: "How many MOA for .308 at 1000 yards?", a: `About ${n(-a10.moa)} MOA (${n(-a10.mil)} MIL) for a 175 gr bullet at 2600 fps with a 100-yard zero at sea level. Your number depends on your velocity and altitude.` },
    { q: "Is 168 gr or 175 gr better for long range?", a: "175 gr, for most .308 rifles. It has a higher BC and stays supersonic longer, which is why it became the standard military and match long-range load." },
    { q: "How much energy does a .308 have at 500 yards?", a: `About ${Math.round(a5.ftlb)} ft·lb for a 175 gr bullet starting at 2600 fps.` },
  ],
  related: ["6-5-creedmoor-ballistics-chart", "bullet-drop-chart", "wind-drift", "transonic", "zero-distance"],
  cta: "Calculate your own .308 trajectory",
},
{
  slug: "6-5-creedmoor-ballistics-chart", cat: "Ballistic charts", term: "6.5 Creedmoor vs .308",
  h1: "6.5 Creedmoor vs .308: trajectory and wind compared",
  title: "6.5 Creedmoor vs .308: Drop and Wind Compared to 1000 Yards",
  description: "6.5 Creedmoor vs .308 Winchester with real numbers: drop, wind drift, velocity and energy to 1000 yards, transonic range, recoil and barrel life.",
  short: "the two most popular long-range cartridges compared, with real numbers.",
  answer: "A 6.5 Creedmoor 140 gr ELD Match at 2710 fps with a 100-yard zero needs about <b>" + n(-c5.mil) + " MIL (" + n(-c5.moa) + " MOA) at 500 yards</b> and <b>" + n(-c10.mil) + " MIL (" + n(-c10.moa) + " MOA) at 1000 yards</b> at sea level. A 10 mph crosswind moves it about " + n(c10.windIn, 0) + " inches at 1000 yards, against " + n(a10.windIn, 0) + " inches for a .308 175 gr.",
  sections: [
    { h: "6.5 Creedmoor 140 gr ELD Match to 1000 yards", html: dropTable("65cm") + `<p>Tables for every 6.5 Creedmoor load in our library: <a href="/ballistics/6-5-creedmoor/">6.5 Creedmoor ballistics charts</a>.</p>` },
    { h: "6.5 Creedmoor vs .308", html: `${table(["At 1000 yd", "6.5 CM 140 gr", ".308 175 gr"], [["Come-up", `${n(-c10.mil)} MIL`, `${n(-a10.mil)} MIL`], ["Wind drift, 10 mph", `${n(c10.windIn, 0)} in`, `${n(a10.windIn, 0)} in`], ["Velocity", `${Math.round(c10.fps)} fps`, `${Math.round(a10.fps)} fps`], ["Energy", `${Math.round(c10.ftlb)} ft·lb`, `${Math.round(a10.ftlb)} ft·lb`]], "Sea level, standard atmosphere. Calculated with the ballistics.ge solver.")}
<p>The 6.5 mm bullet's higher <a href="/glossary/ballistic-coefficient/">ballistic coefficient</a> (G7 0.326 vs 0.243) means it drifts about ${Math.round((1 - c10.windIn / a10.windIn) * 100)}% less at 1000 yards, stays supersonic past ${Math.round(F.trans["65cm"].m12 / 100) * 100} yards, and recoils less. The .308 has more barrel life and a wider range of cheap ammunition.</p>` },
    { h: "Barrel and twist", html: `<p>Factory 6.5 Creedmoor rifles use a 1:8 twist (sometimes 1:7.5), needed for long 140–147 gr bullets. Our solver gives a Miller <a href="/glossary/twist-rate/">stability factor</a> of ${n(F.sg65, 2)} for the 140 gr ELD Match in 1:8 at sea level. Box velocities come from 24-inch test barrels; from a 20–22 inch barrel expect 2600–2700 fps, and <a href="/glossary/muzzle-velocity/">measure it</a>.</p>` },
    { h: "Popular 6.5 Creedmoor bullets", html: `${table(["Bullet", "G7 BC", "Notes"], [["Hornady 140 gr ELD Match", "0.315–0.326", "the load used in this chart; factory Hornady Match"], ["Hornady 147 gr ELD Match", "0.351", "highest BC of the factory loads; slightly slower"], ["Sierra 142 gr MatchKing", "0.302", "common in handloads and Federal Gold Medal"], ["Berger 130 gr Hybrid OTM Tactical", "0.287", "faster start, less recoil"]], "Published BCs. All are in the ballistics.ge bullet library.")}<p>Charts for each of them: <a href="/ballistics/6-5-creedmoor/">all 6.5 Creedmoor loads</a>. For hunting, bullets like the Hornady 143 gr ELD-X or Nosler 140 gr AccuBond are designed to expand at 6.5 Creedmoor velocities; match bullets are not always designed for reliable expansion on game.</p>` },
  ],
  faq: [
    { q: "How far can a 6.5 Creedmoor shoot accurately?", a: "Good match loads stay supersonic to roughly 1200–1400 yards at sea level, and competitors regularly hit targets at 1000 yards and beyond." },
    { q: "How much does a 6.5 Creedmoor drop at 500 yards?", a: `About ${n(-c5.dropIn, 0)} inches with a 140 gr bullet at 2710 fps and a 100-yard zero, or ${n(-c5.mil)} MIL / ${n(-c5.moa)} MOA.` },
    { q: "Is 6.5 Creedmoor better than .308 for long range?", a: "For target shooting past 600 yards, yes: less wind drift, less drop and less recoil. For hunting inside 400 yards the practical difference is small." },
    { q: "What is the best zero for 6.5 Creedmoor?", a: "A 100-yard zero is standard for long-range shooting because it is easy to confirm and every calculator and DOPE card assumes it. Hunters sometimes prefer a 200-yard zero." },
    { q: "What twist rate does 6.5 Creedmoor need?", a: "A 1:8 twist stabilizes the popular 140–147 gr bullets. Very long bullets such as the 156 gr Berger EOL prefer 1:7.5 or 1:7." },
  ],
  related: ["308-ballistics-chart", "ballistic-coefficient", "transonic", "bullet-drop-chart"],
  cta: "Compare your own loads in the calculator",
},
{
  slug: "22lr-bullet-drop", cat: "Ballistic charts", term: ".22 LR bullet drop",
  h1: ".22 LR bullet drop and the best zero distance",
  title: ".22 LR Bullet Drop and Best Zero: 50 vs 100 Yards",
  description: ".22 LR bullet drop chart from 25 to 300 yards in inches, MOA and MIL, wind drift, and the best zero distance for plinking, hunting and rimfire precision.",
  short: "rimfire drop and wind from 25 to 300 yards, and which zero to choose.",
  answer: "A standard-velocity .22 LR (40 gr at 1070 fps) zeroed at 50 yards drops about <b>" + n(-r1.dropIn, 0) + " inches at 100 yards</b> (" + n(-r1.mil) + " MIL) and <b>" + n(-r2.dropIn, 0) + " inches at 200 yards</b> (" + n(-r2.mil) + " MIL). A 10 mph crosswind moves it about " + n(r1.windIn, 1) + " inches at 100 yards. A 50-yard zero is the most common choice.",
  sections: [
    { h: "Drop with a 50-yard zero", html: dropTable("22lr") + `<p>Drop tables for each .22 LR brand in our library: <a href="/ballistics/22-lr/">.22 LR ballistics charts</a>.</p>` },
    { h: "Why .22 LR drops so fast", html: `<p>The .22 LR bullet is light, short and blunt, with a G1 <a href="/glossary/ballistic-coefficient/">BC</a> around 0.13–0.14, and it starts slow. It spends about ${n(r1.tof, 2)} seconds reaching 100 yards, more than twice as long as a .308, so gravity and wind have more time to act. That makes rimfire an excellent, cheap way to learn wind reading: the drift you see at 100 yards with a .22 is similar to what a .308 shows at around 300–400 yards.</p>` },
    { h: "Which zero to choose", html: `<ul><li><b>50 yards</b>: the most common choice. The bullet stays within about ½ inch of the aim point from 25 to about 60 yards, ideal for plinking and small game.</li>
<li><b>25 yards</b>: for indoor ranges and airgun-like distances; the bullet is then high at 50–75 yards.</li>
<li><b>100 yards</b>: for rimfire precision matches (NRL22, PRS rimfire) where you dial every distance anyway.</li></ul>
<p>Subsonic and standard-velocity ammunition is usually more accurate than high-velocity, because high-velocity .22 LR at about 1250 fps crosses the speed of sound within the first 100 yards. See <a href="/glossary/transonic/">transonic</a>.</p>` },
    { h: "Choosing .22 LR ammunition", html: `<ul><li><b>Standard velocity match ammunition</b> (SK, Lapua Center-X and Midas+, Eley Club and Tenex, RWS R50, CCI Standard Velocity) leaves the barrel at about 1050–1085 fps and gives the best accuracy.</li><li><b>High velocity</b> (CCI Mini-Mag, Fiocchi Performance HV, SK High Velocity) is around 1235–1260 fps, flatter to 75 yards but it passes the speed of sound.</li><li><b>Subsonic</b> (Fiocchi F320, CCI Subsonic, Eley Subsonic HP) runs about 1030–1050 fps and is quietest with a suppressor.</li><li><b>Hyper velocity</b> (CCI Stinger, Velocitor) is for pests at short range, not for accuracy.</li></ul><p>Every rimfire barrel has favorite ammunition. Test several brands at 50 yards before buying a case, and remember that the BC of .22 LR varies more between brands (0.12–0.17) than for centerfire bullets. Drop tables for each brand: <a href="/ballistics/22-lr/">all .22 LR loads</a>.</p>` },
  ],
  faq: [
    { q: "How far will a .22 LR shoot accurately?", a: "Most shooters find 100 yards easy and 200 yards challenging. Rimfire matches go to 300 yards or more with good rifles, careful wind reading and match ammunition." },
    { q: "How much does a .22 drop at 100 yards?", a: `With a 50-yard zero, about ${n(-r1.dropIn, 0)} inches (${n(-r1.mil)} MIL / ${n(-r1.moa)} MOA) for standard velocity. High-velocity ammunition drops a little less, around 4–5 inches.` },
    { q: "What is the best zero for a .22 LR rifle?", a: "50 yards for general use and small game. 100 yards if you shoot rimfire precision and dial for every distance." },
    { q: "Does a .22 LR need a special scope?", a: "No, but a scope with parallax adjustment down to 25–50 yards helps, because many centerfire scopes are parallax-free only at 100 yards." },
    { q: "Is subsonic or high velocity .22 LR better?", a: "For accuracy, subsonic and standard velocity. High velocity gives a flatter trajectory to 75 yards and more energy for small game." },
  ],
  related: ["zero-distance", "transonic", "wind-drift", "bullet-drop-chart"],
  cta: "Make a drop chart for your own .22 LR",
},
{
  slug: "zero-distance", cat: "Trajectory and zeroing", term: "Zero distance",
  h1: "Best zero distance: 100 vs 200 yard zero",
  title: "Best Zero Distance: 100 vs 200 Yard Zero Compared",
  description: "What zero distance means, 100 vs 200 yard zero compared with real .308 numbers, the 50/200 and 36-yard AR-15 zeros, and which zero suits hunting or long range.",
  short: "what zeroing means and how 100 and 200 yard zeros compare.",
  answer: "Your <b>zero distance</b> is the range where the bullet hits exactly at your aim point. For long range, a <b>100-yard (or 100 m) zero</b> is standard because it is easy to confirm and every calculator assumes it. For hunting, a <b>200-yard zero</b> keeps the bullet within a few inches of aim out to about 250 yards.",
  sections: [
    { h: "Why the bullet crosses the line of sight twice", html: `<p>The scope sits above the bore, so the barrel is tilted slightly up to make the bullet meet the line of sight at the zero distance. The bullet crosses the line of sight going up close to the muzzle, rises above it, then falls back through it at the zero distance. With a 200-yard zero the "near zero" for a .308 is around 40–50 yards. <a href="/glossary/sight-height/">Sight height</a> changes these numbers.</p>` },
    { h: "100 vs 200 yard zero for .308", html: `${table(["Yards", "100 yd zero", "200 yd zero"], [100, 200, 300, 400, 500].map((y, i) => [y, `${n(z100[i].dropIn)} in`, `${n(z200[i].dropIn)} in`]), ".308 175 gr at 2600 fps, 1.5\" sight height, sea level. Positive is above the aim point.")}
<p>With a 200-yard zero you can hold dead on for anything from 0 to about 250 yards on a deer-sized target, but you are ${n(z200[0].dropIn)} inches high at 100 yards. With a 100-yard zero every distance past 150 yards needs a correction, but those corrections are easy to calculate and dial, and confirming the zero is quick.</p>` },
    { h: "Popular zeros", html: `<ul><li><b>100 yards / 100 m</b>: precision rifles, dialing, and European hunting. Standard for calculators and DOPE cards.</li>
<li><b>200 yards</b>: hunting rifles used without dialing.</li>
<li><b>50/200 for AR-15</b>: with 55 gr ammunition and a 2.6" sight height the bullet crosses the line of sight near 50 and 200 yards, so you can zero at a short range and still be close at 200.</li>
<li><b>36 yards</b>: an AR-15 zero whose far crossing is around 300 yards; favored for simple military-style holds.</li>
<li><b>50 yards</b> for .22 LR. See <a href="/glossary/22lr-bullet-drop/">.22 LR bullet drop</a>.</li></ul>` },
  ],
  faq: [
    { q: "Is a 100 or 200 yard zero better?", a: "100 yards if you dial for distance or shoot long range; 200 yards if you hunt without dialing and want to hold on the vital zone out to about 250 yards." },
    { q: "Can I zero at 25 yards for 100?", a: "Only approximately, because the relationship depends on your sight height and velocity. It is good for getting on paper, but confirm the zero at the real distance." },
    { q: "What does 'zeroed in different conditions' mean in the calculator?", a: "If you zeroed in very different temperature or pressure, the zero angle itself changes slightly. Enter the zero conditions in the Advanced zero section so the calculator can correct for it." },
  ],
  related: ["sight-height", "bullet-drop-chart", "22lr-bullet-drop", "scope-click-value"],
  cta: "See your trajectory for any zero",
},
{
  slug: "sight-height", cat: "Trajectory and zeroing", term: "Sight height",
  h1: "Sight height: how to measure it and why it matters",
  title: "Sight Height: How to Measure Scope Height Over Bore",
  description: "What sight height (scope height over bore) is, how to measure it with calipers, typical values for bolt rifles and AR-15s, and how much it changes your drop.",
  short: "how high the scope sits over the bore, how to measure it, and its effect.",
  answer: "<b>Sight height</b> is the distance from the center of the bore to the center of the scope. Typical values are about <b>1.5–2.0 inches</b> (38–50 mm) on bolt rifles and <b>2.6 inches</b> (66 mm) on AR-15s. It mostly matters at short range; at long range it changes come-ups only slightly.",
  sections: [
    { h: "How to measure it", html: `<ol><li>Measure the scope's main tube diameter (usually 30 mm, 34 mm or 1 inch) and halve it.</li>
<li>Measure the barrel's outside diameter directly under the scope and halve it.</li>
<li>Measure the gap between the bottom of the scope tube and the top of the barrel.</li>
<li>Sight height = half the tube + the gap + half the barrel.</li></ol>
<p>Calipers give an answer within a millimeter, which is plenty.</p>` },
    { h: "How much it changes the trajectory", html: `${table(["Sight height", "at 50 yd", "at 300 yd", "at 600 yd"], F.sight.map((s) => [`${(s.h / 25.4).toFixed(1)} in (${s.h} mm)`, `${n(s.r[0].dropIn)} in`, `${n(s.r[1].dropIn)} in · ${n(-s.r[1].mil, 2)} MIL`, `${n(s.r[2].dropIn)} in · ${n(-s.r[2].mil, 2)} MIL`]), ".308 175 gr at 2600 fps, 100-yard zero. Negative is below the aim point.")}
<p>With a tall AR-style mount the bullet is lower at short range, which matters for close shots, and needs slightly less come-up at long range. An error of a quarter inch in the input changes the 600-yard come-up by only a few hundredths of a MIL.</p>` },
    { h: "Why an accurate sight height helps at close range", html: `<p>The bigger effect of sight height is inside 50 yards, where the bullet is still climbing toward the line of sight. On an AR-15 with 2.6 inches of sight height, the bullet hits about 2.5 inches below the aim point at 5–7 yards. That matters for pest control, precision shots at small targets, and shooting over obstacles: the scope can see over a branch or a barricade edge that the barrel will hit.</p><p>Offset mounts and cantilever rings add height. If you move the scope to a different mount, re-measure and re-zero.</p>` },
  ],
  faq: [
    { q: "What is a normal sight height?", a: "About 1.5 inches (38 mm) for a bolt rifle with low rings, up to 2 inches with high rings or a large objective. AR-15s with flat-top mounts are usually around 2.6 inches." },
    { q: "Why do I hit low at very close range?", a: "Because the scope is above the bore. At 5–10 yards the bullet is still below the line of sight by nearly the full sight height. Hold high by that amount for very close shots." },
    { q: "Does sight height affect long range?", a: "Only a little. It changes the zero angle slightly, so long-range come-ups shift by a few hundredths of a MIL. Measure it once and leave it." },
    { q: "Is sight height measured to the top or center of the scope?", a: "To the center of the scope tube, where the line of sight runs, and from the center of the bore." },
  ],
  related: ["zero-distance", "bullet-drop-chart", "scope-cant", "ballistic-calculator"],
},
{
  slug: "angle-shooting", cat: "Trajectory and zeroing", term: "Uphill and downhill shooting",
  h1: "Uphill and downhill shooting: the rifleman's rule",
  title: "Shooting Uphill or Downhill: Why You Hit High",
  description: "Why you hit high shooting uphill or downhill, the rifleman's rule and cosine method, and worked .308 numbers for a 30° shot at 600 yards.",
  short: "why steep shots hit high, and how the cosine rule corrects it.",
  answer: "When you shoot <b>uphill or downhill</b>, gravity acts only on the horizontal part of the distance, so the bullet drops less than on flat ground and you hit <b>high</b> in both directions. The rifleman's rule: use the come-up for the horizontal distance, which is the line-of-sight range × cos(angle).",
  sections: [
    { h: "The rifleman's rule", html: `<p class="formula">horizontal distance = line-of-sight range × cos(angle)</p>
<p>At 30°, cos is 0.87, so a 600-yard target up a slope needs about the come-up for 520 yards. At 10° the cosine is 0.98 and the effect is small. Many laser rangefinders give you this "angle-compensated range" directly.</p>` },
    { h: "Worked example: 30° uphill at 600 yards", html: `${table(["", "Come-up", "Drop"], [["Flat, 600 yd", `${n(-F.incline.flat.mil, 2)} MIL`, `${n(-F.incline.flat.dropIn, 0)} in`], ["30° uphill, 600 yd", `${n(-F.incline.up30.mil, 2)} MIL`, `${n(-F.incline.up30.dropIn, 0)} in`]], ".308 175 gr at 2600 fps, 100-yard zero. Calculated with a full angle solution, not the cosine shortcut.")}
<p>Dialing the flat-ground come-up here would put the shot about ${n(F.incline.up30.dropIn - F.incline.flat.dropIn, 0)} inches high, a miss on most targets. The cosine rule is a good approximation up to moderate angles and ranges; a calculator that solves the angled trajectory is more exact at long range and steep angles.</p>` },
    { h: "Measuring the angle", html: `<p>Use a rangefinder with an inclinometer, an angle cosine indicator on the scope, or your phone. Our calculator can read the shot angle from the phone's sensors: lay the phone along the rifle and tap to capture. Uphill and downhill angles give nearly the same correction; downhill is not "the opposite" of uphill.</p>` },
    { h: "Common mistakes", html: `<ul><li><b>Using the angle-compensated range for wind.</b> Wind drift depends on time of flight, which follows the line-of-sight range. Use the real range for wind and the horizontal range only for elevation, or let the calculator do both.</li><li><b>Thinking downhill needs more come-up.</b> Both directions hit high with flat-ground dope.</li><li><b>Ignoring small angles at long range.</b> At 1000 yards even 10° changes the come-up by a noticeable fraction of a MIL.</li><li><b>Guessing the angle.</b> Slopes look steeper than they are. Measure the angle.</li></ul>` },
  ],
  faq: [
    { q: "Do you aim high or low when shooting downhill?", a: "Low, or dial less come-up. Both uphill and downhill shots hit high if you use the flat-ground come-up." },
    { q: "At what angle does it start to matter?", a: "Past about 10–15° at medium range. At 300 yards and 10°, the difference is usually less than an inch; at 600 yards and 30° it is more than a foot." },
    { q: "Does angle change wind drift?", a: "Very slightly, because the time of flight is almost the same. Use your normal wind hold for the line-of-sight range." },
    { q: "What is the improved rifleman\u2019s rule?", a: "It applies the cosine to the drop rather than the range. It is slightly more accurate at long distances, but a calculator that solves the angled trajectory directly is the most accurate option." },
  ],
  related: ["scope-cant", "bullet-drop-chart", "mil-dot-range-estimation", "ballistic-calculator"],
  cta: "Solve an angled shot",
},
  ];
};

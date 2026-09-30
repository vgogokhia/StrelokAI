export default ({ F, n, table }) => {
  const at = (k, yd) => F.tables[k].find((r) => r.yd === yd);
  const a8 = at("308", 800), b8 = at("65cm", 800), a10 = at("308", 1000), b10 = at("65cm", 1000);
  return [
{
  slug: "ballistic-coefficient", cat: "Bullets and drag", term: "Ballistic coefficient (BC)",
  h1: "Ballistic coefficient: what BC means and why it matters",
  title: "Ballistic Coefficient (BC) Explained: What Is a Good BC?",
  description: "What ballistic coefficient means, how BC changes drop and wind drift, what counts as a good G1 or G7 BC, and why the box value is not always what you get.",
  short: "how well a bullet resists air drag, and what a good number looks like.",
  answer: "<b>Ballistic coefficient (BC)</b> is a number describing how well a bullet overcomes air resistance compared to a standard reference bullet. Higher BC means the bullet keeps its speed longer, so it drops less and drifts less in the wind. BC is always tied to a drag model, usually G1 or G7.",
  sections: [
    { h: "What the number means", html: `<p>BC is the bullet's sectional density divided by a form factor: it combines how heavy the bullet is for its diameter with how streamlined its shape is compared to a reference projectile. In US units it is expressed in lb/in², and usually written without units: "G7 BC 0.243".</p>
<p>A bullet with twice the BC of another, on the same drag model, loses speed about half as fast. That translates directly into less drop, less wind drift and more retained energy downrange.</p>` },
    { h: "BC in practice: .308 175 gr vs 6.5 Creedmoor 140 gr", html: `<p>The 175 gr .308 SMK has a G7 BC of 0.243. The 140 gr 6.5 mm ELD Match has 0.326. The 6.5 starts only 110 fps faster, but its higher BC widens the gap with distance:</p>
${table(["", ".308 175 gr (G7 0.243)", "6.5 CM 140 gr (G7 0.326)"], [["Velocity at 800 yd", `${Math.round(a8.fps)} fps`, `${Math.round(b8.fps)} fps`], ["Come-up at 800 yd", `${n(-a8.mil)} MIL`, `${n(-b8.mil)} MIL`], ["10 mph wind at 800 yd", `${n(a8.windIn, 0)} in`, `${n(b8.windIn, 0)} in`], ["Velocity at 1000 yd", `${Math.round(a10.fps)} fps`, `${Math.round(b10.fps)} fps`], ["10 mph wind at 1000 yd", `${n(a10.windIn, 0)} in`, `${n(b10.windIn, 0)} in`]], "Sea-level standard atmosphere, 100-yard zero. Calculated with the ballistics.ge solver.")}
<p>That wind difference is the main reason 6.5 mm cartridges took over precision rifle competition: wind calls are the hardest part of long-range shooting, and a high BC forgives errors.</p>` },
    { h: "What is a good BC?", html: `<ul><li><b>G7 above 0.30</b> is very good for long-range match and hunting bullets (6.5 mm 140–147 gr, .30 cal 200+ gr).</li>
<li><b>G7 0.22–0.30</b> is typical for .308 match bullets (0.243 for the 175 SMK, around 0.26–0.28 for 178–185 gr high-BC designs).</li>
<li><b>G1 0.10–0.15</b> is normal for .22 LR; it is why rimfire drops so fast past 100 yards.</li></ul>
<p>Never compare a G1 number with a G7 number: a G1 BC is roughly twice the G7 value for the same boat-tail bullet. See <a href="/glossary/g1-vs-g7/">G1 vs G7</a>.</p>` },
    { h: "Why published BC is not always what you get", html: `<p>BC changes with velocity, because the drag curve of a real bullet never matches the reference exactly. Manufacturers may publish an average, a high-velocity value, or several velocity bands (Sierra does this for G1). Our calculator accepts velocity-banded BCs. Barrel condition, bullet lot and your own atmosphere also play a part. If long-range impacts do not match predictions after you have verified velocity, <a href="/glossary/truing/">true the BC</a> with real impacts.</p>` },
  ],
  faq: [
    { q: "Is a higher ballistic coefficient always better?", a: "For long range, yes: less drop and wind drift. But BC is only one part: velocity, accuracy, the bullet's terminal performance for hunting, and what your barrel twist can stabilize matter too." },
    { q: "Does BC depend on velocity?", a: "Yes. The drag of a real bullet does not follow the reference curve exactly, so the effective BC changes with speed, especially near the speed of sound. G7 BCs stay more constant for long boat-tail bullets than G1 BCs." },
    { q: "Where do I find my bullet's BC?", a: "On the bullet manufacturer's website or box. Our calculator's bullet library includes published G1 and G7 values for common .22 LR, .223, .308 and 6.5 mm loads." },
    { q: "What does BC stand for?", a: "Ballistic coefficient. It is a measure of how efficiently a projectile moves through air relative to a standard reference projectile." },
  ],
  related: ["g1-vs-g7", "truing", "transonic", "wind-drift", "bullet-drop-chart"],
},
{
  slug: "g1-vs-g7", cat: "Bullets and drag", term: "G1 vs G7 drag model",
  h1: "G1 vs G7 ballistic coefficient: which should you use?",
  title: "G1 vs G7 Ballistic Coefficient: Which Should You Use?",
  description: "The difference between G1 and G7 drag models, why a G7 BC is about half the G1 number, and which one to enter in a ballistic calculator for your bullet.",
  short: "the two reference drag curves, and which one fits your bullet.",
  answer: "G1 and G7 are two reference drag curves. <b>G1</b> is modeled on a flat-based, short-nosed bullet; <b>G7</b> on a long, sleek boat-tail bullet. Use <b>G7</b> for modern long-range boat-tail bullets because its BC stays nearly constant with speed; use G1 for flat-base, round-nose and most rimfire bullets.",
  sections: [
    { h: "Where the models come from", html: `<p>Early ballisticians could not measure the drag of every bullet, so they measured a few "standard projectiles" and described every other bullet relative to them. The G1 standard was a flat-based bullet with a blunt nose, typical of 19th-century projectiles. The G7 standard is a long, pointed boat-tail shape very similar to modern match and VLD bullets.</p>
<p>A BC tells the calculator: "this bullet has the same drag curve as the reference, scaled by this number". The closer the real bullet's shape is to the reference, the more constant that scale factor stays across speeds, and the more accurate the prediction.</p>` },
    { h: "Why the G7 number is smaller", html: `<p>The G7 reference projectile is already streamlined, so a modern bullet is only "slightly better" than it, giving a smaller number. For the 175 gr Sierra MatchKing, Sierra publishes about <b>0.505 G1</b> (at typical speeds) and Bryan Litz measured <b>0.243 G7</b>. Both describe the same bullet. As a rough rule, a G1 BC is 1.9–2.1 times the G7 value for boat-tail rifle bullets. That ratio is only a rough guide, so do not convert with it; use the manufacturer's G7 figure when available.</p>` },
    { h: "Which one to use", html: `${table(["Bullet type", "Best model"], [["Long boat-tail match / VLD / ELD / Berger", "G7"], ["Hunting boat-tails (SST, AccuBond, ELD-X)", "G7 if published, else G1"], ["Flat-base spitzer, round nose, FMJ military", "G1"], [".22 LR and most rimfire", "G1"], ["Pistol bullets and slugs", "G1"]])}
<p>If the manufacturer publishes only a G1 BC, many list it in velocity bands. Enter those bands; they fix most of the G1 model's weakness at long range. In our calculator, switch the drag model on the Ammo tab and optionally add velocity-banded BCs.</p>` },
  ],
  faq: [
    { q: "Can I convert G1 BC to G7?", a: "Only roughly. The ratio between the two changes with velocity and bullet shape. Use the published G7 value if one exists, or true the BC with real long-range impacts." },
    { q: "Why does my G1 prediction miss at long range?", a: "A single G1 BC is usually fitted at high velocity. As the bullet slows, the real drag curve departs from the G1 shape, and predictions typically come out too optimistic past 600–800 yards. G7 or velocity-banded G1 BCs fix this." },
    { q: "Is G7 better for .22 LR?", a: "No. .22 LR bullets are short, round-nosed and flat-based, much closer to the G1 shape. Use G1 for rimfire." },
  ],
  related: ["ballistic-coefficient", "truing", "transonic", "308-ballistics-chart"],
},
{
  slug: "muzzle-velocity", cat: "Bullets and drag", term: "Muzzle velocity",
  h1: "Muzzle velocity: why it's the most important calculator input",
  title: "Muzzle Velocity: Chronograph, Temperature and Accuracy",
  description: "Why muzzle velocity matters more than any other ballistic input, how temperature and barrel length change it, and what 60 fps costs at 1000 yards.",
  short: "the input that moves your long-range come-ups the most, and how temperature changes it.",
  answer: "<b>Muzzle velocity</b> (MV) is the bullet's speed as it leaves the barrel, in feet or meters per second. It is the most important ballistic input: an error of 50–60 fps changes a .308's 1000-yard come-up by more than half a MIL. Measure it with a chronograph from your own rifle, at the temperature you shoot in.",
  sections: [
    { h: "How much does velocity error cost?", html: `<p>A .308 175 gr load at 2600 fps versus the same load 60 fps slower (2540 fps), at 1000 yards:</p>
${table(["MV", "Come-up at 1000 yd", "Drop"], [["2600 fps", `${n(-F.mvTemp.base.mil, 2)} MIL`, `${n(-F.mvTemp.base.dropIn, 0)} in`], ["2540 fps", `${n(-F.mvTemp.slow.mil, 2)} MIL`, `${n(-F.mvTemp.slow.dropIn, 0)} in`]])}
<p>That is <b>${n(F.mvTemp.base.dropIn - F.mvTemp.slow.dropIn, 0)} inches</b> of vertical difference, bigger than a full-size IPSC target. Box velocities are measured in test barrels that are often longer than yours; real MVs from 20–22 inch barrels are commonly 50–150 fps lower.</p>` },
    { h: "Temperature sensitivity", html: `<p>Powder burns faster when warm, so MV rises with ammunition temperature. Typical sensitivity is around 0.5–2 fps per °F depending on the powder; "temperature-stable" powders are at the low end. A 40 °F change at 1.5 fps/°F is exactly the 60 fps in the example above.</p>
<p>Our calculator lets you enter the temperature at which you measured MV and a sensitivity in % per °C, and it adjusts MV automatically from the current temperature. Keep ammunition out of direct sun at the range: a round lying in the sun can be far hotter than the air.</p>` },
    { h: "How to measure it properly", html: `<ul><li>Use a chronograph (a Doppler unit like LabRadar or Garmin Xero is easiest) and shoot at least 10 rounds; use the average.</li>
<li>Note the temperature of the ammunition, not just the air.</li>
<li>Re-check after barrel cleaning, a new powder lot or a few hundred rounds; velocity can drift as a barrel wears.</li>
<li>If you have no chronograph, start from the box value, then <a href="/glossary/truing/">true the velocity</a> from real impacts at 500–600 yards.</li></ul>` },
  ],
  faq: [
    { q: "How much velocity do you lose per inch of barrel?", a: "It varies by cartridge; for .308 Winchester a common figure is roughly 20–30 fps per inch between 16 and 26 inches, more for magnum cartridges and far less for .22 LR." },
    { q: "Is the velocity on the ammo box accurate?", a: "It is accurate for the manufacturer's test barrel, which is often 24 inches or longer. Your rifle will usually be slower. Always measure or true it." },
    { q: "What is standard deviation (SD) in velocity?", a: "The shot-to-shot variation around the average. A low SD (under about 10 fps) keeps vertical spread small at long range. The calculator uses the average." },
  ],
  related: ["truing", "density-altitude", "ballistic-calculator", "308-ballistics-chart"],
},
{
  slug: "twist-rate", cat: "Bullets and drag", term: "Twist rate",
  h1: "Barrel twist rate and bullet stability explained",
  title: "Barrel Twist Rate: What 1:10 Means and Which to Choose",
  description: "What barrel twist like 1:8 or 1:10 means, the Miller stability factor, and which twist suits .308, 6.5 Creedmoor, .223 and .22 LR bullets.",
  short: "what 1:8 or 1:10 means, and how twist keeps long bullets stable.",
  answer: "<b>Twist rate</b> is how far a bullet travels down the barrel to make one full turn: 1:10 means one turn in 10 inches. Faster twist (smaller number) spins the bullet faster, which is needed to stabilize long, heavy bullets. A stability factor (SG) of <b>1.5 or more</b> is the usual target.",
  sections: [
    { h: "Why bullets need spin", html: `<p>A pointed bullet is aerodynamically unstable: air pressure on its nose tries to flip it over. Spin makes it behave like a gyroscope and keeps it pointed forward. Longer bullets are harder to stabilize, so they need more spin. Bullet length matters more than weight, which is why modern long, high-BC bullets often need faster twists than older designs of the same weight.</p>` },
    { h: "The Miller stability factor", html: `<p>Don Miller's formula estimates gyroscopic stability (SG) from bullet weight, diameter, length, twist and velocity, with a correction for air density. Our calculator shows it for every load.</p>
${table(["SG", "Meaning"], [["below 1.0", "unstable: bullets tumble and keyhole"], ["1.0–1.4", "marginal: BC suffers, accuracy may suffer in cold, dense air"], ["1.5 and above", "fully stable: the usual target"]])}
<p>For the 175 gr SMK (1.24 in long) at 2600 fps our solver gives SG ${n(F.sg308_12, 2)} in a 1:12 barrel, ${n(F.sg308, 2)} in 1:11.25 and ${n(F.sg308_10, 2)} in 1:10. The 6.5 mm 140 gr ELD Match in 1:8 gives ${n(F.sg65, 2)}. Cold, dense air lowers SG; high altitude raises it.</p>` },
    { h: "Common twist rates", html: `${table(["Cartridge", "Common twist", "Notes"], [[".22 LR", "1:16", "standard for 40 gr bullets"], [".223 / 5.56", "1:7 to 1:9", "1:12 only for light 40–55 gr bullets; 1:7–1:8 for 69–77 gr"], [".308 Win", "1:10 to 1:12", "1:10 handles 200+ gr bullets"], ["6.5 Creedmoor", "1:8 (1:7.5)", "made for long 140–150 gr bullets"]])}
<p>Twist direction also sets which way the bullet drifts: a right-hand twist barrel produces right <a href="/glossary/spin-drift/">spin drift</a>.</p>` },
    { h: "How to find your barrel's twist", html: `<p>If the rifle or barrel maker does not list it, you can measure the twist in a few minutes:</p><ol><li>Make sure the rifle is unloaded and remove the bolt.</li><li>Push a cleaning rod with a snug patch or jag into the bore from the breech end.</li><li>Put a piece of tape on the rod as a flag and mark the rod's position at the receiver.</li><li>Push the rod slowly forward, letting it turn freely, until the flag has made one full turn.</li><li>Measure how far the rod moved. That distance in inches is your twist: 10 inches means 1:10.</li></ol><p>Enter it in the Rifle tab together with the bullet length from the manufacturer or measured with calipers. Bullet length is important: for the same weight, a longer bullet needs more twist.</p>` },
  ],
  faq: [
    { q: "What does 1:8 twist mean?", a: "The rifling makes one full turn every 8 inches of barrel. It is a faster twist than 1:10, which makes one turn every 10 inches." },
    { q: "Can a twist rate be too fast?", a: "Rarely for accuracy. Very fast twists can over-spin thin-jacketed varmint bullets at high velocity and cause them to come apart in flight, and they increase spin drift slightly." },
    { q: "Does twist rate affect accuracy?", a: "Only indirectly. A bullet that is not stable will be inaccurate; once SG is above about 1.5, extra spin does not improve accuracy." },
    { q: "Why does bullet length matter more than weight?", a: "Stability depends on how long the bullet is compared to its diameter. A long, sleek bullet has its center of pressure far ahead of its center of mass, which makes it harder to stabilize, even at the same weight as a shorter one." },
  ],
  related: ["spin-drift", "ballistic-coefficient", "density-altitude", "muzzle-velocity"],
  cta: "Check your bullet's stability factor",
},
{
  slug: "transonic", cat: "Bullets and drag", term: "Transonic range",
  h1: "Transonic range: what happens when a bullet goes subsonic",
  title: "Transonic Bullet: What Happens Near the Speed of Sound",
  description: "What the transonic zone is, where .308 and 6.5 Creedmoor bullets go subsonic, why accuracy and predictions suffer there, and how subsonic .22 LR avoids it.",
  short: "why bullets become less predictable as they slow through the speed of sound.",
  answer: "The <b>transonic zone</b> is the speed range from roughly Mach 1.2 down to Mach 0.8, around 1340 to 900 fps at sea level. There the airflow around the bullet is partly supersonic and partly subsonic, drag changes sharply, and some bullets wobble. Predictions become less reliable, so long-range loads are chosen to stay supersonic.",
  sections: [
    { h: "Where common loads go transonic", html: `<p>The speed of sound is about 1116 fps (340 m/s) at 59 °F and falls in colder air. Using the same loads as our charts, at sea level:</p>
${table(["Load", "Reaches Mach 1.2", "Reaches Mach 1.0"], [[".308 175 gr @ 2600 fps", `${Math.round(F.trans["308"].m12)} yd`, `${Math.round(F.trans["308"].m10)} yd`], ["6.5 CM 140 gr @ 2710 fps", `${Math.round(F.trans["65cm"].m12)} yd`, `${Math.round(F.trans["65cm"].m10)} yd`]], "Calculated with the ballistics.ge solver, standard atmosphere, sea level.")}
<p>That is why 1000 yards is a hard distance for a .308 at sea level and an easy one for a 6.5 Creedmoor. At altitude, where the air is thinner, both stay supersonic farther.</p>` },
    { h: "Why it matters", html: `<ul><li><b>Drag spikes.</b> Drag coefficient rises steeply as a bullet approaches Mach 1, so a small error in BC or velocity becomes a big error in drop.</li>
<li><b>Stability.</b> The shock wave moving along the bullet can upset marginally stable bullets and open groups. A good <a href="/glossary/twist-rate/">stability factor</a> helps.</li>
<li><b>Model limits.</b> BC values are least accurate here, which is why <a href="/glossary/truing/">truing</a> at long range matters.</li></ul>
<p>Our calculator warns when the bullet is transonic at the target, and skips the warning for loads that start subsonic.</p>` },
    { h: "Subsonic ammunition", html: `<p>Subsonic loads start below the speed of sound and never cross it. Standard-velocity and subsonic .22 LR, and .300 Blackout subsonic loads, are chosen for this reason: they are quieter, especially with a suppressor, and avoid the accuracy penalty of passing through Mach 1. High-velocity .22 LR at about 1250 fps goes transonic within the first 50–100 yards, which is one reason match shooters use standard velocity.</p>` },
  ],
  faq: [
    { q: "At what speed does a bullet go subsonic?", a: "Below the local speed of sound: about 1116 fps (340 m/s) at 59 °F, about 1090 fps at 32 °F, and about 1150 fps at 90 °F." },
    { q: "Is it bad if my bullet goes subsonic before the target?", a: "It is not automatically a miss, but accuracy and prediction quality often drop. For long-range work, pick a load that stays above about Mach 1.1–1.2 at your longest target." },
    { q: "Why do subsonic .22 LR rounds shoot more accurately?", a: "They never pass through the speed of sound, so they avoid the buffeting and drag changes of the transonic zone." },
    { q: "Can a calculator predict the transonic zone correctly?", a: "Roughly. The G7 drag model tracks long boat-tail bullets through Mach 1 better than G1, and truing the BC close to the transonic range improves predictions. Expect somewhat more vertical dispersion there than at supersonic speeds." },
  ],
  related: ["ballistic-coefficient", "22lr-bullet-drop", "truing", "6-5-creedmoor-ballistics-chart"],
},
{
  slug: "truing", cat: "Bullets and drag", term: "Truing a ballistic calculator",
  h1: "How to true a ballistic calculator (velocity and BC)",
  title: "How to True a Ballistic Calculator: Velocity and BC",
  description: "Step-by-step guide to truing a ballistic calculator: when to adjust muzzle velocity, when to adjust BC, which distances to use, and mistakes to avoid.",
  short: "matching the calculator to real impacts by adjusting velocity, then BC.",
  answer: "<b>Truing</b> means adjusting the calculator's inputs so its predictions match where your bullets actually hit. First true <b>muzzle velocity</b> at a mid distance where the bullet is still fast (about 500–600 yards for .308), then true the <b>ballistic coefficient</b> at long range, near where it slows toward Mach 1.2.",
  sections: [
    { h: "Why truing is needed", html: `<p>Even with a chronograph, small errors add up: the chronograph itself, a scope whose clicks are slightly off, sight height, bullet lot BC. Truing lets real impacts correct all of them at once. It is the step that turns "close" into first-round hits past 800 yards.</p>` },
    { h: "Step by step", html: `<ol><li><b>Verify your zero and click value first.</b> Confirm the zero at 100 yards, and do a <a href="/glossary/scope-click-value/">tall target test</a> if you have not. Truing cannot fix a bad zero.</li>
<li><b>Measure conditions.</b> Get station pressure, temperature and exact range (a laser rangefinder, not an estimate).</li>
<li><b>True velocity at mid range.</b> Shoot a 5-round group at 500–600 yards with the calculator's come-up. Measure how far the group center is above or below the aim point, convert to MIL or MOA, and enter the actual come-up that would have centered it. The calculator finds the velocity that matches. On ballistics.ge this is on the Calculator tab under Truing.</li>
<li><b>True BC at long range.</b> Repeat at the far end, typically where the bullet is around Mach 1.2–1.4. Now adjust the BC (or drag scale) rather than velocity.</li>
<li><b>Confirm at a third distance</b> in between. If it matches, you are done.</li></ol>` },
    { h: "Common mistakes", html: `<ul><li>Truing BC at short range, where drop hardly depends on BC. You end up with a nonsense BC that fails at long range.</li>
<li>Truing on a windy day and blaming vertical error on the calculator. Wind can move impacts up or down slightly through aerodynamic jump.</li>
<li>Truing with 1–2 shots. Use the center of at least 3–5.</li>
<li>Forgetting to switch back to real conditions after a truing session in unusual weather.</li></ul>` },
  ],
  faq: [
    { q: "Should I true velocity or BC first?", a: "Velocity first, at a mid distance where the bullet is still fast. Then BC at long range. Doing it the other way round mixes up the two errors." },
    { q: "What if my trued velocity is very different from my chronograph?", a: "More than 30–40 fps apart suggests something else is wrong: an incorrect click value, sight height, zero, or range. Check those before accepting the new number." },
    { q: "Do I have to re-true for every lot of ammunition?", a: "Re-check velocity for each new powder or ammunition lot. BC usually stays the same for the same bullet." },
  ],
  related: ["muzzle-velocity", "ballistic-coefficient", "transonic", "dope-card"],
  cta: "True your load in the calculator",
},
{
  slug: "dope-card", cat: "Getting started", term: "DOPE card",
  h1: "DOPE card: what it is and how to make one",
  title: "DOPE Card: What It Is and How to Make One for Your Rifle",
  description: "What a DOPE card is, what to put on it (range, come-ups in MOA or MIL, wind holds), how to make one from a ballistic calculator and how to keep it accurate.",
  short: "a printed table of your come-ups and wind holds, and how to make one.",
  answer: "A <b>DOPE card</b> is a small printed table of your rifle's elevation and wind corrections at different distances. DOPE is commonly expanded as \"Data On Previous Engagements\". It lets you dial or hold fast without a phone, and it is the backup every long-range shooter should carry.",
  sections: [
    { h: "What to put on it", html: `<ul><li><b>Distance</b>, in your rangefinder's units, every 50 yards or meters out to your maximum range.</li>
<li><b>Elevation come-up</b> in the same unit as your turret (MIL or MOA), plus clicks if you prefer.</li>
<li><b>Wind hold for a 10 mph (or 5 m/s) full-value wind.</b> Scale it for other speeds: half for 5 mph, and so on.</li>
<li><b>The conditions</b> it was made for: temperature, pressure or density altitude, load and velocity.</li></ul>
<p>Here is part of a card for a .308 175 gr load at 2600 fps:</p>
${table(["Yards", "Up (MIL)", "Wind 10 mph (MIL)"], [300, 400, 500, 600, 700, 800].map((y) => { const r = F.tables["308"].find((x) => x.yd === y); return [y, n(-r.mil), n(Math.abs(r.windMil))]; }))}` },
    { h: "How to make one", html: `<p>Set up the rifle and load in the calculator with the conditions you expect, then open the DOPE tab to generate the table. Save it as CSV and print it, or take a screenshot. Tape it to the stock, the scope cap, or keep it in a wrist coach. Make separate cards for summer and winter, or for high and low elevation, because <a href="/glossary/density-altitude/">density altitude</a> changes come-ups noticeably at long range.</p>
<p>Before trusting the card, confirm it at two or three distances and <a href="/glossary/truing/">true the calculator</a> if impacts are off. Then write down your actual confirmed dope in a data book: real-world data beats any prediction.</p>` },
    { h: "Using a DOPE card under time pressure", html: `<ul><li><b>Round the range</b> to the nearest line on your card and interpolate only if you have time. Between 500 and 600 yards, the come-up changes by about 1.3 MIL for a .308, so a 50-yard error is worth more than half a MIL.</li><li><b>Wind brackets.</b> Next to the 10 mph column, some shooters add columns for 5 and 15 mph. Others memorize a "wind constant": for a .308 175 gr load a 10 mph full-value wind is close to 0.2 MIL per 100 yards out to about 600 yards, a quick check for the card.</li><li><b>Mark confirmed lines.</b> Put a dot next to distances you have confirmed with real shots. Lines without a dot are predictions.</li><li><b>Keep units consistent.</b> If your rangefinder reads meters, build the card in meters.</li></ul>` },
  ],
  faq: [
    { q: "What does DOPE stand for?", a: "It is commonly expanded as \"Data On Previous Engagements\", although the word \"dope\" for shooting data is older than that phrase. Either way it means your rifle's recorded corrections." },
    { q: "Do I still need a DOPE card with a phone app?", a: "Yes. Phones die, get cold, and are slow to use in a hurry. A card is instant and never needs a battery." },
    { q: "How often should I update my DOPE card?", a: "When the season changes, when you change ammunition lot, or when you shoot at a very different altitude." },
    { q: "What should be on a hunting DOPE card?", a: "Keep it short: distances every 50 yards or meters within your ethical range, the come-up or holdover for each, and the wind hold for 10 mph. Hunting cards are often taped to the scope cap or the stock." },
  ],
  related: ["ballistic-calculator", "wind-drift", "scope-click-value", "truing"],
  cta: "Generate and print your DOPE card",
},
  ];
};

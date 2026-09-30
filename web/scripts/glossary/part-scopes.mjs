export default ({ F, n, table }) => {
  const at = (k, yd) => F.tables[k].find((r) => r.yd === yd);
  const r5 = at("308", 500), r10 = at("308", 1000);
  return [
{
  slug: "ballistic-calculator", cat: "Getting started", term: "Ballistic calculator",
  h1: "Ballistic calculator: what it does and how to use one",
  title: "Ballistic Calculator: What It Does and How to Use It",
  description: "What a ballistic calculator is, which inputs matter most, and how to get accurate elevation and wind holds in MOA or MIL for .308, 6.5 Creedmoor and .22 LR.",
  short: "what it computes, the inputs that matter, and how to get a firing solution you can trust.",
  answer: "A <b>ballistic calculator</b> predicts where a bullet will hit at a given distance and tells you how much to adjust your scope, in MOA or MIL, for elevation and wind. It solves the bullet's flight step by step from its muzzle velocity, ballistic coefficient, your zero and the current air conditions.",
  sections: [
    { h: "What a ballistic calculator actually computes", html: `<p>Once a bullet leaves the barrel, gravity pulls it down and air drag slows it. The slower it gets, the longer it spends in the air and the more it drops and drifts. A modern calculator integrates those forces in small time steps. Our calculator uses a fourth-order Runge–Kutta point-mass solver with the standard G1 and G7 drag tables, the same method used by Applied Ballistics, Hornady 4DOF-style tools and py_ballisticcalc.</p>
<p>The result is a <b>firing solution</b>: the elevation adjustment ("come-up"), the wind hold, the remaining velocity and energy, and the time of flight. Good calculators also add the small effects that matter past 600 yards: <a href="/glossary/spin-drift/">spin drift</a>, <a href="/glossary/coriolis-effect/">Coriolis</a>, aerodynamic jump, <a href="/glossary/scope-cant/">cant</a> and <a href="/glossary/angle-shooting/">shot angle</a>.</p>` },
    { h: "The inputs, ranked by how much they matter", html: `<ol>
<li><b>Muzzle velocity.</b> The single biggest source of error. Use a chronograph reading from your rifle, not the box value. See <a href="/glossary/muzzle-velocity/">muzzle velocity</a>.</li>
<li><b>Ballistic coefficient</b> and drag model. Use the manufacturer's G7 BC for long, boat-tail match bullets. See <a href="/glossary/ballistic-coefficient/">ballistic coefficient</a>.</li>
<li><b>Range to target.</b> An error of 25 yards at 800 yards is worth more than a foot of vertical.</li>
<li><b>Wind speed and direction.</b> The hardest input to know, and the biggest reason for misses.</li>
<li><b>Air density</b>: temperature, pressure (station pressure, not the TV weather "sea-level" value) and altitude. See <a href="/glossary/density-altitude/">density altitude</a>.</li>
<li><b>Zero distance and sight height.</b> Easy to measure once, then leave alone.</li>
<li><b>Twist rate and bullet length.</b> Used for stability and spin drift.</li>
</ol>` },
    { h: "Example: what a calculator gives you", html: `<p>For a .308 Winchester with 175 gr Sierra MatchKings at 2600 fps, zeroed at 100 yards, our solver gives these come-ups at sea level:</p>
${table(["Distance", "Drop", "Come-up", "10 mph wind"], [[ "500 yd", `${n(-r5.dropIn, 0)} in`, `${n(-r5.mil)} MIL / ${n(-r5.moa)} MOA`, `${n(r5.windMil)} MIL`], ["1000 yd", `${n(-r10.dropIn, 0)} in`, `${n(-r10.mil)} MIL / ${n(-r10.moa)} MOA`, `${n(Math.abs(r10.windMil))} MIL`]])}
<p>You dial the come-up on the elevation turret and either dial or hold the wind correction with your reticle. See the full <a href="/glossary/308-ballistics-chart/">.308 ballistics chart</a>.</p>` },
    { h: "How to get accurate results", html: `<p>Start with measured velocity and the published BC. Shoot at a known distance around 500–600 yards and compare the real impact with the prediction. If the calculator is consistently off, <a href="/glossary/truing/">true</a> the muzzle velocity. Then check again at long range, near where the bullet slows toward the <a href="/glossary/transonic/">transonic</a> zone. Once the numbers match, print a <a href="/glossary/dope-card/">DOPE card</a> as a backup for when the phone battery dies.</p>` },
  ],
  faq: [
    { q: "Are free ballistic calculators accurate?", a: "Yes, if the inputs are accurate. The physics in free solvers is the same point-mass model used by paid apps. Almost all real-world errors come from wrong muzzle velocity, wrong range or wrong wind, not from the software." },
    { q: "Does a ballistic calculator work without internet?", a: "ballistics.ge does. After the first visit it is stored on the phone and runs fully offline. Weather auto-fill needs a connection, but you can type the conditions in by hand." },
    { q: "Should I use MOA or MIL in the calculator?", a: "Use whatever your scope turrets and reticle use. Mixing them is the most common beginner mistake. See <a href=\"/glossary/mil-vs-moa/\">MIL vs MOA</a>." },
    { q: "What is the most important input?", a: "Muzzle velocity measured with a chronograph from your own rifle. Box velocities often come from longer test barrels and can be 50–150 fps optimistic." },
  ],
  related: ["mil-vs-moa", "ballistic-coefficient", "muzzle-velocity", "truing", "bullet-drop-chart"],
},
{
  slug: "mil-vs-moa", cat: "Scopes and adjustments", term: "MIL vs MOA",
  h1: "MIL vs MOA: what's the difference and which is better?",
  title: "MIL vs MOA: What's the Difference and Which Is Better?",
  description: "MIL vs MOA explained simply: how big each unit is at 100 yards and 100 meters, how to convert, and which scope system to choose for hunting or long range.",
  short: "the two angular units scopes use, with conversions and which to choose.",
  answer: "<b>MOA</b> (minute of angle) and <b>MIL</b> (milliradian) are both angles. 1 MOA is about 1.047 inches at 100 yards; 1 MIL is 3.6 inches at 100 yards, or 10 cm at 100 meters. 1 MIL equals 3.438 MOA. Neither is more accurate: pick the one that matches your reticle, and use it everywhere.",
  sections: [
    { h: "How big is 1 MOA and 1 MIL?", html: `<p>Because they are angles, the size they cover grows with distance:</p>
${table(["Distance", "1 MOA", "1 MIL", "¼ MOA click", "0.1 MIL click"], [100, 200, 300, 500, 1000].map((y) => [`${y} yd`, `${(1.047 * y / 100).toFixed(2)} in`, `${(3.6 * y / 100).toFixed(1)} in`, `${(0.2618 * y / 100).toFixed(2)} in`, `${(0.36 * y / 100).toFixed(2)} in`]), "Inch values per unit and per click. In metric: 1 MIL = 10 cm at 100 m, 1 MOA = 2.91 cm at 100 m.")}
<p>The formula is the same at any distance: <span class="formula">size = angle × distance</span>. For MIL that means inches = MIL × yards × 0.036, or centimeters = MIL × meters ÷ 10.</p>` },
    { h: "Converting between them", html: `<p><b>MOA = MIL × 3.438</b> and <b>MIL = MOA ÷ 3.438</b>. For example, a 12.0 MOA come-up is 3.5 MIL. You rarely need to convert in practice, because a calculator can output either one directly.</p>
<p>A few American scopes use "shooter's MOA" (exactly 1 inch at 100 yards) instead of true MOA. The difference is about 5%, which adds up: at 1000 yards and 40 MOA of come-up it is nearly two MOA. Check your scope manual.</p>` },
    { h: "Which is better?", html: `<p>Neither unit is more precise. A ¼ MOA click (0.26 in at 100 yd) is slightly finer than a 0.1 MIL click (0.36 in), but both are finer than any rifle can reliably group. What matters is:</p>
<ul><li><b>Match the reticle to the turrets.</b> A MIL reticle with MOA turrets forces you to convert under pressure. Almost all modern tactical scopes are MIL/MIL or MOA/MOA.</li>
<li><b>Communication.</b> Precision rifle matches, military and most of Europe use MIL. Many US hunters and older scopes use MOA. If your spotter uses one, use the same.</li>
<li><b>Metric friendliness.</b> MIL is decimal: 1 MIL is 10 cm at 100 m and 1 m at 1000 m, so ranging with the reticle is simpler. See <a href="/glossary/mil-dot-range-estimation/">mil-dot range estimation</a>.</li></ul>
<p>If you are buying your first long-range scope, MIL/MIL is the safer default today because more reticles, calculators and shooters use it.</p>` },
  ],
  faq: [
    { q: "How many inches is 1 MOA at 100 yards?", a: "1.047 inches. At 200 yards it is 2.09 inches, at 500 yards 5.2 inches, and at 1000 yards 10.5 inches." },
    { q: "How many inches is 1 MIL at 100 yards?", a: "3.6 inches. At 1000 yards it is 36 inches. In metric it is 10 cm at 100 meters." },
    { q: "Is MIL more accurate than MOA?", a: "No. Both are just units of angle. The finer ¼ MOA click is about 0.26 inches at 100 yards versus 0.36 inches for a 0.1 MIL click, a difference no rifle will show on paper." },
    { q: "Can I use a MOA scope with a MIL calculator?", a: "Yes, as long as the calculator's output is set to MOA. On ballistics.ge, choose MOA under Settings and pick your click value; it will give come-ups in MOA and in clicks." },
    { q: "How do I convert MIL to MOA?", a: "Multiply by 3.438. For example 2.5 MIL × 3.438 = 8.6 MOA. To go the other way, divide MOA by 3.438." },
  ],
  related: ["scope-click-value", "ffp-vs-sfp", "mil-dot-range-estimation", "ballistic-calculator"],
  cta: "Get come-ups in MIL or MOA",
},
{
  slug: "ffp-vs-sfp", cat: "Scopes and adjustments", term: "First focal plane (FFP) vs second focal plane (SFP)",
  h1: "FFP vs SFP: first focal plane or second focal plane?",
  title: "FFP vs SFP Scopes: Which Focal Plane Is Better?",
  description: "First vs second focal plane scopes: how each reticle behaves when you zoom, when holdover marks are correct, and which suits hunting or long range.",
  short: "why reticle marks only stay true at every zoom in a first focal plane scope.",
  answer: "In a <b>first focal plane (FFP)</b> scope the reticle grows and shrinks with magnification, so its MIL or MOA marks are correct at every zoom setting. In a <b>second focal plane (SFP)</b> scope the reticle stays the same size, so the marks are only correct at one magnification, usually the highest.",
  sections: [
    { h: "Why the focal plane matters", html: `<p>A riflescope has two image planes. If the reticle sits in the front one (first focal plane), it is magnified together with the target. A 1 MIL gap on the reticle covers 1 MIL on the target whether you are on 5× or 25×. If the reticle sits in the rear one (second focal plane), it looks the same size at every setting while the target gets bigger, so the angle each mark covers changes when you zoom.</p>` },
    { h: "How to correct an SFP reticle", html: `<p>SFP reticles are calibrated at one magnification, printed in the manual (often maximum, sometimes 10×). At any other setting:</p>
<p class="formula">true subtension = marked value × (calibrated power ÷ current power)</p>
<p>Example: a mil-dot SFP scope calibrated at 10×, used at 5×. Each 1 MIL dot spacing now covers 1 × 10 ÷ 5 = <b>2 MIL</b>. If you hold "2 dots" for wind at 5×, you are really holding 4 MIL. That mistake is a clean miss at any distance. Some shooters use this deliberately: on half power every mark is worth double, which extends holdover range.</p>
<p>The reticle page in our calculator lets you set FFP or SFP, the calibrated power and the current power, and draws the holds at the correct size.</p>` },
    { h: "Which one should you choose?", html: `<ul>
<li><b>FFP</b> suits precision and long-range shooting, where you hold for wind or elevation with the reticle at different magnifications, and where you range with the reticle. Downside: at low power the reticle becomes thin and hard to see, and FFP scopes tend to cost more.</li>
<li><b>SFP</b> suits hunting and most rimfire use, where you shoot at a single zero with a simple center crosshair, or dial rather than hold. The reticle stays bold and visible at low power in dim light.</li>
</ul>
<p>If you dial every correction with the turrets and only use the crosshair center, the focal plane does not matter for accuracy: turret clicks are the same in both designs.</p>` },
  ],
  faq: [
    { q: "Which is better, FFP or SFP?", a: "For long range and reticle holdovers, FFP, because the marks are correct at every magnification. For hunting at moderate range with a duplex-style reticle, SFP is often better because the reticle stays visible at low power." },
    { q: "Do turret clicks change with magnification in an SFP scope?", a: "No. A 0.1 MIL or ¼ MOA click moves the point of impact the same amount in both FFP and SFP scopes. Only the reticle markings change meaning." },
    { q: "At what magnification is an SFP reticle accurate?", a: "At the power stated by the manufacturer, usually the maximum magnification. Some scopes mark it on the power ring." },
    { q: "Why does the FFP reticle look tiny at low power?", a: "Because it shrinks together with the image. Many FFP scopes add an illuminated center or a thick outer post so the aiming point stays visible at low magnification." },
  ],
  related: ["mil-vs-moa", "mil-dot-range-estimation", "scope-click-value", "wind-drift"],
  cta: "See your reticle holds at any magnification",
},
{
  slug: "scope-click-value", cat: "Scopes and adjustments", term: "Scope click value",
  h1: "Scope click value: how many clicks is 1 MOA or 1 MIL?",
  title: "How Many Clicks Is 1 MOA or 1 MIL? Scope Adjustment Guide",
  description: "How many scope clicks per MOA or MIL, how far one click moves your impact at 100 yards and 100 meters, and how to convert a come-up into turret clicks.",
  short: "how far one turret click moves your impact, and how to turn a come-up into clicks.",
  answer: "A ¼ MOA scope needs <b>4 clicks per MOA</b>, and each click moves the impact about 0.26 inches at 100 yards. A 0.1 MIL scope needs <b>10 clicks per MIL</b>, and each click moves the impact 0.36 inches at 100 yards, or 1 cm at 100 meters.",
  sections: [
    { h: "Click values at common distances", html: `${table(["Click", "Clicks per unit", "At 100 yd", "At 100 m", "At 500 yd"], [["¼ MOA", "4 per MOA", "0.26 in", "0.73 cm", "1.31 in"], ["⅛ MOA", "8 per MOA", "0.13 in", "0.36 cm", "0.65 in"], ["0.1 MIL", "10 per MIL", "0.36 in", "1.0 cm", "1.80 in"], ["0.05 MIL", "20 per MIL", "0.18 in", "0.5 cm", "0.90 in"]], "Distance values are for one click.")}
<p>Most hunting scopes use ¼ MOA. Most tactical and precision scopes use 0.1 MIL. The value is engraved on the turret cap ("1 click = ¼ MOA" or "0.1 MRAD").</p>` },
    { h: "Converting a come-up to clicks", html: `<p class="formula">clicks = come-up ÷ click value</p>
<p>A 3.5 MIL come-up on a 0.1 MIL turret is 35 clicks. A 12 MOA come-up on a ¼ MOA turret is 48 clicks. The calculator shows clicks directly once you choose your click value in Settings.</p>
<p>For big come-ups, know how much one turret revolution is worth, often 10 MIL or 15–25 MOA. A .308 at 1000 yards needs about ${n(-r10.mil)} MIL, more than one full turn on a 10 MIL turret, so the turret's revolution indicator or zero stop is important.</p>` },
    { h: "Why you should verify your click value", html: `<p>Turrets are not always perfect. A "box test" or "tall target test" checks them. Put a tall sheet with a vertical line at 100 yards, fire a group, dial up exactly 10 MIL (or 30 MOA), fire again, and measure the distance between group centers. 10 MIL should be exactly 36.0 inches at 100 yards (or 100 cm at 100 m). If it is 35.2 inches, your turret moves 2% less than labeled, and every long-range come-up will be short.</p>
<p>Also remember that "cm clicks" are sometimes printed on European scopes: a "1 cm at 100 m" click is exactly 0.1 MIL.</p>` },
  ],
  faq: [
    { q: "How many clicks is 1 inch at 100 yards?", a: "About 4 clicks on a ¼ MOA scope (each click is 0.26 inches), or about 2.8 clicks on a 0.1 MIL scope (each click is 0.36 inches)." },
    { q: "How many clicks to move 1 inch at 50 yards?", a: "At 50 yards each click moves half as much, so about 8 clicks on a ¼ MOA scope or about 5.5 clicks on a 0.1 MIL scope." },
    { q: "How many MOA is one turn of the turret?", a: "It depends on the scope; common values are 15, 20 or 25 MOA per turn for MOA scopes and 10 MIL per turn for MIL scopes. It is in the manual and often on the turret." },
    { q: "Which way do I turn the turret?", a: "Turn toward the arrow marked UP to move the impact up, and toward R to move it right. You adjust in the direction you want the bullet to go." },
  ],
  related: ["mil-vs-moa", "zero-distance", "dope-card", "ballistic-calculator"],
  cta: "Get your come-ups in clicks",
},
{
  slug: "mil-dot-range-estimation", cat: "Scopes and adjustments", term: "Mil-dot range estimation",
  h1: "Mil-dot range estimation: how to range with your reticle",
  title: "Mil-Dot Range Estimation: Formula, Examples and Tips",
  description: "How to estimate range with a mil-dot or MOA reticle: the mil-relation formula in yards and meters, worked examples, target sizes to know and common mistakes.",
  short: "the mil-relation formula for ranging a target of known size with your reticle.",
  answer: "To range with a reticle, measure the target in MIL and use <b>range (m) = target size (cm) × 10 ÷ MIL</b>, or <b>range (yd) = target size (in) × 27.78 ÷ MIL</b>. With MOA use range (yd) = size (in) × 95.5 ÷ MOA. It only works when you know the target's real size.",
  sections: [
    { h: "The mil-relation formula", html: `<p>A milliradian is 1/1000 of the distance. So an object 1 meter tall that measures 1 MIL is 1000 meters away. Rearranged for everyday units:</p>
<p class="formula">range (m) = size (cm) × 10 ÷ MIL<br>range (yd) = size (in) × 27.78 ÷ MIL<br>range (yd) = size (in) × 95.5 ÷ MOA</p>` },
    { h: "Worked examples", html: `${table(["Target", "Size", "Measured", "Range"], [["IPSC / torso", "45 cm", "1.0 MIL", "450 m"], ["Deer chest (back to brisket)", "18 in", "0.8 MIL", "625 yd"], ["Steel plate", "12 in", "1.5 MOA", "764 yd"], ["Fence post height", "150 cm", "2.5 MIL", "600 m"]])}
<p>The rangefinder on our calculator's More tab does this math: enter the target size and the reading and press Use to send the range to the solution.</p>` },
    { h: "How to get a good reading", html: `<ul><li><b>In an SFP scope</b>, only range at the calibrated magnification. At half power every mark is worth double. See <a href="/glossary/ffp-vs-sfp/">FFP vs SFP</a>.</li>
<li>Brace the rifle and measure to tenths of a MIL. At 500 m on a 45 cm target, an error of 0.1 MIL in the reading is 50 m of range error.</li>
<li>Measure the dimension you know best. Heights of standing animals vary; the back-to-brisket depth of an adult deer is more consistent.</li>
<li>Measure twice, from different edges, and average.</li></ul>
<p>Reticle ranging is a backup skill. Past 400–500 yards, a laser rangefinder is far more accurate, and range errors turn directly into vertical misses: with a .308 at 600 yards, 25 yards of range error is about 0.6 MIL, or 13 inches.</p>` },
    { h: "Target sizes worth memorizing", html: `${table(["Object", "Typical size", "Reads 1 MIL at"], [["Human head (width)", "15–16 cm / 6 in", "150 m / 170 yd"], ["Human torso (width)", "45–50 cm / 18–20 in", "450–500 m"], ["Adult roe deer, chest depth", "30–35 cm / 12–14 in", "300–350 m"], ["Whitetail deer, back to brisket", "45 cm / 18 in", "450 m / 500 yd"], ["Wild boar, body height", "50–60 cm / 20–24 in", "500–600 m"], ["Car wheel (tire outside)", "60–65 cm / 24–26 in", "600–650 m"], ["IPSC target", "45 × 75 cm / 18 × 30 in", "450 m (width)"]], "Sizes vary between individuals; use them as starting points, not exact values.")}` },
  ],
  faq: [
    { q: "How accurate is mil-dot ranging?", a: "Under field conditions expect roughly ±5–10% error. That is fine for flat-shooting cartridges inside 400 yards, but not enough for first-round hits at long range." },
    { q: "What does the 27.78 in the formula mean?", a: "It converts inches and yards into the mil relation: 1000 ÷ 36 = 27.78. In meters and centimeters the constant is simply 10." },
    { q: "Can I range with a MOA reticle?", a: "Yes. Use range (yd) = size (in) × 95.5 ÷ MOA, or range (m) = size (cm) × 34.4 ÷ MOA." },
    { q: "What if my reticle has no dots, only hash marks?", a: "Hash marks work the same way. Most modern MIL reticles have marks every 0.2 or 0.5 MIL with finer subdivisions near the center, which makes readings more precise than classic dots." },
  ],
  related: ["mil-vs-moa", "ffp-vs-sfp", "bullet-drop-chart", "angle-shooting"],
  cta: "Use the built-in reticle rangefinder",
},
{
  slug: "scope-cant", cat: "Scopes and adjustments", term: "Scope cant",
  h1: "Scope cant: how a tilted rifle moves your impact",
  title: "Scope Cant: How Much a Tilted Rifle Throws Your Shot",
  description: "What scope cant is, how a few degrees of rifle tilt turns elevation into horizontal error at long range, worked numbers for .308, and how to level your scope.",
  short: "how tilting the rifle turns your elevation hold into a sideways miss.",
  answer: "<b>Cant</b> is tilting the rifle and scope to the side. When canted, part of your elevation correction points sideways, so the bullet lands low and to the side you tilted toward. The error grows with come-up: 2° of cant with a 12 MIL come-up moves the impact about 0.4 MIL sideways.",
  sections: [
    { h: "Why cant matters more at long range", html: `<p>At your zero distance the scope and bore lines cross, and a little tilt changes almost nothing. When you dial a large come-up, the barrel points well above the line of sight. Tilt the rifle and that upward angle rotates, so some of it becomes left or right:</p>
<p class="formula">horizontal error ≈ come-up × sin(cant angle)</p>
${table(["Cant", "At 500 yd (3.5 MIL up)", "At 1000 yd (11.9 MIL up)"], [1, 2, 5].map((d) => { const s = Math.sin(d * Math.PI / 180); return [`${d}°`, `${(3.5 * s).toFixed(2)} MIL · ${(3.5 * s * 18).toFixed(1)} in`, `${(11.9 * s).toFixed(2)} MIL · ${(11.9 * s * 36).toFixed(0)} in`]; }), ".308 175 gr at 2600 fps with a 100-yard zero. 1 MIL is 18 in at 500 yd and 36 in at 1000 yd.")}
<p>At 1000 yards, 5° of cant costs more than a MIL, which is a complete miss on a typical steel target.</p>` },
    { h: "How to avoid it", html: `<ul><li>Level the scope to the rifle when mounting: level the rifle's action first, then the reticle, using a plumb line or a reticle leveling tool.</li>
<li>Use an anti-cant bubble level on the scope tube and check it before every long shot.</li>
<li>On uneven ground, adjust the bipod or rear bag rather than tilting your head and rifle.</li>
<li>If you cannot remove the tilt, enter the cant angle in the calculator. Ours can read it from the phone's sensors when you lay the phone against the rifle.</li></ul>` },
    { h: "Cant or a crooked reticle?", html: `<p>Two different problems look alike. <b>Rifle cant</b> is how you hold the rifle; a bubble level fixes it. <b>Reticle cant</b> is a scope mounted rotated in its rings: the rifle is level but the crosshair is not. A canted reticle makes the elevation turret move the impact diagonally, so at long range every come-up also shifts you sideways.</p><p>To check for reticle cant, hang a plumb line (a weighted string) 50–100 yards away, level the rifle with its bubble, and see whether the vertical stadia line follows the string. Then do a tall-target test: dial up 10 MIL and confirm the group moves straight up. If it moves diagonally, loosen the rings and rotate the scope until it tracks straight.</p>` },
  ],
  faq: [
    { q: "Which way does cant move the bullet?", a: "Toward the side you tilt the top of the scope, and slightly low. Tilt right and you hit right and low." },
    { q: "Does cant matter at 100 yards?", a: "Very little if you are zeroed at 100 yards, because there is almost no come-up to rotate. It becomes important past 300–400 yards." },
    { q: "How accurate does my level need to be?", a: "Within about 1° is enough for most shooting. A standard scope bubble level achieves that easily." },
    { q: "Should I put the bubble level on the scope or the rifle?", a: "On the scope tube or the rail, once you have confirmed that the reticle is square to the rifle. The level must tell you whether the reticle is vertical, because that is the line along which your elevation adjustment moves." },
  ],
  related: ["angle-shooting", "wind-drift", "scope-click-value", "ballistic-calculator"],
},
  ];
};

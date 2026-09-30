export default ({ F, n, table }) => {
  const at = (k, yd) => F.tables[k].find((r) => r.yd === yd);
  const w5 = at("308", 500), w10 = at("308", 1000);
  return [
{
  slug: "wind-drift", cat: "Wind and environment", term: "Wind drift",
  h1: "Wind drift: how to read wind and hold for it",
  title: "Wind Drift: How to Read Wind for Long Range Shooting",
  description: "How crosswind moves a bullet, how much drift to expect at 300, 500 and 1000 yards, the clock method for full and half value wind, and how to hold for it.",
  short: "how much a crosswind moves the bullet, and the clock method for calling it.",
  answer: "<b>Wind drift</b> is how far a crosswind pushes the bullet sideways. It grows faster than distance: a 10 mph full-value wind moves a .308 175 gr bullet about " + n(w5.windIn, 0) + " inches at 500 yards and " + n(w10.windIn, 0) + " inches at 1000 yards. A wind from the right pushes the bullet left.",
  sections: [
    { h: "Why drift grows so fast", html: `<p>Drift depends on "lag time": how much longer the bullet takes to reach the target than it would in a vacuum. The farther it goes, the more it has slowed, and the more lag it accumulates. That is why wind drift in inches roughly quadruples from 500 to 1000 yards, and why high-<a href="/glossary/ballistic-coefficient/">BC</a> bullets, which slow less, drift less.</p>
${table(["Yards", ".308 175 gr", "6.5 CM 140 gr", ".223 55 gr"], [300, 500].map((y) => [y, `${n(at("308", y).windIn)} in`, `${n(at("65cm", y).windIn)} in`, `${n(at("223", y).windIn)} in`]).concat([[1000, `${n(w10.windIn)} in`, `${n(at("65cm", 1000).windIn)} in`, "—"]]), "Drift in a full-value 10 mph crosswind, sea level.")}` },
    { h: "Full value, half value: the clock method", html: `<p>Picture yourself in the middle of a clock facing 12 o'clock, the target.</p>
<ul><li><b>3 and 9 o'clock</b>: full value. Use the whole drift.</li>
<li><b>1, 2, 4, 5, 7, 8, 10, 11 o'clock</b>: roughly 50–90%. A common shortcut: 1, 5, 7 and 11 o'clock are half value; 2, 4, 8 and 10 are about 85%.</li>
<li><b>12 and 6 o'clock</b>: no value for drift, although head- and tailwinds change drop slightly at long range.</li></ul>
<p>The calculator does this for you: enter the wind speed, the direction it blows from, and your shooting direction, or use the phone compass to set the heading.</p>` },
    { h: "Reading the wind", html: `<ul><li>Measure speed at your position with a wind meter, then look downrange: mirage, grass, trees and dust show what the wind is doing where it matters most, usually in the middle and far part of the bullet's path.</li>
<li>Mirage leaning slightly is about 3–5 mph; flat, fast mirage is 8–12 mph or more; "boiling" mirage straight up means little or no crosswind.</li>
<li>Call the wind in steps (for example 0.1 MIL). Hold the correction on an FFP reticle, or dial it if you have time.</li>
<li>If your first shot misses, correct from the observed impact rather than re-estimating the wind from scratch.</li></ul>` },
  ],
  faq: [
    { q: "How much does a 10 mph wind move a bullet at 100 yards?", a: `Less than an inch for most centerfire rifles (about ${n(at("308", 100).windIn, 1)} in for .308 175 gr), and about ${n(at("22lr", 100).windIn, 1)} inches for .22 LR standard velocity.` },
    { q: "Does a wind from the right push the bullet left?", a: "Yes. A wind blowing from the right (3 o'clock) pushes the bullet to the left, so you hold or dial right, into the wind." },
    { q: "Why do I miss high or low in a crosswind?", a: "Aerodynamic jump: a crosswind tilts the spinning bullet slightly, which moves the impact vertically. With right-hand twist, a wind from the left pushes the impact up a little and a wind from the right pushes it down." },
    { q: "What is a full-value wind?", a: "A wind blowing at 90° to the line of fire, from 3 or 9 o'clock. It produces the maximum drift for its speed." },
  ],
  related: ["spin-drift", "ballistic-coefficient", "dope-card", "308-ballistics-chart"],
  cta: "Calculate wind holds for your load",
},
{
  slug: "spin-drift", cat: "Wind and environment", term: "Spin drift",
  h1: "Spin drift: why bullets drift right with no wind",
  title: "Spin Drift: Why Bullets Drift Right With No Wind",
  description: "What spin drift is, why right-twist barrels push bullets to the right, how much drift to expect at 1000 yards with .308, and when it is worth correcting for.",
  short: "why a spinning bullet drifts sideways even in calm air.",
  answer: "<b>Spin drift</b> is the sideways movement of a spinning bullet, even in still air. A bullet from a right-hand twist barrel drifts <b>right</b>; left twist drifts left. For a .308 175 gr bullet at 1000 yards our solver predicts about " + n(F.spin308In, 0) + " inches, around " + n(F.spin308In / 36, 2) + " MIL: small at short range, but worth correcting past about 600 yards.",
  sections: [
    { h: "What causes it", html: `<p>A spinning bullet's nose follows the curve of its trajectory, but it points very slightly to the side of its path (the "yaw of repose"). That small angle creates a sideways lift force in the direction of spin. The effect is tiny at first but grows with time of flight, so it matters most at long range where the bullet is falling steeply.</p>` },
    { h: "How much", html: `<p>Bryan Litz's empirical formula, used by most calculators including ours:</p>
<p class="formula">spin drift (in) = 1.25 × (SG + 1.2) × TOF<sup>1.83</sup></p>
<p>where SG is the gyroscopic <a href="/glossary/twist-rate/">stability factor</a> and TOF is the time of flight in seconds. For our .308 example (SG ${n(F.sg308, 2)}) that gives about ${n(F.spin308In, 0)} inches at 1000 yards. More stability, from a faster twist, means a little more spin drift.</p>` },
    { h: "Should you correct for it?", html: `<p>Inside 500 yards, spin drift is usually less than the rifle's group size, so most shooters ignore it. At 800–1000 yards it is similar to a 1–2 mph wind error, which is worth taking out. The calculator includes it in the wind correction automatically. Because it always goes the same way, some shooters simply move their zero slightly left for long-range rifles, but that makes the short-range zero wrong; letting the calculator handle it is better.</p>` },
    { h: "Separating spin drift from wind at the range", html: `<p>If you confirm long-range dope on a calm morning, you will notice your impacts are a little right of center with no wind. That is spin drift plus, in the northern hemisphere, a small Coriolis drift. Record it. When the calculator includes both effects and your group is still off to one side in calm air, check for <a href="/glossary/scope-cant/">reticle cant</a> or a zero that is slightly right before blaming the model.</p>` },
  ],
  faq: [
    { q: "Which way does spin drift go?", a: "In the direction of rifling twist: right for right-hand twist barrels, which covers most rifles, and left for left-hand twist." },
    { q: "Is spin drift the same as Coriolis?", a: "No. Spin drift comes from the bullet's rotation; Coriolis comes from the Earth's rotation. Both are small and both are handled by the calculator." },
    { q: "Does spin drift matter for hunting?", a: "Rarely. At typical hunting distances it is under an inch or two." },
    { q: "Does spin drift change with distance in a straight line?", a: "No, it grows faster than distance, because it depends on time of flight raised to the power 1.83. Doubling the time of flight more than triples the drift." },
  ],
  related: ["twist-rate", "coriolis-effect", "wind-drift", "ballistic-calculator"],
},
{
  slug: "coriolis-effect", cat: "Wind and environment", term: "Coriolis effect",
  h1: "Coriolis effect in shooting: does Earth's rotation matter?",
  title: "Coriolis Effect in Long Range Shooting Explained",
  description: "How Earth's rotation moves a bullet: why it drifts right in the northern hemisphere, why shooting east hits high, and how much it matters at 1000 yards.",
  short: "how the Earth's rotation moves a long-range bullet.",
  answer: "The <b>Coriolis effect</b> is a small shift in the bullet's impact caused by the Earth rotating during its flight. In the northern hemisphere the bullet drifts <b>right</b>; shooting <b>east</b> it hits slightly high and shooting west slightly low. For a .308 at 1000 yards at 40° latitude it is about " + n(F.corNorthHIn, 0) + " inches sideways and up to " + n(Math.abs(F.corEastVIn), 0) + " inches vertically.",
  sections: [
    { h: "Horizontal: always right in the north", html: `<p>While the bullet flies, the ground under it keeps turning. From the shooter's point of view the bullet seems to curve: to the right in the northern hemisphere and to the left in the southern. The effect depends on latitude (zero at the equator, largest at the poles) and time of flight, and it does not depend on which direction you shoot.</p>` },
    { h: "Vertical: the Eötvös effect", html: `<p>Shooting east, the bullet moves with the Earth's rotation, and the surface curves away beneath it: it hits slightly high. Shooting west, it hits slightly low. North or south, the vertical part is zero. For our .308 example at 40° latitude and 1000 yards:</p>
${table(["Direction", "Horizontal", "Vertical"], [["North", `${n(F.corNorthHIn)} in right`, "≈ 0"], ["East", `${n(F.corNorthHIn)} in right`, `${n(F.corEastVIn)} in high`], ["West", `${n(F.corNorthHIn)} in right`, `${n(Math.abs(F.corWestVIn))} in low`]], ".308 175 gr at 2600 fps, 40° N. Calculated with the ballistics.ge solver.")}` },
    { h: "Does it matter?", html: `<p>Inside 600 yards, no: it is smaller than normal wind uncertainty. At 1000 yards and beyond, a few inches can decide a hit on a small target, and extreme long range (ELR) shooters always include it. Our calculator includes Coriolis when you allow location access (for latitude) and set your shooting direction, which you can do with the phone compass.</p>` },
    { h: "Horizontal Coriolis by latitude", html: `${table(["Latitude", "Horizontal at 1000 yd"], F.corLat.map((c) => [`${c.lat}°`, `${n(c.h)} in`]), ".308 175 gr at 2600 fps. Tbilisi is at about 42° N, most of the continental US between 30° and 48° N.")}<p>At the equator the horizontal part vanishes, and it grows with latitude. The vertical Eötvös part is largest at the equator and zero at the poles.</p>` },
  ],
  faq: [
    { q: "Which way does Coriolis push a bullet?", a: "To the right in the northern hemisphere and to the left in the southern hemisphere, regardless of the direction you shoot." },
    { q: "How much is Coriolis at 1000 yards?", a: `A few inches: about ${n(F.corNorthHIn, 0)} inches horizontally for a .308 at 40° latitude, plus up to ${n(Math.abs(F.corEastVIn), 0)} inches high or low when shooting east or west.` },
    { q: "Do snipers account for Coriolis?", a: "At extreme ranges, yes. Military and competition ballistic solvers include it, but at typical engagement distances it is much smaller than wind error." },
    { q: "Does Coriolis matter for .22 LR?", a: "No. At rimfire distances the time of flight is short enough that Coriolis is a small fraction of an inch." },
  ],
  related: ["spin-drift", "wind-drift", "density-altitude", "ballistic-calculator"],
},
{
  slug: "density-altitude", cat: "Wind and environment", term: "Density altitude",
  h1: "Density altitude: how air density changes your trajectory",
  title: "Density Altitude for Shooting: Temperature, Pressure, Altitude",
  description: "What density altitude is, how temperature, pressure, humidity and elevation change bullet drop, why station pressure matters, and a .308 example.",
  short: "one number that captures how thin the air is, and how it changes your come-ups.",
  answer: "<b>Density altitude</b> is the altitude in the standard atmosphere that has the same air density as your current conditions. Thinner air (high, hot, low pressure) means less drag, so the bullet drops less. A .308 175 gr needs " + n(-F.da.sea.mil) + " MIL at 1000 yards at sea level but only " + n(-F.da.high.mil) + " MIL at 5000 ft and 90 °F.",
  sections: [
    { h: "What changes air density", html: `<ul><li><b>Altitude and pressure</b>: the biggest factor. Air at 5000 ft is about 15% thinner than at sea level.</li>
<li><b>Temperature</b>: warm air is thinner. A 40 °F rise lowers density by about 8%. Temperature also changes <a href="/glossary/muzzle-velocity/">muzzle velocity</a> through powder temperature.</li>
<li><b>Humidity</b>: humid air is slightly thinner (water vapor is lighter than dry air), but the effect is small.</li></ul>` },
    { h: "Worked example", html: `${table(["Conditions", "Come-up at 1000 yd", "Drop", "Velocity at 1000 yd"], [["Sea level, 59 °F, 29.92 inHg", `${n(-F.da.sea.mil, 2)} MIL`, `${n(-F.da.sea.dropIn, 0)} in`, `${Math.round(F.da.sea.fps)} fps`], ["5000 ft, 90 °F", `${n(-F.da.high.mil, 2)} MIL`, `${n(-F.da.high.dropIn, 0)} in`, `${Math.round(F.da.high.fps)} fps`]], ".308 175 gr at 2600 fps, 100-yard zero. Same muzzle velocity in both cases, to isolate the air-density effect.")}
<p>That is a ${n(F.da.sea.mil - F.da.high.mil, 1)} MIL difference, ${n(F.da.high.dropIn - F.da.sea.dropIn, 0)} inches at 1000 yards. The bullet also stays supersonic in the thinner air, so the load that struggles at sea level works well in the mountains. See <a href="/glossary/transonic/">transonic</a>.</p>` },
    { h: "Station pressure vs barometric pressure", html: `<p>The pressure on weather reports is "sea-level corrected" barometric pressure. For ballistics you need <b>station pressure</b>, the actual pressure where you stand. At 3000 ft they differ by about 3 inHg (100 mbar). If you enter the weather-report value, also enter your altitude; if you enter station pressure from a Kestrel or similar, the altitude is already included. Our calculator can fetch current weather for your location and handles the conversion.</p>` },
    { h: "Using density altitude in the field", html: `<ul><li>Make DOPE cards for the conditions you actually shoot in, for example summer and winter, or home range and mountain hunting area.</li><li>A handheld weather meter such as a Kestrel reads station pressure, temperature, humidity and density altitude. You can photograph its screen in our calculator to fill in the values.</li><li>As a rough guide for a .308, each 1000 ft of density altitude changes the 1000-yard come-up by roughly a quarter of a MIL. The table above shows the full example.</li></ul>` },
  ],
  faq: [
    { q: "Does a bullet drop less at high altitude?", a: "Yes. Thinner air slows the bullet less, so it arrives faster and drops less. The difference is small at 300 yards but large at 1000 yards." },
    { q: "Does temperature affect bullet drop?", a: "Yes, in two ways: warm air is thinner, and warm powder usually gives higher muzzle velocity. Both reduce drop." },
    { q: "Should I use density altitude or pressure and temperature?", a: "Either works if entered correctly. Density altitude is a convenient single number; entering station pressure and temperature separately also lets the calculator adjust muzzle velocity for temperature." },
    { q: "Does humidity affect trajectory?", a: "Slightly. Humid air is a little less dense, so drop is slightly smaller, but the effect is far smaller than temperature or altitude." },
    { q: "What is a normal density altitude?", a: "At sea level on a standard 59 °F day it is 0 ft. On a hot summer day at low elevation it is often 2000–3000 ft, and in the mountains it can exceed 8000 ft." },
  ],
  related: ["muzzle-velocity", "transonic", "308-ballistics-chart", "dope-card"],
  cta: "Get come-ups for today's conditions",
},
  ];
};

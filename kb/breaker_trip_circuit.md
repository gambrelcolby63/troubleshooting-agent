# Circuit Breaker Trip and Close Circuit Troubleshooting
<!-- Self-written. General concepts only; always follow the breaker manufacturer's instructions. -->

## 1. Trip circuit components
A typical trip circuit is: station DC positive → protective fuse → relay trip contact or 86 lockout contact (or control switch trip) → breaker 52a auxiliary contact → trip coil → DC negative. The 52a contact opens when the breaker opens, which removes current from the trip coil so it is not burned out. Many schemes add a trip-coil monitor (red light or relay) that shows trip-circuit continuity when the breaker is closed.

## 2. Breaker trips immediately on close
If a breaker trips as soon as it is closed, determine whether a protective relay operated. If relay targets show an instantaneous (50) or differential (87) trip, the breaker likely closed into a fault or a setting/CT issue exists (see protective relay basics). If no relay target is present, suspect the control scheme: a maintained trip signal (stuck relay contact, an 86 lockout that was not reset, a shorted control switch), an anti-pump or trip-free mechanism problem, or a mechanical latch that does not hold. Do not keep re-closing; each close into a fault adds damage.

## 3. Breaker fails to trip
A breaker that will not trip electrically while closed is a serious protection failure. Common causes: blown or removed DC trip fuse, loss of station DC, an open trip coil, a 52a auxiliary contact that is misadjusted or dirty, broken wiring, or a mechanically binding trip latch. With the breaker isolated, check DC voltage at the trip coil terminals when a trip is initiated, then check coil resistance against the nameplate. If the trip coil monitor light is out while the breaker is closed, the trip circuit is open.

## 4. Breaker fails to close
Causes include: closing spring not charged (failed charging motor, open motor fuse, or motor limit switch), an active 86 lockout or trip signal (trip-free), anti-pump relay sealed in, open close coil, low DC voltage, a racking or position interlock that is not satisfied, or a 52b contact problem in the close circuit. Check the spring-charged indicator and the close circuit voltage first.

## 5. Breaker maintenance tests
Typical maintenance tests include contact resistance (micro-ohm) testing, insulation resistance testing across open contacts and phase-to-ground, trip and close coil timing, minimum trip voltage tests, and for low-voltage breakers primary or secondary injection of the trip unit. Results are compared to manufacturer data and previous results.

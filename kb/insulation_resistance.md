# Insulation Resistance (Megger) Testing
<!-- Self-written. General practice only; follow the equipment manufacturer and your site's acceptance criteria. -->

## 1. Purpose
An insulation resistance (IR) test applies a DC voltage (commonly 500 V, 1000 V, 2500 V or 5000 V depending on the equipment rating) between a conductor and ground, or between conductors, and measures the leakage resistance in megohms. Low IR indicates moisture, contamination, overheating damage, or insulation breakdown in cables, motor windings, transformers and breakers.

## 2. Preparation and safety
The equipment must be de-energized, locked out, and verified for absence of voltage first. Disconnect or isolate electronics, surge arresters, VFDs, capacitors and anything that the test voltage could damage. Warn others and barricade the far end of long cables, because the test voltage can be dangerous.

## 3. Performing the test
Connect the instrument line lead to the conductor and the earth lead to ground or the frame. Apply the test voltage for one minute and record the reading, along with the temperature and humidity. For a polarization index (PI) test, record the readings at 1 minute and 10 minutes; PI = R10min / R1min. A PI below about 1.0 suggests wet or contaminated insulation; around 2 or higher generally indicates good insulation (check the applicable standard and manufacturer guidance).

## 4. Interpreting results
A common rule of thumb for rotating machines is a minimum of roughly 1 megohm per kV of rating plus 1 megohm, but acceptance criteria come from the manufacturer and site standards. Trending is more valuable than a single reading: a large drop compared to previous tests is significant. IR readings drop as temperature rises, so correct readings to a common base temperature before comparing. A winding-to-ground reading near zero indicates a ground fault in the winding or cable.

## 5. Discharge after testing
The insulation stores charge during the test. Ground and discharge the conductor after the test for at least as long as the test voltage was applied (many instruments do this automatically) before disconnecting the leads or touching the conductor.

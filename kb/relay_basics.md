# Protective Relay Basics (ANSI Device Numbers)
<!-- Self-written. General concepts only. -->

## 1. Common ANSI device numbers
50 = instantaneous overcurrent; 51 = time overcurrent; 50N/51N or 50G/51G = neutral or ground overcurrent; 87 = differential; 21 = distance (impedance); 27 = undervoltage; 59 = overvoltage; 81 = frequency; 86 = lockout relay; 52 = AC circuit breaker; 52a / 52b = breaker auxiliary contacts that are closed when the breaker is closed / open; 49 = thermal; 46 = negative sequence (current unbalance).

## 2. Overcurrent protection (50/51)
A 51 element trips after a time delay that gets shorter as current increases, defined by its pickup setting, curve type and time dial. A 50 element trips with no intentional delay when current exceeds its pickup. An instantaneous (50) trip right after closing usually means the breaker closed into a real fault, the 50 pickup is set too low for the inrush or cold-load current, or the CT ratio entered in the relay is wrong. Check the relay event record for which element tripped and the fault currents.

## 3. Differential protection (87)
An 87 relay compares current entering and leaving a protected zone (transformer, bus, generator, motor). In normal service the difference is near zero. A differential trip on energization or under load with no actual fault commonly comes from CT problems: reversed CT polarity, wrong CT ratio or tap setting, an open or shorted CT secondary, or an incorrect transformer phase-angle compensation setting. Transformer inrush can also cause operation if harmonic restraint is not set correctly.

## 4. Distance protection (21)
A 21 relay measures the apparent impedance (voltage divided by current) to a fault and trips if it falls inside its zones. Because it needs voltage, a loss of potential (blown VT fuse or open VT circuit) can cause the relay to misoperate; most relays have loss-of-potential logic that blocks distance elements. A 21 trip during a VT problem points to the VT circuit rather than a line fault.

## 5. Reading relay targets and event records
Before resetting anything, record the front-panel targets, the 86 lockout status, and download the event report. The event shows which element operated, the phases involved, the current and voltage magnitudes, and the timing. Do not repeatedly reset and re-close a breaker that tripped on a protective function without finding the cause.

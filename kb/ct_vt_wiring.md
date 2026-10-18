# CT and VT (PT) Wiring Checks
<!-- Self-written. General concepts only. -->

## 1. Never open-circuit an energized CT secondary
A current transformer drives current into its burden. If the secondary is opened while primary current flows, the secondary voltage can rise to thousands of volts, which is a shock hazard and can destroy the CT. Use the shorting terminal block to short the CT secondary before disconnecting a relay or meter, and confirm the shorting screws or links are installed correctly.

## 2. CT ratio and secondary current
CT ratio is primary amps to secondary amps, for example 600:5. Primary current = secondary current × (ratio primary / ratio secondary). With a 600:5 CT, 4 A secondary equals 480 A primary. If a relay or meter reads a value that is off by a constant factor, check that the CT ratio setting in the device matches the CT tap actually wired on a multi-ratio CT.

## 3. CT polarity
CTs have polarity marks (H1/X1 or dots). Differential and directional relays depend on correct polarity. A reversed CT on one side of a differential zone makes through-load current look like an internal fault, causing a differential (87) trip once load increases. Verify polarity during commissioning with a polarity test or by checking phase angles of in-service currents.

## 4. Open or high-resistance CT circuits
Signs of an open or loose CT circuit: one phase current reads zero or erratic while the others are normal, residual (ground) current appears equal to the missing phase, buzzing or arcing at terminal blocks, and heating at a loose terminal. Check terminations, shorting blocks, and test switches. Measure loop resistance and burden only with the circuit isolated per procedure.

## 5. VT (PT) circuits and blown fuses
Voltage transformers supply relay and meter potential, usually 120 V or 69 V secondary. A blown VT primary or secondary fuse causes one or more phase voltages to read low or zero, which can trigger undervoltage (27) alarms, loss-of-potential alarms, and misoperation of distance (21) or directional elements. Check fuses and the VT secondary voltages phase-to-phase and phase-to-neutral. Treat VT secondaries as energized and never short them (a shorted VT secondary draws high current and blows the fuse or damages the VT).

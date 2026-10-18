# UPS Fault Troubleshooting
<!-- Self-written. General concepts for typical online (double-conversion) UPS units. -->

## 1. UPS operating modes
An online UPS normally runs rectifier → DC bus/battery → inverter → load. On input power failure the battery supplies the inverter. In bypass mode the load is fed directly from the input (raw utility) through a static switch, so it is not protected. Note which mode the UPS is in and what alarms are present before acting.

## 2. UPS on battery with input power present
If the UPS reports it is on battery while utility voltage is present, the input may be out of the UPS's acceptable voltage or frequency window (common with a generator that has unstable frequency), the input breaker or fuse may be open, or the rectifier may have failed. Measure input voltage and frequency at the UPS input terminals and check the input breaker.

## 3. Short runtime and battery faults
Short runtime or a battery fault alarm usually means aged or failed batteries (valve-regulated lead-acid batteries often last about 3 to 5 years, less at high ambient temperature), a failed cell, or a loose battery connection. Run the UPS battery self-test, check individual battery voltages and internal resistance, and check the battery temperature and age.

## 4. Overload and transfer to bypass
An overload alarm means the connected load exceeds the UPS rating; the UPS may transfer to bypass or shut down. Compare the output kW and kVA to the rating. Inverter faults, overtemperature (blocked filters or failed fans), or DC bus faults can also force a transfer to bypass. Clear the cause before transferring back to inverter.

## 5. Safety around UPS equipment
A UPS has multiple sources: utility input, bypass input, the battery string, and charged DC capacitors. Opening the input breaker does not de-energize the output or the battery. Follow the manufacturer's shutdown and isolation procedure, lock out every source, and wait for the DC bus capacitors to discharge before work.

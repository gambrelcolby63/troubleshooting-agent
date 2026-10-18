# Station DC and Battery Systems
<!-- Self-written. General concepts only. -->

## 1. Role of the station battery
Substation and switchgear protection depends on a DC battery and charger (commonly 125 V or 48 V nominal). The battery must be able to trip breakers even when AC is lost. Low DC voltage can cause breakers to fail to trip or close, relays to reboot, and alarms.

## 2. Float voltage and charger problems
A charger normally holds the battery at a float voltage set by the battery manufacturer (for a 60-cell lead-acid 125 V battery this is typically around 130 to 135 V). Low DC bus voltage with the charger running suggests a failed charger, open AC supply to the charger, or a battery with failed cells. High float voltage causes gassing and water loss in flooded cells. Check charger output current and alarms.

## 3. DC ground faults
Station DC systems are normally ungrounded with a ground detector. A ground detector alarm, or positive-to-ground and negative-to-ground voltages becoming unbalanced (for example one side near zero), indicates a ground on the DC system. One ground does not trip anything, but a second ground can cause a false trip or failure to trip. Locate grounds by sectionalizing circuits one at a time under a coordinated procedure, because opening the wrong DC circuit can disable protection.

## 4. Battery testing
Routine checks include overall float voltage, individual cell voltages, specific gravity (flooded lead-acid), internal ohmic (impedance or conductance) measurements, connection resistance, and temperature. A cell with low voltage or rising internal resistance compared with others is failing. Capacity (load) testing verifies the battery can deliver its rated amp-hours. Batteries can deliver very high short-circuit currents and give off hydrogen: use insulated tools, eye protection and no ignition sources.

# Motor Starter and Motor Controller Faults
<!-- Self-written. General concepts for across-the-line starters and general-purpose VFDs. -->

## 1. Starter will not pull in
If the contactor does not close when START is pressed, check the control circuit: control transformer fuse, control voltage present, stop buttons and other permissives in series (normally closed contacts), an overload relay contact that is tripped open, and the contactor coil itself. Use the point-by-point voltage method from the control power source toward the coil to find the open. A coil reading open-circuit on an ohmmeter (de-energized) has failed.

## 2. Overload relay trips
Repeated overload trips mean the motor is drawing more than the overload setting for too long. Causes: mechanical overload or a jammed or binding load, failing bearings, low or unbalanced supply voltage, single phasing (one phase lost), an overload set below the motor nameplate FLA, or high ambient temperature. Measure the running current on all three phases and compare with nameplate FLA, and check the supply voltage balance.

## 3. Motor hums but will not start (single phasing)
A three-phase motor that hums but does not start, or runs hot and noisy, is often single phasing: one phase is missing because of a blown fuse, a failed contactor pole, or a loose or broken conductor. Measure voltage on all three phases at the line and load side of the starter, and check fuses. Do not keep trying to restart; the motor will overheat.

## 4. Motor winding and insulation faults
A motor that trips its breaker or ground-fault protection instantly on start may have a grounded or shorted winding or a damaged cable. With the motor locked out, perform an insulation resistance test from each phase to ground, and measure winding resistance phase-to-phase; the three readings should be closely balanced.

## 5. VFD fault codes (general)
General-purpose drives report faults such as overcurrent (fast acceleration, a short circuit on the output, or a motor fault), DC bus overvoltage (decelerating a high-inertia load too quickly, or high line voltage), undervoltage (supply dip or lost phase), ground fault on the output, and overtemperature (fans or filters). Exact fault-code meanings are manufacturer-specific: consult that drive's manual. Allow the DC bus to discharge (check the drive's indicated wait time and verify with a meter) before touching drive terminals.

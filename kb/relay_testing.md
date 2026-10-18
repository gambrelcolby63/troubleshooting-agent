# Protective Relay Testing (Acceptance and Maintenance Concepts)
<!-- Self-written summary of common field-testing practice; follow the relay manufacturer, the applicable acceptance/maintenance testing specification, and your site procedures. -->

## 1. Secondary injection testing
Relays are tested by injecting secondary current and voltage from a test set into the relay inputs, with the relay isolated from the CTs, VTs and trip circuits using test switches. Short the CT circuits and open the trip outputs before injecting, so the test does not trip in-service breakers or open-circuit a CT.

## 2. Pickup and timing tests
A pickup test slowly raises current until the element operates, and compares it with the setting. A timing test injects a multiple of pickup (for example 2, 3 and 5 times pickup) and records operate time versus the expected time on the curve. For instantaneous elements, check both pickup and that operation is fast.

## 3. Percent error and tolerance
Percent error = (measured − expected) / expected × 100. For example, if a relay is set to pick up at 5.00 A and picks up at 5.15 A, the error is +3.0%. Compare the error with the manufacturer's published tolerance (and site acceptance criteria). A result outside tolerance is investigated: verify the test connections and settings first, then the relay.

## 4. Verifying settings and logic
Compare the relay's active settings group against the approved settings file, including CT and VT ratios. Test the trip outputs to the breaker (functional trip test) after secondary injection, with operations coordinated. Many misoperations come from wrong settings (CT ratio, wrong group active, wrong curve) rather than failed hardware.

## 5. CT tests
Common CT tests include ratio, polarity, excitation (saturation) curve, insulation resistance and secondary loop burden. Ratio error is again a percent-error calculation between measured and nameplate ratio.

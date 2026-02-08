# Solar Collection Research

## Overview

This document covers research into concentrated solar power (CSP) collection methods for the solar power generator project.

---

## Primary: Parabolic Dish (Two-Axis Tracking)

- Highest optical efficiency (~85–93%) and concentration ratio (1,000–3,000x) of any CSP type
- Achieves **300–1,500°C** at the focal point
- Two-axis tracking required (alt-azimuth or equatorial mount)
- Can be built on a repurposed satellite dish frame with mirror tiles
- Materials: aluminum reflective sheet (e.g., Alanod MIRO-SUN, 91% reflectance), steel frame, dual-axis motor tracking
- All materials non-toxic and commonly available
- Solar-to-thermal efficiency: **55–70%**

---

## Alternative: Fresnel Lens + Parabolic Dish Hybrid (Two-Axis Tracking)

- A large Fresnel lens (2x the dish diameter) acts as the primary collector, focusing sunlight down to fill the aperture of a smaller parabolic dish, which further concentrates it to a focal point
- Two-axis tracking required for both elements (mounted together as a unit)
- The Fresnel lens captures **4x the light collection area** of the dish alone
- Due to étendue conservation, concentration ratio (W/m²) remains similar to the dish alone — the focal spot grows proportionally — but **total thermal power is ~4x greater** (minus lens losses)
- Temperature at the receiver is comparable to a dish alone; the advantage is significantly more total energy delivered
- Fresnel lens transmission loss: ~8–15% for acrylic, ~4–8% for glass
- Chromatic aberration spreads the focal spot slightly (polychromatic light focused at different distances)

### Tradeoffs vs. Building a Larger Dish

| Factor | Larger Dish Alone | Fresnel + Smaller Dish |
|--------|-------------------|------------------------|
| Optical efficiency | Higher (no lens loss) | ~85–92% of equivalent dish |
| Concentration ratio | Higher | Same as small dish alone |
| Structural weight | Heavier (large curved surface) | Lighter (flat lens + small dish) |
| Fabrication | Harder (accurate large parabola) | Easier (flat lens is cheap, small dish is easier to make accurate) |
| Wind loading | Very high | Lower (flat lens has less wind catch) |
| Cost | Higher | Potentially lower |
| Alignment | Simpler (one element) | More complex (two elements must stay aligned) |

- **Best suited when**: building a large accurate parabolic dish is the fabrication bottleneck, or weight/wind loading is a concern
- Materials: acrylic or glass Fresnel lens, aluminum mirror sheet for dish, steel frame
- All materials non-toxic

---

## Alternative: Scheffler Reflector Dish

- Fixed-focus parabolic reflector designed for DIY/community builds
- One-axis tracking (simpler than parabolic dish)
- Achieves **300–700°C** at the focal point
- Fixed focal point — ideal for a stationary thermal storage receiver
- Optical efficiency: ~60–75% (lower than parabolic dish due to seasonal reshaping compromise)
- Concentration ratio: ~50–200x
- Solar-to-thermal efficiency: **55–70%** (lower end of range)
- Materials: aluminum reflective sheet, steel frame, simple motor/clockwork tracking
- All materials non-toxic and commonly available

---

## Fallback: Parabolic Trough

- One-axis tracking, well-documented DIY builds
- Temperature range: 150–250°C (lower, reduces Carnot efficiency)
- Simpler geometry but lower performance ceiling

---

## Not Recommended

- **Flat plate collectors**: max ~80°C — too low for heat engines
- **Evacuated tubes**: max ~150–200°C — borderline, requires factory-made tubes
- **Linear Fresnel**: lowest CSP efficiency (35–50%), added complexity

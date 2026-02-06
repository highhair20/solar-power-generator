# Materials Specification

## Overview

All materials used in this project must be:
- **Non-toxic** — safe to handle, no hazardous disposal requirements
- **Non-exotic** — commonly available, not rare earth elements or specialty alloys
- **Green to manufacture** — minimal environmental impact in production

---

## Materials by Component

| Component | Key Materials | Notes |
|-----------|--------------|-------|
| Reflector | Aluminum mirror sheet, steel frame | Alanod MIRO-SUN or similar (91% reflectance) |
| Fresnel lens | Acrylic (PMMA) or glass | Acrylic cheaper, glass more durable |
| Receiver | Copper/steel pipe, flat black high-temp paint | Selective coatings optional |
| Sand battery | Silica sand, steel silo, firebrick, mineral wool | Sand is free/cheap |
| Erythritol buffer | Food-grade erythritol, stainless steel container | Bio-derived sugar alcohol |
| Stirling engine | Stainless steel, copper, aluminum, graphite seals | Air or helium working gas |
| ORC system | Stainless steel, copper, pentane or ethanol | Ethanol is green/bio-derived |
| Tesla turbine | Stainless steel or aluminum discs | Standard bearings |
| TEG modules | Bismuth telluride (Bi₂Te₃) | Mildly exotic but acceptable for small quantities |
| Water tank | Steel tank, mineral wool insulation | Standard plumbing |
| Tracking system | Steel frame, linear actuator, Arduino | Off-the-shelf components |

---

## Material Details

### Reflector Materials

**Aluminum mirror sheet (e.g., Alanod MIRO-SUN)**
- High-purity aluminum (Al 1085)
- 91% hemispheric solar reflectance
- 0.5 mm thick, bendable
- Weatherproof (anodized + PVD-coated + nano-composite lacquer)
- Non-toxic

### Thermal Storage Materials

**Silica sand**
- SiO₂, completely inert
- Fine-grained (~0.5–2mm) for good heat transfer
- Avoid limestone sand (decomposes at ~850°C)
- Essentially free

**Firebrick**
- Refractory ceramic for inner insulation
- Withstands 1000°C+
- Non-toxic when solid

**Mineral wool**
- Outer insulation layer
- Good thermal resistance
- Non-toxic (irritant during handling)

### Working Fluids

**Stirling engine**
- Air (simplest, lower performance)
- Nitrogen (similar to air)
- Helium (best performance, requires better sealing)

**ORC system**
- Pentane/isopentane: BP 28–36°C, flammable, low GWP
- Ethanol: BP 78°C, bio-derived, flammable
- Silicone oil (MM/MDM): 200–350°C range, very stable, non-toxic

### Sealing Materials

- Graphite: high-temp compatible, self-lubricating
- PTFE (Teflon): lower temp, excellent chemical resistance
- Silicone: flexible, moderate temp range

---

## Materials to Avoid

| Material | Reason |
|----------|--------|
| Lead | Toxic |
| Mercury | Toxic |
| Cadmium | Toxic |
| Beryllium | Toxic |
| Asbestos | Carcinogenic |
| Rare earth magnets (large qty) | Exotic, supply concerns |
| Gallium arsenide | Toxic (arsenic) |
| Cobalt (large qty) | Supply chain concerns |

---

## Sourcing Notes

- **Aluminum mirror sheet**: Industrial suppliers, solar concentrator specialty vendors
- **Sand**: Local aggregate suppliers, construction supply
- **Firebrick**: Kiln supply, refractory suppliers
- **Stainless steel**: Metal suppliers, online (McMaster-Carr, etc.)
- **Erythritol**: Food-grade bulk suppliers, Amazon
- **Pentane/ethanol**: Chemical suppliers (flammable handling required)
- **TEG modules**: Electronics suppliers, eBay, AliExpress

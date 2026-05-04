## What is the final output?

- [x] Dashboard *(interactive web UI with maps / filters / tables)*
- [ ] Annotated map / report *(static, designed to be read)*
- [ ] Notebook tool *(Jupyter notebook with parameter cells, designed to be
      opened, tweaked, re-run by the user)*
- [ ] Web tool / app
- [ ] Grasshopper component / Rhino plugin
- [ ] API service
- [ ] Other: 


> A web dashboard where a planning analyst searches for a development site address, sees predicted PM2.5 on an interactive map, picks 2-3 interventions from a ranked table, and clicks a button to download a 2-page PDF report for the planning committee.

---

## Who is the user?

*Be specific. A person with a job title and a moment of use. Not a category
("urban planners") — a person ("a capital planning analyst at the Barcelona
Urban Resilience Office, on Tuesday morning, deciding which 5 buildings get
priority retrofit funding").*

> A planning analyst at Krakow Municipal Planning Office (Biuro Planowania Przestrzennego), on Thursday morning before the weekly zoning variance meeting, reviewing a developer's application to build 200 residential units on ul. Krowoderska, deciding which green interventions to require as conditions of approval.

### What does the user already know?

*What's their professional context? What tools do they already use?*

- Reads zoning applications (addresses, site plans, number of units)
- Uses GIS software (QGIS or ArcGIS) to check land use, zoning districts, overlays
- Knows what PM2.5 is and that WHO guideline is 15 µg/m³ (Krakow regularly exceeds this)
- Familiar with Krakow geography (neighborhoods, major roads, parks)
- Writes memos for planning committee with site assessments and recommended conditions
- Does NOT know machine learning, remote sensing, or statistics beyond basic percentages

### What does the user NOT know?

*What's the gap your output fills?*

- Which specific sites have high pollution (currently checks general "Krakow air quality" websites that show city-wide averages, not site-specific)
- How much pollution reduction to expect from green interventions (currently just requires "some" green space without quantifying benefit)
- How to defend intervention requirements when developers push back in hearings (needs numbers with uncertainty ranges, not just "green space is good")

---

## The top 3 actions this output enables

*Each action should be concrete: a thing the user does after looking at
the output. "Raises awareness" is not an action. "Adds 3 buildings to
the shortlist" is.*

1. **Write the variance condition:** "Condition 1: Green corridor (60m × 100m, min. 40 trees) along ul. Krowoderska. Expected PM2.5 reduction: 4.5 µg/m³ [±2.1]" (copies from PDF report into memo template)

2. **Defend in public hearing:** Developer asks "Why require this expensive green corridor?" Analyst responds: "The site currently has predicted PM2.5 of 36 µg/m³, which is 2.4× the WHO guideline. The model predicts a green corridor reduces this by 4.5 µg/m³ with medium confidence. Here's the PDF with full methodology." (clicks Model Card link in dashboard to show limitations)

3. **Prioritize high-pollution applications:** Stack of 8 variance applications this week. Analyst clicks each address in dashboard, sees PM2.5 predictions, prioritizes the 3 in red zones (>35 µg/m³) for stricter conditions, approves the 2 in green zones (<20 µg/m³) without additional requirements.

---

## Sketch

```
┌────────────────────────────────────────────────────────────────┐
│ Krakow Air Quality - Decision Support          [Help] [Logout]│
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Search: [ul. Krowoderska 45___________] [Find]               │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ MAP (click anywhere to see prediction)                   │ │
│  │                                                           │ │
│  │        Planty Park                                        │ │
│  │        🟢🟢🟢🟢                                            │ │
│  │                                                           │ │
│  │  Old Town        ul. Krowoderska                          │ │
│  │  🟡🟡●🟡🟡           ↓                                     │ │
│  │                 🔴🔴▢🔴🔴  ← clicked site                 │ │
│  │                 🔴🔴🔴🔴🔴                                  │ │
│  │                                                           │ │
│  │  Legend: 🟢<15  🟡15-25  🟠25-35  🔴>35 µg/m³            │ │
│  │          ● Station  ▢ Selected site                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  📍 ul. Krowoderska 45                                        │
│     PM2.5: 36 µg/m³ [±8]                                      │
│     ⚠️ EXCEEDS WHO GUIDELINE (15 µg/m³)                       │
│     1.4 km to nearest station                                 │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ RECOMMENDED INTERVENTIONS (click to select)              │ │
│  ├──┬─────────────────┬──────────┬─────────────────────────┤ │
│  │☑ │Green corridor   │ -4.5 µg/m³│ [±2.1] Medium conf.    │ │
│  │☑ │Traffic calming  │ -3.2 µg/m³│ [±1.8] Medium conf.    │ │
│  │☐ │Green roofs      │ -1.8 µg/m³│ [±2.5] Low conf.       │ │
│  │☐ │New park (1 ha)  │ -2.1 µg/m³│ [±3.0] Low conf.       │ │
│  └──┴─────────────────┴──────────┴─────────────────────────┘ │
│                                                                │
│  [📄 Generate PDF Report]  [🗺️ Uncertainty Map]               │
│  [📊 Model Card - What this tool CAN'T do]                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

> **Visual layout:**
> - **Top:** Search bar (type address, hit Find, map zooms there)
> - **Center:** Interactive color-coded map (Krakow boundary, 100m cells colored by PM2.5, station markers, clicked cell highlighted)
> - **Below map:** Selected site details (address, PM2.5 number with ± range, WHO comparison, distance to validation station)
> - **Bottom:** Intervention table (checkbox to select, intervention name, predicted reduction, uncertainty, confidence level), buttons for PDF export, uncertainty map, and model card

---

## What this output is NOT

- **NOT a real-time air quality monitor.** This shows predictions based on urban form (greenness, roads, buildings), not current weather-driven pollution. It won't tell you if today is a bad air day. Use it for planning decisions (where to require interventions), not daily health alerts.

- **NOT building-scale precision.** Predictions are 100m × 100m neighborhood averages. It can't tell you "this side of the street is worse than that side" or "unit 3B has higher exposure than unit 2A." Use it to compare sites across the city, not to differentiate buildings on the same block.

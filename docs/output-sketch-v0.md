# Output Sketch v0 — What the Planner Sees

**User:** Planning analyst at Krakow Municipal Planning Office  
**Task:** Review zoning variance for new 200-unit residential development  
**Time budget:** 2 minutes to generate report for planning committee  
**Last updated:** December 2024

---

## The Scenario

Developer wants to build apartments on ul. Krowoderska (currently industrial zone). Planning analyst needs to:
1. Check if site is in a pollution hotspot
2. Pick 2-3 interventions to require as permit conditions
3. Generate PDF for Thursday's planning committee meeting

---

## Dashboard Interface (Streamlit Web App)

```
╔══════════════════════════════════════════════════════════════╗
║  Krakow Air Quality - Decision Support Tool        [Help]   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌────────────────────────────────────────────────────────┐ ║
║  │ 📍 SEARCH LOCATION                                     │ ║
║  │ [ul. Krowoderska 45____________] [Find Location]       │ ║
║  └────────────────────────────────────────────────────────┘ ║
║                                                              ║
║  ┌────────────────────────────────────────────────────────┐ ║
║  │ MAP VIEW                              [2024] [PM2.5]   │ ║
║  │                                                         │ ║
║  │   [Interactive color-coded map]                        │ ║
║  │                                                         │ ║
║  │   Legend:                                              │ ║
║  │   🟢 Good (<15)   🟡 Moderate (15-25)                 │ ║
║  │   🟠 Poor (25-35) 🔴 Unhealthy (>35 µg/m³)            │ ║
║  │                                                         │ ║
║  │   ● AQICN Station  ▢ Selected Site                    │ ║
║  └────────────────────────────────────────────────────────┘ ║
║                                                              ║
║  📍 SELECTED: ul. Krowoderska 45                            ║
║     Predicted PM2.5: 36 µg/m³ [Uncertainty: ±8]             ║
║     ⚠️  EXCEEDS WHO GUIDELINE (15 µg/m³)                    ║
║     Distance to nearest station: 1.4 km                     ║
║                                                              ║
║  ┌────────────────────────────────────────────────────────┐ ║
║  │ RECOMMENDED INTERVENTIONS                              │ ║
║  ├────┬──────────────────┬──────────┬──────────────────┬──│ ║
║  │ #  │ Intervention     │ Impact   │ Confidence       │  │ ║
║  ├────┼──────────────────┼──────────┼──────────────────┼──│ ║
║  │ 1  │ Green corridor   │ -4.5     │ Medium ±2.1      │  │ ║
║  │    │ (ul. Krowoderska)│ µg/m³    │                  │  │ ║
║  ├────┼──────────────────┼──────────┼──────────────────┼──│ ║
║  │ 2  │ Traffic calming  │ -3.2     │ Medium ±1.8      │  │ ║
║  │    │ (30 km/h zone)   │ µg/m³    │                  │  │ ║
║  ├────┼──────────────────┼──────────┼──────────────────┼──│ ║
║  │ 3  │ Green roofs 50%  │ -1.8     │ Low ±2.5         │  │ ║
║  │    │ of buildings     │ µg/m³    │                  │  │ ║
║  └────┴──────────────────┴──────────┴──────────────────┴──┘ ║
║                                                              ║
║  [📄 Generate PDF Report]  [🗺️ View Uncertainty Map]       ║
║  [📊 Model Card (limitations)]                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Map Visualization (Detailed View)

When analyst clicks on map:

```
┌──────────────────────────────────────────────────────────────┐
│              KRAKOW POLLUTION MAP (2024)                     │
│                         N ↑                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│     Planty Park (city center)                                │
│     🟢🟢🟢🟢                                                  │
│     🟢🟢🟢🟢                                                  │
│                                                              │
│  Old Town              ul. Krowoderska                       │
│  🟡🟡━━━🟡🟡                ↓                                │
│  🟡🟡 ● 🟡🟡          🔴🔴🔴━━━🔴🔴                          │
│  🟡 station🟡         🔴🔴▢🔴🔴🔴                             │
│                       🔴🔴 site 🔴                           │
│  Krowodrza            🔴🔴━━━🔴🔴                             │
│  🟠🟠🟠🟠                                                     │
│  🟠🟠●🟠🟠          Industrial Zone                           │
│   station                                                    │
│                                                              │
│  Vistula River                                               │
│  🟢🟢🟢🟢                                                     │
│  ~~~~~~~~~~                                                  │
│                                                              │
│  Click any cell → See prediction + contributing factors     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Cell Detail Popup** (when clicked):

```
┌────────────────────────────────────────┐
│ ul. Krowoderska 45                     │
│ 100m cell (50.063°N, 19.948°E)         │
├────────────────────────────────────────┤
│ PM2.5: 36 µg/m³ [±8 µg/m³]             │
│                                        │
│ Why pollution is high here:            │
│ • Road density: 4.8 km/km²             │
│   (85th percentile citywide)           │
│ • NDVI: 0.18 (very low greenness)      │
│   (15th percentile citywide)           │
│ • Building density: 62%                │
│ • Land cover: Industrial (55%)         │
│                                        │
│ Nearest monitoring station:            │
│ • 1.4 km away (Krowodrza)              │
│ • Measured PM2.5: 38 µg/m³ (2024)      │
│ • Prediction accuracy: ±8 µg/m³        │
│                                        │
│ [View Recommended Interventions]       │
└────────────────────────────────────────┘
```

---

## PDF Report (2 Pages)

### PAGE 1: Site Assessment

```
╔══════════════════════════════════════════════════════════════╗
║ MIASTO KRAKÓW                                                ║
║ Biuro Planowania Przestrzennego                             ║
║ Air Quality Impact Assessment                                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║ Development Site: ul. Krowoderska 45                         ║
║ Applicant: [Developer name]                                  ║
║ Date: 15 December 2024                                       ║
║ Prepared by: [Analyst name]                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────┐
│ SITE LOCATION & CURRENT CONDITIONS                          │
│                                                              │
│ [Map showing site highlighted in red]                        │
│                                                              │
│ Predicted Annual PM2.5: 36 µg/m³ [±8 µg/m³]                  │
│ ⚠️  EXCEEDS WHO GUIDELINE (15 µg/m³) by 2.4×                │
│                                                              │
│ Contributing Factors:                                        │
│ • High road density (4.8 km/km², 85th percentile citywide)   │
│ • Low vegetation (NDVI=0.18, only 8% green within 500m)     │
│ • Industrial land use (55% of surrounding area)              │
│ • Heavy traffic corridor (ul. Krowoderska freight route)     │
│                                                              │
│ Validation:                                                  │
│ • Nearest station: Krowodrza (1.4 km away)                   │
│ • Measured at station: 38 µg/m³ (2024 annual mean)           │
│ • Model prediction: 36 µg/m³                                 │
│ • Accuracy: Within ±5% at this location                      │
│                                                              │
│ Site Context:                                                │
│ • Zoning: Currently industrial, proposed residential         │
│ • Surroundings: Industrial warehouses (north), busy road     │
│   (west), sparse residential (south/east)                    │
│ • Population impact: ~400 new residents (200 units)          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### PAGE 2: Conditions of Approval

```
┌──────────────────────────────────────────────────────────────┐
│ RECOMMENDED ZONING CONDITIONS                                │
│                                                              │
│ VARIANCE APPROVAL CONDITIONAL ON:                            │
│                                                              │
│ 1. GREEN CORRIDOR (ul. Krowoderska)                          │
│    Area: 0.6 hectare (60m × 100m along street)               │
│    Details:                                                  │
│    • Min. 40 trees (10+ cm diameter, native species)         │
│    • Understory: Shrubs and groundcover                      │
│    • Irrigation system required                              │
│    Expected reduction: 4.5 µg/m³ [±2.1]                      │
│    Timeline: Complete before occupancy permit                │
│                                                              │
│ 2. TRAFFIC CALMING (ul. Krowoderska section)                 │
│    Area: 500m road section                                   │
│    Details:                                                  │
│    • 30 km/h speed limit                                     │
│    • Speed bumps every 100m                                  │
│    • Truck route diversion (coordinate with ZIKiT)           │
│    Expected reduction: 3.2 µg/m³ [±1.8]                      │
│    Timeline: Implemented during construction phase           │
│                                                              │
│ 3. GREEN ROOFS (50% of building roof area)                   │
│    Area: ~5,000 m² (estimated, 50% of planned roofs)         │
│    Details:                                                  │
│    • Extensive green roofs (sedum, 10cm substrate min)       │
│    • Stormwater retention integrated                         │
│    Expected reduction: 1.8 µg/m³ [±2.5]                      │
│    Timeline: Installed during construction                   │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ COMBINED EFFECT:                                             │
│ • Total predicted reduction: 9.5 µg/m³                       │
│ • Final PM2.5 estimate: 26.5 µg/m³                           │
│ • Improvement: 26% reduction from current                    │
│ • Still above WHO guideline but significant progress         │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ IMPORTANT LIMITATIONS:                                       │
│                                                              │
│ • Predictions are correlations, not guaranteed outcomes.     │
│   Actual reductions may vary ±2-3 µg/m³.                     │
│                                                              │
│ • Green corridor benefits assume mature trees (3-5 years).   │
│   Immediate benefit will be lower.                           │
│                                                              │
│ • Traffic calming assumes compliance. If truck traffic       │
│   isn't actually diverted, benefit will be minimal.          │
│                                                              │
│ • Model based on 10 monitoring stations citywide.            │
│   This site is 1.4 km from nearest station. Prediction       │
│   uncertainty is ±8 µg/m³ (22% relative error).              │
│                                                              │
│ • New residents will add ~150 cars. If most drive instead    │
│   of using transit, pollution may increase despite           │
│   green interventions. Encourage transit access.             │
│                                                              │
│ For methodology details: [link to model card]                │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ RECOMMENDATION:                                              │
│                                                              │
│ Approve variance with Conditions 1-3 as mandatory.           │
│                                                              │
│ Rationale: Site is in high-pollution area. Without           │
│ mitigation, adding 400 residents would expose vulnerable     │
│ populations (children, elderly) to unhealthy air quality.    │
│ Interventions reduce but don't eliminate risk. Conditions    │
│ are proportional to impact.                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Signed: ________________________    Date: ________________
        [Planning analyst]

Reviewed: ______________________    Date: ________________
          [Department head]
```

---

## User Workflow (Step-by-Step)

**Time: 2 minutes total**

1. **Open dashboard** (15 seconds)
   - URL: `https://krakow-air-quality.streamlit.app`
   - Bookmarked in browser, loads instantly

2. **Search location** (20 seconds)
   - Type "ul. Krowoderska 45" in search box
   - Click "Find Location"
   - Map zooms to site, shows red/orange colors (high pollution)

3. **Review prediction** (30 seconds)
   - Popup shows: PM2.5 = 36 µg/m³ ±8
   - Analyst notes: "Above WHO guideline, moderate confidence"
   - Scroll to intervention table

4. **Select interventions** (30 seconds)
   - Interventions auto-ranked by impact
   - Analyst checks top 3 (green corridor, traffic calming, green roofs)
   - Total reduction: 9.5 µg/m³

5. **Generate report** (25 seconds)
   - Click "Generate PDF Report"
   - PDF downloads: `Krowoderska_45_Report_2024-12-15.pdf`
   - 2 pages, ready to attach to planning committee memo

**Done. Total: 2 minutes.**

---

## Alternative Views

### Uncertainty Map

Click "View Uncertainty Map" to see where predictions are reliable:

```
┌──────────────────────────────────────────────────────────────┐
│ PREDICTION UNCERTAINTY MAP                                   │
│                                                              │
│ Legend:                                                      │
│ 🟩 High confidence (<±5 µg/m³)    - Near monitoring stations │
│ 🟨 Medium confidence (±5-15 µg/m³) - 1-2 km from stations    │
│ 🟥 Low confidence (>±15 µg/m³)     - Suburbs, >2 km from any │
│                                                              │
│ [Map showing green around 10 station locations, yellow in    │
│  center city, red in suburbs]                                │
│                                                              │
│ Note: Most variance applications are in central city         │
│ (yellow/green zones). Suburban applications (red zones)      │
│ require extra scrutiny.                                      │
└──────────────────────────────────────────────────────────────┘
```

### Model Card (Limitations)

Click "Model Card" to see what the tool can't do:

```
┌──────────────────────────────────────────────────────────────┐
│ MODEL CARD - LIMITATIONS                                     │
│                                                              │
│ This tool CANNOT:                                            │
│                                                              │
│ ✗ Predict pollution at building-scale (<100m)                │
│   → Only neighborhood-scale (100m grid)                      │
│                                                              │
│ ✗ Prove interventions will work                             │
│   → Correlations only, not causal proof                      │
│                                                              │
│ ✗ Account for future traffic changes                        │
│   → Based on 2019-2024 data, before Low Emission Zone       │
│                                                              │
│ ✗ Validate predictions >2km from monitoring stations        │
│   → 40% of city has high uncertainty                         │
│                                                              │
│ ✗ Distinguish pollution sources (traffic vs heating)        │
│   → Measures total PM2.5 only                                │
│                                                              │
│ Example Failure Case:                                        │
│ • Location: Old Town narrow street                           │
│ • Predicted: 28 µg/m³                                        │
│ • Actual: 52 µg/m³                                           │
│ • Why failed: Tall buildings create "street canyon" effect   │
│   (pollution trapped), but model doesn't know building       │
│   heights. Underestimated by 46%.                            │
│                                                              │
│ For full methodology: [link to GitHub repo]                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Design Principles

**1. Scannable, not readable**
- Color-coded map = instant visual (red = bad, green = good)
- Numbers in table, sortable
- ⚠️ symbols for WHO exceedances

**2. Uncertainty is visible**
- Every prediction shows ±range
- Not buried in footnotes
- Model limitations on page 2 of PDF

**3. Actionable**
- Output is ranked interventions (what to do)
- Not data dump, not technical jargon
- PDF export prominent (that's what goes to committee)

**4. Fast**
- 2-minute workflow (meets success criterion)
- No login required
- No complex menus

---

## Success Metrics

**Quantitative:**
- ✓ Task completion <2 minutes
- ✓ 0 support tickets in first month (UI is self-explanatory)
- ✓ PDF generated, not hand-typed reports

**Qualitative (what we'll ask users):**
- "Does this save you time vs previous process?"
- "Do you trust the predictions enough to defend in hearings?"
- "Are the limitations clear?"

**Red flags (means we need to redesign):**
- Analyst ignores uncertainty warnings
- Analyst exports to Excel to do own analysis (UI missing functionality)
- >5 support calls per month (UI confusing)

---

## Technical Implementation Notes

**Dashboard:** Streamlit (Python)
```python
import streamlit as st
import folium

# Map
m = folium.Map(location=[50.06, 19.94], zoom_start=12)
# Add pollution layer (GeoTIFF overlay)
# Add station markers
# Add click handler → show popup

st_folium(m)  # Render in Streamlit

# Intervention table
st.dataframe(interventions)

# PDF generation
if st.button("Generate PDF"):
    pdf = generate_report(location, interventions)
    st.download_button("Download", pdf)
```

**PDF:** ReportLab or WeasyPrint
- Template: HTML → PDF conversion
- Include: Map screenshot, intervention table, limitations

**Hosting:** Streamlit Cloud (free tier)
- GitHub repo auto-deploys
- URL: krakow-air-quality.streamlit.app
- No server management needed

---

## Future Enhancements (Not MVP)

**Phase 2:**
- Side-by-side comparison (current vs with interventions)
- Mobile-responsive (field use on tablets)
- Cost optimizer ("I have €200k budget, what's best combo?")

**Phase 3:**
- Real-time updates (connect to live AQICN API)
- Historical trends (show how site pollution changed 2019-2024)
- Multi-language (Polish + English versions)

---

## Bottom Line

**Will this actually get used?**

Yes, if:
- It's faster than current process (manual research → 2 hours, tool → 2 minutes)
- Predictions are defensible (model card shows we're honest about limits)
- PDF output looks professional (can attach to official documents)

No, if:
- UI is confusing (people will ignore it)
- Predictions are obviously wrong (loses trust)
- PDF looks amateurish (embarrassing to present to committee)

**Our job in Session 3:**
Build the simplest version that works. Fancy features come later. Focus on:
1. Map loads fast
2. Predictions look reasonable
3. PDF is clean and professional

**Test with real user:** Show to one planning analyst before official launch. Get feedback. Fix obvious problems.

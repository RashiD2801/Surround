# Problem Brief — Krakow Air Quality & Urban Form

## The Environmental Question

**Which specific urban form characteristics (building density, road network configuration, green space distribution) predict fine particulate matter (PM2.5) concentrations at 100-meter resolution in Krakow's residential districts, and by how much?**

**Your question:**
Quantifying the relationship between measurable urban features (e.g., "% green cover within 500m radius") and measured PM2.5 levels (µg/m³), with prediction uncertainty bounds.

---

## The Design Decision This Supports


**Decision point:** Quarterly zoning variance reviews for new residential developments

**Your decision:**

When a developer requests permission to build in a high-pollution area, planning officers use our tool to:
1. Identify the predicted PM2.5 level at the proposed site (with uncertainty range)
2. Select 2-3 urban form interventions (green corridors, traffic calming, green roofs) that would reduce pollution by the largest amount
3. Attach these interventions as mandatory conditions in the building permit

---

## The Intended User

**Your user:**
Krakow Municipal Planning Office (Biuro Planowania Przestrzennego)

**Secondary users (informational only, not decision makers):**
- Climate activists → use our open data/code for advocacy
- Architectural firms → consult tool during early design phase
- Academic researchers → cite our methodology in papers

---

## Measurable Success Criteria

>1. Reproducibility
 User can clone the repo on your laptop, run the code, and produces the final output in <30 minutes without asking us questions

>2. Model Performance
Leave-one-station-out cross-validation achieves R² ≥ 0.40 (explains ≥40% of PM2.5 variance).


>3. Spatial Precision
Predictions made at 10-meter resolution

>4. Actionable Output
A web dashboard where you can pick an area and within 2 minutes see:
- Predicted PM2.5: 38 µg/m³ [95% CI: 32-44]
- Top 3 interventions ranked by pollution reduction
- One-click "Generate Report" button → PDF downloads

>5. Transparency
Non technical professionist reads the model card and can correctly state 3 limitations in a public hearing when challenged by a developer.

---

## Risks and Open Questions


**Risks:**

- Innacurate/Missing Data points 
- Overfitting 
- Obstruction of urban spaces while using Satellite images 
- Spare validation data



**Open questions for next session:**

- How to clean data
- How to create synthetic data for missing data points 
- How to combine data from satellite data with geograpical co-ordinates 
- How to develop a reliable confidence score 
- How to divide tasks for this project 


---

## Out of Scope

- Other pollutants: NO₂, SO₂, O₃, PM10 excluded. PM2.5 only (WHO priority pollutant, best data coverage).

- Other cities: Krakow only. No Warsaw, Gdańsk, Wrocław comparisons. (Reason: Insufficient time to validate cross-city generalization. Each city has different industrial mix, topography, weather patterns.)

- Health impact assessment: No epidemiology (asthma rates, mortality). We predict PM2.5 concentrations, not health outcomes. (Reason: Different expertise required, outside project scope.)

- Real-time predictions: No live dashboard updating hourly with new satellite images. 

- Cost-benefit analysis: We quantify pollution reduction (µg/m³), not economic ROI (€ saved per € invested). 

- Building-scale resolution: 100m grid cells (city planning scale), not individual buildings.

- Policy advocacy: We provide technical analysis, not policy recommendations. 

---

## Team

| Mafia | Role on this project |
|---|---|
| [Rim] | [] |
| [Martina] | [] |
| [Rashi] | [] |
| [Bhavana] | [] |

> Roles are loose — they help you divide work, not lock you in. Everyone
> reads everyone's code. Everyone defends every line.

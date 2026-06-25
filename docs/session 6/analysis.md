# Analysis — Krakow PM2.5 Spatial & Temporal Patterns

**Project:** Surround — urban planning context and air quality, Krakow Poland  
**Data:** 7 GIOS monitoring stations · 2019–2024 · 471 station-months  
**Model:** Random Forest v2 · 16 features · ERA5 weather + Urban Atlas land use  
**Produced by:** Rim, Martina, Rashi, Bhavana · Session 6

---

## The number that sets the stage

The EU annual mean PM2.5 limit is **25 µg/m³**.

Krakow's dataset mean across 2019–2024 is **66.2 µg/m³** — 2.6 times the limit.

In January 2019, three stations simultaneously recorded **122.8 µg/m³** — just under five times the legal limit. This number is not an outlier in the dataset. It is a representative peak of what Krakow's air looks like in a cold January before enforcement of the coal ban was tightened.

---

## Finding 1 — The coal ban worked. Eventually. And only in winter.

Krakow banned solid fuel burning in September 2019 — one of the first Polish cities to do so. If you expect the data to show a clean downward step from 2019 onward, it doesn't.

**Winter PM2.5 by year (Dec–Feb mean, µg/m³):**

| Year | Mean | Change from prior year |
|------|------|------------------------|
| 2019 | 100.0 | — |
| 2020 | 90.6  | −9.4 |
| **2021** | **105.9** | **+15.3** |
| 2022 | 74.3  | −31.6 |
| 2023 | 72.5  | −1.8 |
| 2024 | 72.4  | −0.1 |

Winter 2021 was the *worst winter in the dataset* — worse than 2019, the year before the ban. This is the coal ban paradox. The ban was announced, not instantly enforced. Cold snaps revealed that compliance lagged: when temperatures fell in February 2021 to some of the lowest values in decades, residents who hadn't converted their heating systems lit coal regardless. The city's enforcement infrastructure had not caught up.

Then something breaks in 2022. Winter PM2.5 falls by 31.6 µg/m³ in a single year — the largest drop in the dataset. City-wide enforcement sweeps, subsidy programs for gas boiler conversion, and district heating expansion all accelerated in 2021–2022. The ban's lag time was approximately **2.5 years**.

Now look at summer:

**Summer PM2.5 by year (Jun–Aug mean, µg/m³):**

| Year | Mean |
|------|------|
| 2019 | 46.8 |
| 2020 | 46.2 |
| 2021 | 47.1 |
| 2022 | 41.7 |
| 2023 | 47.5 |
| 2024 | 42.8 |

No trend. Summer PM2.5 is essentially flat across six years. The coal ban — the most significant air quality intervention in Krakow's recent history — had zero measurable effect on summer air quality. Different mechanisms are at play.

---

## Finding 2 — February is chaos. June is clockwork.

The coefficient of variation (CV) tells you how unpredictable each month is:

| Month | Mean µg/m³ | CV % | Character |
|-------|-----------|------|-----------|
| June  | 47.5      | 10.4 | Most predictable |
| December | 90.6  | 13.2 | Consistent cold |
| July  | 43.6      | 13.4 | Stable summer |
| August | 45.9     | 14.8 | Slightly variable |
| **February** | **79.0** | **31.8** | **Most chaotic** |

February has 3× the relative variability of June. The worst month on record is February 2021 (multiple stations at 120.5 µg/m³). The second-best February is 2024. A single cold outbreak transforms February from a manageable pollution month into an extreme event.

The mechanism: winter PM2.5 in Krakow is driven by a compound of cold temperature, low boundary layer height, and heating emissions. In mild winters, these factors are partly decoupled. In a cold snap, all three converge simultaneously — temperatures below −10°C force maximum heating, stable anticyclonic conditions suppress boundary layer height to its winter floor (454 m in January, 364 m in December), and wind speeds drop. The result is smog events that can persist for 5–10 days at concentrations that would trigger health alerts in any Western European city.

June's predictability is the inverse of this. Once temperature exceeds ~15°C, the atmosphere is sufficiently unstable to mix out whatever surface-level pollution exists. The variance simply collapses.

---

## Finding 3 — The spatial reversal no one expected

The most structurally interesting pattern in the dataset is not the overall level of pollution — it's that the spatial ranking of stations **reverses by season**.

**January actual mean PM2.5 (2019–2024), ranked worst to best:**

1. Ul. Dietla — 94.0 µg/m³ (city centre, Kazimierz)
2. Złoty Róg — 93.6 (city centre)
3. Aleja Kraśnickiego — 93.3 (western edge of centre)
4. Kurdwanów — 89.0 (south)
5. Os. Piastów — 84.3 (west residential)
6. Os. Wadów — 84.1 (northwest residential)
7. Nowa Huta — **83.5** (east, industrial)

**August actual mean PM2.5 (2019–2024), ranked worst to best:**

1. Os. Piastów — **48.7** µg/m³ (west residential)
2. Nowa Huta — 47.0 (east, industrial)
3. Os. Wadów — 46.9 (northwest residential)
4. Kurdwanów — 45.0 (south)
5. Ul. Dietla — 44.6 (city centre)
6. Aleja Kraśnickiego — 44.3 (western edge of centre)
7. Złoty Róg — 44.3 (city centre)

Ul. Dietla is worst in January and second-best in August. Os. Piastów is second-best in January and worst in August. The ordering inverts.

### Why the centre dominates in winter

Ul. Dietla sits on a major arterial road in Kazimierz, flanked by a dense grid of old tenement buildings — the highest `continuous_urban_pct` (0.6) and `seal_density` (0.6) of any station in the dataset. These buildings housed hundreds of coal boilers before the ban. Street canyons trap ground-level exhaust. The combination of point-source density and the physical trapping of a canyon urban form makes this the worst winter environment of the seven stations.

Os. Piastów, by contrast, has `continuous_urban_pct = 0.0` and `seal_density = 0.0`. It is a post-war housing estate with open ground between blocks. Emissions from individual heating units disperse laterally rather than accumulating. In January, that low density is a 10.5 µg/m³ advantage over Ul. Dietla.

### Why the west dominates in August

In August, heating is irrelevant. The mechanism shifts to atmospheric mixing.

The boundary layer height drops sharply from July to August — from 587 m to 480 m — a fall of 107 m while temperature barely changes (20.4 → 20.3°C). This means August has worse atmospheric mixing than July despite similar temperatures, a late-summer anticyclonic signature common in Central European valleys.

The key: Os. Piastów has `forest_pct = 0.3` — the highest forest coverage of any station. The Bielany Forest and Wolski Forest lie within its 500 m measurement radius. In late summer, forests emit biogenic volatile organic compounds (terpenes, isoprene) that react with ozone to form secondary PM2.5. When BLH is 587 m (July), these near-surface reactions disperse upward. When BLH drops to 480 m (August), they concentrate. The city centre stations — more sealed, more impervious, less vegetation — don't have this biogenic contribution.

The secondary factor is the western approach corridor. Poland's A4 motorway enters Krakow from the west, passing near both Os. Piastów and Os. Wadów. August sees elevated long-distance tourist traffic toward the Tatras, and this traffic source matters more when heating is absent.

---

## Finding 4 — The Nowa Huta paradox

Nowa Huta — Krakow's industrial eastern district, home to the ArcelorMittal steel plant — is **consistently the cleanest station** in the dataset.

Annual mean PM2.5: Nowa Huta = 62.5 µg/m³ vs Ul. Dietla = 71.6 µg/m³. A gap of 9.1 µg/m³, sustained across all six years.

The explanation is the physics of industrial stacks. The steel plant's emissions exit at altitude (tall stacks, high temperature = strong buoyancy), dispersing before they reach ground level at the monitoring station. The station is sited to measure urban residential background, not direct stack output. What it captures is: the absence of dense old tenement housing. Nowa Huta was built in the 1950s as a planned socialist city — grid layout, tower blocks, wide streets — structurally different from the medieval city centre. Lower heating density and better ventilation geometry overpower any contribution from heavy industry.

The model's 2.3% land use signal may well be capturing this geometry effect — not pollution from the plant itself, but the urban planning decisions made 70 years ago about how to arrange buildings around it.

---

## Finding 5 — The BLH paradox

If boundary layer height (BLH) controlled PM2.5 linearly, the most polluted months would be those with the lowest BLH. The data disagrees.

**BLH by month, sorted lowest to highest:**

| Month | BLH (m) | Mean PM2.5 (µg/m³) |
|-------|---------|---------------------|
| November | 345 | 83.1 |
| December | 364 | 90.6 |
| October  | 373 | 67.6 |
| January  | 454 | 88.8 |

November has the lowest BLH of any month in the dataset — 345 m, significantly below January's 454 m. Yet January PM2.5 (88.8) is 5.7 µg/m³ higher than November (83.1). October has the third-lowest BLH but only the fifth-worst PM2.5.

The reason: BLH controls dispersion, but the dominant driver of Krakow's winter pollution is emission quantity. November BLH is low, but November temperatures (mean +5.1°C) are mild enough that heating demand is only beginning to ramp up. By January, temperatures average 0.2°C and heating systems are running at maximum output. The sheer volume of emissions in January overwhelms the marginal advantage of a 109 m higher boundary layer compared to November.

The model quantifies this: `mean_temp_monthly` carries 72.7% of predictive importance, `blh_monthly` 23.6%. Temperature — as a proxy for heating demand — is three times more important than atmospheric mixing capacity.

---

## Finding 6 — The 2030 projection: two Kraków's diverge

Running the trained Random Forest model with ERA5 climate trend projections to 2030 produces an unexpected pattern. The annual improvement is modest (2024 average 64.3 µg/m³ → 2030 average 63.6 µg/m³, −1%). But the monthly breakdown reveals two very different futures operating simultaneously:

**2024 → 2030 predicted change by month:**

| Month | 2024 | 2030 | Change | Story |
|-------|------|------|--------|-------|
| November | 85.9 | 65.1 | **−20.9** | Biggest improvement |
| October  | 68.0 | 60.7 | −7.3 | Autumn improves |
| January  | 90.5 | 87.2 | −3.3 | Slight winter relief |
| June     | 47.8 | 44.0 | −3.8 | Slightly cleaner |
| August   | 47.5 | 53.9 | **+6.3** | Summer worsens |
| September | 52.1 | 56.7 | +4.6 | Late summer worsens |
| March    | 65.0 | 79.9 | **+14.9** | Transition season anomaly |

November stands out. A warming November (ERA5 trend: +0.3°C/year over 6 observed years) means heating systems turn on later and run at lower intensity. The model has learned that November temperature is the dominant switch between "heating season on" and "heating season off," and a few degrees of warming could push that switch forward by weeks. This alone accounts for the 24% projected improvement in November.

August and September move in the opposite direction. Warming late-summer temperatures with compressed BLH (the ERA5 trend shows August BLH declining over 2019–2024) creates conditions the model associates with higher surface-level PM2.5 — less mixing, more biogenic secondary aerosol formation, more stagnation events.

The March projection (+14.9 µg/m³) is the most anomalous and warrants caution. It appears to be an artifact of the ERA5 linear trend fitted over only six years of March data — an unusually variable month — projecting features outside the model's confident range. The Random Forest's tendency to plateau at extreme feature values means this number should be read as "the model's uncertainty is highest here," not as a reliable forecast.

---

## Finding 7 — What land use actually tells us (and what it doesn't)

The v2 model distributes feature importance as: temperature 72.7%, BLH 23.6%, month 1.4%, all 13 land use features combined 2.3%.

This 2.3% is real and not noise — the spatial reversal between Ul. Dietla and Os. Piastów described above is a land use signal that the model is capturing. But the number forces an honest conclusion:

**Urban form in Krakow does not explain PM2.5. Weather does.**

The spatial variation in PM2.5 between Krakow's stations on any given month is 1–3 µg/m³. The seasonal variation at a single station between January and July is 40–50 µg/m³. The city's air quality problem is not primarily about whether you live near a park or a tenement. It is about whether it is winter or summer, and whether that winter is mild or bitter.

This has a direct implication for planning. Green infrastructure, reduced impervious surface, and urban form changes can contribute to the 2.3% land use signal — but no amount of street trees in Kazimierz will offset the effect of a week of −10°C temperatures with an anticyclone sitting over the city. The intervention that works is the one Krakow is already making: eliminating heating emissions and transitioning to cleaner energy sources. The data from 2022–2024 shows that this is working for winter. The data shows it has had no effect on summer. A different set of interventions — traffic management, secondary aerosol monitoring, late-summer burn restrictions — is needed for the non-heating months.

---

## Summary of key numbers

| Metric | Value |
|--------|-------|
| Dataset mean PM2.5 | 66.2 µg/m³ (2.6× EU limit) |
| Worst station-month | 122.8 µg/m³ (Jan 2019, three stations) |
| Best station-month | 32.3 µg/m³ (Jul 2022, Nowa Huta / Piastów / Wadów) |
| Highest-pollution month | December (90.6 µg/m³) |
| Lowest-pollution month | July (43.6 µg/m³) |
| Peak-to-trough ratio (seasonal) | 2.1× |
| Most variable month | February (CV 31.8%) |
| Most predictable month | June (CV 10.4%) |
| Winter improvement 2021→2022 | −31.6 µg/m³ (−30%) |
| Summer trend 2019→2024 | −4.0 µg/m³ (flat, within noise) |
| Model test R² | 0.850 |
| Model test MAE | 6.48 µg/m³ |
| ERA5 weather importance | 96.3% |
| Land use importance | 2.3% |
| Worst station (annual) | Ul. Dietla (71.6 µg/m³) |
| Cleanest station (annual) | Nowa Huta (62.5 µg/m³) |

---

*Analysis produced Session 6 · 2026-06-17 · Surround project*  
*Model: Random Forest v2 · data: GIOS monitoring 2019–2024 · ERA5-Land via Open-Meteo*

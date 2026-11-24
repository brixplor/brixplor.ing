[![brixplor.ing logo](images/brixplor_logomintext.svg)](index.llms.md)

Projects: [Fuel Burden ⛽](mpg.llms.md)

# Driving? In this economy!?

With elevated fuel costs hanging over society, how much does your daily commute actually eat into your household budget? Select any vehicle from 1984 to the present and compare historical fuel prices across the United States from 1993 to 2025.

We define a household’s annual fuel burden as a portion of the household’s income as estimated by ($\text{Burden}_{i,t}$) in *state* ($i$) and *year* ($t$):

$$\text{Burden}_{i,t} = \frac{\left(\frac{\text{Mileage}}{\text{MPG}}\right) \times P_{\text{gas}_{i, t}}}{\text{Median Income}_{i,t}} \times 100$$

## What does a mile cost?

Select your vehicle of interest to find its combined fuel efficiency in highway and city driving. Input annual mileage in a certain state and year to calculate the cost of fuel for the selected vehicle.

There are no limits on your selections! Try selecting a fuel efficient modern vehicle in the 1990s to see how far your current fuel budget would get you.

``` js
Plotly = require("https://cdn.plot.ly/plotly-2.35.2.min.js")

// Load datasets (using DuckDB Parquet or JSON)
mpgData = FileAttachment("data/mpg_clean.json").json()
fredData = FileAttachment("data/fred_state_macro.json").json()

stateNames = ({
  "US": "United States",
  "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
  "CO": "Colorado", "CT": "Connecticut", "DC": "District of Columbia", "DE": "Delaware",
  "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
  "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
  "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
  "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
  "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
  "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
  "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
  "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
  "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
})

// 1. Select Vehicle for Fuel Efficiency (MPG)
vehicleYears = Array.from(new Set(mpgData.map(d => d.year))).sort((a, b) => b - a)
viewof selCarYear = Inputs.select(vehicleYears, {
  label: "Vehicle Year",
  value: 2020,
  format: d => `${d}`
})

availableMakes = Array.from(
  new Set(mpgData.filter(d => d.year === selCarYear).map(d => d.make))
).sort()
viewof selMake = Inputs.select(availableMakes, {label: "Make"})

availableModels = Array.from(
  new Set(mpgData.filter(d => d.year === selCarYear && d.make === selMake).map(d => d.model))
).sort()
viewof selModel = Inputs.select(availableModels, {label: "Model"})

selectedCar = mpgData.find(
  d => d.year === selCarYear && d.make === selMake && d.model === selModel
) || {comb08: 25}
vehicleMpg = selectedCar.comb08

// Making a slider to selecte fuel year that selects a random year upon initialization
// Sort ascending so [0] is 1993 and [length - 1] is 2025
macroYears = Array.from(new Set(fredData.map(d => d.year))).sort((a, b) => a - b)

// Custom Fuel Price Year Slider (initializes to a random year on every page load)
viewof selFuelYear = {
  const minYear = macroYears[0];
  const maxYear = macroYears[macroYears.length - 1];
  const randomStart = macroYears[Math.floor(Math.random() * macroYears.length)];

  const container = html`<div class="year-slider-card">
    <div class="year-slider-title">Fuel Price Year</div>
    <div class="year-slider-wrap">
      <input
        type="range"
        class="year-slider-input"
        min="${minYear}"
        max="${maxYear}"
        step="1"
        value="${randomStart}"
        aria-label="Fuel Price Year"
      />
      <div class="year-slider-endpoints">
        <span class="min-lbl">${minYear}</span>
        <span class="max-lbl">${maxYear}</span>
      </div>
      <div class="year-slider-active-label">${randomStart}</div>
    </div>
  </div>`;

  const input = container.querySelector("input");
  const activeLbl = container.querySelector(".year-slider-active-label");
  const minLbl = container.querySelector(".min-lbl");
  const maxLbl = container.querySelector(".max-lbl");

  const syncLabel = (val) => {
    const pct = ((val - minYear) / (maxYear - minYear)) * 100;
    // Offset slightly for the 18px thumb width so label stays centered under the thumb
    activeLbl.style.left = `calc(${pct}% + (${9 - pct * 0.18}px))`;
    activeLbl.textContent = `${val}`;
    // Fade endpoint labels when thumb is right next to them to avoid text overlap
    minLbl.style.opacity = val - minYear <= 2 ? "0.15" : "1";
    maxLbl.style.opacity = maxYear - val <= 2 ? "0.15" : "1";
  };

  container.value = randomStart;
  syncLabel(randomStart);

  input.addEventListener("input", (e) => {
    e.stopPropagation();
    const val = Number(input.value);
    container.value = val;
    syncLabel(val);
    container.dispatchEvent(new Event("input", { bubbles: true }));
  });

  return container;
}

stateCodes = Array.from(new Set(fredData.filter(d => d.state_code !== "US").map(d => d.state_code))).sort()
viewof selState = Inputs.select(stateCodes, {
  label: "Inspect State",
  value: "CA",
  format: code => `${stateNames[code] || code} (${code})`
})

viewof annualMiles = Inputs.number([1000, 100000], {
  step: 500,
  value: 12000,
  label: "Annual Mileage (mi/yr)"
})

// 4. Weekly Mileage & Gallons Consumed per Week
weeklyMiles = annualMiles / 52
weeklyGallons = weeklyMiles / vehicleMpg
```

``` js
// Render the 2-Row Setup & Weekly Breakdown Summary
html`
<div class="calc-row">
  <div>
    <strong>1. Select vehicle for fuel efficiency (MPG):</strong>
    <div class="dropdown-row">
      ${viewof selCarYear}
      ${viewof selMake}
      ${viewof selModel}
    </div>
  </div>
  <div>
    <p class="result-line">
      Combined Fuel Efficiency: <span class="stat-pill">${vehicleMpg.toFixed(1)} MPG</span>
    </p>
  </div>
</div>

<div class="calc-row">
  <div>
    <strong>2 & 3. Select annual mileage & year of fuel costs:</strong>
    <div class="dropdown-row">
      ${viewof annualMiles}
      ${viewof selState}
    </div>
  </div>
  <div>
    <p class="result-line">
      Weekly Driving Rate: <span class="stat-pill">${weeklyMiles.toFixed(1)} mi/wk</span>
      (<span class="stat-pill">${weeklyGallons.toFixed(2)} gal/wk</span>)
    </p>
  </div>
</div>
`
```

## Annual Fuel Burden as a Share of Median Income

``` js
getPriceSum52 = (row) => (row.price_sum_52wk !== undefined ? row.price_sum_52wk : row.gas_price * 52)

// 5. Calculate Summed Fuel Cost & % of Median Income for all 50 States + DC
yearStateRows = fredData
  .filter(d => d.year === selFuelYear && d.state_code !== "US")
  .map(d => {
    const priceSum52 = getPriceSum52(d);
    const summedFuelCost = priceSum52 * weeklyGallons;
    const incomePct = (summedFuelCost / d.median_income) * 100;
    return {
      ...d,
      state_name: stateNames[d.state_code] || d.state_code,
      summed_cost: summedFuelCost,
      income_pct: incomePct
    };
  })

// National ("US") Benchmark Stats for Top Side Card
usRow = fredData.find(d => d.year === selFuelYear && d.state_code === "US") || {
  gas_price: 3.50,
  price_sum_52wk: 3.50 * 52,
  median_income: 75000
}
usSummedCost = getPriceSum52(usRow) * weeklyGallons
usIncomePct = (usSummedCost / usRow.median_income) * 100

// Selected State Stats for Bottom Side Card
sideState = yearStateRows.find(d => d.state_code === selState) || yearStateRows[0]
```

``` js
html`${viewof selFuelYear}`
```

``` js
mapShell = {
  const container = html`<div class="map-layout">
    <div id="choropleth-map"></div>
    <div class="side-cards-stack">
      <div id="national-card-slot" class="side-card national-card"></div>
      <div id="state-card-slot" class="side-card state-card"></div>
    </div>
  </div>`;

  const mapDiv = container.querySelector("#choropleth-map");

  mapDiv.onEditReady = () => {
    mapDiv.on("plotly_click", function(data) {
      if (!data.points || !data.points.length) return;
      const clickedState = data.points[0].location;
      if (clickedState) {
        viewof selState.value = clickedState;
        viewof selState.dispatchEvent(new Event("input", {bubbles: true}));
      }
    });

    mapDiv.on("plotly_hover", function(data) {
      if (!data.points || !data.points.length) return;
      const hoveredState = data.points[0].location;
      const currentSelected = viewof selState.value;
      const locArray = (hoveredState && hoveredState !== currentSelected) ? [hoveredState] : [];
      const zArray = locArray.length ? [1] : [];
      Plotly.restyle(mapDiv, { locations: [locArray], z: [zArray] }, [1]);
    });

    mapDiv.on("plotly_unhover", function() {
      Plotly.restyle(mapDiv, { locations: [[]], z: [[]] }, [1]);
    });
  };

  return container;
}
```

``` js
// 2. Reactive Update for the Two Stacked Side Cards (National + Selected State)
{
  const natSlot = mapShell.querySelector("#national-card-slot");
  const stateSlot = mapShell.querySelector("#state-card-slot");
  const vehicleLabel = `${selCarYear} ${selMake} ${selModel}`;

  // Top Card: National Stats (Matches top box in sketch)
  natSlot.innerHTML = `
    <h4 style="margin-top:0; color:#139ddd; border-bottom: 2px solid #139ddd; padding-bottom: 0.35rem;">
      U.S. National Benchmark (${selFuelYear})
    </h4>
    <p style="margin-bottom:0;">
      The average driver of a <strong>${vehicleLabel}</strong> in the U.S. spent
      <span class="stat-pill">$${usSummedCost.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
      in <span class="stat-pill">${selFuelYear}</span>. This represents
      <span class="stat-pill">${usIncomePct.toFixed(2)}%</span> of the nation's
      median income (<span class="stat-pill">$${usRow.median_income.toLocaleString()}</span>).
    </p>
  `;

  // Bottom Card: Selected State Stats (Matches bottom box in sketch)
  stateSlot.innerHTML = `
    <h4 style="margin-top:0; color:#dd5313; border-bottom: 2px solid #dd5313; padding-bottom: 0.35rem;">
      ${sideState.state_name} (${selFuelYear})
    </h4>
    <p style="margin-bottom:0.5rem;">
      The average driver in <span class="stat-pill">${sideState.state_name}</span> spent
      <span class="stat-pill">$${sideState.summed_cost.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
      in <span class="stat-pill">${selFuelYear}</span>. This represents
      <span class="stat-pill">${sideState.income_pct.toFixed(2)}%</span> of median income
      (<span class="stat-pill">$${sideState.median_income.toLocaleString()}</span>).
    </p>
    <small style="color:#666;">💡 Click any state on the map to update this card.</small>
  `;
}
```

``` js
// 3. Reactive Choropleth Update (Preserves zoom & highlights selected/hovered state)
{
  const mapDiv = mapShell.querySelector("#choropleth-map");
  const isMobile = window.innerWidth < 768;

  const hoverTemplate =
    "<b>%{customdata[0]}</b><br>" +
    "Summed 52-wk fuel cost (%{customdata[1]}): <b>$%{customdata[3]:,.0f}</b><br>" +
    "Share of median income ($%{customdata[4]:,.0f}): <b>%{z:.2f}%</b><extra></extra>";

  const maxIncomePct = Math.max(...yearStateRows.map(d => d.income_pct));
  const minIncomePct = Math.min(...yearStateRows.map(d => d.income_pct));

  const baseTrace = {
    type: "choropleth",
    locationmode: "USA-states",
    locations: yearStateRows.map(d => d.state_code),
    z: yearStateRows.map(d => d.income_pct),
    zmin: minIncomePct,
    zmax: maxIncomePct,
    colorscale: [
      [0.0, "#2ca02c"],    // Low %: Green
      [0.5, "#f4d03f"],    // Mid %: Yellow
      [1.0, "#d62728"]     // High %: Red
    ],
    marker: { line: { color: "#ffffff", width: 0.75 } },
    colorbar: isMobile
      ? {
          title: { text: "% of Income", side: "top" },
          ticksuffix: "%",
          orientation: "h",
          y: -0.05,
          x: 0.5,
          xanchor: "center",
          len: 0.85,
          thickness: 12
        }
      : {
          title: { text: "% of Income" },
          ticksuffix: "%",
          len: 0.85,
          thickness: 16
        },
    customdata: yearStateRows.map(d => [
      d.state_name,
      d.year,
      d.gas_price,
      d.summed_cost,
      d.median_income
    ]),
    hovertemplate: hoverTemplate
  };

  const hoverOutlineTrace = {
    type: "choropleth",
    locationmode: "USA-states",
    locations: [],
    z: [],
    colorscale: [[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
    showscale: false,
    hoverinfo: "skip",
    marker: { line: { color: "#808080", width: 2.5 } }
  };

  const selectedOutlineTrace = {
    type: "choropleth",
    locationmode: "USA-states",
    locations: selState ? [selState] : [],
    z: selState ? [1] : [],
    colorscale: [[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
    showscale: false,
    hoverinfo: "skip",
    marker: { line: { color: "#000000", width: 3 } }
  };

  const layout = {
    uirevision: "keep-zoom-state",
    geo: {
      scope: "usa",
      projection: { type: "albers usa" },
      bgcolor: "rgba(0,0,0,0)",
      uirevision: "keep-zoom-state"
    },
    margin: { l: 0, r: 0, t: 10, b: isMobile ? 45 : 0 },
    paper_bgcolor: "rgba(0,0,0,0)",
    hoverlabel: {
      bgcolor: "#ffffff",
      bordercolor: "#dd5313",
      font: { family: "sans-serif", size: 13, color: "#2b2625" }
    }
  };

  Plotly.react(
    mapDiv,
    [baseTrace, hoverOutlineTrace, selectedOutlineTrace],
    layout,
    { responsive: true, displayModeBar: false }
  ).then(() => {
    if (!mapDiv._listenersAttached) {
      mapDiv.onEditReady();
      mapDiv._listenersAttached = true;
    }
  });
}
```

``` js
numBins = 5

histogramData = {
  const values = yearStateRows.map(d => d.income_pct);
  const minPct = Math.min(...values);
  const maxPct = Math.max(...values);
  const span = Math.max(maxPct - minPct, 1e-6);
  const binWidth = span / numBins;

  // Interpolate smoothly along the exact choropleth palette: Green -> Yellow -> Red
  const lerpHex = (hex1, hex2, t) => {
    const parse = (h) => [
      parseInt(h.slice(1, 3), 16),
      parseInt(h.slice(3, 5), 16),
      parseInt(h.slice(5, 7), 16)
    ];
    const [r1, g1, b1] = parse(hex1);
    const [r2, g2, b2] = parse(hex2);
    const r = Math.round(r1 + (r2 - r1) * t);
    const g = Math.round(g1 + (g2 - g1) * t);
    const b = Math.round(b1 + (b2 - b1) * t);
    return `rgb(${r}, ${g}, ${b})`;
  };

  const getBinColor = (i) => {
    const t = numBins === 1 ? 0.5 : i / (numBins - 1);
    return t <= 0.5
      ? lerpHex("#2ca02c", "#f4d03f", t * 2)        // Min (Green) -> Mid (Yellow)
      : lerpHex("#f4d03f", "#d62728", (t - 0.5) * 2); // Mid (Yellow) -> Max (Red)
  };

  // Initialize empty bins
  const bins = Array.from({ length: numBins }, (_, i) => {
    const x0 = minPct + i * binWidth;
    const x1 = i === numBins - 1 ? maxPct : minPct + (i + 1) * binWidth;
    return {
      index: i,
      x0,
      x1,
      center: (x0 + x1) / 2,
      color: getBinColor(i),
      states: []
    };
  });

  // Assign each state to its bin (right-inclusive on the max bin)
  for (const row of yearStateRows) {
    const idx = Math.min(Math.floor((row.income_pct - minPct) / binWidth), numBins - 1);
    bins[idx].states.push(row);
  }

  // Format sorted state list for the hover tooltip
  const decimals = binWidth < 0.5 ? 2 : 1;
  for (const bin of bins) {
    bin.states.sort((a, b) => b.income_pct - a.income_pct);
    bin.codes = bin.states.map(s => s.state_code);
    bin.rangeLabel = `${bin.x0.toFixed(decimals)}% – ${bin.x1.toFixed(decimals)}%`;

    if (bin.states.length === 0) {
      bin.tooltipList = "<i>No states in this range</i>";
    } else if (bin.states.length <= 8) {
      bin.tooltipList = bin.states
        .map(s => `<b>${s.state_name}</b>: ${s.income_pct.toFixed(2)}%`)
        .join("<br>");
    } else {
      // Compact 2-column layout when a bin has many states so the tooltip never clips
      const lines = [];
      for (let k = 0; k < bin.states.length; k += 2) {
        const s1 = bin.states[k];
        const s2 = bin.states[k + 1];
        const col1 = `<b>${s1.state_code}</b> ${s1.income_pct.toFixed(2)}%`;
        const col2 = s2 ? `  |  <b>${s2.state_code}</b> ${s2.income_pct.toFixed(2)}%` : "";
        lines.push(col1 + col2);
      }
      bin.tooltipList = lines.join("<br>");
    }
  }

  // Exact boundary tick marks matching your sketch (e.g., 6 ticks for 5 bins)
  const tickvals = Array.from({ length: numBins + 1 }, (_, i) => minPct + i * binWidth);
  const ticktext = tickvals.map(v => `${v.toFixed(decimals)}%`);

  return { bins, binWidth, minPct, maxPct, tickvals, ticktext };
}
```

``` js
// Histogram cell 2/3
// B. Persistent Histogram Shell & Linked Choropleth Hover Listeners
histShell = {
  const container = html`<div class="histogram-card">
    <div id="burden-histogram"></div>
  </div>`;

  const histDiv = container.querySelector("#burden-histogram");

  histDiv.attachLinkedHover = () => {
    // Hovering a bar outlines all states in that bin in gray on the choropleth (Trace 1)
    histDiv.on("plotly_hover", (data) => {
      const pt = data.points && data.points[0];
      if (!pt || !pt.customdata) return;
      const binCodes = pt.customdata.codes || [];
      const mapDiv = mapShell.querySelector("#choropleth-map");
      if (mapDiv && mapDiv.data && mapDiv.data.length > 1) {
        Plotly.restyle(
          mapDiv,
          {
            locations: [binCodes],
            z: [binCodes.map(() => 1)]
          },
          [1] // Updates hoverOutlineTrace (#808080 solid gray outline)
        );
      }
    });

    // Leaving a bar clears the gray outlines on the choropleth
    histDiv.on("plotly_unhover", () => {
      const mapDiv = mapShell.querySelector("#choropleth-map");
      if (mapDiv && mapDiv.data && mapDiv.data.length > 1) {
        Plotly.restyle(mapDiv, { locations: [[]], z: [[]] }, [1]);
      }
    });
  };

  return container;
}
```

``` js
// Histogram cell 3/3
// C. Reactive Histogram Render with National Average Reference Line
{
  const histDiv = histShell.querySelector("#burden-histogram");
  const { bins, binWidth, minPct, maxPct, tickvals, ticktext } = histogramData;
  const maxCount = Math.max(...bins.map(b => b.states.length), 5);

  // Pull annual national average gas price ($/gal) safely from usRow
  const usGasPrice =
    usRow.avg_gas_price ??
    usRow.gas_price ??
    (usRow.price_sum_52wk ? usRow.price_sum_52wk / 52 : 0);

  // Keep the badge from clipping if the national average sits near either edge
  const relPos = (usIncomePct - minPct) / Math.max(maxPct - minPct, 1e-6);
  const labelAnchor = relPos < 0.18 ? "left" : relPos > 0.82 ? "right" : "center";

  const trace = {
    type: "bar",
    x: bins.map(b => b.center),
    y: bins.map(b => b.states.length),
    width: bins.map(() => binWidth),
    marker: {
      color: bins.map(b => b.color),
      line: { color: "#4f4947", width: 1.25 }
    },
    customdata: bins.map(b => ({
      codes: b.codes,
      rangeLabel: b.rangeLabel,
      count: b.states.length,
      tooltipList: b.tooltipList
    })),
    hovertemplate:
      "<b>Fuel Burden: %{customdata.rangeLabel}</b> (%{customdata.count} states)<br>" +
      "────────────────────────<br>" +
      "%{customdata.tooltipList}<extra></extra>"
  };

  const layout = {
    title: {
      text: `States by Fuel Burden (${selFuelYear})`,
      font: { size: 16, weight: 700 },
      x: 0.5,
      y: 0.96,
      yref: "container"
    },
    xaxis: {
      title: { text: "Fuel Burden (% of State Median Income)", standoff: 10 },
      tickmode: "array",
      tickvals: tickvals,
      ticktext: ticktext,
      fixedrange: true
    },
    yaxis: {
      title: { text: "Number of States" },
      range: [0, Math.ceil((maxCount + 2) / 5) * 5],
      dtick: 5,
      fixedrange: true,
      gridcolor: "rgba(128, 128, 128, 0.2)"
    },
    shapes: [
      {
        type: "line",
        xref: "x",
        yref: "paper",
        x0: usIncomePct,
        x1: usIncomePct,
        y0: 0,
        y1: 1,
        layer: "above",
        line: {
          color: "#666260", // Medium-dark warm gray for visibility over yellow/green bars
          width: 2.5,
          dash: "dash"
        }
      }
    ],
    annotations: [
      {
        x: usIncomePct,
        y: 1.02,
        xref: "x",
        yref: "paper",
        xanchor: labelAnchor,
        yanchor: "bottom",
        showarrow: false,
        text: `<b>U.S. Avg:</b> ${usIncomePct.toFixed(2)}% ($${usGasPrice.toFixed(2)}/gal)`,
        font: { size: 11.5, color: "#4f4947", family: "sans-serif" },
        bgcolor: "rgba(255, 255, 255, 0.9)",
        bordercolor: "#808080",
        borderwidth: 1,
        borderpad: 3
      }
    ],
    bargap: 0,
    margin: { l: 55, r: 25, t: 72, b: 55 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    hoverlabel: {
      bgcolor: "#ffffff",
      bordercolor: "#4f4947",
      align: "left",
      font: { family: "sans-serif", size: 12.5, color: "#2b2625" }
    }
  };

  Plotly.react(
    histDiv,
    [trace],
    layout,
    { responsive: true, displayModeBar: false }
  ).then(() => {
    if (!histDiv._linkedListenersAttached) {
      histDiv.attachLinkedHover();
      histDiv._linkedListenersAttached = true;
    }
  });
}
```

> **NOTE:**
>
> | Metric | Region / State Coverage | FRED Series Pattern | Frequency / Aggregation |
> |:---|:---|:---|:---|
> | [**Median Household Income**](https://fredaccount.stlouisfed.org/public/datalist/12549) | 50 States + DC + National (52 Series) | `MEHOINUS<ST>A646N` (e.g., `MEHOINUSFLA646N`) + `MEHOINUSA646N` | Annual (Census CPS ASEC) |
> | [**Retail Gas: PADD + US Total**](https://fredaccount.stlouisfed.org/public/datalist/12548) | National Benchmark + PADD Regions (6 Series) | `GASALLW` + `GASALL<PADD>W` (e.g., `GASALLMWW`) | Annual Mean of Weekly (`frequency=a`, `avg`) |
> | [**EPA Vehicle Fuel Economy Data**](https://www.fueleconomy.gov/feg/ws/) | Vehicle Fuel Economy Data since 1984 | Entry for each Year, Make, Model | U.S. Environmental Protection Agency |

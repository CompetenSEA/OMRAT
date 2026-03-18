# OMRAT GUI and User Interface: Complete End-to-End Workflow

## Purpose of this document

This document provides a full, practical, and implementation-aligned description of how the OMRAT user interface works from the perspective of an analyst using the QGIS plugin. It follows the full lifecycle you requested:

1. Ingestion
2. Preparation
3. Leg design
4. Area design
5. Reports and result presentation

It also includes model behavior details from the help and compute modules so the GUI narrative is not just screen-deep, but connected to what the calculation engine actually does.

---

## 1) How the UI is organized in QGIS

OMRAT runs as a docked plugin panel inside QGIS. Once opened, it exposes a tab-driven workflow and an internal menu strip. In practical terms, users work in three places at once:

- The **OMRAT dock widget** (tables, fields, buttons, tabs)
- The **QGIS map canvas** (digitizing and editing geometry)
- The **QGIS layer tree/task manager** (visual outputs and background task progress)

### Main tabs

The top-level tabs correspond to the operational flow:

- **Routes**
- **Traffic data**
- **Depths**
- **Objects**
- **Run Analysis**
- **Analyse drift**

### Menu entries exposed by the plugin

Inside the dock widget menu area, OMRAT provides:

- **File**
  - Save
  - Load
  - Export to IWRAP XML
  - Import from IWRAP XML
- **Settings**
  - Drift settings
  - Ship categories
  - Causation factors
  - AIS connection settings

This menu architecture mirrors the computational requirements: geometry + traffic + parameters + persistence + interoperability.

---

## 2) Ingestion: every way data enters the GUI

In OMRAT, ingestion is multi-source. You can ingest manually, from GIS files, from AIS databases, and from project/interchange files.

## 2.1 Route ingestion

### A) Manual route digitizing (primary path)

On the **Routes** tab:

1. Click **Add**
2. Click map to set first point
3. Click map again to create first leg
4. Continue clicking to add connected legs
5. Click **Stop** to end current route chain

Each segment gets generated metadata:

- Segment ID
- Route ID
- Leg name (`LEG_<segment>_<route>`)
- Start and end coordinate text
- Width (default 5000 m)
- Direction pair labels (e.g., North going / South going)

A row is added to the route table and a line layer is added on the map.

### B) Load-route button status

A **Load** route button exists in UI, but current controller implementation marks route load/remove actions as placeholders. In working usage, route ingestion is done through:

- map digitizing,
- project load (`.omrat`),
- IWRAP XML import.

## 2.2 Traffic ingestion

Traffic data is ingested by matrix entry or AIS extraction.

### A) Manual matrix entry

In **Traffic data** tab, user selects:

- Segment
- Direction
- Variable type
  - Frequency (ships/year)
  - Speed (knots)
  - Draught (meters)
  - Ship heights (meters)
  - Ship Beam (meters)

The table is ship-type rows × length-bin columns. Frequency usually uses integer spin widgets; others can use float widgets.

### B) AIS ingestion

AIS ingestion is two-step:

1. Configure connection in **Settings → AIS connection settings**
2. Trigger update per leg (row button) or broader update

The AIS flow in practice:

- leg geometry + width defines extraction corridor
- SQL queries pull ship passages and vessel metadata
- heading/course filtering splits traffic by leg direction
- AIS type-and-cargo code mapped to ship category index
- per-cell values accumulated (frequency, speed, draught, etc.)
- values converted from lists to averages where needed
- missing observations become `inf` sentinel in some cells
- lateral distribution defaults are auto-populated (`dist1`, `dist2`, means/std)

This is key: AIS ingestion does more than fill frequency table; it seeds lateral distributions for probabilistic geometry modeling.

## 2.3 Depth ingestion

Depth polygons can be ingested by three routes.

### A) Manual depth polygon

On **Depths** tab:

- Click **Add manual**
- Draw polygon on canvas
- Click **Save**

A depth row is created with default depth value (editable), and geometry is transferred to consolidated depth layer.

### B) Load depth shapefile

- Click **Load**
- Select `.shp`
- Features are read and inserted into depth table
- Depth attribute `depth` is used if present; else fallback value
- Geometries are copied into consolidated internal depth memory layer

### C) GEBCO bathymetry fetch

Depth tab includes GEBCO controls:

- OpenTopography API key
- Bounding box extension percent
- Max depth
- Interval size and generated interval list table

Workflow:

1. Derive bbox from leg endpoints
2. Expand bbox by user extension
3. Build API URL and download GeoTIFF
4. Polygonize raster values
5. Filter/merge polygons by user depth intervals
6. Insert interval polygons into depth table and depth layer

This enables rapid environmental ingestion when no curated depth polygons are available.

## 2.4 Structure/object ingestion

On **Objects** tab:

### A) Manual object polygon

- Add manual
- Draw polygon
- Save

Creates row with id/height/polygon and keeps object layer.

### B) Load object shapefile

- Load `.shp`
- Append features to object table
- value attribute resolved by configured field name path (fallback possible)

## 2.5 Whole-model ingestion

### A) Load OMRAT project

From **File → Load**:

- Select `.omrat`
- If model already has data: choose **Clear & Load** or **Merge**
- Data is normalized and repopulated into tables and in-memory structures

### B) Import IWRAP XML

From **File → Import from IWRAP XML**:

- parse XML to OMRAT-like dictionary
- normalize legacy keys
- validate against schema (best-effort)
- warning shown on schema mismatches, load continues
- choose clear or merge if existing data exists

This is major for migration/interoperability workflows.

---

## 3) Preparation phase: getting data analysis-ready

Preparation in OMRAT is where ingested data becomes coherent and computationally consistent.

## 3.1 Route and segment preparation

In route table, users verify and tune:

- Segment/route IDs
- Start/end points
- Width
- Leg name

Changing width redraws offset/tangent indicator line. Geometry edits on map trigger table coordinate updates through geometry-changed hooks.

Segment length is computed in UTM-transformed metric coordinates, avoiding naive degree-based length errors.

## 3.2 Ship category preparation

Ship categories define matrix dimensions. In **Ship Categories** dialog:

- Edit ship types
- Edit length interval boundaries

Traffic table headings are rebuilt from these definitions:

- rows = ship type labels
- columns = `min - max` length bins

This directly affects all downstream arrays and report naming.

## 3.3 Per-leg lateral distribution preparation

In route/distribution panel, for each direction users can define:

- up to 3 normal components (mean, std, weight)
- 1 uniform component (min, max, probability)
- powered repair/check interval (`ai`) style fields

Distribution editor behavior:

- weights auto-adjust to sum to 100
- combined distributions are visualized in embedded matplotlib plot
- selecting route row updates plotted segment
- AIS-derived `dist1` and `dist2` can initialize normal parameters

These distributions are critical inputs for overlap probabilities and collision candidate calculations.

## 3.4 Drift settings preparation

In **Drift settings** dialog, users configure:

- Drift probability (blackout rate semantics)
- Anchor probability
- Maximum anchor depth
- Drift speed
- Wind rose (8 direction probabilities)
- Repair model parameters
  - free function string support
  - lognormal parameters (`std`, `loc`, `scale`)
  - use_lognormal toggle

Rose percentages are rebalanced so total equals 100 before commit.

## 3.5 Causation factor preparation

In **Causation factors** dialog, users define multipliers/constants for:

- powered causation
- drifting causation
- head-on collision
- overtaking collision
- crossing collision
- bend/merging collision
- grounding
- allision

Defaults are included but can be scenario-tuned.

## 3.6 GEBCO interval preparation

When using GEBCO ingestion, users set:

- max depth
- interval size

Then click update list to auto-generate interval breaks. These breaks drive raster class filtering and polygon generation.

## 3.7 Integrity preparation during load/import

Normalization logic handles legacy/partial models by:

- remapping key names (`Start Point` → `Start_Point`, etc.)
- ensuring required segment defaults
- ensuring traffic beam matrix exists
- ensuring drift keys and repair fields exist
- preserving ship category metadata where available

Schema validation warns users but does not hard-block import, which is practical for real-world mixed-quality historical files.

---

## 4) Leg design in depth

Leg design in OMRAT is not just geometry drawing; it is a coupled operational design step linking geometry, traffic, and probabilities.

## 4.1 Geometry creation behavior

For each new leg:

- a line feature is created in memory layer
- style applied (blue line, label)
- label field receives leg name
- route table row appended
- segment record created in `segment_data`
- default width marker added via tangent computation

The plugin supports continuous leg chain creation until user stops route mode.

## 4.2 Direction semantics

Direction pairs are inferred from azimuth quadrant and shown in UI labels. These labels become keys in traffic data dictionaries, thereby controlling:

- directional traffic matrix lookup
- head-on/opposite direction pairing
- overtaking same-direction calculations
- leg-direction report entries

If direction semantics are wrong, all directional risk calculations can skew; thus users should verify direction labels after route creation.

## 4.3 Leg width significance

Width controls more than visual offset:

- AIS extraction corridor width
- geometric context of lane breadth
- lateral overlap implications in calculations

The midpoint perpendicular indicator provides immediate QC signal for unrealistic widths.

## 4.4 Leg metadata fields that drive computation

Each segment eventually holds computationally relevant fields including:

- `line_length`
- `Dirs`
- `dist1`, `dist2`
- normal/uniform distribution parameters for both directions
- `ai1`, `ai2`
- route/segment naming and geometry texts

These are assembled into a full data package by gather-data routines before model runs.

---

## 5) Area design in depth

Area design defines hazard footprints used by drifting and powered models.

## 5.1 Depth area design

### Consolidated depth layer concept

Unlike objects, depths are merged into one internal memory layer with numeric depth attributes. This simplifies symbology and geometry synchronization.

### Editing synchronization

- geometry edits on map update table polygon text
- table row deletion removes corresponding features
- mapping between feature IDs and rows is rebuilt when needed

### Visual encoding

Depth layer uses graduated blue palette by depth:

- shallow = darker (higher grounding concern)
- deeper = lighter

This visual cue helps analysts inspect hazard proximity before running model.

## 5.2 Object area design

Objects are kept as per-layer entities, suitable when structures have distinct provenance. Object rows include:

- object id
- height
- polygon WKT

Manual structure layers can be named by height value, reinforcing semantic clarity.

## 5.3 GEBCO-derived area design nuances

When vectorizing GEBCO:

- raster values are negative depths
- interval filters invert sign logic accordingly
- polygons may be merged per depth band
- stored table values can reflect interval text; numeric depth representative is used in layer features

This means users should confirm depth interval interpretation aligns with study conventions.

---

## 6) Running full risk analysis

The **Run Analysis** tab is the central execution and summary panel.

## 6.1 Inputs before run

- Optional model name
- Optional report output path (markdown)
- Ensure routes, traffic, depths/objects, and settings are prepared

## 6.2 Execution model

Click **Run model** triggers background `QgsTask` execution:

- non-blocking UI
- progress callbacks to task manager/log
- success/failure handlers
- final values written into result fields

## 6.3 Result fields shown in GUI

The main scalar outputs displayed are annual frequencies/probabilities in scientific notation:

- Drifting allision
- Powered allision
- Drifting grounding
- Powered grounding
- Overtaking collision
- Head-on collision
- Crossing collision
- Merging/Bend collision

The “View way” buttons open geometry-focused visual diagnostics where implemented.

---

## 7) What the compute engine is doing behind those GUI numbers

To enhance interpretation, this section ties GUI outcomes to compute logic.

## 7.1 Data preparation stage in compute modules

Before heavy calculations, compute preparation includes:

- parsing and cleaning traffic matrices
- safe WKT loading
- splitting obstacle sets into structures vs depths
- CRS transformation to UTM-like metric frames
- preparing line/distribution lists for iteration

This stage ensures mathematically meaningful distances and robust geometry operations.

## 7.2 Drifting model behavior

The drifting pipeline generally:

1. builds transformed lines/obstacles
2. computes reach distance from drift settings
3. precomputes spatial overlap/probability-hole terms
4. iterates traffic by leg, direction, ship type/size
5. applies anchoring and non-repair probabilities
6. cascades residual probability across ordered obstacles
7. accumulates allision and grounding contributions
8. stores detailed breakdown report

Important practical concepts for users:

- **Probability holes** represent intercepted probability mass in drift corridor overlap.
- **Cascade behavior** means downstream obstacle contribution is reduced by upstream interception.
- **Repair and anchoring factors** can strongly damp or amplify outcome depending on settings.

The GUI’s drifting fields are post-aggregation totals (with applicable reduction factors).

## 7.3 Powered model behavior

Powered calculations (allision/grounding) use pathway and recovery logic with shadow-aware obstacle interaction.

For powered allision/grounding, the engine uses:

- per leg-direction traffic and speed
- obstacle intersection summaries (`mass`, mean distance)
- recovery distance/time style terms (`ai` and speed)
- causation factors

It then sums per ship category and obstacle context. The final totals are written directly to powered result line edits.

## 7.4 Collision model behavior

Ship-ship collisions are separated by type:

- head-on (opposite direction on same leg)
- overtaking (same direction differential behavior)
- crossing (between different legs)
- bend/merging

The engine combines:

- directional traffic rates
- speed estimates
- beam estimates (explicit or estimated from LOA intervals)
- lateral distribution weighted mean/sigma
- causation factors per collision class

Results are aggregated both total and by-leg internally; GUI shows class totals.

---

## 8) Analyse drift tab: corridor generation and map interpretation

This tab is distinct from the full risk run. It is for corridor visualization analysis.

Inputs:

- depth threshold (m)
- height threshold (m)

When user clicks **Run analyses**:

- old corridor layers are removed
- data is pre-collected in main thread
- generation runs in background task
- status label updates with percentage
- resulting corridor polygons are grouped by leg and added as layers

### Corridor layer style

Corridors are categorized by direction (N, NE, E, SE, S, SW, W, NW) with distinct colors and transparency. This helps users visually inspect directional exposure patterns and identify legs with high obstacle interaction risk regions.

---

## 9) Reports: what they look like for decision-making

## 9.1 In-panel summary report (Run Analysis tab)

This is the quickest executive view:

- eight core accident frequency values
- immediately comparable
- scientific notation suitable for low-probability domains

Typical interpretation pattern:

- compare drifting vs powered classes
- compare collision class composition
- identify dominant risk mechanism

## 9.2 Drifting markdown appendix report

If report path is provided (or default path used), drifting model writes a markdown report containing:

- parameter summary
- total allision/grounding
- directional aggregates
- leg-direction-angle aggregates
- per-structure directional contributions
- per-object totals
- ship category breakdown with labels when available
- leg-level summaries

The report is tabular and audit-friendly. It is useful for QA, annexes, and stakeholder documentation.

## 9.3 Visual diagnostic outputs

The GUI supports visualization dialogs for geometric pathways (drift and powered variants). These views show how routes and hazard geometries interact, helping explain why a numeric result is high or low.

## 9.4 Map-layer outputs

Users also consume outputs as map layers:

- depth/structure layers (inputs)
- drift corridor layers (analysis output)
- potential result layers for allision/grounding representations

This is essential for spatial communication in maritime planning studies.

---

## 10) Full recommended user workflow (practical checklist)

1. Open OMRAT dock.
2. Define legs in **Routes** tab (draw on map, stop route).
3. Verify route table IDs, coordinates, width, directions.
4. Configure ship categories and length bins.
5. Fill or import traffic in **Traffic data** tab.
6. If AIS available, configure DB and run AIS updates per leg.
7. Tune lateral distributions for each leg/direction.
8. Add depth areas (manual, shapefile, or GEBCO).
9. Add object/structure areas (manual or shapefile).
10. Configure drift settings (rose, anchoring, repair).
11. Configure causation factors.
12. Optionally run **Analyse drift** for corridor visualization and sanity-checking.
13. Enter model name and report path in **Run Analysis**.
14. Run model and monitor background task progress.
15. Review all eight result fields.
16. Open visualization views for pathway interpretation.
17. Review generated markdown drifting report.
18. Save project (`.omrat`) and/or export IWRAP XML.

---

## 11) What “good” final results look like in UI terms

A complete, analysis-ready project should have:

- At least one leg with sensible width and direction labels.
- Traffic data populated for both directions where relevant.
- Depth polygons covering realistic grounding exposure regions.
- Structure polygons representing real collision/allision hazards.
- Drift and causation settings matching scenario assumptions.
- Run Analysis fields populated (not blank), with plausible orders of magnitude.
- Drift markdown report generated and stored.
- Optional drift corridors visible and interpretable on map.

If one of these is missing, the GUI may still run, but results can be incomplete or deceptively low.

---

## 12) Key interpretation cautions for advanced users

- **Direction assignment matters**: wrong leg orientation can bias directional risk.
- **Width is influential**: it affects AIS capture and geometric overlap context.
- **Distribution assumptions are not cosmetic**: they drive overlap/candidate integrals.
- **Repair/anchor settings can dominate drift outcomes** under certain scenarios.
- **Imported legacy data may load with defaults** where fields are absent; always validate assumptions in settings dialogs.
- **Visual diagnostics are crucial**: do not rely solely on scalar outputs.

---

## 13) Conclusion

OMRAT’s GUI is best understood as an integrated risk-workbench where map editing, tabular traffic definition, stochastic parameterization, and background computation all converge. The workflow is deliberately layered:

- ingest geometry and traffic,
- prepare assumptions and distributions,
- run probabilistic engines,
- inspect outputs numerically, spatially, and through markdown reporting.

When used in this order, the interface supports both exploratory scenario analysis and defensible, documented maritime risk studies compatible with IWRAP-style methodological expectations.

---

## 14) Extended example scenario (from raw setup to final reporting)

To make the workflow concrete, consider a typical wind-farm shipping-lane assessment. The analyst starts with an empty QGIS project and opens OMRAT. In Routes, they digitize three connected legs representing inbound, transit, and outbound traffic. Widths are adjusted to reflect known traffic separation behavior: a wider inbound lane, narrower constrained transit lane, and moderate outbound lane. Direction labels are checked for each leg.

Next, in Ship Categories, the analyst confirms category labels and length intervals to match local authority reporting classes. In Traffic data, the baseline matrix is imported through AIS update per leg; then manual edits adjust sparse categories where AIS under-sampled events are known from pilot logs.

In Depths, they first use GEBCO to create broad bathymetry context, then load a local hydrographic shapefile with more accurate near-shore depths, ensuring shallow critical banks are represented. In Objects, they load turbine foundation polygons and manually add a bridge support area omitted from source data.

In Drift settings, they calibrate wind rose with seasonal weighting and set anchoring assumptions based on local seabed characteristics. Repair model settings are tuned to reflect expected intervention time. In Causation Factors, default values are used initially, then a sensitivity rerun is planned with conservative alternatives.

Before running the full model, the analyst opens Analyse drift and generates directional corridors. The map reveals one leg with strong corridor overlap toward structure clusters under NE winds. This confirms the geometry and motivates scrutiny of that leg’s distribution settings.

Finally, in Run Analysis, they set report path and model name, execute calculations, and monitor progress in QGIS task manager. The resulting panel values show drifting allision dominates powered allision on the transit leg, while crossing collisions remain low. The markdown drifting report is then attached to the technical memo, and both `.omrat` and IWRAP XML exports are archived for reproducibility and peer review.

---

## 15) Refactor continuation plan (implementation-ready)

To continue the refactor in a controlled way, use a phased approach that separates behavior-preserving cleanup from behavior changes.

### Phase A — Stabilize and expose current behavior

1. Add/expand tests around current GUI workflows before changing logic:
   - route creation and width updates,
   - depth/object table ↔ geometry synchronization,
   - AIS ingestion table writes,
   - run-model field updates.
2. Add logging for key state transitions (segment selection, run start/end, load/import clear-vs-merge).
3. Fix obvious UX inconsistencies first (button labels and unimplemented button behavior warnings).

### Phase B — Extract cohesive services from controller-heavy modules

1. Split `omrat.py` responsibilities into services:
   - project I/O service,
   - run-task orchestration service,
   - map-layer management service.
2. Keep UI signal wiring in one place and move business logic out of callbacks.
3. Create a thin adapter around QGIS side effects so pure logic can be unit tested.

### Phase C — Normalize schema and data contracts

1. Define one canonical in-memory schema for:
   - `segment_data`,
   - `traffic_data`,
   - depths/objects records,
   - settings/causation values.
2. Centralize normalization in one module (load/import/AIS all pass through same normalizer).
3. Add explicit validation at boundaries (dialogs, file load/import, run start).

### Phase D — Improve UX reliability and observability

1. Replace silent `except` blocks with targeted exceptions + user-facing messages.
2. Add progress/status indicators consistently across long-running operations.
3. Surface report output and last run metadata in a single “run summary” area.

### Phase E — Final hardening

1. Regression test suite for all tabs and major actions.
2. Backward compatibility checks for `.omrat` and IWRAP imports.
3. Document migration notes and known limitations.

---

## 16) Codex prompt to finalize the refactor

Use the following prompt as-is in Codex to complete the refactor with minimal ambiguity:

```text
You are working in /workspace/OMRAT.

Goal:
Finalize a behavior-preserving refactor of the OMRAT QGIS plugin while improving testability, maintainability, and UX reliability.

Scope and priorities:
1) Keep user-visible behavior unchanged unless explicitly listed as a bug fix.
2) Preserve existing file import/export compatibility for .omrat and IWRAP XML.
3) Reduce controller complexity in omrat.py by extracting focused services.
4) Improve error handling: no silent broad exceptions without logging/user feedback.
5) Add or update tests for the refactored paths.

Required deliverables:
A) Refactor architecture
- Extract service modules for:
  - project load/save/import/export orchestration,
  - task execution/progress reporting,
  - map layer lifecycle management.
- Keep signal wiring centralized; business logic should move out of UI callbacks.

B) Data contract improvements
- Introduce a canonical normalized data contract for segment_data, traffic_data, depths, objects, and settings.
- Ensure all data entry points (manual UI, AIS, load/import) use the same normalization and validation path.

C) UX and robustness
- Replace silent except blocks with explicit handling + log entries.
- Standardize user-facing error messages.
- Ensure unimplemented actions are either implemented or disabled with clear messaging.

D) Testing
- Add/extend tests covering:
  - route creation/edit synchronization,
  - depth/object table-layer synchronization,
  - AIS update data writes,
  - background calculation task completion/failure,
  - load/import clear-vs-merge behavior.
- Keep tests deterministic and independent of external services where possible (mock DB/API).

E) Documentation
- Update top-level GUI workflow documentation to match final behavior.
- Add a concise “refactor notes” section summarizing architecture changes and migration impact.

Constraints:
- Follow existing style and project conventions.
- Do not add unnecessary dependencies.
- Keep patches reviewable: prefer incremental commits.
- Run tests and report exact commands and outcomes.

Output format:
1) Summary of architectural changes.
2) List of files changed with rationale.
3) Test results (commands + pass/fail).
4) Remaining risks / follow-up items.
```

This prompt is intentionally strict about preserving current behavior while improving structure and reliability.

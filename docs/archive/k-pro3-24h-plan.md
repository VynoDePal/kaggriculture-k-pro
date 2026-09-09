> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

# K Pro — continuation 24 heures Implementation Plan

> **For agentic workers:** Use executing-plans to implement the approved continuation task-by-task. Keep all unrelated work intact; this is not a request to merge or submit.

**Spec:** The four follow-up experiments in `docs/k-pro2-report.md`, approved by the user's request to continue for 24 hours and incorporate the two submissions. This continuation is bounded by those existing mechanisms; a fundamentally different architecture must be separately described before implementation.

## Task 2 — portable zoning and delayed urgency

Files: new `k_pro/pro3/prototype_a.py`, tests `tests/test_k_pro3_priority.py`, compiled candidates under `k_pro/pro3/`. Existing sources and compilers stay immutable.

Interface: `assignment_urgency(value, hour, day)` consumes the same task value as the auction and returns its urgency component. `zone_total(values)` selects stable or legacy summation through configuration.

## Task 4 — subsequent bounded experiments within the remaining window

These are hypotheses, not permission to modify a frozen source. Before each experiment, record its trigger, exact profile, expected failure mode, counterfactual and new data namespace in the journal.

### Experiment C — initial capital, factorial interaction (predeclared before C data)

Commit policy for this bounded preparation: do not commit the dirty worktree. Return exact changed-file list/hashes and test evidence in the implementer report; a reviewer will inspect a snapshot diff. This preserves unrelated user changes.

## Task 7 — idle/storage census before any new delivery policy

This is a bounded diagnostic implementation of Task4, not a new policy architecture. D and E are terminal. Current J6 has `idle_delivery=False`; a mixed inventory calculation in that inactive option cannot explain J6's current losses. Its `shed+carry` total before market is only an instantaneous capacity risk, not a forecast of inevitable night loss. Existing public-state accounting/delivery variations have negative history. Therefore count real opportunities before choosing a branch intervention.

For each post-unit snapshot in days0..28, hours12..23, enumerate only units whose chosen command was exactly `['PASS']`, carry a saleable product listed in candidate.PARAMS, have quote×quantity at least30, and can reach a shed tile plus deposit within the remaining day (`hour+distance+1<=24`). Preserve the old conservative exclusion of wheat before hour20. Record uid, position, item, quantity, public quote and Manhattan distance to nearest candidate.SHED tile. This is an **eligibility census**, not an action recommendation or a claim that the trip is profitable; market sales may eliminate the risk and fresh tasks may appear. Do not choose a new action, alter orders, count eligibility as avoided waste or penalize PASS.

## Task 8 — workload-conditioned urgency, isolated preparation G

Bounded implementation of the already approved Task4 public-workload hypothesis. No new architecture, macro, food buffer or idle-return policy. D supports J6 as research reference but not universal80. F does not justify generalized deliveries. Recalculating per-worker feasible marginal value was already tested in prototype_b/candidate_feasible and rejected on A; do not recreate or activate it. The new question is whether a fixed urgency divisor should instead respond to remaining service load. This is a heuristic proxy, not a proven lower bound or an exact route scheduler.

Extend `assignment_urgency(value, hour, day, pressure=1.0)` so its old divisor choice remains exact, then calculate `min(CFG['urgency_cap'], value * pressure / divisor) * (1.8 if hour>=17 else 1.0)`. Three-argument calls remain identical. In the actual auction `act_units`, after positions are formed compute pressure once from the original work and all current unit positions; use it only as the fourth argument to assignment_urgency. Greedy actions, fixed units, feasibility masks, zones, bids' other costs, macro/market and last-day logic remain unchanged. Disabled defaults must retain prototype_a decisions exactly.

## Task 10 — public delayed CARE quote I, independent of H

Extend `incremental_task_value(tile,sequence,day,prices,care_price=None)` so only its CARE term changes to `prices[product] if care_price is None else care_price`. All immediate HARVEST valuation, FEED costs/bonus, fertilizer/crop calculations, survival bonus and floor remain exactly unchanged. Legacy four-argument calls must remain equivalent. Do not change action availability or `animal_tasks`; even a CARE with no remaining payoff may remain in the bundle but its marginal CARE term becomes0 under the enabled new flag. This is not H's action-removal gate and not a composition with H.

## Task 11 — PASS allocation census J, observation before intervention

Status: COMPLETE, 16 terminal observation-only trajectories; preparation fix-round review and terminal evidence review approved. Report `docs/k-pro3-pass-census-j-report.md`; separate post-hoc subclassification `docs/k-pro3-pass-census-j-secondary.md`. J bank is exposed and excluded from future confirmation/final. No policy changed or promoted. Original import-only RED sequencing deviation is retained explicitly in the preparation report/progress ledger.

## Task 15 — user-requested small price-triggered TOMATO allocation N

Prepare these six NEW files only, plus the task report:

Add one configuration key `tomato_spot_cap=0` (neutral default). At normal `plan()` execution only, when this cap is positive, add TOMATO to the wanted targets: preserve the count of existing TOMATO plants, and target up to the configured cap if `day < 20` and `4 * p['TOMATO'] >= 5 * PARAMS['TOMATO'][0]`. Otherwise target only existing plants. Do not make permission sticky: new allocation stops at the next normal replan if price falls or J20 is reached. Existing plants remain serviced; never DIG a living plant to satisfy this option. Keep the original day/hour replanning cadence.

### Task15 controller coverage ruling, before any N100 outcome

Root changes only the exploration gate: the frozen N100 comparison may now proceed to measure reachability and outcomes, using the approved behavioral boundary/market tests and source/compiled equivalence; active-prefix/receipt/plant/collection/sale evidence remains UNMET and blocks selection/certification, not this read-only offline exploration. This is a disclosed pre-N-data protocol amendment, not a passed gate or evidence-based parameter retune. If N reveals a promising active dose, independent fixed diagnostic coverage and confirmation are required before selection. No N outcome may be interpreted as a causal tomato-sale profit without actual receipts. User informed of absent activation and this limitation.

## Continuation mechanism

The thread heartbeat previously revisited this work every 20 minutes; it has now been deleted after the completed research delivery. Do not recreate it or resume any terminal campaign. All outcomes, source closures and reviewed reports are preserved; further research requires a new authorized scope and fresh banks, not tuning on Q.

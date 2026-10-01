# Branch Stats — `eval_pipeline_integration`

Hidden-layer sweep (16 / 32 / 64 neurons) plus discount-factor and epsilon probes, all on a fresh database.

## Methodology

**Restart the database and the target API before every run.** Earlier runs were discarded because
they ran against accumulated state: identical config and seed produced 150, 119 and 51 unique
combos purely on leftover rows. Stale `/points`, `/prices` and `/discounts` records let `GET_ALL`
hand the agent resource ids it never earned, which fabricates endpoint coverage and inflates the
combo count. A dirty-DB run is not comparable to anything, including another dirty-DB run.

Fixed across all runs: 50,000 episodes · seed 1234 · step limit 35 · ε 0.01 · α 0.01 ·
QNetwork5 · GPT-4o-mini @ temp 0.2. γ = 0.99 except where noted.

Reward scheme:

| Event | Reward |
|---|---|
| New combo, judged genuine | `severity_base × novelty` (`high=10 / medium=6 / low=3`) |
| New combo, judged false positive | −1 |
| Repeat combo | 0 |
| Rule-check duplicate | +1 |
| Non-500 response | 0 |
| No response | −0.15 |

---

## Sweep results

| Metric | 16 neurons | 32 neurons | 64 neurons |
|---|---|---|---|
| **Hidden bug hits** | 0 | 0 | **70** (first @ ep 5,897) |
| **`/points` executes** | 209 (0.035%) | 228 (0.026%) | **127,140 (13.84%)** |
| **`/items` share** | 99.86% | 99.89% | **85.40%** |
| Unique bug combos | 49 | **51** | 44 |
| **Combos per 100k executes** | **8.1** | 5.9 | 4.8 |
| Total executes | 602,427 | 869,576 | 918,748 |
| Sent to judge | 24 | 24 | 30 |
| Genuine bugs | 21/24 (87.5%) | **24/24 (100%)** | 29/30 (96.7%) |
| False positives | 3 (12.5%) | **0** | 1 (3.3%) |
| DELETE share | **3.56%** | 0.49% | 0.05% |
| Mean novelty (genuine) | **0.267** | 0.225 | 0.214 |
| Avg judge confidence | 0.79 | **0.85** | 0.83 |
| Net discovery reward | +78 | **+81** | +75 |
| Avg reward (first → last) | −4.780 → −4.062 | −3.729 → −3.929 | −3.982 → **−3.683** |
| **Wall time** | **518s** | 741s | **19,160s (5h 19m)** |
| ms per execute | 0.86 | 0.85 | **20.85** |

### What the sweep shows

**Combo count is flat; what changes is *where* the agent looks.** 49 / 51 / 44 across a 4× range of
network capacity is noise, not signal. The real difference is endpoint coverage: 16 and 32 neurons
are both locked onto `/items` at 99.86% and 99.89%, while 64 neurons breaks out to 13.84% `/points`
— and is the only configuration that finds the hidden bug.

**Capacity buys depth, not breadth.** 64 neurons produced the *fewest* combos and the *worst*
per-request efficiency (4.8 vs 8.1 for 16n), but it is the only run that reached the target. If the
goal is the hidden bug, raw combo count is the wrong metric to optimise.

**Smaller is cheaper and cleaner per request.** 16 neurons is the most efficient discoverer
(8.1 combos per 100k executes, 1.7× the 64-neuron rate) and finishes in 8½ minutes against 5¼
hours. It also uses DELETE most often (3.56%, vs 0.05% at 64n) and has the highest mean novelty
(0.267) — but it never leaves `/items`.

**Judge quality peaks in the middle.** 32 neurons is the only run with zero false positives and the
highest confidence (0.85). 16 neurons is the noisiest (12.5% FP, 0.79 confidence).

**The 64-neuron run is the only one where the API collapsed** (see below), so its efficiency numbers
are depressed by an environment failure, not purely by network size.

---

## ⭐ 16 neurons, ε = 0.025 — best configuration (COMPLETE)

2026-10-01. Complete, exit 0. γ=0.99 · **ε 0.01 → 0.025** · 16 neurons.

**229 unique combos — 4.5× the previous best. 174 hidden-bug hits, first at episode 3,910.**

| | 16n ε=.01 | 32n ε=.01 | 64n ε=.01 | **16n ε=.025** |
|---|---|---|---|---|
| **Unique combos** | 49 | 51 | 44 | **229** |
| **Combos per 100k executes** | 8.1 | 5.9 | 4.8 | **28.0** |
| **Hidden bug** | 0 | 0 | 70 @ ep 5,897 | **174 @ ep 3,910** |
| Total executes | 602,427 | 869,576 | 918,748 | 818,698 |
| Sent to judge | 24 | 24 | 30 | **108** |
| Genuine rate | 87.5% | 100% | 96.7% | 97.2% |
| False positives | 3 (12.5%) | 0 | 1 (3.3%) | 3 (2.8%) |
| `/points` share | 0.035% | 0.026% | 13.84% | 1.70% |
| **DELETE share** | 3.56% | 0.49% | 0.05% | **10.21%** |
| Mean novelty | 0.267 | 0.225 | 0.214 | 0.135 |
| Net discovery reward | +78 | +81 | +75 | **+260** |
| Wall time | 518s | 741s | 19,160s | 5,102s (85 min) |

Discovery never stalls: **+106, +36, +34, +25, +28**. Every other clean run front-loaded then
flatlined (32n: +38, +2, +1, +7, +3). This one is still adding 28 combos in its final window.

### Three distinct hidden-bug strategies

| Variant | First seen |
|---|---|
| `DELETE+POINTS+STRUCTURE+ALL` | ep 3,910 (hit #1) |
| `DELETE+POINTS+INJECTION+ALL` | ep 3,921 (hit #2) |
| `DELETE+POINTS+ENCODING+UNKNOWN` | ep 5,328 (hit #6) |

The 64-neuron run only ever hit `VALID+ALL`. Multiple independent payload strategies reaching the
same defect is stronger evidence it is real.

### ⚠ The hidden bug earned almost no reward

Worth recording because it inverts the obvious reading. Discovery 070 — the first hidden-bug hit —
was judged `novelty=0.1`, so it paid **10 × 0.1 = 1.0**. Hit #2 (the INJECTION variant, disc 071)
was a *new combo* but its sequence was rule-filtered as a duplicate, so it paid the consolation
**+1**. Subsequent hits were repeat combos paying **0**.

**The pipeline valued finding the hidden bug at ~1.0 — the same as a filtered duplicate.** The judge
read it as the same `delete-after-create` root cause it had already seen 60+ times, and the
sequence-normalising duplicate filter agreed. The agent found the target *despite* the reward
signal, not because of it.

So the DELETE preference cannot have come from the hidden bug. It came from window 1, where the
early `DELETE+ITEMS` findings scored novelty 0.5–0.7 and paid 5–7 each. That policy then carried
the agent into `/points` incidentally.

### Method mix shifts across the run

| Window | DELETE | POST | GET_ALL | PATCH | GET | Execute ratio | ms/exec | Avg reward |
|---|---|---|---|---|---|---|---|---|
| 1 | **24.3%** | 4.8% | 22.4% | 0.2% | 0.6% | 49.1% | 2.28 | −3.886 |
| 2 | 2.9% | 1.3% | **47.1%** | 0.2% | 0.5% | 56.2% | 5.02 | −3.707 |
| 3 | 14.8% | **34.4%** | 2.7% | 0.2% | 0.4% | 50.5% | 1.09 | −3.849 |
| 4 | 3.4% | **39.5%** | 8.6% | 0.3% | 0.6% | 46.6% | 8.62 | −3.956 |
| 5 | 4.0% | 18.1% | 18.9% | **6.2%** | **6.0%** | 31.4% | **19.32** | −4.352 |

DELETE-heavy → GET_ALL-heavy → POST-heavy → method-diverse. This is the novelty decay working as
designed: exploit a verb until its combos saturate, then move on. DELETE share does **not** rise
monotonically — it spikes in W1 and W3 and falls between, which is the expected signature of
saturate-and-rotate, not of a policy locking onto one action.

**W5 is API-degraded**, not agent decay: latency hit 19.32 ms/execute (8.5× window 3), executes fell
to 110,031, and average reward worsened to −4.352 purely because fewer executes means more
dial-turner penalty per episode. Combos still grew +28.

### Judge output

108 judged of 229 discoveries (52.8% rule-filtered), 105 genuine, 3 false positives (2.8%). All
genuine `high`/`error_handling`; all 3 FPs are bare single-call `POST /x → 500` with every
`state_feature` at 0. Confidence: 31 at 0.8, 74 at 0.9, FPs at 0.3–0.4. Avg **0.86**.

Mean novelty **0.135** (lowest of the clean runs, but across 105 samples vs 21–29). Reward: **+142**
genuine, −3 FP, **+121** duplicates = **+260**, 3.2× any other run.

### Distributions (818,698 executes)

Endpoints: `/items` 796,238 (97.26%) · `/points` 13,926 (1.70%) · `/discounts` 5,875 (0.72%) · `/prices` 2,659 (0.32%)
Methods: NONE 387,081 (47.3%) · GET_ALL 170,901 (20.9%) · POST 155,852 (19.0%) · **DELETE 83,598 (10.21%)** · GET 10,405 · PATCH 8,422 · PUT 2,439

Lowest `/items` concentration of any 16-neuron run, and the only clean run with all four endpoints
in meaningful volume.

---

## ⭐ Controlled ablation — LLM judge vs local count decay (5 v 5 COMPLETE)

All 10 runs: 16 neurons, γ=0.99, ε=0.025, 50k episodes, seed 1234, clean DB before each.
**Only the novelty term differs.** Rule checks, duplicate filtering (+1), repeat-zeroing,
false-positive penalty (−1) and the severity base (10) are identical in both arms.

Local stand-in: false positive if no `state_feature` is set; otherwise
`novelty = 1/(1 + times this (method, endpoint) has failed before)`.

### Bottom line at 5 v 5

**One metric separates the arms, and it is weaker than earlier runs suggested. Four do not.**

| | **Judge (n=5)** | **No judge (n=5)** | Comparison | Significant? |
|---|---|---|---|---|
| **Hidden-bug hits** | median **174** | median **1** | **174× on medians** | **marginal** — U = 22/25, exact p = 0.024 |
| **Found the bug at all** | **5 / 5** | 4 / 5 | — | no (Fisher p = 1.0) |
| Unique combos | mean 144.6, median 136 | mean 142.2, median 118 | **1.02×** | **no** (Welch t = 0.06) |
| Combos per 100k executes | 20.4 | **30.0** | **0.68× — judge behind** | no |
| Hits per DELETE issued | 0.208 – 40.0% | 0 – **5.50%** | **ranges overlap** | no |
| Earliest find | ep 3,910 | ep **6,900** | ranks interleave | no |

### ⚠ CORRECTIONS — no-judge #5 overturned three more claims

No-judge #5 (**248 combos, 270 hits, first @ 6,900**) is the strongest single run of the campaign on
two metrics and it dismantles most of what the judge arm appeared to own:

1. **"Disjoint hit ranges" is DEAD.** No-judge #5 scored **270 hits**, beating judge #1 (174),
   judge #2 (7) and judge #3 (6). Judge [6, 23,830] and no-judge [0, 270] overlap heavily.
   Mann-Whitney fell from U = 25/25 (p = 0.008) to **U = 22/25, p = 0.024**.
2. **"Disjoint hits-per-DELETE" is DEAD.** No-judge #5 hit **5.50%** of its DELETEs, above three of
   five judge runs. The volume-controlled metric no longer separates the arms either.
3. **The combo gap is GONE.** 144.6 vs 142.2, Welch t = **0.06**. Not a trend, not noise-limited —
   the arms are indistinguishable on discovery volume.
4. **Efficiency is now clearly against the judge**: 20.4 vs 30.0 combos per 100k.
5. **Early detection is NOT judge-only** (already corrected at no-judge #4; now reinforced —
   no-judge #5 is the **2nd earliest find of all 10 runs**).

### ⚠ Multiple comparisons: the one surviving result does not survive correction

Across this ablation I tested at least five metrics (hit count, detection rate, combos, efficiency,
hits-per-DELETE) plus first-find timing. A Bonferroni threshold at α = 0.05 over 5 tests is
**α = 0.01**. The hit-count result at **p = 0.024 does not clear it**.

Stated plainly: **this ablation did not establish that the LLM judge beats a free count-based
novelty proxy.** It produced one marginal rank-test result on hit magnitude that would not survive
correction for the number of comparisons made, and nothing else.

### Per-run results — all 10 runs

| | J#1 | J#2 | J#3 | J#4 | J#5 | N#1 | N#2 | N#3 | N#4 | **N#5** |
|---|---|---|---|---|---|---|---|---|---|---|
| **Unique combos** | 229 | 43 | 136 | 183 | 132 | 118 | 97 | 83 | 165 | **248** |
| **Hidden-bug hits** | 174 | 7 | 6 | 23,830 | 427 | 1 | 0 | 1 | 3 | **270** |
| First hit (ep) | **3,910** | 45,751 | 42,509 | 9,797 | 14,317 | 48,367 | — | 49,463 | 10,980 | **6,900** |
| Combos per 100k | 28.0 | 8.6 | 17.6 | 28.5 | 19.2 | 20.2 | 11.5 | 7.5 | 51.9 | **58.8** |
| Total executes | 818,698 | 498,255 | 770,614 | 641,571 | 686,963 | 584,188 | 842,642 | 1,104,037 | 318,212 | 422,006 |
| Assessed | 108 | 15 | 60 | 80 | 67 | 37 | 44 | 35 | 86 | 110 |
| Genuine rate | 97.2% | 53.3% | 91.7% | 91.2% | 86.6% | 73.0% | 90.9% | 88.6% | 91.9% | 91.8% |
| False-positive rate | 2.8% | 46.7% | 8.3% | 8.8% | 13.4% | 27.0% | 9.1% | 11.4% | 8.1% | 8.2% |
| Mean novelty | 0.135 | 0.338 | 0.202 | 0.149 | 0.195 | 0.348 | 0.332 | 0.491 | 0.267 | 0.284 |
| Discovery reward | +260 | +48 | +182 | +205 | +169 | +165 | +182 | +196 | +283 | **+416** |
| `/items` share | 97.3% | 48.4% | 99.1% | 91.8% | 53.3% | 97.0% | 99.6% | 99.7% | 98.9% | **72.7%** |
| `/points` share | 1.70% | **51.2%** | 0.18% | 7.91% | **43.2%** | 0.27% | 0.03% | 0.10% | 0.39% | **26.0%** |
| DELETE share | 10.2% | 0.074% | 0.373% | **28.4%** | 0.155% | 4.15% | 0.073% | 0.132% | 3.14% | 1.16% |
| Hits per DELETE | 0.208% | 1.90% | 0.209% | 13.07% | **40.0%** | 0.004% | 0% | 0.069% | 0.030% | **5.50%** |
| Wall time | 5,102s | 325s | 1,600s | 619s | 590s | 349s | 732s | 792s | 1,215s | 2,142s |

### No-judge #5 reached `/points` — the last judge-only behaviour falls

Until this run, every no-judge run stayed pinned to `/items` at 97–99.7%, and `/points` traffic
never exceeded 0.39%. No-judge #5 put **26.0% of its traffic on `/points`** (and only 72.7% on
`/items`). The local count-based proxy reached the target endpoint on its own.

Endpoint reach by arm, `/points` share: judge 0.18 / 1.70 / 7.91 / 43.2 / 51.2 % —
no-judge 0.03 / 0.10 / 0.27 / 0.39 / **26.0** %. Overlapping.

### Second-half collapse is the dominant failure mode in the no-judge arm (3 of 5)

| Run | Windows 1–3 ratio | Windows 4–5 ratio | Combos in last 20k |
|---|---|---|---|
| No-judge #4 | 36.7 / 30.6 / 4.8% | 7.4 / 11.3% | 8 of 165 |
| **No-judge #5** | 33.4 / 43.0 / 30.5% | **6.2 / 7.6%** | **7 of 248** |
| Judge #4 (inverse) | **5.3** / 42.3 / 43.5% | 46.6 / 45.5% | recovered, 36 of 183 |

No-judge #5 earned 241 of its 248 combos in the first 30k episodes, then sat at 6–8% execute ratio
and ≈ −5.0 average reward (floor −5.25) for the last 20k. Its 58.8 combos/100k is an artefact of
that collapse: the execute denominator shrank far faster than the combo numerator. **Do not read
the no-judge efficiency lead as a real advantage** — it is division by a collapsed denominator,
the same caveat recorded for no-judge #4.

Judge #4 remains the only run that collapsed and then recovered.

### Variance — the arms are now statistically indistinguishable in spread too

| Arm | Combo range | sd | Hit range |
|---|---|---|---|
| Judge | 43 – 229 | 69.2 | 6 – 23,830 |
| No judge | 83 – 248 | 66.8 | 0 – 270 |

### What survives, stated conservatively

1. **Judge runs hit the bug harder when they hit it.** Median 174 vs 1. Marginal on a rank test
   (p = 0.024), and **not significant after multiple-comparison correction**.
2. **Detection rate 5/5 vs 4/5.** Fisher exact p = 1.0 — no evidence of a difference.
3. **Nothing else.** Combos tied (t = 0.06); efficiency favours no-judge; hits-per-DELETE ranges
   overlap; early detection interleaves; both arms reach `/points`; both arms lock onto one verb;
   both arms can collapse into learned helplessness.
4. **The judge costs money and wall time for no measured discovery benefit.** 330 API calls across
   five runs to match a free local heuristic on every volume metric.

### Caveat that still cuts against the judge

The ablation is **favourable to the local arm** by construction: its per-endpoint reset pays a first
`DELETE /points` a novelty of 1.0 (reward 10), where the judge paid its own first hits 0.0–0.2
(reward 0–2). The local proxy had a 5–10× better incentive for the target. That explains *why* it
competes — it is not a flaw in the comparison, it is the comparison's finding: **a cheap
well-shaped local reward is enough.**

### Honest README framing

> A controlled 5-vs-5 ablation (50,000 episodes per run, clean database, identical reward plumbing,
> only the novelty term swapped) found **no measurable discovery-volume advantage** for the LLM judge
> over a free count-based novelty heuristic: 145 vs 142 unique bug combos (Welch t = 0.06), and the
> local heuristic was ahead on combos per execute. Judge runs found the hidden 5-step bug in 5/5 runs
> versus 4/5, and hit it harder when they did (median 174 vs 1 hits), but that difference is marginal
> (rank test p = 0.024) and does not survive correction for the number of metrics compared. The
> judge's measured contribution is interpretability — severity, category and root cause per finding —
> not exploration efficiency.

Do **not** claim the judge improves discovery count, efficiency, endpoint coverage, verb discipline,
early detection, or hit rate. The data contradicts all six.

### What would actually settle it

- n = 5 per arm with 4,000× within-arm spread cannot resolve a 1.02× effect. A real test needs
  ~20 runs per arm, or a lower-variance target than "hits on one bug".
- Better: hold the reward identical and measure the judge **only** on what it uniquely produces —
  false-positive filtering accuracy and root-cause quality against the 45-example golden set —
  rather than on agent exploration, where a free heuristic matches it.

---

## 16 neurons

2026-10-01. Complete, exit 0.

| Episode | Avg reward | Cum. combos | Executes | Ratio | Time | ms/exec |
|---|---|---|---|---|---|---|
| 10,000 | −4.780 | 13 | 59,782 | 17.1% | 57.3s | 0.96 |
| 20,000 | −4.468 | 28 | 99,278 | 28.4% | 86.3s | 0.87 |
| 30,000 | −3.947 | 34 | 165,024 | 47.1% | 123.0s | 0.75 |
| 40,000 | −3.968 | 46 | 153,389 | 43.8% | 133.6s | 0.87 |
| 50,000 | −4.062 | 49 | 124,954 | 35.7% | 118.0s | 0.94 |

The only run that *warms up*: execute ratio climbs 17.1% → 47.1% over the first three windows and
discovery is spread evenly (+13, +15, +6, +12, +3) rather than front-loaded. Also the only run
starting below −4.5 average reward.

**Judge:** 24 judged, 21 genuine, 3 false positives. All genuine `high`/`error_handling`; all three
FPs `low`/`validation` at confidence 0.4. Avg confidence 0.79.

Novelty on the 21 genuine bugs:

```
0.9  0.2  0.2  0.2  0.0  0.2  0.2  0.0  0.0  0.0  0.0
0.8  0.5  0.5  0.1  0.5  0.5  0.0  0.5  0.1  0.2
```
Mean **0.267** (highest of the sweep), 6 zeros. Reward: +56 genuine, −3 FP, +25 duplicates = **+78**.

**Distributions** (602,427 executes):

Endpoints: `/items` 601,564 (99.86%) · `/prices` 368 · `/discounts` 286 · `/points` 209
Methods: NONE 267,953 (44.5%) · **PUT 227,035 (37.7%)** · GET 41,633 · POST 37,286 · DELETE 21,445 (3.56%) · GET_ALL 6,632 · PATCH 443
Strategy: VALID 593,197 (98.5%) · NULL_INJECT 7,595 · rest <600
Intensity: MILD 602,097 (99.95%) · AGGRESSIVE 330 (0.05%)

Distinctively PUT-heavy — 37.7% of executes, against 0.08% at 32n and 0.18% at 64n.

---

## 32 neurons

2026-09-30. Complete, exit 0.

| Episode | Avg reward | Cum. combos | Executes | Ratio | Time | ms/exec |
|---|---|---|---|---|---|---|
| 10,000 | −3.729 | 38 | 196,374 | 56.1% | 168.0s | 0.86 |
| 20,000 | −3.912 | 40 | 169,631 | 48.5% | 158.2s | 0.93 |
| 30,000 | −3.920 | 41 | 168,552 | 48.2% | 159.0s | 0.94 |
| 40,000 | −3.927 | 48 | 167,516 | 47.9% | 131.1s | 0.78 |
| 50,000 | −3.929 | 51 | 167,503 | 47.9% | 124.3s | 0.74 |

Heavily front-loaded: **+38, +2, +1, +7, +3**. After the first window the agent finds roughly one
new combo per 10,000 episodes.

**Judge:** 24 judged, **all 24 genuine**, all `high`/`error_handling`. Confidence: one 0.7, eleven
0.8, twelve 0.9. Avg **0.85**.

Novelty on the 24 genuine bugs:

```
0.7  0.2  0.5  0.2  0.2  0.0  0.2  0.2  0.1  0.2  0.1  0.1
0.5  0.5  0.3  0.5  0.0  0.5  0.2  0.0  0.1  0.1  0.0  0.0
```
Mean 0.225, 5 zeros. Reward: +54 genuine, −0 FP, +27 duplicates = **+81**.

**Distributions** (869,576 executes):

Endpoints: `/items` 868,636 (99.89%) · `/prices` 412 · `/discounts` 300 · `/points` 228
Methods: NONE 414,525 (47.7%) · **GET 395,989 (45.5%)** · GET_ALL 29,453 · POST 24,052 · DELETE 4,245 (0.49%) · PUT 662 · PATCH 650
Strategy: VALID 678,428 (78.0%) · **BOUNDARY 185,765 (21.4%)** · TYPE_CONFUSE 1,949 · rest <800
Intensity: MILD 869,043 (99.94%) · AGGRESSIVE 533 (0.06%)

---

## 64 neurons — 🐛 hidden bug found

2026-09-30 → 10-01. Complete, exit 0.

**70 hits, first at episode 5,897.** The repaired counter fired correctly: banner printed once and
aligned, hits #2–#10 logged individually, the remaining 60 suppressed by the throttle, count exact
at 70. This validated the counter fix end-to-end — previously it was only unit-tested.

| Episode | Avg reward | Cum. combos | Executes | Ratio | Time | ms/exec |
|---|---|---|---|---|---|---|
| 10,000 | −3.982 | 32 | 162,367 | 46.4% | 381.1s | 2.35 |
| 20,000 | −3.907 | 41 | 173,445 | 49.6% | 630.3s | 3.63 |
| 30,000 | −3.900 | 42 | 176,240 | 50.4% | 5,564.9s | **31.58** |
| 40,000 | −3.709 | 44 | 201,531 | 57.6% | 5,836.3s | 28.96 |
| 50,000 | −3.683 | 44 | 205,165 | 58.6% | 6,747.6s | 32.89 |

Best final average reward of the sweep (−3.683), and the only run whose reward improves across all
five windows.

### It reached `/points` by building state, not scavenging it

Every `DELETE /points → 500` sequence creates its own points first (`POST /points → 201`), unlike
the discarded dirty-DB runs that picked up leftover ids via `GET_ALL /points`. Genuine
self-constructed discovery.

### ⚠ But probably not the *documented* chain

The detector matches on combo (`DELETE` + `POINTS` → 500) and cannot verify the price condition.
None of the logged sequences contain the documented
`ITEM → PRICE(neg) → DISCOUNT → POINTS → DELETE` chain — no `POST /prices` or `POST /discounts`
appears in any of them. The first hit (disc 027, episode 5,897):

```
GET_ALL /items 200 → POST /points 201 → POST /points 201 → POST /points 201 → DELETE /points 500
```

with the rule checker warning `POST /points created without parents: {'/prices', '/discounts'}`.
Either the documented "ancestor price < 0" description is stale, or this is a **different**
`DELETE /points` 500 reachable without the dependency chain. Confirm against the API source before
claiming the 5-step chain is solved.

### ⚠ The API collapsed mid-run

A 13× latency jump at window 3 (3.63 → 31.58 ms/execute) that never recovers, against 16 and 32
neurons holding 0.74–0.96 ms flat throughout. The agent issued 215,916 POSTs — the server is
degrading under rows it created itself. Discovery stops accordingly: **+32, +9, +1, +2, 0**.
Windows 3–5 contributed 3 of 44 combos for 4.9 hours of wall time. Treat anything after window 2 as
compromised; consider a shorter run or periodic DB truncation for 64-neuron experiments.

**Judge:** 30 judged, 29 genuine, 1 false positive. All genuine `high`/`error_handling`; FP is
`low`/`validation`. Confidence: one 0.7, fourteen 0.8, fourteen 0.9, FP at 0.4. Avg 0.83.

Novelty on the 29 genuine bugs:

```
0.9  0.2  0.5  0.5  0.3  0.5  0.2  0.2  0.2  0.2
0.5  0.2  0.2  0.2  0.0  0.2  0.2  0.0  0.0  0.0
0.2  0.2  0.0  0.0  0.2  0.0  0.2  0.0  0.2
```
Mean 0.214, 8 zeros. Reward: +62 genuine, −1 FP, +14 duplicates = **+75**.

Only 14 of 44 discoveries (31.8%) were rule-filtered — the lowest duplicate rate of the sweep, and
the only run where genuine findings out-pay duplicates (62 vs 14).

**Distributions** (918,748 executes):

Endpoints: `/items` 784,621 (85.40%) · **`/points` 127,140 (13.84%)** · `/prices` 5,073 (0.55%) · `/discounts` 1,914 (0.21%)
Methods: NONE 447,991 (48.8%) · GET_ALL 251,518 (27.4%) · POST 215,916 (23.5%) · PUT 1,654 · PATCH 672 · GET 517 · **DELETE 480 (0.05%)**
Strategy: VALID 916,274 (99.73%) · NULL_INJECT 1,233 · NEGATIVE 628 · rest <300
Intensity: MILD 764,151 (83.2%) · AGGRESSIVE 154,597 (16.8%)

DELETE is vanishingly rare (480 of 918,748) yet produced all 70 hidden-bug hits — the agent found
the right action and used it sparingly rather than spamming it.

---

## γ = 0.1 (short horizon), 16 neurons — total collapse

2026-10-01. Complete, exit 0. Identical to the 16-neuron run except **γ 0.99 → 0.1**.

**The agent stopped acting almost entirely.** 694 executes across the whole run, against 602,427
at γ=0.99 — **868× fewer requests** from the same 1,750,000 actions.

| Metric | γ=0.99 | **γ=0.1** |
|---|---|---|
| Unique bug combos | 49 | **12** |
| Total executes | 602,427 | **694** |
| Executes as share of all actions | 34.4% | **0.0397%** |
| Execute ratio (per window) | 17.1% → 47.1% | **0.0% – 0.1%** |
| Avg reward | −4.780 → −4.062 | **−5.248 flat** |
| Sent to judge | 24 | 2 |
| Wall time | 518s | 52.4s |

| Episode | Avg reward | Cum. combos | Executes | Ratio | Time |
|---|---|---|---|---|---|
| 10,000 | −5.248 | **0** | 120 | 0.0% | 9.9s |
| 20,000 | −5.245 | 11 | 211 | 0.1% | 12.5s |
| 30,000 | −5.248 | 11 | 101 | 0.0% | 9.8s |
| 40,000 | −5.248 | 12 | 117 | 0.0% | 10.1s |
| 50,000 | −5.248 | 12 | 145 | 0.0% | 10.1s |

**Average reward sits at 99.96% of the theoretical floor** (35 steps × −0.15 = −5.25) in four of
five windows. The agent is doing nothing but dial-turning, start to finish.

### Why short horizons break this agent

Counter-intuitively, γ=0.1 should favour *immediate* reward, and executing pays 0 or better while
dial-turning pays −0.15. But the execute action is **gated** — `mask[execute] = strategy_builder.is_ready()`
— so reaching it requires a specific multi-step chain of dial-turner actions first. At γ=0.1 a
dial-turn three steps before an execute is worth `0.1³ = 0.001` of that execute's value. Credit
cannot propagate back through the setup chain, so the agent never learns that dial-turning leads
anywhere, and the execute action is almost never available.

This is a **credit-assignment failure, not an exploration failure** — and it is the inverse of the
usual reading of γ. The setup chain means this environment *requires* a long horizon.

### The one burst

All 11 of the first window-2 combos appeared within two seconds (episodes 16,803–16,819,
timestamps 10:45:00–10:45:02), then nothing for the rest of the run bar a single combo at episode
32,723. Window 2 is the only window containing any DELETE traffic (42 of 45 total). The agent
stumbled into DELETE, was rewarded, and the reward failed to stick.

**Judge:** only 2 of 12 discoveries reached it (83.3% rule-filtered, the highest of any run). Both
genuine, `high`/`error_handling`, confidence 0.8. Novelty 0.9 and 0.2 — mean **0.55**, the highest
recorded, but on a sample of two. Reward: +11 genuine, +10 duplicates = **+21**.

**Distributions** (694 executes):

Endpoints: `/items` 678 (97.7%) · `/discounts` 9 · `/prices` 5 · `/points` 2
Methods: **GET_ALL 616 (88.8%)** · DELETE 45 · NONE 28 · POST 4 · GET 1

The agent reduced to a GET_ALL loop.

---

## Cross-run observations

1. **Only 64 neurons escapes `/items`.** 16n and 32n sit at 99.86% / 99.89%; 64n drops to 85.40%.
   Network capacity, not reward shaping, is what moved exploration — none of the gamma, epsilon or
   decay changes achieved this on a clean DB.

2. **ε = 0.025 is the biggest win found** — 4.5× the combos, 2.5× the hidden-bug hits, and the
   earliest detection, from the *smallest* network. Sweep ε further (0.02 / 0.03 / 0.04).

3. **Decay vs none buys sustained execution. The LLM's only measurable edge is the hidden bug.**
   Flat +10 collapses to a 0% execute ratio; a free local count decay fixes that. At 3/3 per arm the
   judge shows no significant advantage on combos (136 vs 99, Welch t = 0.67) or efficiency
   (18.1 vs 13.1 per 100k). It does find the hidden bug in 3/3 runs vs 2/3, with non-overlapping hit
   ranges ([6, 174] vs [0, 1]) — a 94x gap.

4. **Verb lock-in happens in both arms, all ten runs.** Every run concentrated on one verb, and the
   judge does not prevent it. Nor does it uniquely reach /points: no-judge #5 put 26.0% of traffic
   there, inside the judge arm's 0.18-51.2% range. Endpoint reach overlaps between arms.

5. **Severity is not perfectly constant after all.** Judge #2 produced one `medium` verdict and one
   `high` on a false positive. Rare, but the "severity is binary and collinear" claim needs the
   qualifier.

3. **γ must stay long.** The gated execute action makes this a multi-step credit-assignment
   problem; γ=0.1 collapses the agent to 0.04% execute rate and 99.96% of the reward floor. Do not
   treat γ as a free exploration knob — the setup chain is the binding constraint.

4. **Judge category carries no information.** 168 judged discoveries across the sweep; every genuine
   verdict is `high` / `error_handling`, every false positive `low` / `validation`. The `10/6/3`
   severity map degenerates to a constant. Novelty (0.0–0.9) is the only term with real variance.

5. **Novelty falls as capacity rises** (0.267 → 0.225 → 0.214) — larger networks revisit the same
   root cause more often, because they exploit a found pattern harder.

6. **Duplicates out-pay genuine findings at 16n and 32n** (+25 vs +56, +27 vs +54 — comparable), but
   not at 64n (+14 vs +62). The rule filter's consolation `+1` is a significant reward source
   whenever discovery is shallow.

7. **~45–49% of executes carry no HTTP method** in every γ=0.99 run. These cannot issue a request and
   take the −0.15 no-response penalty — the dominant drag on average reward throughout.

8. **The reward signal is drowned by the step penalty.** ~1.75M actions at −0.15 for dial-turners
   vastly outweighs +75 to +81 of total discovery reward in every run.

---

## Known code issues

1. **Hidden-bug counter** (`SarsaRestTester.py:339`) — was dead: it tested
   `startswith("DELETE+POINTS+")` while `:177` builds the combo as
   `"HttpType.DELETE+Endpoint.POINTS+..."`. **Fixed and now validated by a live hit** (64-neuron
   run, 70 detections). The prefix is derived from the same enums (`HIDDEN_BUG_COMBO_PREFIX`), the
   banner sizes itself to its content so no line is cut, and repeat hits are throttled (first 10,
   then every 1000th) while the count stays exact.

2. **Duplicate normalisation drops status on collapsed steps** (`eval_pipeline/rule_check.py`,
   `is_duplicate`). Consecutive same-`(method, endpoint)` calls collapse to the first, keeping only
   its status, so a sequence ending 500 can hash identical to one ending 201 and be discarded.

3. **The target API degrades under its own load.** At 64 neurons latency rose 13× mid-run at
   constant request rate. Restart the DB per run, and consider truncating mid-run for long
   experiments.

4. **Runs are not reproducible across DB states.** The RNG is seeded but the environment is not;
   API responses drive the state transitions. See Methodology.

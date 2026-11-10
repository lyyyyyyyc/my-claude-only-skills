# Model Selection Diagnostics

Use this reference to turn model selection into an auditable decision process. Apply only the task-specific sections that match the current problem. Do not convert example constants, algorithm rankings, or contest folklore into universal rules.

## 1. Evidence discipline

Use one status for each important route:

| Status | What supports it | What may be claimed |
|---|---|---|
| `题面候选` | task wording and stated conditions | plausible route and required validation plan |
| `诊断支持的暂定路线` | inspected current data and stated assumptions | data-informed provisional preference |
| `试验支持的路线` | recorded pilot or fair comparison | observed comparative result in that protocol |
| `完成验证后选定` | specified independent validation completed | selected route within the recorded scope |

Separate current-problem facts from external methods, teaching examples, and planning assumptions. A recommendation is not evidence that it has won a comparison.

Use `best` only with scope: data, candidate set, information boundary, metrics, assumptions, and budget. A proven optimum for a specified optimization model is different from an empirical preference among candidate modeling routes.

## 2. Task type and deliverable

Before selecting methods, complete this table for every material subtask.

| Type | Diagnostic question | Typical deliverable | Typical validation target |
|---|---|---|---|
| Evaluation/ranking | Are existing alternatives scored rather than changed? | score, weight, rank, or priority | rank stability and criterion traceability |
| Supervised classification | Are meaningful classes defined before prediction? | label, probability, or decision rule | legal out-of-sample discrimination and task loss |
| Unsupervised grouping | Must classes be discovered and described? | grouping plus profiles | stability, structure, and interpretability |
| Prediction | Is a future/unseen quantity required? | point forecast, interval, or distribution | legal holdout accuracy and calibration/coverage if needed |
| Optimization | Are decision variables adjusted under constraints? | feasible decision and objective value | feasibility, objective recomputation, and solution status |
| Mechanism/inverse estimation | Must an equation explain data or recover parameters? | equations, parameters, or reconstruction | physical consistency and forward reconstruction |

Mixed tasks may contain several rows. Interpret ambiguous words from required action and information:

- `分类`: defined labels imply classification; unknown latent groups imply grouping;
- `影响因素`: decide whether the task asks for association, explanation, prediction, or causation;
- `最优`: decide whether the task ranks fixed alternatives or optimizes adjustable decisions with constraints.

## 3. Data diagnosis before candidate comparison

When data affects selection, fill this table with actual findings.

| Check | Inspect | Selection consequence |
|---|---|---|
| Observational unit and effective sample size | identify independent entities and repeated measures | bound complexity; choose grouped/hierarchical validation if needed |
| Targets and labels | define response, prediction time, class meaning, and label source | choose supervised/unsupervised route and legal metrics |
| Time, space, and availability | ordering, adjacency, and information known when acting | prevent future leakage; select split and features |
| Missingness | rate, concentration, and observable associations | justify deletion, imputation, missing indicators, or explicit modeling |
| Anomalies | units, collection process, domain limits, and provenance | distinguish errors from legitimate extremes; compare justified treatments |
| Imbalance and support | class prevalence, zero/near-zero targets, covariate coverage | choose metrics, thresholds, and extrapolation cautions |
| Dependence and collinearity | repeated entities, correlation structure, proxy variables | avoid invalid folds and overconfident interpretations |

Fit learned preprocessing only on permitted training data: imputation, scaling, feature selection, dimensionality reduction, target encoding, and threshold tuning all have the same information boundary as the model.

Do not impose fixed sample-size cutoffs, fixed fold counts, fixed thresholds, or a universal sensitivity range. Choose them from the task, data structure, and computational constraints.

## 4. Baseline, comparison, and recovery

### Baseline

Include a simple runnable baseline whenever it meaningfully answers the same task:

- prediction: persistence, seasonal-naive, or simple trend;
- classification: majority-class and/or simple regularized model;
- mechanism: reduced physical model;
- optimization: feasible historical, rule-based, or greedy solution;
- ranking: transparent equal-weight or stated-rule comparator.

The baseline is a decision instrument, not a mandatory loser. It may be selected if it best satisfies the stated objective, reliability, constraints, and interpretability.

### Fair comparison

Define the protocol before inspecting final results:

| Item | Must state |
|---|---|
| Target | same required output and decision horizon |
| Information | fields, time boundary, and preprocessing allowed to each route |
| Data/scenarios | legal split, resampling, entity/time isolation, or uncertainty set |
| Metrics | direction, main/secondary role, class averaging or forecast horizon |
| Constraints | hard feasibility checks and original-system recomputation |
| Budget | tuning scope, solver limit, restart count, runtime or evaluation budget |
| Randomness | seeds, repetitions, and summary distribution |
| Final audit | untouched holdout, reconstruction, conservation, calibration, or high-fidelity check |

Report failed, infeasible, or timeout runs. Do not compare methods on different information sets or select a predictor by repeatedly looking at the final test set.

### Recovery loop

If the main route loses to a meaningful baseline, violates hard constraints, fails a legal validation, or changes conclusion under justified perturbation:

1. recheck task type, exact output, units, and constraint interpretation;
2. audit data quality, availability, leakage, and feature construction;
3. revisit assumptions, interface representation, and candidate fit;
4. simplify, repair, or switch routes with a recorded reason;
5. rerun the same legal comparison.

Do not use a more complex algorithm as the default response to a failed validation.

## 5. Grouping

Before comparing grouping algorithms, define scaling and distance, then inspect plausible shape, density variation, overlap, and noise. Compare methods with genuinely different structural assumptions.

For an unknown class count, use compatible diagnostics to generate candidates, then test stability and whether profiles support a coherent interpretation. A projection or a single internal index is supporting evidence, not proof.

Deliver for each accepted group: size, key feature summary, group difference, descriptive label, and treatment of noise or boundary objects.

Internal indices measure the chosen geometric structure. ARI compares two partitions; interpret it as recovery accuracy only when an independent reference labeling exists. If no stable, interpretable grouping is supported, say so and diagnose feature, distance, scale, parameter, and data-quality alternatives before deleting observations.

## 6. Classification and decision thresholds

Start with an interpretable simple route when compatible with the boundary and data. Add flexible methods only when nonlinear structure, interactions, or validation results justify them.

For imbalance, report class prevalence and use task-aligned measures beyond accuracy. Define the positive class, averaging convention, and error consequences.

Treat the decision threshold as part of the model. Choose it from stated costs, constraints, or a declared utility on validation data; reserve final test data for assessment. A threshold of `0.5` is neither mandatory nor forbidden. When probabilities drive downstream decisions, examine probability calibration separately from discrimination.

## 7. Prediction and explanatory analysis

Engineer features from lawful information only. For every feature, state construction, meaning, availability at prediction time, and how it is fitted without leakage.

For time-dependent prediction, preserve causal order and state horizon, rolling/fixed origin, and update policy. Compare with a relevant naive baseline. Report errors by relevant segment or horizon when aggregate error hides failure. Use interval coverage and width only when intervals are required or used downstream.

Do not equate training fit with prediction quality. Do not interpret correlation, model importance, or a coefficient without considering dependence, covariate structure, collinearity, and the difference between association and causation.

## 8. Optimization

Specify:

- indexed decision variables, physical meaning, units, domains, and valid bounds;
- objectives and term units;
- hard constraints, soft penalties, state transitions, initial/terminal conditions, and parameter provenance;
- model structure separately from solver, heuristic, or software.

Translate natural-language constraints only after checking whether equality/inequality, time index, resource accounting, and exceptions match the current task. Big-M or indicator formulations require defensible bounds; do not silently convert a hard requirement into a penalty.

Prefer a structure-exploiting exact or decomposed route when practical. If using a heuristic or approximation, state why, compare under equivalent budget, report feasibility and repeated-run behavior, and distinguish proven optimum, bounded-gap solution, and best known feasible solution.

For multiple objectives, state scaling and preference source. Use suitable scalarization or constraint approaches, report representative trade-offs, and do not imply that one weight scan proves all Pareto trade-offs were found.

## 9. Uncertainty and sensitivity

At every cross-question interface, state whether uncertainty is passed as a point estimate, interval, probability model, or scenario set. Keep units, time granularity, and dependency assumptions consistent.

Different uncertainty analyses answer different questions:

- finite scenario analysis: behavior under the specified cases;
- stochastic/probabilistic model: behavior under the stated distribution and risk definition;
- robust model: worst-case behavior over the declared uncertainty set;
- fixed-plan stress test: whether the original decision remains feasible/effective;
- re-optimization study: how the best decision changes when conditions change.

Do not claim a probability guarantee from a method name or from endpoint checks alone. Choose perturbation ranges from data, measurement limits, domain constraints, or explicit assumptions. Include joint scenarios when dependence or interactions matter.

For rankings, perturb valid weights or methods and report rank ranges, top-k frequency, or reversals. These are robustness results under the specified experiment, not probabilities of an objectively true rank.

## 10. Minimum evidence artifacts

Use only artifacts that answer a real question:

| Task | Useful evidence artifacts |
|---|---|
| Grouping | scale/distance rationale, candidate class-count evidence, profiles, stability or reference-label context |
| Classification | prevalence, error trade-off, confusion matrix, threshold rationale, calibration when needed |
| Prediction | legal holdout plot/table, baseline comparison, error by horizon/segment, interval diagnostics when needed |
| Optimization | variable/constraint audit, feasibility recomputation, trade-off table/frontier, gap/bound or restart distribution |
| Ranking | criteria/weight provenance, perturbation and rank-stability output |
| Cross-question decision | interface table, uncertainty propagation, fixed-plan and re-optimization checks where relevant |

Every figure or table must be interpreted in prose: what question it answers, what evidence it supplies, and what conclusion it does not establish.

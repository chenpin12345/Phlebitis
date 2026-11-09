# Experimental discipline for small-data medical ML: overfitting to validation/test sets, researcher degrees of freedom, pre-registration, learning curves, and a first-phase experiment plan (phlebitis photo prototype)

All access dates are 2026-10-30. Source grades: [A] official / reporting standard; [B] systematic review / top journal / top conference; [C] other peer-reviewed; [D] preprint; [E] blog / code / forum (supporting only).
Labels used on claims: **[研究證據]** research evidence; **[業界慣例]** industry or community convention; **[推論]** my inference for this project.
"Verified" means I fetched the page (or an authoritative abstract or record) in this session. Items I did not verify are marked **(未驗證)** and given without a URL.

Project anchor used for every applicability judgement: about 120 photos from **14 patients**. Binary: 47 phlebitis vs 9 normal. Staging: normal 9 / stage 1 23 / stage 2 24. About 24 photos have boxes. One annotator. Evaluation is patient-grouped StratifiedGroupKFold (3-fold), with an optional held-out set of about 20% of patients (about 3 patients, 14–18 photos). The target is about 1,000 photos with balanced classes. No auto-training and no auto-deploy.

---

## Q1. Is there evidence that ML overfits validation and test sets, through adaptive analysis, researcher degrees of freedom and leakage? How does this apply at n = 14 patients?

### Takeaway
On **large, shared** benchmarks, adaptive reuse of a test set causes surprisingly little overfitting (Recht 2019; Roelofs 2019). On **small** data, selecting a model or hyperparameters with the same cross-validation that reports the score produces large optimistic bias: on pure-noise data, a naive CV error can come out below 30% while the true error is 50% (Varma & Simon 2006). Cawley & Talbot (2010) show the same for model-selection criteria. Medical imaging adds small test sets, dataset reuse and leakage (Varoquaux & Cheplygina 2022; Kapoor & Narayanan 2023). With 14 patients the project sits in the high-risk regime. The reassuring Kaggle and ImageNet results do not transfer.

### Cited Findings

**Adaptive overfitting on large benchmarks (mostly reassuring, but only for large test sets)**
- [B][研究證據] Recht, Roelofs, Schmidt & Shankar (ICML 2019, "Do ImageNet classifiers generalize to ImageNet?") built new test sets following the original procedures. They report "accuracy drops of 3% – 15% on CIFAR-10 and 11% – 14% on ImageNet". The authors conclude the drops "are not caused by adaptivity" but by "the models' inability to generalize to slightly 'harder' images". Model rankings were largely preserved. Note: the brief said "3–15%" for ImageNet, but the abstract gives **11–14% for ImageNet**; 3–15% is CIFAR-10. — [arXiv:1902.10811](https://arxiv.org/abs/1902.10811) (abstract verified 2026-10-30)
  - Applicability [推論]: the lesson for this project is not "adaptivity is harmless". It is that **distribution shift (new patients, new photographers, new lighting) can cost more than adaptivity**. A phlebitis model judged on 3–5 test patients per fold says almost nothing about new wards or cameras.
- [B][研究證據] Roelofs et al. (NeurIPS 2019, "A Meta-Analysis of Overfitting in Machine Learning") analysed "over one hundred machine learning competitions" on Kaggle and found "little evidence of substantial overfitting". The brief's figure of "120" does not appear in the abstract, which says only "over one hundred". — [NeurIPS proceedings page](https://papers.nips.cc/paper/9117-a-meta-analysis-of-overfitting-in-machine-learning) (verified); companion [Berkeley tech report EECS-2019-102](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2019/EECS-2019-102.html)
  - Counter-evidence and applicability: the analysis targeted competitions with large test sets (the OpenReview PDF says it focused on competitions with ≥1,000 submissions; [OpenReview PDF](https://openreview.net/pdf/98fdb4bb89fd868a5dda9f827133eec6e11bb4fa.pdf), from the search snippet only). Varoquaux & Cheplygina (below) re-analysed 8 **medical** Kaggle challenges. In pneumothorax segmentation, "overfitting [was] larger than the winner gap". In most of the others, evaluation noise exceeded the gap between winners. **Not applicable to a 14-patient test pool.** [推論]
- [B][研究證據] Dwork, Feldman, Hardt, Pitassi, Reingold & Roth, "The reusable holdout" (Science 2015): "Reusing a holdout set adaptively multiple times can easily lead to overfitting to the holdout set itself". They propose a mechanism (Thresholdout) that answers holdout queries through noise and thresholding, which allows many adaptive reuses. — [arXiv:1506.02629](https://arxiv.org/abs/1506.02629) (abstract verified). The Science citation is commonly given as 349(6248):636–638, doi 10.1126/science.aaa9375 **(未驗證: not shown on the arXiv page)**.
- [B][研究證據] Blum & Hardt, "The Ladder: A reliable leaderboard for machine learning competitions" (ICML 2015). They address how to keep a leaderboard faithful when teams adaptively submit, and introduce a parameter-free variant "with no tuning required whatsoever". — [arXiv:1502.04585](https://arxiv.org/abs/1502.04585) (abstract verified). The mechanism (the leaderboard updates only when a submission beats the previous best by more than a margin, with rounded scores) is from my knowledge of the paper **(未驗證 on the fetched page)**.
  - Applicability [推論]: the Ladder idea maps directly onto a local workbench. Show the user a **rounded** CV score, and flag a new run as "better" only if it beats the incumbent by more than a pre-set margin. This reduces how much information leaks from repeated peeking.

**Selection bias from CV-based model selection (directly relevant to small data)**
- [B][研究證據] Varma & Simon 2006, BMC Bioinformatics 7:91, doi:10.1186/1471-2105-7-91. They simulated "null" microarray data where the true error is 50%. With parameters tuned by minimizing CV error, the CV error was <30% on 18.5% of datasets for Shrunken Centroids and on 38% for SVM. Mean CV estimates were 37.8% and 41.7% against a true 50.0%. "Performance of the optimized classifiers on the independent test set was no better than chance." "A nested CV procedure provides an almost unbiased estimate of the true error": 54.2% vs 50.0% for Shrunken Centroids, and 35.3% vs 32.0% for SVM on non-null data. — [PMC1397873](https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/) (verified)
- [B][研究證據] Cawley & Talbot 2010, JMLR 11:2079–2107, "On over-fitting in model selection and subsequent selection bias in performance evaluation": "the degradation in performance due to over-fitting the model selection criterion can be surprisingly large". They recommend that performance evaluation be unbiased with respect to the whole selection procedure, which means nested evaluation. — [JMLR page](https://jmlr.org/papers/v11/cawley10a.html) (verified)
  - Applicability [推論]: the workbench lets the user choose among EfficientNet frozen or unfrozen, optimizer, learning rate, class weights, DINOv2+LR C, YOLO size and so on, then read the same 3-fold summary. **That summary is the selection criterion.** Reporting it as performance is exactly the Varma & Simon / Cawley & Talbot bias. With 14 patients, 9 normal photos and per-fold test sets of about 4–5 patients, the variance of the criterion is huge, and the bias grows with the number of configurations compared.

**Researcher degrees of freedom and seed variance**
- [B][研究證據] Simmons, Nelson & Simonsohn 2011, Psychological Science 22(11):1359–1366, doi:10.1177/0956797611417632, "False-Positive Psychology". Undisclosed flexibility (several dependent variables, optional stopping, covariates, dropping conditions) inflates false positives far above the nominal 5%. Combining these flexibilities gives about **61% (60.7%)**. Optional stopping alone raises the rate by about 50% relative. — figures confirmed only through secondary sources, e.g. [BITSS course page](https://www.bitss.org/education/mooc-parent-page/week-2-publication-bias/is-there-a-credibility-crisis/false-positive-psychology-2/) and [Gelman blog 2012](https://statmodeling.stat.columbia.edu/2012/02/16/false-positive-psychology/) ([E], supporting only). **I did not fetch the original full text; check the Table 1 value before quoting.**
- Gelman & Loken, "The garden of forking paths" (2013 working paper; American Scientist 2014 "The statistical crisis in science"). Even without conscious fishing, data-contingent analysis choices create multiplicity. **(未驗證 in this session; no URL given.)**
- [B/D][研究證據] Bouthillier et al., "Accounting for variance in machine learning benchmarks" (submitted to MLSys 2021). "variance due to data sampling, parameter initialization and hyperparameter choice impact markedly the results". "Adding more sources of variation to an imperfect estimator approaches better the ideal estimator at a 51 times reduction in compute cost." — [arXiv:2103.03098](https://arxiv.org/abs/2103.03098) (verified; the page says "submitted to MLSys 2021"). Their specific recommendation (randomize data splits, seeds and hyperparameter-optimization seeds jointly, and judge with a probability-of-improvement P(A>B) threshold rather than mean differences) is from my knowledge of the full paper **(未驗證)**.
- [D][研究證據] Picard 2021, "torch.manual_seed(3407) is all you need" (arXiv preprint, grade D as the brief requires). The author scanned "up to 10^4" seeds on CIFAR-10 and found that "even if the variance is not very large, it is surprisingly easy to find an outlier that performs much better or much worse than the average." — [arXiv:2109.08203](https://arxiv.org/abs/2109.08203) (verified)
- Lipton & Steinhardt 2019, "Troubling trends in machine learning scholarship" (ACM Queue / arXiv 1807.03341). They describe failure to identify the sources of empirical gains (e.g., tuning rather than architecture), among other problems. **(未驗證 in this session.)**

**Small-data medical imaging specifics**
- [B][研究證據] Varoquaux & Cheplygina 2022, npj Digital Medicine 5:48, doi:10.1038/s41746-022-00592-y, "Machine learning for medical imaging: methodological failures and recommendations for the future" — [PMC9005663](https://pmc.ncbi.nlm.nih.gov/articles/PMC9005663/) (verified):
  - In an Alzheimer's diagnosis meta-analysis, "studies with larger sample sizes tend to report worse prediction accuracy". The text cites 478 studies; the figure caption says ">500". This internal inconsistency is in the source.
  - "Overfitting by observer": researchers tune against CV test folds. Reusing the same datasets across studies creates implicit multiple comparisons.
  - Across 8 medical Kaggle challenges, "6 of the 8 challenges are in the diminishing returns category". Evaluation noise exceeded the winner gap in several, and pneumothorax showed overfitting larger than the winner gap.
  - Only "6% of segmentation challenges surveyed" and "15% out of 410 popular computer science papers" used a statistical test.
  - They recommend test sets of "at least several hundreds samples, ideally thousands or more" with confidence intervals. They also say "Preregistration or registered reports can bring more robustness and trust", noting that ML rarely acquires new data, which makes this harder. They point to Varoquaux 2018 (NeuroImage), "Cross-validation failure: small sample sizes lead to large error bars".
- [B][研究證據] Kapoor & Narayanan, "Leakage and the reproducibility crisis in machine-learning-based science", Patterns 4:100804 (2023), doi:10.1016/j.patter.2023.100804. The published version reports that leakage affects "at least 294 papers across 17 disciplines". It gives a taxonomy of **8 leakage types** and proposes **model info sheets**. **Version conflict:** the arXiv preprint abstract currently says "17 fields where errors have been found, collectively affecting 329 papers". — [arXiv:2207.07048](https://arxiv.org/abs/2207.07048) (verified 329); [NSF PAR copy of published version](https://par.nsf.gov/servlets/purl/10513990) (294, from the search snippet; the Cell/Patterns page returned 403). Cite 294 for the Patterns version and state which version you use.
  - Relevant leakage types for this project [推論]: (a) **non-independence between train and test**, i.e., multiple photos of the same patient or the same IV site split across folds (already mitigated by patient-grouping); (b) preprocessing or normalisation fitted on all data; (c) **feature or threshold selection on the test fold**; (d) temporal leakage if later photos of a patient show lesion progression.
- [B][研究證據] Liu et al. 2019, Lancet Digital Health, systematic review and meta-analysis of deep learning vs health-care professionals in medical imaging (studies 2012 to 6 June 2019). In **25** studies an out-of-sample external validation was performed. **14** compared deep learning and professionals in the same sample. In those 14, pooled sensitivity was 87.0% vs 86.4% and pooled specificity 92.5% (95% CI 85.1–96.4) vs 90.5% (80.6–95.7). The authors flagged poor reporting. — [DOAJ record, Lancet Digit Health Oct 2019](https://doaj.org/article/c73287f0c1f24d9abbb2cb81ce6add3e) (from the search snippet). The often-quoted "82 included studies" and "31,587 screened" **(未驗證: I could not open the PRISMA flow; UCL PDF returned 403)**. DOI commonly given as 10.1016/S2589-7500(19)30123-2 **(未驗證)**.

### Inferences
- [推論] **Bias magnitude scales with (number of configurations compared) × (noise of the criterion).** Noise at n = 14 patients is extreme. Example: with 9 normal photos, observing 0 false positives gives a Wilson 95% CI for the normal false-positive rate of **0%–29.9%**, and 1/9 gives **2.0%–43.5%** (my calculation: Wilson, z = 1.96). The clustering of photos within patients makes the true uncertainty larger still. Any configuration that "wins" by a few percentage points is indistinguishable from seed or fold luck.
- [推論] The **9 normal photos probably come from even fewer patients**. Balanced accuracy and the normal false-positive rate therefore rest on a handful of independent units. Any per-fold normal FPR is close to meaningless, and only the pooled out-of-fold estimate should be reported.
- [推論] "Snapshot diff comparisons" in the workbench are a forking-paths engine unless (i) every run is logged, including failures, (ii) comparisons use identical splits and seeds, and (iii) a pre-set improvement margin and repeated-split variance are shown next to each diff.
- [推論] Now (14 patients): treat every number as **feasibility/descriptive**. Future (~1,000 photos, perhaps 100+ patients): the Recht/Roelofs regime begins to apply only if the locked test set reaches several hundred **patients' worth** of independent units, which Varoquaux & Cheplygina's "several hundreds samples" implies. A ~1,000-photo dataset with ~5–10 photos per patient may still have only ~100–200 independent patients.

### Gaps
- I did not fetch the original Simmons et al. 2011 Table 1 (61% figure checked only through secondary sources), the Gelman & Loken paper, Lipton & Steinhardt, or the Science version of Dwork et al.
- Liu et al. 2019: total included studies (82?) not verified.
- 未找到可靠證據 on overfitting magnitude specific to **wound / skin-site photo classification with <20 patients**. The closest evidence is the general small-sample CV literature above.

---

## Q2. How should an ML prediction-model study be pre-registered, what should be fixed in advance, and how can a local platform enforce it?

### Takeaway
Registration is still rare in ML prediction research: 1 of 46 oncology ML prognostic studies was registered (Collins et al. 2024). Reporting standards now explicitly ask for it (TRIPOD+AI items on protocol and registration). An ML-specific two-phase template exists: fix the problem, data, splits, metrics and baselines **before training**, and the final model **before testing** (Hofman et al. 2023, preprint). A local workbench can enforce much of this mechanically: hashed split files, a locked test set with an audit log and written justification for unlock, a registry of all runs including failures, and an evaluation budget.

### Cited Findings
- [B][研究證據] Collins et al. 2024, J Clin Epidemiol 165:111199, doi:10.1016/j.jclinepi.2023.10.015, "Open science practices need substantial improvement in prognostic model studies in oncology using machine learning". It is a systematic review of **46** ML prognostic-model publications in oncology (MEDLINE, Dec 2022):
  - only **1** reported study-protocol availability and only **1** was registered
  - 2 (4%) shared data
  - 12 (26%) had code-sharing statements
  - 8 (18%) mentioned a reporting guideline and 4 used TRIPOD.
  - Sources: [Birmingham research portal](https://research.birmingham.ac.uk/en/publications/open-science-practices-need-substantial-improvement-in-prognostic/), [FORRT summary](https://forrt.org/curated_resources/open-science-practices-need-substantial/), from search snippets of these records.
- [A][業界慣例/報告標準] TRIPOD+AI (Collins et al., BMJ 2024;385:e078378) has a 27-item checklist plus a 13-item abstracts checklist and supersedes TRIPOD 2015. Its "Open science" items include **protocol (18c)**: say where the protocol can be accessed, or state that none was prepared. They also include **registration (18d)**: give the register name and number, or state that the study was not registered. Both apply to development (D) and evaluation (E) studies. — item numbers from a [Cambridge-hosted supplementary checklist (docx)](https://static.cambridge.org/content/id/urn%3Acambridge.org%3Aid%3Aarticle%3AS2056472425000328/resource/name/S2056472425000328sup001.docx) and the [EQUATOR Network listing](https://www.equator-network.org/?p=11341) (search snippets; **confirm item numbering against the BMJ original before citing item numbers**).
  - Implication [推論]: TRIPOD+AI does **not** require registration; it requires you to **state** whether there was a protocol or registration. "Not registered" is reportable. For a research prototype, an internal time-stamped protocol (git commit + hash) plus optional OSF registration satisfies 18c/18d honestly.
- [A][報告標準] PROBAST+AI (BMJ 2025;388:e082505, published 24 March 2025) is the update of PROBAST for regression and AI/ML prediction models. It has separate development and evaluation parts with four domains: participants and data sources, predictors, outcome, analysis. Development uses 16 signalling questions and evaluation uses 18. — [Oxford ORA record](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370); [Birmingham portal](https://research.birmingham.ac.uk/en/publications/probastai-an-updated-quality-risk-of-bias-and-applicability-asses/) (search snippets). The exact wording of the analysis-domain questions on overfitting, optimism and selection was **未驗證**.
- [D][研究證據] Hofman, Chatzimparmpas, Sharma, Watts & Hullman 2023, "Pre-registration for Predictive Modeling", arXiv:2311.18807 (preprint, no journal version found). — [arXiv HTML](https://arxiv.org/html/2311.18807) (verified); template repo [ml-preregister/preregistration-template](https://github.com/ml-preregister/preregistration-template) [E]
  - **Phase A (before training or validation):** research question; outcome and its measurement; features and planned feature engineering; construction of training/validation data; **construction of the test set**; filtering and transformations; **metrics including classification thresholds**; **baselines**. Exploring structure (missingness, ranges) is allowed before Phase A; examining feature–outcome relationships is not.
  - **Phase B (after validation, before testing):** prediction method; CV scheme, **random seeds, hyperparameters, compute budget**; **confirmation the test data has not been accessed**; planned secondary or exploratory analyses; explicit reporting of any deviation from Phase A.
  - Limitations the authors state: "not a panacea". It cannot verify adherence and does not fix poor proxy metrics, unrepresentative data or distribution shift. Publication bias remains, and they point to registered reports. Several participants did not grasp that test data should be accessed once. The evidence is a qualitative study of 6 ML PhD students in a 90-minute session.
  - Supporting commentary: [Hullman on Statistical Modeling blog, 2023-12-06](https://statmodeling.stat.columbia.edu/2023/12/06/exploring-pre-registration-for-predictive-modeling/) [E].
- [A/E][業界慣例] OSF / Center for Open Science. The general **OSF Preregistration** template is the most common. A **Secondary Data Preregistration** template exists for existing datasets (osf.io/x4gzt). The **Registered Report Protocol** template is only for use after a journal's in-principle acceptance. COS says 11 templates are available. — [OSF help: Select a Registration Template](https://help.osf.io/hc/en-us/articles/360019738794-Select-a-Registration-Template); [COS blog guide](https://www.cos.io/blog/choosing-preregistration-template-guide-for-researchers); [LDbase description of secondary-data template](https://ldbase.org/resources/templates/preregistrations-using-secondary-data-analysis) (search snippets).
  - Applicability [推論]: this project's existing ~120 photos are **already collected and already looked at**. The "Secondary Data Preregistration" template (which asks what you already know about the data) is the honest fit for phase 1. The **future** photos (toward ~1,000) can be covered by a standard preregistration filed **before** they are collected or labelled. That is the strong form Varoquaux & Cheplygina say ML rarely achieves.
- [推論/業界慣例] ClinicalTrials.gov registration is designed for clinical studies with assigned interventions. A retrospective, non-interventional model-development prototype with no clinical use does not need it. I did not fetch ClinicalTrials.gov's scope definitions in this session **(未驗證)**. The local IRB/ethics requirements for photo collection are a separate question outside this note.
- [B][研究證據] Varoquaux & Cheplygina 2022 (above): "Preregistration or registered reports can bring more robustness and trust"; also: separate all test data from the start and document hyperparameter selection without touching the test set. — [PMC9005663](https://pmc.ncbi.nlm.nih.gov/articles/PMC9005663/)
- Sculley et al. ("Hidden technical debt", "Winner's curse? On pace, progress, and empirical rigor" 2018) argue for empirical rigor, ablations and reporting of tuning effort. **(未驗證 in this session; not cited for any number.)**

### What to fix in advance (synthesised checklist) [推論, built from Hofman 2023 Phase A/B + TRIPOD+AI + Varma & Simon + Bouthillier]
1. **Units and splits:** the patient is the unit. The split file (patient_id → fold or role) is generated once with a recorded seed, stored, and **SHA-256 hashed**. The hash goes in the protocol. Repeated-CV seeds are listed (e.g., 10 or 20 seeds).
2. **Label definition:** staging criteria (which phlebitis scale and its version), one annotator, how ambiguous photos are handled. A plan to re-label a subset blind, for intra-rater agreement, if time allows.
3. **Primary endpoint and primary metric:** one only. Suggest **pooled out-of-fold balanced accuracy for binary**, with the normal FPR as a co-primary *safety-direction* descriptor. Staging (ordinal) is secondary.
4. **Threshold rule:** fixed before looking (e.g., 0.5 on calibrated probability), or chosen **inside the training folds only** by a stated rule (e.g., maximize Youden on inner CV).
5. **Model set (arms) and per-arm hyperparameter search budget:** e.g., ≤ 8 configurations per arm, a fixed epoch cap, early-stopping rule on an inner split.
6. **Stopping rule for the whole phase:** e.g., "phase 1 ends after the pre-listed arms × seeds are run once; no additional arms are added in phase 1". New ideas go to an "exploratory" log and are labelled as such.
7. **Analysis plan:** CI method (patient-cluster bootstrap); how to aggregate across repeats; subgroup analyses (e.g., arm vs hand, skin tone, camera) declared as **exploratory only**. At n = 14 they cannot be confirmatory.
8. **Deviation log:** every change after registration, with a date and reason (Hofman Phase B requires this).

### How a local workbench can enforce it (design notes) [推論; mechanisms inspired by Dwork 2015 / Blum & Hardt 2015 / Hofman 2023]
- **Protocol object:** a frozen protocol (markdown + JSON) is committed to git. Its hash is stored in SQLite and attached to every run. Runs launched under a different protocol hash are labelled "exploratory".
- **Split file hash check:** training and evaluation refuse to start if the split file hash ≠ the registered hash. Silent re-splitting is the most common forking path.
- **Locked test set:** test-patient IDs are excluded from every dataset view, thumbnail grid and metric endpoint. Unlocking needs (a) a **written justification**, (b) a protocol hash, (c) the single model ID to be evaluated, and (d) a human confirmation step. The event is written to an append-only audit log (timestamp, user, model hash, result). A **second** unlock of the same test set is allowed but flags all later results as "test set reused" ([研究證據] basis: Dwork 2015 on adaptive reuse).
- **Run registry including failures:** every started run (crashed, aborted, "bad-looking") is kept with its config. The comparison UI shows "N configurations tried so far in this arm" next to any best score. This is the denominator that Simmons-style flexibility hides.
- **Evaluation budget:** a per-phase counter (e.g., 40 CV evaluations). The UI warns when it is exceeded and requires a reason. Optionally, show CV scores **rounded** (e.g., to 0.05) and flag "improvement" only beyond a pre-set margin (a Ladder-style idea; an engineering adaptation, not a validated clinical method).
- **Consistent with the project's principles:** none of this auto-trains or auto-deploys. Every run and every unlock is human-started, and the platform only records and gates.

### Inferences
- [推論] Now (14 patients): a held-out test of ~3 patients would give a balanced-accuracy estimate whose uncertainty spans most of [0, 1] for the normal class. It would also cost about 20% of training patients. **Recommendation:** in phase 1, do **not** carve a static held-out test from the 14 patients. Instead, pre-register now that the **next N newly collected patients** (e.g., the first 10–15 new patients, all classes) will form a **locked prospective test set**, labelled and hashed before any model sees them. This turns the slow data growth into an advantage: new data collected after registration is the gold standard.
- [推論] Future (~1,000 photos): register a fixed patient-level test set (e.g., ≥ 25–30% of **patients**, stratified, ideally from a later time period or a different ward or camera). Access it once, at the end, under the unlock protocol.

### Gaps
- PROBAST+AI signalling-question wording and the TRIPOD+AI item numbers were confirmed only through secondary or supplementary files. Verify against the BMJ PDFs.
- 未找到可靠證據 that pre-registration measurably improves ML prediction-model validity. The evidence is argument plus a 6-person qualitative study (Hofman 2023).
- I did not verify ClinicalTrials.gov's official applicability text.

---

## Q3. How should learning curves be done correctly, how should they be interpreted, how dangerous is extrapolating from 14 patients, and what sample-size planning alternatives exist?

### Takeaway
Correct learning curves subsample **patients** (not photos) at increasing sizes. They repeat many random draws per size, evaluate on a fixed held-out set or with nested/grouped CV, and fit an inverse power law with weighting toward larger sizes (Figueroa 2012). Learning curves can be non-monotone, and no universal shape holds (Viering & Loog 2022). With 14 patients the curve has perhaps 3–4 usable points with huge variance, so it is **descriptive only**. Extrapolating it to 1,000 photos is not defensible. Formal sample-size methods exist for regression-type prediction models (Riley et al. 2020, pmsampsize) and for validation studies (Goldenholz et al. 2023, SSAML). They are more useful for planning the **future test set** than for deep-net training size.

### Cited Findings
- [C][研究證據] Figueroa, Zeng-Treitler, Kandula & Ngo 2012, BMC Med Inform Decis Mak 12:8, doi:10.1186/1472-6947-12-8. They fit an **inverse power law** to an early learning curve by **weighted nonlinear least squares**, with larger-sample points weighted more, and predict performance with a 95% CI at larger sizes. The data were clinical text (smoking status) and UCI waveform, with active and passive sampling. Fitting started at 80 instances, with sizes up to 992. Prediction error fell below 0.01 after "between 80 to 560 annotated samples". Across 568 fitted models, the weighted fits had lower RMSE/MAE than unweighted fits (p < 0.05). — [PMC3307431](https://pmc.ncbi.nlm.nih.gov/articles/PMC3307431/) (verified)
  - Applicability [推論]: their smallest starting point (80 **independent** instances) is already larger than the project's whole independent sample (14 patients). The method has not been shown to work from ~14 clusters.
- [D][研究證據] Cho, Lee, Shin, Choy & Do 2015, "How much data is needed to train a medical image deep learning system to achieve necessary high accuracy?", arXiv:1511.06348. A CNN classified axial CT into **six anatomical classes** with training sizes of **5, 10, 20, 50, 100, 200** per class, and a learning curve was used to predict accuracy at larger sizes. — [arXiv:1511.06348](https://arxiv.org/abs/1511.06348) (abstract verified). The often-quoted extrapolation of "4,092 images per class for 99.5%" is **not in the abstract (未驗證)**; I did not open the full text.
  - Counter-point [推論]: a near-trivial task (distinguishing CT body regions) where images are independent. Not comparable to subtle erythema grading with clustered photos.
- [B][研究證據] Viering & Loog, "The shape of learning curves: a review" (IEEE TPAMI; arXiv:2103.10948 v2, Nov 2022). Some evidence "supports well-behaved curves that often have the shape of a power law or an exponential". They also document examples "showing worse learning performance with more training data" (non-monotone curves: peaking, dipping, double descent). Their conclusion is that "learning curves are surprisingly diverse and no universal model can be identified". — [arXiv:2103.10948](https://arxiv.org/abs/2103.10948) (verified). The TPAMI DOI is commonly given as 10.1109/TPAMI.2022.3220744 **(未驗證)**.
- Hestness et al. 2017, "Deep learning scaling is predictable, empirically" (arXiv:1712.00409, [D]). They report power-law generalization-error scaling across domains, but at large data scales. **(未驗證 in this session; cite only qualitatively.)**
- Mukherjee et al. 2003, J Comput Biol, "Estimating dataset size requirements for classifying DNA microarray data". It fits inverse power-law learning curves with permutation-based significance at small n. **(未驗證 in this session.)**
- [B][研究證據] Riley et al. 2020, BMJ, "Calculating the sample size required for developing a clinical prediction model". For binary outcomes the criteria are: expected shrinkage of predictor effects ≤ 10% (shrinkage ≥ 0.9); a small (0.05) absolute difference between apparent and adjusted Nagelkerke R²; and precise estimation (±0.05) of the overall outcome proportion. They are implemented in the **pmsampsize** R package, which can approximate R² from an anticipated C-statistic and prevalence. — [pmsampsize CRAN manual](https://search.r-project.org/CRAN/refmans/pmsampsize/html/pmsampsize.html) [A/E: official package docs]. BMJ volume/article commonly given as 368:m441, doi:10.1136/bmj.m441 **(未驗證: not fetched)**.
  - Applicability [推論]: these criteria assume a **regression model with a countable number of predictor parameters**. They map reasonably onto the **DINOv2-frozen + logistic regression** arm only if the number of effective parameters is controlled (e.g., PCA to k components, strong L2). They do **not** map onto fine-tuned CNNs. Use them as a *lower-bound sanity check*. For example, a logistic model with k = 10 features at prevalence ~0.5 typically needs hundreds of **independent** events. I did not run pmsampsize here; this needs to be computed.
- [B/C][研究證據] Goldenholz, Sun, Ganglberger & Westover 2023, Biomedicines 11(3):685, "Sample Size Analysis for Machine Learning Clinical Validation Studies" (SSAML). Validation aims to *estimate* performance (low bias, tight CIs) rather than to reject a null. SSAML picks the smallest n that meets thresholds on bias, coverage and relative CI width for AUC/C-index, calibration slope and calibration-in-the-large. It is model-agnostic, demonstrated on three published models (Cox, ordinal regression, deep learning), with open-source code. — [PMC10045793](https://pmc.ncbi.nlm.nih.gov/articles/PMC10045793/); [medRxiv preprint](https://www.medrxiv.org/content/10.1101/2021.10.26.21265541.full.pdf) (search snippets). I found no independent replication.
  - Applicability [推論]: this is the appropriate tool for sizing the **future locked test set** (how many patients are needed for a balanced-accuracy or normal-FPR CI of acceptable width). It needs a pilot model's predictions, which phase 1 can supply.

### Correct learning-curve protocol for this project [推論, assembled from Figueroa 2012 + Viering & Loog 2022 + Varma & Simon 2006]
1. **Sizes in patients:** e.g., m ∈ {4, 6, 8, 10} training patients. The ceiling is set by the outer CV training size: with 3-fold over 14 patients, about 9–10 patients are available per training fold. Stratify so every subsample contains ≥ 1 normal patient. If the normals come from very few patients, some sizes are infeasible; record that rather than forcing it.
2. **Evaluation set fixed per outer fold:** subsample only within the outer training patients, and always evaluate on the same outer test patients. Repeat over outer folds × several outer seeds.
3. **Repeated draws:** ≥ 20 random patient subsets per size per outer fold (cheap for DINOv2 + LR; costly for EfficientNet, so use fewer draws for it and say so).
4. **No tuning inside the curve:** hyperparameters are frozen to the pre-registered default. Otherwise the curve mixes data effects with selection effects (Varma & Simon).
5. **Report** mean ± spread (e.g., 10th–90th percentile across draws) per size, with patient counts and photo counts. Fit an inverse power law with weights à la Figueroa **only as a descriptive overlay**, with its CI. **Do not** report an extrapolated "photos needed".
6. **Future (~1,000 photos):** repeat with sizes up to ~70% of patients, on a fixed locked test set. A power-law fit on ≥ 5 sizes spanning an order of magnitude becomes informative, but still inform the reader of Viering & Loog's non-monotonicity caveat.

### Inferences
- [推論] With 14 patients the dominant variance in each learning-curve point is *which* patients were drawn. A rising curve could be patient composition, not data quantity. Interpretation at most: "performance did / did not visibly increase between 4 and 10 patients, with overlapping spreads".
- [推論] Industry convention (a power law fitted to early points and projected forward) is **not** endorsed by the evidence at this n. The Figueroa method was validated from ≥ 80 independent instances, and Viering & Loog show no universal shape.

### Gaps
- 未找到可靠證據 on learning-curve extrapolation reliability from **< 20 clusters/patients** in imaging.
- I did not compute Riley criteria or SSAML for this project's plausible prevalence and C-statistic. These need pilot predictions.
- Cho 2015 extrapolated numbers and Hestness 2017 / Mukherjee 2003 details were not verified.

---

## Q4. Draft first-phase experiment plan (feasibility phase, 14 patients), plus the transition to the future (~1,000 photos)

### Takeaway
Phase 1 should be framed as a **pre-registered feasibility and pipeline-validation study**, not a performance claim. Use a small, fixed set of arms (trivial and colour baselines, DINOv2+LR, EfficientNet frozen and partially unfrozen). Run each under identical, hashed, patient-grouped **repeated** CV with nested (inner) selection and a capped tuning budget. Log every run. Report pooled out-of-fold metrics with patient-cluster-bootstrap CIs. No arm is expected to "significantly" beat the baseline at n = 14. Success is defined by feasibility outcomes. The real test is a prospectively collected, locked set of new patients.

### Cited Findings (evidence underpinning the design choices)
- Nested CV for any selection step: [Varma & Simon 2006](https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/) [B]; [Cawley & Talbot 2010](https://jmlr.org/papers/v11/cawley10a.html) [B].
- Randomize and repeat over data splits and seeds; the variance from data sampling and initialization is large: [Bouthillier et al. 2021](https://arxiv.org/abs/2103.03098) [B/D]; [Picard 2021](https://arxiv.org/abs/2109.08203) [D].
- Small test sets mean large error bars; separate the test set from the start; preregistration recommended: [Varoquaux & Cheplygina 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9005663/) [B].
- Leakage taxonomy, including non-independence: [Kapoor & Narayanan](https://arxiv.org/abs/2207.07048) [B].
- Two-phase registration (before training / before testing): [Hofman et al. 2023](https://arxiv.org/html/2311.18807) [D].
- Report protocol and registration status: TRIPOD+AI 18c/18d ([EQUATOR](https://www.equator-network.org/?p=11341)) [A].

### Inferences — the plan itself [推論 throughout; this is design, not evidence]

**P0. Before any phase-1 run (registration, Hofman Phase A)**
- Freeze: the label definitions (staging scale), the photo inclusion/exclusion list, and the patient→fold assignment for **R = 10 repeats of patient-grouped stratified 3-fold CV**. Stratify on the patient's "has normal photos" and dominant stage. With 14 patients, 3 folds means about 4–5 test patients per fold. Hash the split file, commit the protocol to git, and optionally file an OSF *Secondary Data* preregistration.
- Declare up front: one annotator (no inter-rater reliability available; a limitation); whole-image input; and no clinical claims.
- Pre-register the **prospective locked test set**: the next ≥ 10–15 newly enrolled patients (covering all three classes) are labelled, hashed and sealed before any phase-2 model is finalised.

**P1. Arms (fixed list; nothing added mid-phase)**

| # | Arm | Purpose |
|---|---|---|
| A0 | Majority / prior classifier | Floor: balanced accuracy = 0.5 by construction, normal FPR = 100% if "phlebitis" is the majority class |
| A1 | Colour-histogram (e.g., HSV/Lab histograms of the whole image) + L2 logistic regression | Cheap "redness" baseline; tests whether deep features add anything beyond colour |
| A2 | DINOv2-small frozen embeddings + L2 logistic regression (C chosen by inner CV from a pre-listed grid of ≤ 5 values) | Low-variance foundation-feature arm; best-suited to tiny n |
| A3 | EfficientNet-B0 frozen backbone + head (class weights, fixed optimizer and schedule) | Standard transfer baseline |
| A4 | EfficientNet-B0 with the last block unfrozen | Tests whether partial fine-tuning helps or overfits at n = 14 |
| A5 (optional, exploratory) | Lesion-crop variant of the best of A2/A3, using the ~24 boxed photos | Hypothesis-generating only: boxes exist for a minority, and crops at test time need a detector, so the pipeline differs |

YOLO detection is **out of the phase-1 confirmatory scope**. Report it descriptively (per-image recall at a fixed IoU on out-of-fold patients) because 24 boxes give no stable mAP.

**P2. Controlled variables (identical across arms)**
- The same hashed patient splits and the same R × 3 folds. The same seed list per repeat (e.g., seeds 0–9). The same preprocessing (resize, normalisation constants fixed from ImageNet / DINOv2 defaults, **not** fitted on data). The same augmentation for the CNN arms (rotation only, as pre-registered). The same epoch cap and early-stopping rule using an **inner** patient-grouped split of the training fold only.
- **Threshold rule:** the default is fixed at 0.5 on the predicted probability. An alternative may be pre-registered: Youden-optimal on inner-CV out-of-fold predictions within the training fold. The test fold is never used to set it.
- **Tuning budget:** ≤ 5 configurations per arm, selected by inner CV (nested). The total phase-1 budget is about 6 arms × ≤ 5 configs × 10 repeats × 3 folds. Count and display it.
- Class weights are computed inside each training fold.

**P3. Metrics**
- **Primary (binary):** pooled out-of-fold **balanced accuracy**, computed over all photos per repeat, then summarised across repeats as the median and the 2.5–97.5 percentile range. A 95% CI comes from a **patient-cluster bootstrap** (resample patients, not photos).
- **Co-primary safety descriptor:** the pooled **normal false-positive rate**, reported as a count k/9 photos and k/(number of normal patients), with a Wilson CI on photos plus a cluster-bootstrap CI.
- **Secondary:** macro-F1; per-class sensitivity; for staging, ordinal metrics (e.g., quadratic-weighted kappa or MAE on 0/1/2) as descriptive only; calibration plot (descriptive, very noisy).
- **Paired comparison** of each arm vs A1 (colour baseline): the patient-cluster-bootstrap distribution of the difference in balanced accuracy over the *same* out-of-fold predictions, and the proportion of repeats in which arm > A1 (a probability-of-improvement view, Bouthillier-style).

**P4. Success criteria (realistic; feasibility, not efficacy)**
- F1: the pipeline runs end-to-end for all arms with grouped splits, logged and reproducible from the protocol hash (re-running a config reproduces the metrics within seed tolerance).
- F2: no leakage detected. Automated checks show no patient in both train and test; preprocessing is not fitted on the test fold; thresholds are not set on the test fold.
- F3: report effect sizes with CIs for each arm vs A0 and A1. **Pre-stated expectation:** CIs for arm − A1 will likely include 0 at n = 14. That is an expected outcome, not a failure.
- F4: a learning curve (Q3 protocol) for A2 (and A3 if compute allows) is produced and reported descriptively, with no extrapolated sample-size claim.
- F5: the uncertainty estimates (e.g., the width of the balanced-accuracy CI) are used as inputs to SSAML / pmsampsize-style planning of the prospective test-set size.
- "Promising for phase 2" is defined **descriptively**, for example: an arm's median balanced accuracy exceeds A1 in ≥ 80% of repeats **and** its normal FPR is not worse than A1. It is explicitly labelled hypothesis-generating.

**P5. Preventing repeated tuning on the same data**
- All selection happens inside the inner CV. Outer folds are only for reporting.
- The run registry records every attempted config, including failures. The phase-1 report states "N configs tried".
- Any new idea after viewing results (e.g., a different augmentation) is run as **exploratory** under a new protocol version and reported separately, never merged into the confirmatory table.
- There is no static held-out set from the 14 patients. The **prospective locked set** is opened once, for one pre-specified model per task, via the audit-logged unlock with a written justification and human confirmation. The model to be tested is chosen **before** unlock, by the pre-registered phase-1 rule.
- No auto-training and no auto-deploy: the platform only gates and records. Every run and every unlock is started by a human.

**P6. Now vs future**

| Aspect | Now (14 patients, ~120 photos) | Future (~1,000 photos, balanced) |
|---|---|---|
| Claim type | Feasibility / descriptive | Internal validation with a pre-registered locked test set; possibly temporal or site validation |
| Split | Repeated grouped 3-fold, nested; no static holdout | Locked patient-level test set (sized with SSAML-style precision targets) + nested grouped CV on the remainder |
| Arms | 5 + 1 exploratory | Winner(s) from phase 1 + the A1 baseline, re-registered |
| Learning curve | Descriptive, patient sizes 4–10 | Power-law fit across ≥ 5 sizes, still with the non-monotonicity caveat |
| Subgroups | None confirmatory | Pre-declared (arm vs hand, skin tone, camera) with CIs |
| Labels | Single annotator (stated limitation) | Add a second blinded annotator on a subset for agreement and label noise |

### Gaps
- Number of **distinct patients among the 9 normal photos**: not provided. It determines whether 3-fold stratification is even feasible for the normal class. If the normals come from ≤ 2 patients, the binary task in phase 1 is effectively a patient-identification risk, and the plan should fall back to leave-one-normal-patient-out reporting.
- No empirical benchmark was found for colour-histogram vs foundation-feature performance on **phlebitis** photos (未找到可靠證據). Arm expectations are therefore not evidence-based.
- SSAML / pmsampsize calculations for the future test set were not performed; they need phase-1 predictions.

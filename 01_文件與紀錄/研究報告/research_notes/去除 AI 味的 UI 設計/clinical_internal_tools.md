# Professional interface design for data-dense clinical research tools

Scope: a desktop-first hospital research workbench (1440px main, also usable at 820px and 390px) in Traditional Chinese (zh-TW). It covers image review with bounding-box annotation, ML training and evaluation dashboards, job monitors, audit logs, and trash/retention. Research date: 2026-10-14. The research used 19 tool calls. Primary design-system docs were fetched directly. Some academic and regulatory items come from search-result summaries and are flagged as such.

## Q1. What do healthcare, government and clinical HCI sources recommend for layout, density, typography, colour, status, alerts and error prevention?

### Takeaway
Healthcare and government sources treat colour as a meaning-carrying resource, not decoration. They require WCAG 2.2 AA contrast and say colour must never be the only signal. Evidence from EHR research says complexity and inconsistency hurt clinicians' perceived performance. Interruptive alerts are overridden most of the time. So a trustworthy clinical tool is consistent, quiet by default, and saves interruption for things that truly need action.

### Cited Findings
**Colour (NHS)**
- The NHS service manual says not to rely on colour or position alone. It notes that people with colour vision deficiency often struggle to tell reds, yellows and greens apart. — [NHS Service Manual: Colour](https://service-manual.nhs.uk/design-system/styles/colour)
- Text, interface components and graphics must meet WCAG 2.2 AA, and AAA is the aim where possible. AA means 4.5:1 for small text and 3:1 for large text, components and graphics. AAA means 7:1 and 4.5:1. — [NHS Service Manual: Colour](https://service-manual.nhs.uk/design-system/styles/colour)
- Status colours are reserved for specific jobs: yellow for focus states and warning callouts, red for urgent care cards. Designers should use the semantic error variable rather than the raw palette red. — [NHS Service Manual: Colour](https://service-manual.nhs.uk/design-system/styles/colour)
- The NHS uses a light grey background tint to reduce glare and make components stand out. It cites dyslexia-friendly advice to put dark text on a light, but not pure white, background. White is used for emphasis and alternating backgrounds. — [NHS Service Manual: Colour](https://service-manual.nhs.uk/design-system/styles/colour)
- Disabled components are exempt from contrast minimums. Meeting them is still encouraged if it doesn't cause confusion. — [NHS Service Manual: Colour](https://service-manual.nhs.uk/design-system/styles/colour)

**EHR usability and density (academic and AHRQ)**
- In a mixed-methods study of ICU physicians (n=25 enrolled), higher EHR complexity or inconsistency was associated with lower perceived performance. Physicians also stayed frustrated by how hard it was to find patient information. — [PMC6584062](https://pmc.ncbi.nlm.nih.gov/articles/PMC6584062) (via search summary)
- AHRQ funded a "dense display" project on primary-care EHR information design. It noted that "little systematic evidence" existed on how EHR design affects cognitive task flow and efficiency, and convened an expert panel on interface design considerations. — [AHRQ Digital Healthcare Research](https://digital.ahrq.gov/ahrq-funded-projects/use-dense-display-data-and-information-design-principles-primary-care-health)
- Ratwani et al. (JAMIA 2018, doi 10.1093/jamia/ocy027) analyse EHR usability problems. They describe structural incentives that keep poor design in place, because vendors sell to organisations rather than to end users. — [Textbook of Digital Health ref](https://textbookofdigitalhealth.com/references/rm2018ehr.html) (via search summary)
- A JAMIA Open study (2022) observed residents prerounding. It recommends reducing information access cost, automating calculations, and standardising notes. — (via search summary; primary URL not retrieved)

**Alerts and alert fatigue**
- A systematic review of 23 CPOE studies (JMIR Med Inform 2020) found average alert override rates of about 46% to 96%. Between 29.4% and 100% of overrides were judged appropriate, and the share varied by alert type. Inappropriate overrides were associated with more potential adverse drug events. — [JMIR Med Inform 2020;8(7):e15653](https://medinform.jmir.org/2020/7/e15653) / [PMC7400042](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7400042/)
- Higher figures appear in secondary sources: a 90% pooled override rate (Felisberto et al. 2024 meta-analysis) and 95.7% across 10 sites (Cho et al., JAMIA 2019). These were not verified against the primary papers. — [Mindbowser blog (secondary)](https://www.mindbowser.com/alert-fatigue-healthcare/)

**Dialogs, alerts and error prevention (Carbon)**
- Dialogs should be started by the user. System alerts about background processes should use toast notifications instead. This applies directly to job monitors: a finished training job is a toast, not a modal. — [Carbon: Dialog pattern](https://carbondesignsystem.com/patterns/dialog-pattern/)
- Validation errors stay inline. The dialog remains open, the entry is marked with an error state, and an inline error message is shown. Use a full page rather than a dialog when the user needs to consult other information. — [Carbon: Dialog pattern](https://carbondesignsystem.com/patterns/dialog-pattern/)

**Regulatory context (FDA)**
- FDA revised its Clinical Decision Support software guidance in January 2026, replacing the 2022 version. Automation bias is now explicit. Time-critical use moved from automatic exclusion to a "Criterion 4" factor, because there is more automation-bias risk when clinicians lack time to consider other information. — [Cooley, 2026-01-20](https://www.cooley.com/news/insight/2026/2026-01-20-automation-bias-and-clinical-practice-fda-makes-incremental-updates-to-clinical-decision-support-software-guidance); [Jones Day](https://www.jonesday.com/zh-hans/insights/2026/01/a-relaxing-2026-fda-updates-general-wellness-and-clinical-decision-support-software-guidance)
- The 2026 guidance puts more weight on transparency about data inputs, underlying logic, and how recommendations are generated. The key question is whether a clinician can independently evaluate the basis for a recommendation. — [Faegre Drinker](https://faegredrinker.com/en/insights/publications/2026/1/key-updates-in-fdas-2026-general-wellness-and-clinical-decision-support-software-guidance); [Ketryx](https://ketryx.com/blog/understanding-the-fdas-2026-clinical-decision-support-software-guidance-what-medical-device-companies-need-to-know)
- Sources disagree. Ketryx calls the Criterion 4 transparency requirements "more prescriptive", while Jones Day says FDA softened them. Dates also differ: January 6, a further revision on January 29, and "February 2026". — [Ketryx](https://ketryx.com/blog/understanding-the-fdas-2026-clinical-decision-support-software-guidance-what-medical-device-companies-need-to-know) vs [Jones Day](https://www.jonesday.com/zh-hans/insights/2026/01/a-relaxing-2026-fda-updates-general-wellness-and-clinical-decision-support-software-guidance); [Johner Institute](https://blog.johner-institute.com/regulatory-affairs/decision-support-systems-medical-device/)

### Inferences
- In a research workbench, "trustworthy" mostly means predictable. That calls for one consistent layout per page type, semantic colour tokens rather than raw hues, and no decorative colour. The NHS habit of tying colours to named variables (for example `error`) is a good pattern to copy as design tokens.
- Alert-fatigue evidence says to keep interruptive UI (modals, red banners) for things that block work or carry risk: a failed job affecting data, permanent purge, or a PHI or de-identification problem. Routine completions belong in toasts, badges or inline status.
- The workbench is research-only, but the FDA's automation-bias framing still applies to how model output is shown. Show inputs, logic and limits so a clinician can evaluate them independently, rather than a bare score.
- A light-grey page background with white cards or tables, as in the NHS approach, is a sober, evidence-backed alternative to gradients and glass effects.

### Gaps
- I did not fetch the FDA "Applying Human Factors and Usability Engineering to Medical Devices" (2016) guidance or IEC 62366-1 text, so I have no specific UI-level rules from them.
- I did not fetch the AHRQ "EHR Usability: Interface Design Considerations" PDF itself, because its link redirected to a tokenised file host. Its specific principles (density, font size, colour coding) are therefore not captured. The report is by Armijo, McDonnell and Werner (AHRQ 2009, publication 09(10)-0091-2-EF); this is from background knowledge and was not verified this session.
- I found no recent peer-reviewed paper that sets a numeric "optimal information density" for clinical displays.
- I did not fetch the NHS and USWDS typography pages (font sizes, line length).

## Q2. How should data tables, filters, bulk selection, pagination and destructive actions be designed in enterprise tools?

### Takeaway
Enterprise systems agree on the basics. Offer a small set of row-density options, with Carbon's default at 40px and compact at 24 or 32px. Show a contextual batch-action bar that replaces the toolbar when rows are selected. Put pagination at the bottom and make sort state explicit. For deletion, scale friction to blast radius: undo for reversible actions, a named confirmation dialog for single irreversible deletes, and type-to-confirm only for irreversible actions with a wide blast radius.

### Cited Findings
**Tables (IBM Carbon)**
- Carbon offers five row and header heights: xs 24px, sm 32px, md 40px (default), lg 48px and xl 64px. xl is only for two-line rows. The header row should always match the row size. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)
- The toolbar and pagination heights match the row height. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)
- When items are selected, a batch action bar appears at the top of the table and applies actions to all selected items. Users exit it with a cancel button at the far right or by deselecting all. Single-row action icons and overflow menus are disabled while batch mode is active. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)
- Multi-select uses a checkbox per row, and the header checkbox has an indeterminate state. Single-select uses a radio button in the first column. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)
- Sorting has three states. Unsorted arrows appear only on hover, and only the sorted column shows an icon. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)
- Pagination sits at the bottom. The simple version has current page plus previous and next. The advanced version adds items per page and jump-to-page. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)
- The toolbar holds global actions such as settings, complex filters, export and edit, with at most five actions; extras go in an overflow menu. Search sits on the left under the title. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)
- Zebra stripes are optional and help horizontal scanning. Row hover should always be on. With fewer than three inline actions, use icon buttons rather than an overflow menu. Overflow menus stay visible on touch devices. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)
- Column titles should be one or two words in sentence case. Long titles wrap to two lines, then truncate, with the full text in a tooltip. — [Carbon: Data table usage](https://carbondesignsystem.com/components/data-table/usage/)

**Destructive actions (GitHub Primer, IBM Carbon)**
- Primer says to match friction to blast radius. Type-to-confirm suits org-wide or repo-wide impact, a simple dialog suits single resources, and reversible actions need no confirmation. It says to "Reserve type-to-confirm for irreversible actions with wide blast radius" so the friction keeps its meaning. — [Primer: Delete scenario pattern](https://primer.style/product/scenario-patterns/delete)
- Primer warns not to confirm routine, reversible actions, because people learn to click through. It says to "Offer an undo window for actions you can reverse". — [Primer: Delete](https://primer.style/product/scenario-patterns/delete)
- High-impact deletions belong in a "danger zone" within settings. Low-impact ones stay inline or in a context menu. For high-value resources, offer a reversible disable step alongside permanent deletion. — [Primer: Delete](https://primer.style/product/scenario-patterns/delete)
- Use "Remove" when the item still exists elsewhere and "Delete" only when it is permanently destroyed. Label buttons with the specific action, such as "Delete repository", not "Yes", "OK" or "Confirm". Pair the danger colour with a text label. — [Primer: Delete](https://primer.style/product/scenario-patterns/delete)
- The dialog should name what is affected and say whether the action is permanent. Avoid "Are you sure?". The confirm button shows a loading state for slow deletes. On failure, the dialog stays open with a critical banner so the user can retry. Move focus sensibly afterwards. — [Primer: Delete](https://primer.style/product/scenario-patterns/delete)
- A type-to-confirm flow should use Dialog rather than ConfirmationDialog and manage focus return manually. A full phrase such as "I understand, delete this project" is acceptable. — [Primer: Delete](https://primer.style/product/scenario-patterns/delete); [Primer ConfirmationDialog](https://primer.style/product/components/confirmation-dialog/guidelines)
- Carbon says to use a "transactional danger modal" for destructive or irreversible actions and to explain consequences. Cancel goes on the left and there is one primary action. The title and button should both reflect the action, using verbs like "Delete" rather than "OK". — [Carbon: Dialog pattern](https://carbondesignsystem.com/patterns/dialog-pattern/)
- Third-party tutorials say GitHub's own repository deletion disables the button until the exact repository name is typed, possibly case-sensitively. This was not verified against GitHub docs. — (search summary; [DataCamp tutorial](https://www.datacamp.com/sv/tutorial/how-to-delete-a-github-repository))

### Inferences
- **Trash/retention mapping.** Moving to trash is reversible, so use no confirm dialog and offer an undo toast. Restoring from trash needs no confirmation. Permanently purging one item is a named danger dialog, for example 永久刪除「影像 IMG_0231」？. Bulk purge or "empty trash" uses type-to-confirm with the count or project name, and the button stays disabled until the text matches. The retention countdown, such as 30 天後自動永久刪除, should appear in each row.
- In zh-TW, keep the Remove versus Delete distinction: 移除 for taking an item off a list or dataset, 刪除 or 移至垃圾桶 for trash, 永久刪除 for purge. Never use 確定 or 確認 alone as a button label.
- For audit logs and job lists, 32px rows (Carbon sm) are a reasonable density at 1440px. Use 40px when rows hold status pills or thumbnails. Keep header, toolbar and pagination at the same height.
- In batch mode, swap the toolbar for a contextual bar such as 已選取 12 項 · [移至垃圾桶] [匯出] [取消]. Disable per-row actions in that mode, following Carbon.

### Gaps
- I did not fetch the Atlassian, Fluent 2 DataGrid or GOV.UK table pages, so I have no cross-check on numeric alignment. Carbon's page gives no guidance on aligning numbers. Right-aligned tabular figures are common practice, but no source was fetched for that.
- The bulk-delete and soft-delete sections of Primer's page were truncated and not captured.
- I found no source on filter-chip or faceted-filter patterns in this session.

## Q3. How should ML results be presented to clinicians without overclaiming?

### Takeaway
Clinicians often misread sensitivity, specificity and PPV, and usually overestimate post-test probability. Showing results as natural frequencies improves understanding. Best practice is a "Model Facts"-style label covering intended use, population, validation performance with uncertainty, and explicit warnings, plus reporting aligned with TRIPOD+AI, which expects calibration and confidence intervals as well as AUROC.

### Cited Findings
- A BMJ Open systematic review (2015) found that common test-accuracy measures are poorly understood by health professionals. Post-test probability is usually overestimated, and more so when pre-test probability is low. — [PMC4521525](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4521525/)
- Natural frequencies improved post-test probability estimates and calculation speed. The review suggests natural frequencies and visual aids for reporting test accuracy. Likelihood-ratio formats gave mixed results (3 studies better, 3 worse). — [PMC4521525](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4521525/)
- A 2023 study of 898 clinicians found consistently poor statistical proficiency, often with high confidence even in wrong answers. Natural-frequency framing improved accuracy. — [Cognitive Research: Principles and Implications 2023](https://link.springer.com/10.1186/s41235-023-00474-1) (via search summary)
- Sendak et al. proposed "Model Facts" labels (npj Digital Medicine 2020;3:41, doi 10.1038/s41746-020-0253-3). The goal is that front-line clinicians know how and when to use a model's output, and when not to, on a single page. The authors call for standardised presentation and say any deployment should include such a label. The example was Duke's Sepsis Watch, and the label sections are modelled on drug labels. — [DOAJ record](https://doaj.org/article/04a32595eab3442b8044b66e5a84a0f7); [arXiv 1911.08089](https://arxiv.org/pdf/1911.08089)
- TRIPOD+AI (BMJ 2024;385:e078378) is a 27-item checklist for reporting prediction models built with regression or ML, and it supersedes TRIPOD 2015. Secondary sources say it requires calibration as well as discrimination, so AUROC alone is insufficient, and performance estimates with confidence intervals. — [BMJ](https://www.bmj.com/node/1095803); [PMC12627258](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12627258/)
- A 2025 bibliometric study of orthopaedic AI abstracts found confidence-interval reporting stayed low after TRIPOD+AI (18.7% vs 16.6%, p=0.61). — [PMC12627258](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12627258/)
- The 2026 FDA CDS guidance stresses transparency about inputs, logic and how recommendations are generated, so clinicians can independently evaluate them. — [Faegre Drinker](https://faegredrinker.com/en/insights/publications/2026/1/key-updates-in-fdas-2026-general-wellness-and-clinical-decision-support-software-guidance)

### Inferences
- **Evaluation dashboard.** Report each metric with its 95% CI and the n of the test set, for example 敏感度 0.87（95% CI 0.81–0.92，n=312）. Show the threshold used. Always state which split or site the numbers come from (內部驗證 versus 外部驗證).
- Pair each confusion matrix with a natural-frequency sentence, for example 每 100 張陽性影像中，模型標出 87 張；每 100 張陰性影像中，誤報 9 張. State the prevalence so PPV and NPV are not misread.
- Include a calibration plot or Brier score next to ROC and AUROC, following TRIPOD+AI.
- Put a persistent, plainly worded, non-dismissable notice such as 僅供研究使用，非診斷用途 (Research use only — not for diagnostic use) in the page header or metric card of model pages. Use a neutral or info style, not red, so it does not turn into alert noise. Add a Model Facts panel (預期用途、訓練資料族群、驗證結果、已知限制／警示) on each model detail page.
- Avoid hype: no "AI-powered" badges, sparkle icons, or animated count-up numbers. Show at most three significant digits, and never 100% without a CI.

### Gaps
- I could not fetch the full Sendak paper (paywall redirect), so the exact label section headings are not verified. From background knowledge they are Summary, Mechanism, Validation and performance, Uses and directions, Warnings, Other information.
- I did not fetch the TRIPOD+AI checklist item numbers. Sources conflict (item 11 vs 17).
- I found no study that tests AI-specific dashboard displays of metrics to clinicians. The natural-frequency evidence comes from diagnostic-test literature.

## Q4. Colour and status: semantic colour, colour-blind safety, WCAG 2.2 contrast and target size for dense desktop tools

### Takeaway
Use a small semantic palette: red for error, orange or yellow for warning, green for success, blue for info or in progress, grey for not started. Every status pairs colour with a shape or icon and a text label, and indicators meet 3:1 contrast. Under WCAG 2.2 AA, targets are at least 24×24 CSS px, which dense desktop tables can meet. 44×44 is the AAA level and touch-platform norm, so use it at 390px widths.

### Cited Findings
- Carbon's status semantics: red for danger or error, orange for serious warning, yellow for warning, green for success, blue for information or workflow progress, grey for drafts or not-started jobs, purple for outliers or undefined. — [Carbon: Status indicator pattern](https://carbondesignsystem.com/patterns/status-indicator-pattern/)
- "Relying solely on color to convey status is insufficient". Indicators should combine colour, shape and symbol (two at minimum; the page also says three for WCAG — an internal inconsistency). Aim for at least 3:1 contrast between status colours and against the background. — [Carbon: Status indicators](https://carbondesignsystem.com/patterns/status-indicator-pattern/)
- For dense tables, Carbon recommends shape indicators (shape, colour and label) at 12–14pt, left-aligned, placed before the label. When several statuses combine, use the highest-attention colour. More than five or six indicators overwhelms users, so use plain text where no action is needed. — [Carbon: Status indicators](https://carbondesignsystem.com/patterns/status-indicator-pattern/)
- Light orange and yellow shapes on light themes need outlines and text. — [Carbon: Status indicators](https://carbondesignsystem.com/patterns/status-indicator-pattern/)
- WCAG 2.2 SC 2.5.8 Target Size (Minimum), level AA: pointer targets must be at least 24×24 CSS px. Exceptions cover spacing (a 24px circle that doesn't overlap neighbouring targets), inline text links, equivalent controls, user-agent controls, and essential cases. W3C suggests the stricter 2.5.5 for important controls. — [W3C Understanding 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- SC 2.5.5 Target Size (Enhanced), level AAA, is 44×44 CSS px. This is background knowledge; the page was not fetched this session. — [W3C Understanding 2.5.5](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html)
- Fluent 2 sets minimum touch targets at 44×44 on iOS and web and 48×48 on Android. — [Fluent 2: Layout](https://fluent2.microsoft.design/layout)
- SC 1.4.11 Non-text Contrast (AA): component boundaries, state indicators (selected, focused), focus indicators, and graphical objects needed to understand content need 3:1. In charts, lines and slices need 3:1 unless the same values appear as text labels. Inactive controls are exempt. — [W3C Understanding 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
- Text contrast is 4.5:1 for small text and 3:1 for large text (AA). — [NHS Service Manual: Colour](https://service-manual.nhs.uk/design-system/styles/colour)

### Inferences
- **Bounding-box annotation.** Box strokes over grey-scale medical images are "graphical objects" under 1.4.11. Use at least 2px strokes with a contrasting halo (for example a dark 1px outline around a light stroke) so they reach 3:1 on both light and dark image regions. Tell classes apart by label text and line style (solid or dashed), not by hue alone, for colour-blind users.
- **Job states.** Use 排隊中 (grey, hollow circle), 執行中 (blue, spinner or half circle), 成功 (green, check), 失敗 (red, cross), 已取消 (grey, slash). Always pair the icon with a text label. Keep the palette to five or six statuses, per Carbon.
- In dense tables, 24px icon buttons pass 2.5.8 AA. At the 390px breakpoint, grow row actions to 44px or move them into a row overflow menu.
- Avoid red and green as the only difference in confusion-matrix heatmaps. Use a single-hue sequential ramp with the numbers printed in each cell, which also satisfies 1.4.11 via text.

### Gaps
- I did not fetch WCAG 2.2 SC 2.4.11 Focus Not Obscured or 3.3.7 Redundant Entry. Both are relevant to sticky table headers and long forms.
- I did not obtain colour-blind-safe palette values (for example Okabe-Ito or Carbon's data-vis palette).

## Q5. Navigation for multi-section internal tools (sidebar vs tabs, page headers, breadcrumbs) and how much explanatory text to show

### Takeaway
For a tool with five or more sections, such as data review, annotation, training, evaluation, jobs, audit log and trash, a persistent, text-labelled left sidebar is the evidence-backed choice on desktop. It scales, is easy to scan, and shouldn't hide behind a hamburger at 1440px. Collapse it at tablet and mobile widths. Use a responsive "show/hide metadata" approach rather than shrinking everything.

### Cited Findings
- NN/g (Laubheimer, 2021): vertical left navigation "can accommodate as many top-tier items as needed", grows without redesign, and is easier to scan. Users look at the left half of the screen 80% of the time. — [NN/g: Left-side vertical navigation](https://www.nngroup.com/articles/vertical-nav/)
- The trade-off is less room for content. Teams must choose a pattern per breakpoint, and the article gives no specific breakpoint. — [NN/g](https://www.nngroup.com/articles/vertical-nav/)
- NN/g says not to hide desktop navigation in a hamburger ("visible navigation is the gold standard"). Don't duplicate menus, use text labels rather than icons alone, and front-load keywords. — [NN/g](https://www.nngroup.com/articles/vertical-nav/)
- GOV.UK Service navigation shows the service name and section links. The current item uses an active class and `aria-current`. A "Menu" toggle is shown on small screens. — [GOV.UK: Service navigation](https://design-system.service.gov.uk/components/service-navigation/)
- Fluent 2 breakpoints: small 320–479, medium 480–639, large 640–1023, x-large 1024–1365, xx-large 1366–1919, xxx-large 1920 and up. It uses a 4px spacing ramp, 12-column grids, and gutters in multiples of the base unit. — [Fluent 2: Layout](https://fluent2.microsoft.design/layout)
- Fluent's responsive techniques are reposition, resize, reflow, show/hide (less metadata on small screens), and re-architect (for example, list beside detail on wide screens, collapsed on narrow). — [Fluent 2: Layout](https://fluent2.microsoft.design/layout)
- Fluent says "Too much dense information can also be disorienting and overwhelming". Elements with more surrounding space read as more important. — [Fluent 2: Layout](https://fluent2.microsoft.design/layout)
- Carbon says to use a full page rather than a dialog when users need other information while deciding. — [Carbon: Dialog pattern](https://carbondesignsystem.com/patterns/dialog-pattern/)

### Inferences
- **1440px (Fluent xx-large).** Use a fixed left sidebar about 220–240px wide with text labels in zh-TW (資料審閱、標註、模型訓練、模型評估、工作排程、稽核紀錄、垃圾桶). Each page gets a compact header: H1 title, one line of description at most, and primary actions on the right. Use breadcrumbs only below section level, for example 模型評估 / 模型 v3.2 / 混淆矩陣.
- **820px (Fluent large).** Collapse the sidebar to an icon rail with tooltips, or to a toggleable drawer. Tables hide low-priority columns (show/hide), and list-detail views stack.
- **390px (Fluent small).** Use a top bar with a menu button. Tables become stacked cards or keep two or three key columns with horizontal scroll inside the table only, never the page. Bounding-box annotation is probably view-only at this width.
- **Explanatory text.** Use one plain sentence under the page title, put details in help tooltips or a "說明" link, and add no marketing-style hero copy. This follows Fluent's warning about density and the general principle of reducing information access cost.

### Gaps
- I did not fetch Atlassian's or Primer's side-navigation and page-header guidance.
- I found no CJK-specific guidance on navigation-label length. A practical assumption, not sourced: zh-TW labels of 2–4 characters fit an icon rail better than English labels.

## Q6 (constraint). CJK and Traditional Chinese text density

### Takeaway
W3C's Chinese layout requirements (clreq) treat Han characters as 1:1 squares. Taiwan and Hong Kong centre punctuation in the character cell, and rules should follow region (Taiwan) rather than script. Emphasis uses weight (Hei or bold) or emphasis dots, not italics. Mixed Latin and digits should use proportional half-width forms.

### Cited Findings
- Chinese characters and punctuation are squares with a 1:1 ratio, set seamlessly next to each other. — [W3C clreq §1.2](https://www.w3.org/TR/clreq/)
- In Taiwan and Hong Kong, punctuation is usually centred both vertically and horizontally in the square. The interpunct takes a full character's width there, versus half a width in mainland China. — [W3C clreq §2.1.2, §5.1](https://www.w3.org/TR/clreq/)
- An ellipsis takes two Hanzi widths and should not be split across lines. — [W3C clreq §5.1](https://www.w3.org/TR/clreq/)
- User agents should tell typographic rules apart by region rather than by Traditional versus Simplified. — [W3C clreq §1.2 note](https://www.w3.org/TR/clreq/)
- In body text, Hei-style characters with thicker strokes typically indicate emphasis. Emphasis marks go under characters in horizontal text. — [W3C clreq §3.1.1.3, §5.3.1](https://www.w3.org/TR/clreq/)
- Typesetting engines allow proportional or monospace fonts for Western text and numerals mixed into Chinese. — [W3C clreq §4.1](https://www.w3.org/TR/clreq/)

### Inferences
- Use `lang="zh-Hant-TW"` and a system Traditional Chinese sans font stack, such as "PingFang TC", "Noto Sans TC" and "Microsoft JhengHei". Emphasise with weight 500–600, never italics.
- Use half-width digits with `font-variant-numeric: tabular-nums` for metric and table columns so numbers line up. Never use full-width digits.
- CJK glyphs fill the em box, so 14px CJK text looks larger and denser than 14px Latin text. Common practice is a body line-height around 1.5–1.7 for zh-TW, versus about 1.4–1.5 for Latin, and 13–14px for dense table text. This is practice, not a sourced standard (see Gaps).
- zh-TW labels are often shorter in characters than English equivalents, which helps narrow table columns and icon-rail navigation. Abbreviations like "AUROC", "Dice" and "IoU" should stay in Latin script with a tooltip definition.

### Gaps
- The clreq sections on line-height, line length (§6.2, §6.4) and minimum font size fell in the unfetched part of the page (characters 100,000 and beyond), so I have no sourced numeric line-height or font-size rule for zh-TW.
- I found no design-system guidance (Carbon, Fluent, Primer) specific to CJK UI density in this session.

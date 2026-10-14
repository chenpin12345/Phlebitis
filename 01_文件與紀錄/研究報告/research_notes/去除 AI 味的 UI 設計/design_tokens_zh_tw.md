# Design-system tokens for a zh-TW desktop web workbench (plain CSS + React)

Research date: 2026-10-14. All hex/px values below come from the official documentation pages cited inline (fetched on the research date) unless marked "computed" (my WCAG contrast calculation using the standard relative-luminance formula) or "inference".

## 1. Typography for Traditional Chinese UI on Windows (font stack, base size, line-height, weights, tabular numerals, Latin/CJK mixing, Taiwan gov / clreq guidance)

### Takeaway
On Windows the only built-in Traditional Chinese sans is Microsoft JhengHei / Microsoft JhengHei UI (3 weights: Light, Regular, Bold — no 500/600). Productive/enterprise systems (Carbon, Fluent 2, Ant Design) all use **14px** as the base for dense app UI with ~20–22px line-height; a CJK-heavy UI should use the upper end (22px ≈ 1.57) and rely on Regular vs Bold only. No Taiwan-government web design system with concrete type tokens could be found.

### Cited Findings
**Fonts available (zh-Hant)**
- Microsoft JhengHei & Microsoft JhengHei UI ship with Windows (Vista through Windows 11); files Msjhl.ttc / Msjh.ttc / Msjhbd.ttc; styles: Microsoft JhengHei Light / Regular / Bold and Microsoft JhengHei UI Light / Regular / Bold; code page 950 (Traditional Chinese – Taiwan & HK). Licensed separately for web embedding — use as a local font only. — [Microsoft Learn: Microsoft JhengHei font family](https://learn.microsoft.com/typography/font-list/microsoft-jhenghei)
- W3C clreq system-font mapping (Traditional Chinese): Windows 11 sans = Microsoft JhengHei 微軟正黑體 (built-in); serif = PMingLiU 新細明體 and Kai = DFKai-SB 標楷體 are *optional/supplemental*; macOS sans = Heiti TC 黑體-繁 (system), PingFang TC 蘋方-繁 listed as downloadable; Android = Noto Sans CJK TC; Linux = Noto Sans CJK TC / WenQuanYi Zen Hei (packages). The document warns optional/downloadable fonts "should not be assumed to be installed." — [W3C clreq: System font mappings (last verified 2026-07-21)](https://w3c.github.io/clreq/others/system-font-mappings.html)
- `system-ui` on Windows resolves to Microsoft YaHei UI for Simplified-Chinese users; for Traditional Chinese screenshots showed it resolving to Microsoft JhengHei; the thread also notes JhengHei's Bold is weaker/worse than YaHei's. — [W3C public-css-archive, csswg-drafts #3658 (Sep 2022)](https://lists.w3.org/Archives/Public/public-css-archive/2022Sep/0898.html)
- Real-world zh-TW stacks seen: `"Noto Sans TC", "Microsoft JhengHei", "PingFang TC", "Helvetica Neue", Arial, sans-serif` (NTU Law) — [law.ntu.edu.tw local-fonts.css](https://www.law.ntu.edu.tw/templates/protostar/css/local-fonts.css); a VS Code proposal for `:lang(zh-TW)` uses `"PingFang TC", "Microsoft JhengHei", "Source Han Sans TC", sans-serif` — [microsoft/vscode#5260](https://github.com/microsoft/vscode/issues/5260)
- Ant Design default `fontFamily` seed: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'`; `fontFamilyCode`: `'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace`. (No CJK family named — relies on OS fallback.) — [Ant Design: Customize Theme](https://ant.design/docs/react/customize-theme); [Ant Design spec: Font](https://ant.design/docs/spec/font)

**Base size & line-height**
- Ant Design: base raised from 12 → **14px** for "best user reading efficiency" (50 cm viewing distance); 14px pairs with **22px** line-height (`lineHeight` token = 1.5714285714285714); `fontSizeSM` 12, `fontSizeLG` 16, `fontSizeXL` 20; recommends limiting a system to **3–5 font sizes**. — [Ant Design spec: Font](https://ant.design/docs/spec/font); [Ant Design: Customize Theme](https://ant.design/docs/react/customize-theme)
- IBM Carbon productive type set (base 14px, for "dense, containerized information"): `label-01` 12/16 400 ls .32px; `helper-text-01` 12/16; `body-compact-01` 14/18 400 ls .16px; `body-01` 14/20 400; `heading-compact-01` 14/18 600; `heading-01` 14/20 600; `heading-03` 20/28 400; `heading-04` 28/36 400; `heading-05` 32/40 400. Expressive (-02) set is 16px base: `body-02` 16/24, `heading-02` 16/24 600. — [Carbon: Type sets](https://carbondesignsystem.com/elements/typography/type-sets/)
- Fluent 2 web ramp (Segoe UI): Caption1 12/16; Body1 14/20 Regular; Body1Strong 14/20 Semibold; Subtitle2 16/22 Semibold; Subtitle1 20/26; Title3 24/32; Title2 28/36; Title1 32/40; LargeTitle 40/52. Weights used: Regular, Semibold, Bold. No CJK guidance on the page. — [Fluent 2: Typography](https://fluent2.microsoft.design/typography)
- Carbon data table uses `body-compact-01` (14px) for rows and `heading-compact-01` (14px 600) for column headers. — [Carbon: Data table style](https://carbondesignsystem.com/components/data-table/style/)
- GOV.UK notes "smaller font sizes (14px and below) are bad for accessibility" (context: public-facing gov sites, not internal tools). — [GOV.UK Design Notes, Dec 2022](https://designnotes.blog.gov.uk/2022/12/12/making-the-gov-uk-frontend-typography-scale-more-accessible)

**Weights**
- Ant Design: Regular 400 and Medium 500 are usually enough; Semibold 600 for bold English words. — [Ant Design spec: Font](https://ant.design/docs/spec/font)
- clreq 3.1.1.3: in body text, emphasis is expressed with heavier (thicker-stroke) Hei; clreq 5.3.1 describes emphasis dots rather than italics. — [W3C clreq](https://www.w3.org/TR/clreq/)

**Tabular numerals**
- Ant Design: for numbers that must align vertically use `font-variant-numeric: tabular-nums`. — [Ant Design spec: Font](https://ant.design/docs/spec/font)

**CJK layout rules (clreq, W3C Group Note Draft)**
- §6.3.3: spacing between a Han character and a Western letter/numeral in horizontal text is "up to 1/4 em", not at line start/end and not next to Chinese commas/full stops or inside brackets; §6.2.2.3 allows compression to ≥1/8 em. — [W3C clreq](https://www.w3.org/TR/clreq/)
- §2.1.2: Taiwan and Hong Kong centre punctuation in the character frame (Mainland places it at the corner). §1.2: user agents should distinguish rules by region (zh-TW vs zh-CN), not Traditional vs Simplified → set `lang="zh-Hant-TW"`. — [W3C clreq](https://www.w3.org/TR/clreq/)
- §4.1: don't store full-width Latin letters/digits; let rendering handle them. Ellipses/two-em dashes must not split across lines. — [W3C clreq](https://www.w3.org/TR/clreq/)
- §5.6.1 states a line gap must not be smaller than half the font size (single-sided) or 5/8 (double-sided) — this sits in the annotation (ruby/interlinear) section, so it is the minimum *gap* (i.e. line-height ≥ 1.5 em) in that context. — [W3C clreq](https://www.w3.org/TR/clreq/)
- §7.1.1.5: line length should be a multiple of the font size; minimum body size in print is Size 6 (7.875pt). — [W3C clreq](https://www.w3.org/TR/clreq/)

**Taiwan government guidance**
- MODA (數位發展部) brand identity guideline names Poppins as the English font and PANTONE 101 (yellow) / PANTONE 430 as colours; Chinese font name and web type sizes were not extractable. This is a brand guideline, not a UI system. — [MODA 品牌視覺識別基本指引 PDF](https://www-api.moda.gov.tw/File/Get/moda/en/soXa4yq4Vf8gYDa)
- PDIS (Audrey Tang & Sean Chou, 2021-12-07) announced work on a "Government Website Design System" but published no tokens (no font, size, colour, spacing values). — [PDIS blog](https://pdis.nat.gov.tw/en/blog/%E6%89%93%E9%80%A0%E8%A8%AD%E8%A8%88%E7%B3%BB%E7%B5%B1-%E6%8F%90%E5%8D%87%E6%94%BF%E5%BA%9C%E7%B6%B2%E7%AB%99%E4%BD%BF%E7%94%A8%E8%80%85%E9%AB%94%E9%A9%97/)
- 國發會's earlier 政府網站版型與內容管理規範 (2005) and related guides were merged in 2017 into 「政府網站服務管理規範」, later transferred to MODA (2022); search excerpts show no font/size rules. — (search summary of [ithome](https://www.ithome.com.tw/news/94840) and school/government PDFs; not independently verified)

### Inferences
- Recommended stack (inference, assembled from the sources above): `font-family: "Segoe UI", "Microsoft JhengHei UI", "Microsoft JhengHei", "PingFang TC", "Noto Sans TC", "Noto Sans CJK TC", system-ui, sans-serif;` Putting a Latin face first makes digits/Latin render in Segoe UI (good tabular figures, Semibold available) while Han falls through to JhengHei UI. Prefer explicit names over `system-ui` because `system-ui` can resolve to YaHei UI (Simplified glyph shapes) depending on locale. Code: `Consolas, "Cascadia Mono", "Microsoft JhengHei UI", monospace`.
- Weights: because JhengHei has only Light/Regular/Bold, `font-weight: 500/600` will render Han as Regular (or synthesized) while Segoe UI Latin renders Semibold — mixed-weight artefacts. Use only **400 and 700** for anything containing Chinese; reserve 600 for Latin-only/number contexts. Set `font-synthesis: none` if faux bold looks poor.
- Size scale for a dense workbench: 12 / 14 / 16 / 20 / 24 px (5 sizes, within Ant's 3–5 rule). Base 14px with line-height 22px (1.571) for CJK body; 20px (1.43) only for single-line controls/table cells. 16px base is the "expressive"/public-site choice (Carbon -02, GOV.UK); for an internal power-user workbench 14px matches Carbon productive, Fluent 2 Body1 and Ant.
- Apply `font-variant-numeric: tabular-nums` on table numeric columns, timestamps, counters; right-align numbers.
- For Han–Latin spacing, CSS `text-autospace` (CSS Text 4) implements the clreq 1/4-em gap where supported; otherwise rely on authored spaces or nothing — do not insert full-width spaces.

### Gaps
- No official Taiwan government web/UI design system with concrete font-size/colour tokens was found (MODA/NDC/PDIS). The 中央/無障礙 guidelines (WCAG-based) were not fetched.
- Microsoft does not document the vertical-metric difference between "JhengHei" and "JhengHei UI" on the fetched page (the UI variant is commonly described as having tighter line spacing — unverified).
- Whether Microsoft JhengHei supports the OpenType `tnum` feature was not verified; the stack inference avoids depending on it.
- Material 3 typography values were not fetched.

## 2. Spacing / sizing scales, control heights, border radius (actual token values)

### Takeaway
All five systems use a 4px base (Atlassian frames it as 8px base with half-steps). Default control height converges on **32px** (Ant, Primer medium, Carbon "small"), with 24/28 for compact and 40 for large. Radii cluster at 2–4px (Carbon/Fluent, sharper) or 6px (Ant, Primer).

### Cited Findings
**Spacing scales**
- Carbon: spacing-01 2px, -02 4, -03 8, -04 12, -05 16, -06 24, -07 32, -08 40, -09 48, -10 64, -11 80, -12 96, -13 160 ("multiples of two, four, and eight"). — [Carbon: Spacing](https://carbondesignsystem.com/elements/spacing/overview/)
- Atlassian: base unit 8px; space.025 2px, .050 4, .075 6, .100 8, .150 12, .200 16, .250 20, .300 24, .400 32, .500 40, .600 48, .800 64, .1000 80. Small (0–8px) for badges, icon buttons, table cells; medium (12–24) for button padding; large (32–80) for layout. — [Atlassian: Spacing](https://atlassian.design/foundations/spacing)
- Primer base-size: 2, 4, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 64, 80, 96, 112, 128. — [Primer: Size primitives](https://primer.style/foundations/primitives/size)
- Fluent 2: "The base unit is four pixels"; size20 2, size40 4, size60 6, size80 8, size100 10, size120 12, size160 16, size200 20, size240 24, size280 28, size320 32, size360 36, size400 40, size480 48, size520 52, size560 56 (2/6/10 exist for icon alignment). — [Fluent 2: Layout](https://fluent2.microsoft.design/layout)
- Ant Design: `sizeUnit` 4, `sizeStep` 4 (compact mode sizeStep 2). — [Ant Design: Customize Theme](https://ant.design/docs/react/customize-theme)

**Control heights**
- Ant Design: `controlHeight` 32 (default), `controlHeightSM` 24, `controlHeightLG` 40, `controlHeightXS` 16. — [Ant Design: Customize Theme](https://ant.design/docs/react/customize-theme)
- Primer: control-xsmall 24px, small 28, **medium 32**, large 40, xlarge 48; paddingBlock xs 2 / sm 4 / md 6 / lg 10 / xl 14; paddingInline condensed 8 / normal 12 / spacious 16 (xsmall: 4/8/12). — [Primer: Size primitives](https://primer.style/foundations/primitives/size)
- Carbon: small buttons pair with "32px small sized input fields", medium with "40px medium sized input fields"; data-table rows xs 24, sm 32, md 40, lg 48, xl 64. — [Carbon: Button usage](https://carbondesignsystem.com/components/button/usage/); [Carbon: Data table style](https://carbondesignsystem.com/components/data-table/style/)

**Border radius / stroke**
- Ant Design: `borderRadius` 6, `borderRadiusSM` 4, `borderRadiusLG` 8, `borderRadiusXS` 2; `lineWidth` 1. — [Ant Design: Customize Theme](https://ant.design/docs/react/customize-theme)
- Primer: borderRadius-small 3px, medium/default 6px, large 12px, full 9999px; borderWidth thin/default 1px, thick 2px, thicker 4px. — [Primer: Size primitives](https://primer.style/foundations/primitives/size)
- Fluent 2: None 0, Small 2 (small badges), **Medium 4 (buttons, dropdowns)**, Large 8, X-Large 12 (popovers, sheets), Circle 50%; "rectangles default to 4px, drop to 2px for shapes under 32px"; stroke Thin 1, Thick 2, Thicker 3, Thickest 4 (web). — [Fluent 2: Shapes](https://fluent2.microsoft.design/shapes)
- Material 3 baseline (secondary source — Flutter package docs): none 0, extraSmall 4dp, small 8dp, medium 12dp, large 16dp, extraLarge 28dp, full. — [material_design Flutter package](https://pub.dev/documentation/material_design/latest/); token naming `--md-sys-shape-corner-*` — [material-web.dev: Shape](https://material-web.dev/theming/shape)

### Inferences
- Token proposal: `--space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-5:24px; --space-6:32px; --space-7:48px` (+ `--space-half:2px`). Control heights: `--control-sm:28px; --control-md:32px; --control-lg:40px`. Radius: `--radius-sm:4px` (inputs, buttons, tags), `--radius-md:6px` (cards/panels), `--radius-lg:8px` (dialogs). Avoid M3-style 12–28px radii and pills for a desktop data tool — they read as consumer/"AI template" styling (inference; Carbon/Fluent/Primer all stay ≤ 12px).

### Gaps
- Carbon's exact button heights per size and its corner-radius policy (Carbon is largely 0px) were not on the fetched pages.
- Official m3.material.io shape page didn't render; M3 values above are from a secondary source.

## 3. Neutral scales, single accent, semantic status colours with WCAG AA; how status is expressed

### Takeaway
Use one accent (a blue in all reference systems) plus neutral greys, and keep red/green/yellow/blue strictly semantic. Several default "brand" status hexes fail 4.5:1 with white text (Ant success/warning, Carbon success/warning); you need separate darker *text/fg* steps and *subtle bg* steps per status. Status must never rely on colour alone (icon/shape + label).

### Cited Findings
**Carbon White theme tokens**: background #ffffff; layer-01 #f4f4f4; layer-02 #ffffff; field-01 #f4f4f4; border-subtle-01 #c6c6c6; border-strong-01 #8d8d8d; text-primary #161616; text-secondary #525252; text-helper #6f6f6f; text-placeholder rgba(22,22,22,.4); text-disabled rgba(22,22,22,.25); interactive / focus / link-primary / button-primary #0f62fe; focus-inset #ffffff; support-error & button-danger-primary #da1e28; support-success #24a148; support-warning #f1c21b; support-info #0043ce. Themes: White, Gray 10, Gray 90, Gray 100. — [Carbon: Color tokens](https://carbondesignsystem.com/elements/color/tokens/)
- Carbon status palette: Red 60 #da1e28 (error/danger), Orange 40 #ff832b (serious warning; outline Orange 60 #ba4e00), Yellow 30 #f1c21b (warning; outline Yellow 60 #8e6a00), Green 50 #24a148 (success), Blue 70 #0043ce (passive info), Gray 60 #6f6f6f (draft/not started), Purple 60 #8a3ffc (undefined). Rules: "Relying solely on color to convey status is insufficient"; indicators should combine ≥2 (accessibility section) or ≥3 (elsewhere — the page is internally inconsistent) of colour/shape/symbol/type; ≥3:1 between status colours and against the page background; shape indicators need outlines + text label (especially yellow/orange on light themes); icon indicator 16px icon with 14pt type, shape indicator 16px; >5–6 indicators overloads users; use plain text when no action needed. — [Carbon: Status indicator pattern](https://carbondesignsystem.com/patterns/status-indicator-pattern/)
- Ant Design seed: colorPrimary #1677ff, colorSuccess #52c41a, colorWarning #faad14, colorError #ff4d4f, colorInfo #1677ff, colorTextBase #000, colorBgBase #fff. Table: headerBg #fafafa, rowHoverBg #fafafa, borderColor #f0f0f0, rowSelectedBg #e6f4ff. — [Ant Design: Customize Theme](https://ant.design/docs/react/customize-theme); [Ant Design: Table](https://ant.design/components/table)
- Atlassian roles: neutral, brand, information, success, warning, danger, discovery, accent ("meaningless decoration" — never for meaning), inverse, input. Token grammar `color.{text|background|border|icon}.{role}.{emphasis}.{state}` e.g. `color.background.danger.bold.hovered`. Bold yellow backgrounds take `warning.inverse` (dark) text. WCAG AA: 4.5:1 for text <24px, 3:1 for essential UI and ≥24px text. Don't show selection with colour alone; `color.border.focused` only for focus, not selection. — [Atlassian: Color](https://atlassian.design/foundations/color)
- Primer roles: accent (links, selected, focus), success, attention (warning, in-progress), danger, open/closed/done, sponsors. *Muted* bg+border for subtle emphasis; *emphasis* bg always paired with `fgColor-onEmphasis`; neutral step 9 is min for text on steps 0–4; step 8 min for interactive control borders on `bgColor-muted`; high-contrast themes target 7:1. — [Primer: Color overview](https://primer.style/foundations/color/overview)

**Computed contrast ratios (WCAG 2 formula, my calculation)**
- White text on: #0f62fe 5.0 ✓AA; #1677ff 4.10 ✗ (AA-large only); #da1e28 5.0 ✓; #ff4d4f 3.27 ✗; #24a148 3.35 ✗; #52c41a 2.27 ✗; #faad14 1.90 ✗; #f1c21b 1.68 ✗; #0043ce 7.79 ✓; #8a3ffc 5.0 ✓; #ff832b 2.46 ✗.
- On #ffffff as text: #161616 18.1; #525252 7.81; #6f6f6f 5.02; #8e6a00 4.99; #ba4e00 5.03; #0043ce 7.79 (all ✓AA). #8d8d8d 3.32 (OK only as a control border, 1.4.11 3:1); #c6c6c6 1.71 (decorative divider only).
- #161616 on #f1c21b (yellow) 10.75 ✓ — yellow fills need dark text.
- On #f4f4f4: #525252 7.1 ✓; #6f6f6f 4.57 ✓ (barely).
- #1677ff on #e6f4ff (Ant selected row) 3.66 — fine as a non-text indicator, ✗ as small text.
- Ant table borders #f0f0f0 vs white 1.14 and #fafafa header vs #f0f0f0 1.09 — purely decorative separation, invisible on low-quality hospital/office monitors (inference).

### Inferences
- Token structure per status (adapted from Atlassian/Primer): `--{status}-fg` (text/icon, ≥4.5:1 on bg), `--{status}-bg-subtle` (tinted background for badges/rows), `--{status}-border`, `--{status}-solid` (rare, banners/primary danger, with white or dark "on" text). Starting values that pass: danger-fg #da1e28, warning-fg #8e6a00 (with #f1c21b only as a fill/dot with dark text), success-fg — use a darker green than #24a148 for text (#24a148 is fine as a dot/icon at 3.35:1, which meets 3:1 non-text contrast), info-fg #0043ce, neutral-fg #525252.
- Single accent: #0f62fe (Carbon blue 60) passes 5.0:1 with white; Ant's #1677ff does not pass 4.5:1 for 14px button text — prefer a darker accent if using Ant's hue.
- Status display hierarchy for a workbench table: (1) plain text when no action needed; (2) dot/shape (8–10px) + text label for scanning many rows; (3) icon + label + subtle bg (badge/lozenge) for items needing attention; (4) solid banner only for page-level blocking errors. Matches Carbon's attention levels.
- Neutral scale: ~10 steps from #ffffff → #161616 (Carbon gray: f4f4f4, e0e0e0, c6c6c6, a8a8a8, 8d8d8d, 6f6f6f, 525252, 393939, 262626, 161616 — only the values listed in the Carbon tokens above were verified; the intermediate e0e0e0/a8a8a8/393939/262626 are from memory and should be checked).

### Gaps
- Atlassian and Primer hex values for status tokens were not on the fetched pages.
- Carbon Gray 100 (dark) hex values were not returned by the fetch.
- A verified darker Carbon green for text (Green 60/70) was not fetched.

## 4. Tables, form fields, button hierarchy, focus ring, density/compact modes

### Takeaway
Use one primary button per view; secondary/tertiary/ghost for others; danger in primary/tertiary/ghost forms. Focus: solid 2px ring (outside or with offset), ≥3:1 change. Density via row-height tokens (24/32/40/48) and table padding variants; header row height must match body rows.

### Cited Findings
**Buttons (Carbon)**: "Each page should have only one primary button"; secondary "can only be used in conjunction with a primary button" (negative action: Cancel/Back), never alone; tertiary may stand alone or with primary; ghost for least pronounced actions; danger has primary / tertiary / ghost styles and cannot be icon-only; don't put two high-emphasis buttons in a group; groups for 2–3 actions, beyond that use a menu; full-page forms put primary on the left, dialogs/wizards bottom-right; button label left-aligned; full-span buttons max 320px. — [Carbon: Button usage](https://carbondesignsystem.com/components/button/usage/)

**Tables**
- Carbon: row heights xs 24 / sm 32 / md 40 / lg 48 / xl 64; cell padding 16px L/R (`$spacing-05`); column header bg `$layer-accent`, `heading-compact-01` 14px/600; rows `body-compact-01` 14px; zebra uses `$layer-accent`; row bottom border `$border-subtle`; header row must match row size; xl only for two-line rows; 32px toolbar with sm/xs rows, 48px toolbar with lg/xl; pagination height matches row height; table header margins 16 top / 24 bottom. — [Carbon: Data table style](https://carbondesignsystem.com/components/data-table/style/)
- Ant Design Table: large (default) cellPadding 16/16; middle 12 block / 8 inline; small 8/8; font 14 in all sizes; headerBg #fafafa; rowHoverBg #fafafa; borderColor #f0f0f0; rowSelectedBg #e6f4ff. — [Ant Design: Table](https://ant.design/components/table)
- Atlassian: small spacing range (0–8px) is intended for table cells and icon buttons. — [Atlassian: Spacing](https://atlassian.design/foundations/spacing)

**Form fields**
- Carbon field-01 background #f4f4f4 on white, text-placeholder rgba(22,22,22,.4), text-helper #6f6f6f, helper-text-01 12/16. — [Carbon: Color tokens](https://carbondesignsystem.com/elements/color/tokens/); [Carbon: Type sets](https://carbondesignsystem.com/elements/typography/type-sets/)
- Primer: interactive control borders must meet at least neutral step 8 against `bgColor-muted`. — [Primer: Color overview](https://primer.style/foundations/color/overview)
- Atlassian has dedicated `input` colour role. — [Atlassian: Color](https://atlassian.design/foundations/color)

**Focus**
- WCAG 2.2 SC 2.4.13 Focus Appearance (Level **AAA**): indicator area ≥ a 2 CSS px perimeter of the component and ≥3:1 contrast between focused and unfocused pixels; "the simplest way... is a solid 2 CSS pixel thick perimeter"; a 2px *inset* border fails (needs 3px); focus indicators are also subject to 1.4.11 Non-text Contrast. — [W3C Understanding 2.4.13](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html)
- Primer: `--outline-focus-width` 2px, `--outline-focus-offset` -2px. — [Primer: Size primitives](https://primer.style/foundations/primitives/size)
- Carbon: `focus` #0f62fe with `focus-inset` #ffffff (double ring for coloured buttons). — [Carbon: Color tokens](https://carbondesignsystem.com/elements/color/tokens/)
- Atlassian: separate `color.border.focused` token, used only for focus. — [Atlassian: Color](https://atlassian.design/foundations/color)

**Density / compact**
- Ant Design `theme.compactAlgorithm` uses sizeStep 2 instead of 4; combinable with darkAlgorithm. — [Ant Design: Customize Theme](https://ant.design/docs/react/customize-theme)
- Primer exposes condensed/normal/spacious inline padding per control size. — [Primer: Size primitives](https://primer.style/foundations/primitives/size)
- Carbon offers xs/sm row sizes for dense tables and productive (14px) type for dense UI. — [Carbon: Data table style](https://carbondesignsystem.com/components/data-table/style/); [Carbon: Type sets](https://carbondesignsystem.com/elements/typography/type-sets/)

### Inferences
- CSS: `:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }` (outside offset passes 2.4.13 per the W3C note); on accent-filled buttons add `box-shadow: 0 0 0 1px #fff inset` (Carbon inset pattern).
- Density as a single attribute: `[data-density="compact"] { --row-h:32px; --control-md:28px; --cell-px:8px }`, default `--row-h:40px; --cell-px:12–16px`. With 14px/22px CJK text, a 32px row leaves 5px vertical padding — the practical floor; 24px rows are too tight for Han glyphs (inference).
- Table: 1px row dividers with ≥ #e0e0e0 on white (Ant's #f0f0f0 at 1.14:1 is nearly invisible); zebra optional; numeric columns right-aligned + tabular-nums; sticky header same height as rows.

### Gaps
- Carbon/Fluent text-input exact height per size and label spacing were not fetched; Fluent 2 focus ring spec not fetched.
- Ant's compact `controlHeight` value is not stated on the doc page (commonly 28 — unverified).

## 5. Dark mode for an internal tool: worth it? token strategy

### Takeaway
Research summarized by NN/g favours light mode for reading performance (especially small text) in most conditions, and dark mode is mainly a preference/low-vision accommodation; for a 14px-dense zh-TW internal tool, ship light first but structure tokens semantically so dark can be added cheaply.

### Cited Findings
- NN/g "Dark Mode": light (positive polarity) mode yielded better performance in visual-acuity and proofreading tasks; the advantage grows as font size shrinks; holds for young (18–33) and older (60–85) adults; users perceived no readability difference; dark mode may help some low-vision users (e.g., cataracts). — [NN/g: Dark Mode vs. Light Mode](https://www.nngroup.com/articles/dark-mode/)
- Atlassian: every colour token maps to a value per theme; "if you use design tokens, you don't need to map your own dark mode values". — [Atlassian: Color](https://atlassian.design/foundations/color)
- Carbon ships four themes (White, Gray 10, Gray 90, Gray 100) over the same token names. — [Carbon: Color tokens](https://carbondesignsystem.com/elements/color/tokens/)
- Ant Design derives dark map tokens (backgrounds, text) via `darkAlgorithm` from the same seeds; `colorBgElevated` is brighter in dark mode (elevation by lightness, not shadow); advises not to use base seed colours directly in code. — [Ant Design: Customize Theme](https://ant.design/docs/react/customize-theme)
- Primer supports light and dark across nine themes incl. high-contrast (target 7:1). — [Primer: Color overview](https://primer.style/foundations/color/overview)

### Inferences
- For the workbench: light theme only for v1; but name tokens by role (`--bg-canvas`, `--bg-surface`, `--bg-raised`, `--fg-default`, `--fg-muted`, `--border-default`, `--accent`, `--danger-fg`, …) never by value (`--gray-100`), and define them under `:root` with a `[data-theme="dark"]` / `prefers-color-scheme` override block. Dark: canvas ~#161616, surfaces step lighter for elevation (Ant/Carbon approach), re-check every status-fg against dark bg (lighter tints needed).
- Thin CJK strokes (JhengHei Light/Regular) on dark backgrounds at 14px are a further reason to defer dark mode (inference consistent with NN/g small-font finding).

### Gaps
- No source specifically studied dark mode for CJK text or for enterprise/clinical internal tools.
- Carbon Gray 100 hex values not retrieved, so no verified dark palette is provided here.

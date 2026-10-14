# AI-look ("AI slop" / AI 味) UI patterns: catalogue, causes, and counter-practices

Scope note: Research done 2026-10-14. Most sources are practitioner blogs, community "anti-slop" agent skills, and one vendor article (Anthropic). I found **no controlled studies** that measure how often these tells appear. "Consensus" below means the same pattern shows up independently in 3 or more unrelated sources. "Single-author" means one source.

Applicability tags used below: **[INT]** = applies to internal, data-heavy tools such as the zh-TW phlebitis workbench. **[MKT]** = mainly applies to marketing or landing pages. **[BOTH]** = applies to both.

---

## Q1. Which recurring visual patterns are called out as "AI-looking"?

### Takeaway
There is strong consensus on a core set of tells: Inter or another default sans everywhere, purple/indigo (often purple-to-blue) gradients, a centered hero plus three icon cards, uniform large border radii, and decorative effects such as glows, glass, and gradient text. For **internal dashboards** specifically, the tells sources call out are: KPI/metric-card grids as the default layout, hero strips inside dashboards, eyebrow/uppercase letter-spaced labels, pill/badge overload, meaningless status dots, coloured side-border cards, nested cards, emoji as icons, and dramatic shadows.

### Cited Findings

**Consensus tells (3 or more independent sources)**
- **Inter or another default sans as the only typeface [BOTH].** Anthropic lists Inter, Roboto, Arial, Open Sans, Lato and system fonts as the convergent defaults — [Anthropic, "Improving frontend design through Skills" (Nov 12, 2025)](https://claude.com/resources/articles/improving-frontend-design-through-skills). The same tell is named by [prg.sh (Oct 2025)](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website), [Kosta Canatselis, "Spot the Slop" (Jul 2026)](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c), and the [unslop-ui playbook](https://claudecodehq.com/playbooks/unslop-ui), which adds Geist.
- **Purple/indigo accents and purple-to-blue gradients [BOTH].** Anthropic names "purple gradients on white backgrounds" — [Anthropic](https://claude.com/resources/articles/improving-frontend-design-through-skills). Canatselis says the gradient is used decoratively on backgrounds, CTAs and accents — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c). Jeff Humble's list also includes it — [Fountain Institute, "7 Signs a UI Has Been Vibe Coded"](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui). Noqta adds that it appears "with no semantic meaning" — [Noqta (Jun 2026)](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026).
- **Same dashboard skeleton from every tool [INT].** Prompting several tools with the same dashboard request yields the same left-rail sidebar, rounded card grid and `bg-indigo-500` accent — reported in search-result summaries of [vp0.com](https://vp0.com/blogs/vibe-coding-app-ui-components) and similar vibe-coding write-ups (secondary, not independently verified).
- **Centered hero, three icon feature cards, CTA [MKT].** Named by [prg.sh](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website), [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui) and [Noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026).
- **Uniform, oversized border radius on everything [BOTH].** Noqta says cards, buttons, inputs, badges and images all share one exaggerated radius, which "flattens hierarchy" — [Noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026). Unslop-ui lists "large radius everywhere, pill buttons as the only button shape" and untouched shadcn `rounded-lg` — [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui). Uncodixify bans 20–32px radii, says even "12px everywhere" is too much, and bans "the same rounded rectangle across sidebar, cards, buttons, panels" — [Uncodixify SKILL.md](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md). Canatselis lists "uniform everything: identical padding, radius, card height" — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).
- **Glows, aurora or radial backgrounds, especially in dark mode [BOTH].** Named by [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui) ("decorative glow effects in dark mode"), [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui) ("unprompted neon glow"), and [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md), which bans "premium dark mode" built from blue-black gradients, radial backgrounds and cyan accents.
- **Emoji used as icons, headers or bullets [BOTH].** Named by [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui) and [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui). Wikipedia's AI-writing guide also lists emoji in headings and lists as a tell — [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
- **Coloured border on one side of a (rounded) card [BOTH].** Noqta calls it "the single most recognizable signature of AI-generated UI," attributing that to unnamed designers — [Noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026). Humble lists "multicolored side tabs," a different colour bar on every block — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui). Canatselis names "a coloured line along the left edge of a panel combined with a curve" — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).
- **Fake "Live"/"New" badges and meaningless status dots [INT].** Noqta describes a pulsing-dot pill on features that are neither live nor new as "decoration cosplaying as information" — [Noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026). Humble flags "meaningless status dots," whose colours do not map to any real state — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui). Uncodixify bans `::before` status dots, nav badges showing counts or "Live," and "tables with a tag badge on every status" — [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md).
- **Uppercase, letter-spaced "eyebrow" labels [BOTH].** Noqta says wide tracking is auto-applied to uppercase labels and eyebrow text, where it hurts readability — [Noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026). Uncodixify bans "eyebrow labels and uppercase letter-spaced muted labels" and any headline built from `<small>` eyebrow + `<h2>` tagline + explanatory paragraph — [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md).
- **Nested cards / cards for everything [INT].** Humble says nested cards flatten hierarchy, and recommends cards only for independently actionable items — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui). Uncodixify bans multiple nested panel types (panel, panel-2, rail-panel, table-panel) — [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md).
- **Untouched shadcn/Tailwind look [BOTH].** Unslop-ui flags stock slate/zinc cards, default theme tokens, uniform `rounded-lg` and default padding — [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui).
- **Animation overuse, or the opposite [BOTH].** Unslop-ui flags fade-ins on every section and hover-scale on every card — [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui). Canatselis flags motion that is either absent or identical everywhere — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c). Uncodixify bans hover transforms like `translateX(2px)` on nav links — [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md).
- **Glassmorphism [BOTH].** Named in [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md) (frosted panels, glass cards) and in [Lerat, DEV Community (Jul 2026)](https://dev.to/lyd_lyd_d4869af25d33ce0eb/why-do-ai-generated-websites-all-look-the-same-k2j). Unslop-ui, however, lists glassmorphism as only "low-signal / contested" — [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui).

**Dashboard / internal-tool-specific tells, mostly from one source ([Uncodixify SKILL.md](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md), a community skill with about 2.7K GitHub stars, so treat as single-source but detailed)**
- "Hero sections inside internal UI," and "dead space for 'expensive' looks"
- "Metric-card grids as the first instinct," "KPI card grids as the default dashboard layout," and "fake charts that fill space"
- Floating, detached sidebars with rounded outer shells; roughly 280px sidebars with a brand block on top; sidebar workspace blocks with CTA buttons
- Right-rail panels such as "Today," "Team focus" or "Recent activity" filled with decorative copy
- Quota/usage panels with progress bars; donut charts with vague percentages; canvas charts in glass cards
- Dramatic shadows such as `0 24px 60px rgba(0,0,0,0.35)`; coloured shadows; gradient buttons, brand marks and pipeline bars
- Trend indicators shown only as coloured text
- Footer meta lines (e.g., "dark mode • single-file HTML")
- Section notes or mini-notes that explain the UI; overused low-contrast gray-blue text
- Mixed alignment (some content left-hugging, some center-floating)
- Overpadded layouts
- Canatselis adds "everything visible at all times," e.g., an entry table, entry panel and export panel side by side; the fix is progressive disclosure — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c)
- Humble adds "neon palettes," where 5–6 saturated colours compete at equal volume — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui)

**"Second-generation slop" and contested items**
- Unslop-ui ranks a newer default as its #0 tell: cream/beige background + serif display font + sage/forest-green accent. It says swapping indigo for this "just resets the clock" — [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui). Uncodixify likewise bans "serif headline + sans fallback as a shortcut to premium" — [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md).
- Anthropic notes that models converge on Space Grotesk even when told to avoid the common fonts — [Anthropic](https://claude.com/resources/articles/improving-frontend-design-through-skills).
- Unslop-ui says mesh/aurora backgrounds, bento grids, dark mode itself, and shadcn/Tailwind as tools are **not** real complaints. It rates centered-everything layouts, stock illustrations, glassmorphism and bento as low-signal — [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui). This conflicts with Uncodixify's blanket bans.

### Inferences
- For an internal zh-TW workbench, the highest-yield tells to remove are the dashboard-specific ones: KPI card grid at the top, hero/welcome strip, eyebrow labels, badge on every status cell, glow/gradient decoration, floating rounded sidebar, nested cards, decorative explanatory sub-copy, and emoji icons. Marketing-page tells (centered hero, three feature cards) matter only for an app home/landing view.
- **Uppercase letter-spaced eyebrows have no direct CJK equivalent.** In zh-TW UIs the analogous tell is likely a small, muted, letter-spaced label above each heading, often a decorative English word above a Chinese heading (e.g., "OVERVIEW" over 總覽). This is my extrapolation; I found no source discussing CJK eyebrows.
- The tell is the **unconsidered default**, not any specific colour. Purple, serif or cream are acceptable when deliberately chosen, which is unslop-ui's stated principle.

### Gaps
- No quantitative data on how prevalent each tell is.
- The claim that the one-sided coloured border is "the most recognizable signature" is attributed to unnamed designers (Noqta) and is unverified.
- I found no source specifically on "too much whitespace" in AI dashboards other than Uncodixify's "overpadded layouts / dead space," plus Ström's general argument that interfaces have become less dense (Q4).
- The Wes Bos "four horsemen" screenshot is cited by Noqta without a link, and I could not verify it.

---

## Q2. Which copywriting patterns are called out?

### Takeaway
Called-out patterns:
- Generic slogan headlines that could belong to any company ("Scale without limits," "Transform your X," "Supercharge…")
- Em-dash-heavy prose
- "Not just X, but Y" constructions and rule-of-three lists
- Promotional vocabulary (seamless, robust, vibrant, pivotal, showcase…)
- Decorative explanatory copy under headings, which is especially out of place in dashboards

The general-prose evidence (Wikipedia) is strong. The UI-specific copy evidence is thinner and mostly comes from anti-slop skills and designer blogs.

### Cited Findings
- **Generic headlines [MKT].** "Scale without limits."-style headlines could belong to any company. The fix is to rewrite in a real person's voice "until the founder would say it aloud" — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).
- **Copy clichés paired with gradient text [MKT].** Unslop-ui lists "Transform your X" and "Supercharge" — [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui).
- **Decorative copy and the eyebrow/tagline/paragraph formula [INT].** Uncodixify bans "ornamental labels, generic startup copy," and the headline structure of `<small>` eyebrow + `<h2>` tagline + explanatory paragraph. It also bans "section notes / mini-notes explaining the UI" and "decorative copy" in dashboard sections — [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md).
- **Em dashes.** Wikipedia's editor guide lists em-dash overuse as an AI-writing indicator (2022–2026) and notes newer models use more commas and periods — [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). A podcast on polishing AI landing pages calls em dashes "a dead giveaway" — [Audible podcast episode "How to Polish Your AI Landing Page for Launch"](https://www.audible.co.uk/podcast/How-to-Polish-Your-AI-Landing-Page-for-Launch/B0GJTRFKML) (weak source; single host opinion).
- **Overused vocabulary and structures.** Wikipedia lists the following [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing):
  - Overused words: "delve" (2023 to early 2024), "vibrant," "robust," "crucial," "pivotal," "tapestry," "showcase," "testament," "underscore," and "seamlessly" in promotional text
  - "Not just X, but Y" and "no X, no Y, just Z" parallelisms; the rule of three
  - Title Case headings; boldface overuse; emoji in headings and lists
  - Promotional or press-release tone
- **Copy rules for interfaces (Vercel Web Interface Guidelines)** — [Vercel Design Guidelines](https://vercel.com/design/guidelines):
  - Active voice and action verbs; keep copy brief; use numerals for counts
  - Specific button labels rather than "Continue"
  - Errors that say how to fix the problem
  - Locale-formatted dates and numbers
  - Note: Vercel recommends Title Case for headings and buttons in product UI, which conflicts with Wikipedia's "title case" tell. The contexts differ: Vercel's rule is for English app chrome, Wikipedia's is for encyclopedia prose.

### Inferences
- For a zh-TW internal tool:
  - Drop slogan-style page headings (e.g., 「智慧標註，精準洞察」) in favour of plain nouns or noun phrases that name the data (「影像審查」「訓練紀錄」「回收桶」).
  - Remove the one-line explanatory sentence under every heading unless it carries information the user needs.
  - Avoid decorative bilingual labels (an English eyebrow above a Chinese heading). This extrapolates the eyebrow/ornamental-label tell; I found no source specific to bilingual labels.
  - Em-dash-heavy taglines map to Chinese text that leans on 「——」 and four-character parallel slogans. This is also an extrapolation.

### Gaps
- No source found that specifically discusses Chinese-language AI copy tells in UI, or bilingual decorative labels.
- No source specifically lists "seamless/effortless" for UI microcopy; it is supported only via Wikipedia's general promotional-vocabulary list.

---

## Q3. Why do LLM coding tools converge on these defaults?

### Takeaway
Anthropic calls this "distributional convergence." Models sample high-probability "safe" choices that dominate web training data. The specific look reflects the React + Tailwind + shadcn/ui + Lucide stack that coding tools are configured to emit, along with Tailwind's demo-era `bg-indigo-500`. The causal story about indigo is widely repeated but rests on commentary plus a joking tweet, not measurement.

### Cited Findings
- Anthropic: during sampling, models predict tokens from statistical patterns. Safe choices that "work universally and offend no one" dominate training data, so without direction Claude falls back to that center. Anthropic calls this "distributional convergence" — [Anthropic (Nov 2025)](https://claude.com/resources/articles/improving-frontend-design-through-skills).
- prg.sh: LLMs output the statistical average of training data, and for web UI that average is purple — [prg.sh](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website).
- Adam Wathan (Tailwind) posted a joking apology on Aug 7, 2025 for making every Tailwind UI button `bg-indigo-500` five years earlier — [Wathan on X](https://x.com/adamwathan/status/1953510802159219096), reported by [prg.sh](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website) and [AIbase (zh)](https://news.aibase.com/zh/news/20365). Reported view counts differ between sources (about 684K vs. more than 1M). The causal link to model behaviour is commentators' explanation, not something Wathan documented.
- Stack-specific explanation (from search summaries of [managed-code.com](https://managed-code.com/blog-post/why-ai-websites-look-the-same) and [codemyspec](https://codemyspec.com/blog/vibe-coded-websites-look-the-same); I did not fetch these pages in full):
  - Public React code is mostly styled with Tailwind, often through shadcn/ui + Radix + Lucide.
  - shadcn components are copied into repos as source, so identical code appears verbatim in thousands of repos.
  - shadcn's own default primary is neutral (oklch 0.205 0 0), not indigo, so the purple comes from tutorials and templates.
- The model reproduces "patterns they've seen thousands of times," and generic prompts yield the most probable answer — [Lerat, DEV Community](https://dev.to/lyd_lyd_d4869af25d33ce0eb/why-do-ai-generated-websites-all-look-the-same-k2j).
- The tells "reflect averages from training data rather than deliberate design decisions" — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui). "Slop is design with no author" is a framing quoted in search results from the [superdesign.dev blog](https://www.superdesign.dev/blog/why-ai-design-looks-generic) (not fetched).
- A UX Collective critique (fetch blocked, so known only from a search summary) says Anthropic's skill line "NEVER converge on common choices across generations" cannot work as written. Each conversation is isolated, so the model cannot see its other generations, and in-session iteration uses its own already-average output as baseline — [UX Collective, "AI design isn't ugly, it's fluent"](https://uxdesign.cc/ai-design-isnt-ugly-it-s-fluent-and-that-s-the-problem-131b2f4eb78c).
- Swapping component libraries won't help, because the gap is a missing design decision, not the library — per the search summary of [managed-code.com](https://managed-code.com/blog-post/why-ai-websites-look-the-same).

### Inferences
- Three causes compound: (1) the training-data mode, (2) tool scaffolding that defaults to the same stack, and (3) the absence of a brief or reference. Only (3) is in the user's control, so the fix is to supply explicit constraints (tokens, references, bans) rather than to switch frameworks.
- Banning one default tends to produce the next default (Space Grotesk; cream/serif/sage). So constraints should be **positive and project-specific**, i.e., "use these tokens," not only "avoid purple."

### Gaps
- No empirical study measuring the training-data share of Tailwind indigo, or measuring output convergence across models.

---

## Q4. Concrete counter-practices recommended by experienced designers

### Takeaway
Consensus: replace defaults with **explicit, named decisions**:
- A small token system (spacing scale, 1–2 radii, restrained shadows)
- A restrained palette with colour used only for meaning
- Deliberate typographic hierarchy
- Real content and all states (empty, loading, error)
- Grouping by whitespace and proximity rather than card boxes
- Removing decoration that does not communicate state

For internal tools, sources favour information density, plain tables, plain sidebars, and references like Linear, GitHub, Stripe and Raycast over expressive marketing aesthetics.

### Cited Findings

**Colour [BOTH]**
- Use colour semantically, naming tokens by function (primary action, warning, success) rather than appearance (e.g., "gradient-start") — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).
- Use one dominant colour, one accent and one neutral; build hierarchy with contrast, not more colours. Treat colour as a shared resource and define which elements get the accent and why. "Nothing is emphasized when everything is emphasized" — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui).
- Tie every status indicator to a defined, labelled state. If a dot needs explanation, use a text label; remove dots when nothing changes state — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui).
- Uncodixify's colour order: use the existing project palette first, otherwise a calm predefined palette. Colours "should stay calm and not compete" — [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md).
- Don't rely on colour alone (pair it with text labels); use colour-blind-friendly chart palettes — [Vercel guidelines](https://vercel.com/design/guidelines).
- Anthropic (marketing-leaning): "Dominant colors with sharp accents outperform timid, evenly-distributed palettes"; use CSS variables — [Anthropic](https://claude.com/resources/articles/improving-frontend-design-through-skills).

**Hierarchy and grouping [BOTH]**
- Break uniformity on purpose: make the primary element larger, closer and heavier, and let secondary elements recede — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).
- Group with whitespace, proximity and typography; use cards only for independently actionable items — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui).
- Build depth through typography, contrast and surface levels, and remove effects that don't respond to user behaviour or communicate something — [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui).

**Concrete token values for internal UI [INT]** (single source, but the most concrete: [Uncodixify "Keep It Normal"](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md))
- Sidebar: 240–260px fixed, solid background, 1px right border, no rounded outer shell
- Headers: plain h1/h2, no eyebrows, no uppercase labels, no gradient text
- Buttons: radius ≤ 8–10px, no pills or gradients
- Cards: radius ≤ 8–12px, subtle border, shadow blur ≤ 8px
- Badges: 6–8px radius, only when needed
- Icons: 16–20px, monochrome, no icon background tiles
- Body text: 14–16px; spacing scale 4/8/12/16/24/32
- Borders: 1px solid; shadow max `0 2px 8px rgba(0,0,0,0.1)`
- Transitions: 100–200ms, opacity/colour only, no transforms
- Tabs: underline indicator, not pills
- Tables: clean rows, subtle hover, zebra only if needed
- Forms: labels above fields, no floating labels
- Toolbars: 48–56px
- Reference products: Linear, Raycast, Stripe, GitHub
- Process rule: "reason internally about the defaults you would normally reach for, then avoid them"
- Noqta: a restrained radius scale (example: 6px for cards), with pills reserved for where they belong — [Noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026).
- Vercel: nested radii (child ≤ parent, concentric); layered shadows (ambient + direct) paired with semi-transparent borders; align everything to a grid or optical centre — [Vercel guidelines](https://vercel.com/design/guidelines).

**Data, numbers and density [INT]**
- Use tabular numerals (`font-variant-numeric: tabular-nums`) or monospace for comparing figures — [Vercel guidelines](https://vercel.com/design/guidelines).
- Put a space between number and unit, and keep decimals consistent within a context — [Vercel guidelines](https://vercel.com/design/guidelines).
- Matthew Ström, "UI Density" [mattstromawn.com/writing/ui-density](https://mattstromawn.com/writing/ui-density) (first published May 2024):
  - Interfaces have become less dense than 2000s software. Density should be judged as **value delivered per time and space**, not as visual clutter.
  - Maximize information per element in the spirit of Tufte's data-ink ratio; remove non-data ink but keep whitespace that carries meaning.
  - Use Gestalt grouping deliberately.
  - Cut latency first.
  - Feedback by delay: under 100ms nothing; 100ms–1s subtle cue; 1–10s indeterminate loader; 10s–1min determinate progress; over 1min let the user leave and notify on completion.
  - Examples: Bloomberg Terminal, McMaster-Carr, Craigslist.
- Apply progressive disclosure instead of showing every function at once; start from user stories and journey maps — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).

**States and real content [BOTH]**
- Design the unhappy paths deliberately: empty states that prompt action, and errors in human language — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).
- Design every state (empty, sparse, dense, error) and test with short, average and very long user content. Skeletons should match final dimensions — [Vercel guidelines](https://vercel.com/design/guidelines).
- Visual polish ≠ usability. Check bulk-action confirmations, persisted filters and keyboard operability of tables; common AI gaps are missing empty states, broken keyboard navigation and type-scale drift (search summary of [MUI recipes blog](https://recipes.mui.com/blog/vibe-coding-fast-ui-work-without-losing-control); not fetched in full).
- Check generated UIs for validation, required-field indicators and accessibility — [prg.sh](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website).

**Motion [BOTH]**
- Add micro-interactions only to the primary button and inputs; use scroll animation only where it aids navigation; remove purely decorative motion — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).
- Honour reduced-motion preferences — [Vercel guidelines](https://vercel.com/design/guidelines).

**Typography**
- Change the font first: one display face for personality plus one readable body face, used consistently [MKT-leaning] — [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c).
- Uncodixify, for internal UI: system or simple sans-serif, no serif/sans mixing — [Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md). This conflicts with Anthropic's "never use Inter/system fonts" (see Q5), and Uncodixify also bans "Inter, Roboto, Arial, Segoe UI… unless the product already uses them." The two sources target different contexts.

**Process [BOTH]**
- Ban defaults by name; reference specific aesthetics (era or movement); tune one dimension at a time; gather references from Dribbble, Mobbin or Awwwards and describe what works in them — [prg.sh](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website).
- A tell is an *unspecified default*, not a banned colour. Fix findings with the project's actual tokens rather than another attractive default — [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui).

### Inferences
- **For the phlebitis workbench (internal, data-heavy, zh-TW)**, the sources point to the following. This is a synthesis, not a single source's recommendation.
  - Plain fixed sidebar + header + tables as primary views; no hero/welcome banner; no KPI-card row unless the numbers are the task.
  - A 4/8-based spacing scale, radius ≤ 6–8px, 1px borders instead of shadows, and at most one accent colour.
  - Colour reserved for class labels and status (e.g., phlebitis grade, train/val/test split, deleted/restored), always paired with text.
  - Tabular numerals for metrics tables.
  - Real states: empty trash, no images matched by filter, training running/failed.
  - Plain noun headings in Traditional Chinese, without decorative English sublabels.
- **CJK font note (inference, not sourced):** Inter has no CJK glyphs. In a zh-TW UI the Chinese text renders in a fallback (e.g., Microsoft JhengHei / Noto Sans TC / PingFang TC), so "Inter everywhere" is less of a visible tell than mixed or unconsidered font fallback. Pinning one CJK family (plus a Latin family whose x-height pairs with it), and tabular numerals for numbers, is the deliberate choice. Letter-spacing and uppercase tricks do not transfer to CJK.
- The Anthropic skill's advice (distinctive display fonts, atmospheric layered-gradient backgrounds, orchestrated page-load animations) is aimed at marketing pages and creative artifacts. Applied to an internal audit/trash tool it would *add* decoration, so it should not be applied wholesale.

### Gaps
- No NN/g or Smashing Magazine article specifically on "AI-look" UI was retrieved in this pass. NN/g's evergreen guidance on data tables and density was not fetched, so it is not cited.
- Ström's essay date: the live page shows no date, while search snippets say May 20, 2024 (the Gigazine summary is dated May 26, 2024). His current affiliation is inconsistent across sources (Stripe vs. mu.design).

---

## Q5. Published prompts/guides on avoiding the generic AI aesthetic: their concrete rules

### Takeaway
The most authoritative published guide is Anthropic's Nov 2025 article and the ~400-token `frontend_aesthetics` prompt that became the `frontend-design` skill. It is explicitly marketing/creative-oriented. Vercel's Web Interface Guidelines are craft rules rather than anti-slop rules. Community skills (Uncodixify, unslop-ui) carry the most concrete internal-UI rules but are single-maintainer projects. I could not verify an official OpenAI or Vercel v0 "anti-AI-look" guide.

### Cited Findings

**Anthropic, "Improving frontend design through Skills"** (Nov 12, 2025; Prithvi Rajasekaran, Justin Wei, Alexander Bricken) — [link](https://claude.com/resources/articles/improving-frontend-design-through-skills)
- Problem statement: unguided output converges on Inter/Roboto/Arial/Open Sans/Lato/system fonts, purple gradients on white, solid backgrounds, minimal animation and predictable layouts.
- Typography:
  - Never use Inter, Roboto, Open Sans, Lato or default system fonts.
  - Suggested fonts — code: JetBrains Mono, Fira Code, Space Grotesk; editorial: Playfair Display, Crimson Pro; technical: IBM Plex, Source Sans 3; distinctive: Bricolage Grotesque, Newsreader.
  - Pair for high contrast; use extreme weight contrast (100/200 vs. 800/900, not 400 vs. 600) and size jumps of 3x or more (not 1.5x).
  - Pick one distinctive font and use it decisively.
- Colour/theme: commit to one cohesive aesthetic, use CSS variables, take inspiration from IDE themes and cultural aesthetics; dominant colours with sharp accents.
- Motion: CSS-only for HTML, Motion library for React; one orchestrated page load with staggered `animation-delay` reveals rather than scattered micro-interactions.
- Backgrounds: build atmosphere with layered gradients, geometric patterns or contextual effects rather than solid colours.
- Avoid: overused fonts, clichéd palettes (especially purple gradients on white), predictable layouts, cookie-cutter components.
- Vary light/dark themes, fonts and aesthetics across generations; "think outside the box" to avoid a new default like Space Grotesk.
- The article reports the skill as roughly 400 tokens. Adoption of over 277K installs is reported by a third-party blog ([paddo.dev](https://paddo.dev/blog/claude-code-plugins-frontend-design/), not verified).
- Critique: the cross-generation variation instruction is unenforceable because sessions are isolated — [UX Collective](https://uxdesign.cc/ai-design-isnt-ugly-it-s-fluent-and-that-s-the-problem-131b2f4eb78c) (via search summary).
- One blog argues the skill alone is insufficient: skill plus an explicit design brief is what works (search summary of [wmedia.es](https://wmedia.es/en/tips/claude-code-frontend-design-skill)).

**Vercel, Web Interface Guidelines** — [vercel.com/design/guidelines](https://vercel.com/design/guidelines)
- Craft rules rather than an anti-slop manifesto. Grid/optical alignment, nested radii, layered shadows plus borders, and all states (empty/sparse/dense/error) are covered in Q4.
- Also: tabular numerals; colour never the only signal; APCA contrast; stronger contrast on hover/focus than at rest; visible focus rings; reduced motion.
- Copy: active voice, specific button labels, actionable errors, locale formatting, curly quotes and the ellipsis character.

**Uncodixify (community skill, cyxzdev)** — [SKILL.md](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md)
- Defines "Codex UI" as soft gradients, floating panels, eyebrow labels, decorative copy, hero sections in dashboards, oversized rounded corners, transform animations and dramatic shadows. ("Codex" here is a label for the generic AI look, not specifically OpenAI's product.)
- Gives explicit "Keep It Normal" token values (see Q4) and the core principle: "If a UI choice feels like a default AI move, ban it and choose the harder, cleaner option."
- Caveats:
  - Its file says blue-leaning colours are "NOPE," yet several of its own palettes are blue, an internal inconsistency.
  - Its install page shows a mixed security audit (Snyk fail) — [skills.sh listing](https://www.skills.sh/cyxzdev/uncodixfy/uncodixfy).

**unslop-ui (community playbook)** — [claudecodehq.com/playbooks/unslop-ui](https://claudecodehq.com/playbooks/unslop-ui)
- A prioritized tell list (see Q1), plus the principle "don't swap one default for another."
- Build-mode requirements: a reference, a deliberate colour, a reasoned typeface, and a layout tied to the page's purpose.
- Names a "dense and utilitarian (think trading terminal)" direction.
- Explicitly de-lists bento, dark mode and mesh backgrounds as tells.

**OpenAI / v0**
- A third-party guide claims the openai/skills catalog has a frontend skill favouring cardless layouts, restrained motion, at most two typefaces and one accent colour, and a "visual thesis" written before building. **Unverified**: I could not confirm it from OpenAI's repository (search summary only; [skillselion](https://skillselion.com/skills/am-will/codex-skills/frontend-design)).
- No official Vercel v0 anti-generic-design guidance was found in this pass.

### Inferences
- The two best-documented rule sets point in **opposite directions** because they target different contexts:
  - Anthropic says *more* character: distinctive fonts, atmospheric backgrounds, orchestrated motion. This suits marketing and creative pages.
  - Uncodixify says *less* decoration: system sans, 8–12px radius, no transforms, plain tables. This suits internal tools.
- For the phlebitis workbench, the Uncodixify/Vercel/Ström/Fountain rules are the applicable ones. From Anthropic, only "commit to one cohesive aesthetic via CSS variables" and "ban named defaults" carry over.
- The practical way to make any coding assistant comply is to write project tokens and explicit bans into the repo's agent instructions (CLAUDE.md/AGENTS.md). This consensus appears across [prg.sh](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website), [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui) and [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c) ("hand it to your AI tool as context and the defaults stop creeping back in," per search summary).

### Gaps
- Official OpenAI and Vercel v0 guidance on avoiding the AI aesthetic is unverified or not found.
- I found no Figma official guidance on this topic.
- I found no zh-TW / CJK-specific published guide on removing "AI 味" from interfaces. Search in Chinese returned mostly English sources.

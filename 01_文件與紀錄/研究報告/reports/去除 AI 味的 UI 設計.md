# 用明確決策取代預設值：靜脈炎工作台去 AI 味

網頁的「AI 味」不是某個顏色或字體造成的，它來自**沒有人做過決定的預設值**：模型取訓練資料裡最常見、最安全的選擇，Anthropic 稱之為「distributional convergence」（分布收斂）([Anthropic](https://claude.com/resources/articles/improving-frontend-design-through-skills))。最常被點名的跡象有幾類：Inter 字體、紫藍漸層、到處都是大圓角、發光與毛玻璃效果、頂部一排 KPI 卡片、英文大寫小標、每格都塞徽章、單側彩色邊框，以及用 emoji 當圖示。所以只換掉其中一項沒用，因為模型會換上下一個預設值；**真正有效的是把專案自己的 token、元件規格與禁用清單寫成文件，交給開發者與 AI 工具共同遵守**。醫院內部的靜脈炎影像研究工作台應走「少裝飾、重語意」的路線，Anthropic 那套追求獨特字體與氛圍背景的行銷頁建議不適用。具體做法如下：14px／22px 的微軟正黑體 UI 字級，字重只用 400／700；4px 間距格線；控制項高 32px；圓角 4–8px；一個藍色強調色，紅黃綠藍只用來表達狀態，而且一律搭配圖示與文字。可信度的重點不在外觀，在於**可預期性與誠實呈現模型的不確定性**：指標附 95% 信賴區間與樣本數，混淆矩陣旁附自然頻率說明，頁面常駐「僅供研究使用」，刪除操作的摩擦程度跟著影響範圍調整。目前這方面的證據多來自設計系統文件與實務者文章，**沒有任何對照研究量化過這些跡象出現的頻率**，中文介面的特有跡象則是本報告由英文資料推論而來。

## AI 味的根源是沒人負責的預設值，不是紫色本身

以下這組跡象在三個以上互不相關的來源中重複出現，可以視為共識：Inter 或其他預設無襯線字通篇使用、紫／靛藍色以及紫到藍的漸層、所有元素共用一個誇張的大圓角、暗色模式中的光暈與極光背景、emoji 當圖示，以及卡片單側的彩色邊條 ([Noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026); [Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui); [Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c); [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui))。內部儀表板另有一組專屬跡象，主要出自社群技能 Uncodixify，屬單一來源但描述最細：**內部介面裡放 hero 區塊**、把 KPI 卡片網格當成儀表板的預設版面、填版面用的假圖表、浮動的圓角側欄、塞滿裝飾文字的右側欄、`0 24px 60px` 這種戲劇化陰影、在每個狀態欄位都加徽章，以及解釋介面本身的小註解 ([Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md))。Fountain Institute 也指出「沒有意義的狀態圓點」，也就是顏色對應不到任何真實狀態的點 ([Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui))；Noqta 則把假的 Live／New 脈動徽章形容為「裝扮成資訊的裝飾」([Noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026))。

為什麼每個工具都產出一樣的東西？原因有三層。第一層是模型會取樣「放諸四海皆可、不得罪任何人」的高機率選擇 ([Anthropic](https://claude.com/resources/articles/improving-frontend-design-through-skills))。第二層是程式工具預設輸出 React + Tailwind + shadcn/ui 技術棧；Tailwind 作者 Adam Wathan 2025 年曾半開玩笑地為五年前把所有按鈕設成 `bg-indigo-500` 道歉 ([Wathan on X](https://x.com/adamwathan/status/1953510802159219096))。不過「靛藍來自 Tailwind 範例」這個因果說法來自評論者推論，沒有實際量測。第三層是**缺少設計簡報與參考**，這也是使用者唯一能控制的一層。所以換元件庫解決不了問題 ([managed-code.com](https://managed-code.com/blog-post/why-ai-websites-look-the-same))。這也說明了「第二代 AI 味」為什麼會出現：禁掉紫色後，模型改用米白底、襯線標題配鼠尾草綠，unslop-ui 把這組合列為頭號新跡象，並說這種替換「只是把時鐘重設」([unslop-ui](https://claudecodehq.com/playbooks/unslop-ui))。Anthropic 也觀察到，模型在被要求避開常見字體後，會集中改用 Space Grotesk ([Anthropic](https://claude.com/resources/articles/improving-frontend-design-through-skills))。結論很清楚：**限制必須寫成正面、專案專屬的規格（「用這組 token」），不能只寫負面清單（「不要紫色」）**。實務者普遍的做法，是把 token 與禁用清單放進 repo 的 CLAUDE.md／AGENTS.md，讓 AI 工具每次都讀到 ([prg.sh](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website); [unslop-ui](https://claudecodehq.com/playbooks/unslop-ui))。

套用到 zh-TW 介面時，有兩個轉換需要注意，兩者都是本報告的推論，沒有中文來源直接討論。Inter 沒有中文字形，中文字一定會落到後備字體，所以「通篇 Inter」在中文介面上不太明顯；真正的跡象是**沒有指定字體、導致後備字體混雜**。英文的大寫加字距小標（eyebrow）在中文裡也沒有直接對應，常見的變形是**中文標題上方加一個裝飾性英文小字**，例如在「總覽」上面寫「OVERVIEW」。文案方面，Wikipedia 的 AI 寫作指南列出了濫用破折號、「不只是 X，而是 Y」句型、三段式排比，以及 robust、seamless、pivotal 這類宣傳詞彙 ([Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing))；這些在中文裡大致對應到大量「——」與四字對仗口號，例如「智慧標註，精準洞察」。

| 常見 AI 跡象 | 工作台的替代做法 |
|---|---|
| 歡迎橫幅／hero、頂部 KPI 卡片列 | 頁面直接進入主表格；數字本身就是任務時才放摘要列 |
| 浮動圓角側欄、品牌區塊加 CTA | 固定實色側欄，右側 1px 邊線，純文字導覽 |
| 英文 eyebrow 小標＋口號標題＋說明段落 | 只用名詞標題（影像審查、訓練紀錄、垃圾桶），最多一行說明 |
| 每格狀態都加徽章、脈動圓點 | 不需動作就用純文字；需要掃視時用圖形＋文字；需要注意時才用徽章 |
| 統一的大圓角、膠囊按鈕 | 4／6／8px 三級圓角，內層圓角不大於外層 |
| 光暈、漸層、毛玻璃、彩色陰影 | 淺灰底加白色表面，用 1px 邊線區分層次 |
| emoji 圖示、閃亮「AI」徽章、數字跳動動畫 | 16–20px 單色線條圖示；數字直接顯示 |
| 卡片裡再套卡片 | 用留白與鄰近關係分組；只有能獨立操作的項目才用卡片 |

## 內部醫療工具應選「少裝飾」路線，Anthropic 的建議只能借兩條

公開指南中寫得最完整的有兩套，但方向相反。Anthropic 的 `frontend-design` 技能主張**加入性格**：禁用 Inter 與系統字、字重對比拉到 100／200 對 800／900、用多層漸層營造背景氛圍、用錯開時間的進場動畫編排頁面載入 ([Anthropic](https://claude.com/resources/articles/improving-frontend-design-through-skills))。Uncodixify 則主張**移除裝飾**：系統無襯線字、圓角 8–12px 以下、轉場只動透明度與顏色、表格維持樸素 ([Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md))。兩者其實不矛盾，只是適用情境不同：前者寫給行銷頁與創意作品，後者寫給內部工具。把 Anthropic 的建議整套搬進稽核紀錄或垃圾桶頁面，只會**增加**裝飾。這個工作台只該帶走其中兩條原則：用 CSS 變數貫徹單一、一致的美學；以及明確點名禁用的預設值。

醫療與政府設計系統的取向和「少裝飾」路線一致。NHS 把顏色當成承載意義的資源：文字與元件須符合 WCAG 2.2 AA，不能只靠顏色或位置傳達資訊，錯誤狀態要用語意變數而不是原始色票上的紅色。NHS 也用**淺灰背景降低眩光**，讓元件更突出 ([NHS Service Manual](https://service-manual.nhs.uk/design-system/styles/colour))。EHR 研究則顯示，介面越複雜、越不一致，ICU 醫師自評的表現就越差 ([PMC6584062](https://pmc.ncbi.nlm.nih.gov/articles/PMC6584062))。一篇涵蓋 23 項 CPOE 研究的系統性回顧發現，**警示的平均被略過率約 46%–96%** ([JMIR Med Inform 2020](https://medinform.jmir.org/2020/7/e15653))。換句話說，在醫療情境裡「可信」主要意味著**可預期**：每種頁面類型一個固定版面，顏色只表達語意，打斷使用者的介面只留給真正會阻擋工作或帶來風險的事件。

這和「刪減到空白」不同。Matthew Ström 認為，現代介面的資訊密度已比 2000 年代的軟體低，而密度應該用**單位時間與空間所傳遞的價值**來衡量，不是看畫面擠不擠；做法是移除非資料的墨水，同時保留有意義的留白 ([Ström, UI Density](https://mattstromawn.com/writing/ui-density))。Uncodixify 也把「過度留白」、為了看起來高級而刻意製造的「空白死區」列為 AI 跡象 ([Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md))。Fluent 2 則從另一邊提醒，過度密集同樣會讓人迷失 ([Fluent 2](https://fluent2.microsoft.design/layout))。所謂「適中」的密度，具體是指：主要視圖用表格，資料列高 32–40px，用漸進揭露取代把所有功能同時攤開 ([Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c))，並把延遲本身當成設計對象。

## 14px 正黑體、4px 格線與單一藍色構成 token 骨架

### 字體：Windows 上只有正黑體可靠，字重只能用 400 與 700

Windows 內建的繁體中文無襯線字只有微軟正黑體與微軟正黑體 UI，各有 Light、Regular、Bold **三個字重，沒有 500／600**，而且網頁嵌入需另外授權，只能當本機字體使用 ([Microsoft Learn](https://learn.microsoft.com/typography/font-list/microsoft-jhenghei))。W3C clreq 提醒，蘋方等選裝字體「不應假設已安裝」([W3C clreq 系統字體對照](https://w3c.github.io/clreq/others/system-font-mappings.html))；`system-ui` 在部分語系下會解析成雅黑 UI，字形是簡體 ([csswg-drafts #3658](https://lists.w3.org/Archives/Public/public-css-archive/2022Sep/0898.html))，所以應該明確寫出字體名稱。把 Segoe UI 放在字體堆疊最前面，數字與拉丁字母會用 Segoe 呈現，漢字則落到正黑體 UI。若對中文設定 500／600，漢字只會以 Regular 或合成粗體顯示，同一行出現粗細不一的情況；因此**含中文的文字一律只用 400 與 700**，600 只留給純數字或純英文的情境（推論）。強調用加粗，不用斜體，這也符合 clreq 對漢字強調的描述 ([W3C clreq](https://www.w3.org/TR/clreq/))。

字級方面，Carbon productive、Fluent 2 Body1 與 Ant Design 都以 **14px** 作為密集應用的基準。Ant 搭配 22px 行高（1.571），並建議整個系統只用 3–5 種字級 ([Ant Design](https://ant.design/docs/spec/font); [Carbon](https://carbondesignsystem.com/elements/typography/type-sets/); [Fluent 2](https://fluent2.microsoft.design/typography))。漢字填滿整個 em 方框，14px 的中文看起來比 14px 的英文更大、更密，所以中文內文取行高範圍的上限 22px；20px 行高只用在單行控制項與表格儲存格。須注意：clreq 中關於行高的數值規則落在注音／行間注的章節，並非針對網頁內文的標準。數字欄、時間戳與計數器加上 `font-variant-numeric: tabular-nums` 並靠右對齊 ([Ant Design](https://ant.design/docs/spec/font))。頁面設定 `lang="zh-Hant-TW"`，因為 clreq 建議依地區而不是依繁簡區分排版規則，而台灣的標點是置中於字框內的 ([W3C clreq](https://www.w3.org/TR/clreq/))。

| Token | 尺寸／行高 | 字重 | 用途 |
|---|---|---|---|
| `--text-xs` | 12 / 16 | 400 | 輔助說明、表格次要資訊、時間戳 |
| `--text-sm` | 14 / 20 | 400 / 700 | 表格儲存格、控制項、表頭 |
| `--text-md` | 14 / 22 | 400 / 700 | 內文、表單說明、對話框內文 |
| `--text-lg` | 16 / 24 | 700 | 區塊標題、對話框標題 |
| `--text-xl` | 20 / 28 | 700 | 頁面 H1 |
| `--text-2xl` | 24 / 32 | 700 | 僅限單一數值的重點顯示（如模型評估主指標） |

### 間距、尺寸與圓角：與 Carbon、Primer、Fluent 對齊

五套主要設計系統都以 4px 為基本單位 ([Carbon](https://carbondesignsystem.com/elements/spacing/overview/); [Fluent 2](https://fluent2.microsoft.design/layout); [Primer](https://primer.style/foundations/primitives/size); [Atlassian](https://atlassian.design/foundations/spacing))，預設控制項高度都收斂在 **32px** ([Ant Design](https://ant.design/docs/react/customize-theme); [Primer](https://primer.style/foundations/primitives/size))。圓角則集中在 2–4px（Carbon、Fluent）或 6px（Ant、Primer）。Fluent 的規則是「矩形預設 4px，32px 以下的形狀降到 2px」([Fluent 2 Shapes](https://fluent2.microsoft.design/shapes))。Uncodixify 明確禁用 20–32px 的圓角，甚至認為「到處都是 12px」也太多 ([Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md))。Vercel 要求巢狀圓角由外往內遞減，內層不大於外層 ([Vercel](https://vercel.com/design/guidelines))。以 14px／22px 的中文來說，32px 列高上下只剩約 5px 的內距，這就是實際下限；24px 列高對漢字太擠（推論）。

### 顏色：一個藍色，每個狀態拆成四階

所有參考系統的強調色都是藍色，紅黃綠藍則嚴格保留給狀態語意。最容易出錯的地方是：**許多系統預設的狀態色放在白底上，達不到 4.5:1**。白字配 Ant 的 #1677ff 只有 4.10:1，配 Carbon 的成功綠 #24a148 只有 3.35:1，配黃色 #f1c21b 只有 1.68:1。所以每個狀態都要拆出獨立的深色文字階與淺色底階 ([Carbon tokens](https://carbondesignsystem.com/elements/color/tokens/); [Atlassian](https://atlassian.design/foundations/color); [Primer](https://primer.style/foundations/color/overview))。下表的對比值是用 WCAG 2 公式計算的結果。其中 #198038、#0e6027 與各狀態的淺底色（#defbe6、#fff1f1、#fcf4d6、#edf5ff）取自 Carbon 10／60 色階的記憶值，本次研究沒有從官方頁面核實，導入前應再確認一次。

| 角色 token | 值 | 對比（計算值） | 用法 |
|---|---|---|---|
| `--bg-canvas` | #f4f4f4 | — | 頁面底色（NHS 淺灰降眩光的做法） |
| `--bg-surface` | #ffffff | — | 表格、面板、對話框 |
| `--fg-default` | #161616 | 白底 18.1、灰底 16.45 | 主要文字 |
| `--fg-muted` | #525252 | 白底 7.81 | 次要文字 |
| `--fg-subtle` | #6f6f6f | 白底 5.02、灰底 4.57 | 輔助說明（灰底上已接近下限） |
| `--border-control` | #8d8d8d | 白底 3.32、灰底 3.02 | 輸入框、核取方塊邊框（1.4.11 要求 3:1） |
| `--border-subtle` | #e0e0e0 | 白底 1.32 | 表格分隔線，僅裝飾用途 |
| `--accent` | #0f62fe | 白字 5.0、灰底 4.55 | 主要按鈕、連結、選取、焦點 |
| `--danger-fg` / `-bg` | #da1e28 / #fff1f1 | 白底 5.0、淺底 4.55 | 失敗、永久刪除 |
| `--success-fg` / `-bg` | #198038 / #defbe6 | 白底 5.02、淺底 4.55 | 成功（#24a148 只能當圖示用） |
| `--warning-fg` / `-bg` | #8e6a00 / #fcf4d6 | 白底 4.99、淺底 4.52 | 警告（黃色填色必須配深色字） |
| `--info-fg` / `-bg` | #0043ce / #edf5ff | 白底 7.79、淺底 7.09 | 執行中、研究用途聲明 |

暗色模式第一版先不做。NN/g 整理的研究顯示，淺色模式在視力與校對任務上的表現較好，字越小優勢越大，而且年輕與年長族群都是如此 ([NN/g](https://www.nngroup.com/articles/dark-mode/))；14px 的細筆畫中文放在深色底上，問題只會更嚴重（推論）。不過 token 一律依角色命名，例如 `--fg-muted`，不要用 `--gray-600` 這種依色值命名的方式。這樣日後只需加一個 `[data-theme="dark"]` 覆寫區塊，Atlassian 與 Carbon 都是這樣處理多主題的 ([Atlassian](https://atlassian.design/foundations/color); [Carbon](https://carbondesignsystem.com/elements/color/tokens/))。

```css
:root {
  /* 字體 */
  --font-sans: "Segoe UI", "Microsoft JhengHei UI", "Microsoft JhengHei",
               "PingFang TC", "Noto Sans TC", "Noto Sans CJK TC", sans-serif;
  --font-mono: Consolas, "Cascadia Mono", "Microsoft JhengHei UI", monospace;
  --weight-regular: 400;  --weight-bold: 700;   /* 含中文時禁用 500/600 */

  /* 間距（4px 格線） */
  --space-half: 2px; --space-1: 4px; --space-2: 8px; --space-3: 12px;
  --space-4: 16px;  --space-5: 24px; --space-6: 32px; --space-7: 48px;

  /* 尺寸 */
  --control-sm: 28px; --control-md: 32px; --control-lg: 40px;
  --row-h: 40px; --cell-px: 12px;
  --sidebar-w: 232px; --toolbar-h: 48px;
  --icon-sm: 16px; --icon-md: 20px;

  /* 圓角與線條 */
  --radius-sm: 4px;   /* 按鈕、輸入框、標籤 */
  --radius-md: 6px;   /* 面板、表格容器 */
  --radius-lg: 8px;   /* 對話框；上限，不使用膠囊形 */
  --border-w: 1px;
  --shadow-overlay: 0 2px 8px rgba(0,0,0,.10);  /* 只用在浮層 */

  /* 顏色：見上表，依角色命名 */
  --focus: var(--accent);

  /* 動態 */
  --dur-fast: 100ms; --dur-base: 160ms; --ease: cubic-bezier(.2,0,0,1);
}
[data-density="compact"] { --row-h: 32px; --control-md: 28px; --cell-px: 8px; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.num, td.num { font-variant-numeric: tabular-nums; text-align: right; }
@media (prefers-reduced-motion: reduce) { * { transition-duration: 0ms !important; } }
```

焦點環採用 2px 實線並向外偏移，因為 W3C 指出「2 CSS px 實心外框」是最簡單的達標方式，而 2px 的**內縮**邊框不符合 2.4.13 ([W3C 2.4.13](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html))。在強調色填色的按鈕上，比照 Carbon 加一圈白色內環 ([Carbon tokens](https://carbondesignsystem.com/elements/color/tokens/))。陰影只用在下拉選單、對話框這類浮層，上限是 Uncodixify 建議的 `0 2px 8px rgba(0,0,0,.1)` ([Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md))。轉場時間 100–200ms，只動透明度與顏色，不做位移 ([Uncodixify](https://raw.githubusercontent.com/cyxzdev/Uncodixfy/main/SKILL.md))，並遵守減少動態效果的系統設定 ([Vercel](https://vercel.com/design/guidelines))。

## 五個模組的元件規格：表格、框選、工作、垃圾桶各有其摩擦等級

### 版面與導覽

工作台有七個以上的區段，桌面版應使用**常駐、文字標示的左側欄**。NN/g 指出垂直導覽可以容納任意數量的項目，使用者 80% 的時間看著畫面左半部，而桌面版不應把導覽藏進漢堡選單 ([NN/g](https://www.nngroup.com/articles/vertical-nav/))。1440px 時側欄固定約 232px，實色底，右側 1px 邊線，不做浮動圓角外殼。項目依序為資料審查、標註、模型訓練、模型評估、工作監測、稽核紀錄、垃圾桶，目前所在頁加上 `aria-current` ([GOV.UK](https://design-system.service.gov.uk/components/service-navigation/))。頁首只放 H1、最多一行說明，主要動作放右側；麵包屑只在區段以下的層級出現，例如「模型評估 / 模型 v3.2 / 混淆矩陣」。到了 820px，側欄收合成附提示文字的圖示列，表格依 Fluent 的 show/hide 技巧隱藏低優先欄位，清單與詳細頁改成上下堆疊 ([Fluent 2](https://fluent2.microsoft.design/layout))。到了 390px，改用頂部選單按鈕；表格只保留二到三個關鍵欄位，水平捲動限制在表格內部，頁面本身不可橫向捲動；框選在這個寬度只供檢視（推論）。

### 資料表格與批次操作

Carbon 提供 24／32／40／48／64px 五種列高，表頭、工具列與分頁列都要和列高一致 ([Carbon 資料表](https://carbondesignsystem.com/components/data-table/usage/))。工作台預設 40px，含縮圖或狀態標籤的列也用 40px；稽核紀錄與工作清單切換成 32px 的緊湊模式。勾選任一列後，**批次操作列取代原本的工具列**，例如「已選取 12 項 · 移至垃圾桶 · 匯出 · 取消」，同時停用各列自己的動作 ([Carbon](https://carbondesignsystem.com/components/data-table/usage/))。表頭核取方塊要支援「部分選取」狀態。排序有三種狀態，只有已排序的欄位顯示圖示；分頁列放在底部，工具列上的動作最多五個，其餘收進溢位選單。列的懸停效果一律開啟，斑馬紋視需要使用。欄位標題用一到兩個詞，例如「上傳時間」「標註者」「分級」。

### 狀態呈現：四個注意力層級，總數不超過六種

Carbon 的狀態語意是：紅色代表錯誤，橘／黃代表警告，綠色代表成功，藍色代表資訊或流程進行中，灰色代表未開始；它強調「只靠顏色傳達狀態是不夠的」，並指出同時出現超過五到六種指示器就會造成負擔，不需要使用者採取動作時應改用純文字 ([Carbon 狀態指示](https://carbondesignsystem.com/patterns/status-indicator-pattern/))。工作台的狀態呈現分成四個層級：不需動作時用純文字；需要掃視大量列時用 8–10px 圖形加文字；需要注意時用圖示、文字加淺底色；只有阻擋整頁的錯誤才用實色橫幅。訓練完成這類背景事件用 toast 通知，不用模態對話框，因為 Carbon 規定對話框必須由使用者主動開啟 ([Carbon 對話框](https://carbondesignsystem.com/patterns/dialog-pattern/))。

| 工作狀態 | 圖形 | 顏色 token | 文字 |
|---|---|---|---|
| 排隊中 | 空心圓 | `--fg-muted` | 排隊中 |
| 執行中 | 半圓／靜態進度 | `--info-fg` | 執行中 · 第 12/50 輪 |
| 成功 | 勾號 | `--success-fg` | 成功 |
| 失敗 | 叉號 | `--danger-fg` | 失敗 · 查看紀錄 |
| 已取消 | 斜線 | `--fg-muted` | 已取消 |

進度回饋依 Ström 整理的延遲分級處理：100ms 以內不顯示任何東西，100ms–1s 給輕微提示，1–10s 顯示不定進度，10s–1 分鐘顯示確定進度，超過 1 分鐘讓使用者可以離開，完成時再通知 ([Ström](https://mattstromawn.com/writing/ui-density))。模型訓練屬於最後一級，所以適合背景執行加上完成通知，不該用占滿全畫面的轉圈動畫。

### 影像框選

疊在灰階醫學影像上的框線屬於 WCAG 1.4.11 所說的「圖形物件」，必須達到 3:1 對比 ([W3C 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html))。影像本身明暗交錯，任何單一顏色都無法在所有區域維持對比，所以框線用 **2px 主線加 1px 深色外暈**；類別靠標籤文字與實線／虛線區分，不只靠色相（推論）。這也符合 NHS 的提醒：色覺異常者常分不清紅、黃、綠 ([NHS](https://service-manual.nhs.uk/design-system/styles/colour))。框選工具列的圖示按鈕至少 24×24px，符合 WCAG 2.2 AA 的 2.5.8 ([W3C 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html))；390px 寬度時放大到 44px。

### 垃圾桶與刪除：摩擦程度跟著影響範圍走

Primer 的原則是**摩擦程度要對應影響範圍**：可逆的動作不要確認，改提供復原；不可逆的單筆刪除用一個指名對象的對話框；只有不可逆且影響範圍大的動作才要求輸入文字確認，這樣摩擦才能保有意義 ([Primer 刪除模式](https://primer.style/product/scenario-patterns/delete))。按鈕文字要寫出具體動作，不要寫「確定」，也不要問「你確定嗎？」；刪除失敗時對話框保持開啟並顯示錯誤，方便重試 ([Primer](https://primer.style/product/scenario-patterns/delete); [Carbon](https://carbondesignsystem.com/patterns/dialog-pattern/))。

| 動作 | 摩擦 | 介面文案範例 |
|---|---|---|
| 移至垃圾桶（單筆或批次） | 不確認，toast 加復原 | 已將 3 張影像移至垃圾桶　［復原］ |
| 從垃圾桶還原 | 不確認 | 已還原「IMG_0231」 |
| 永久刪除單筆 | 指名的危險對話框 | 永久刪除「IMG_0231」？此動作無法復原。［取消］［永久刪除影像］ |
| 清空垃圾桶或批次永久刪除 | 輸入數量或專案名稱，相符才啟用按鈕 | 請輸入「刪除 48 項」以繼續 |
| 保留期限 | 每列顯示 | 29 天後自動永久刪除 |

用詞也要一致：從清單或資料集拿掉，但項目仍存在時，用「移除」；進垃圾桶用「移至垃圾桶」；真正銷毀才用「永久刪除」。這對應 Primer 的 Remove／Delete 區分 ([Primer](https://primer.style/product/scenario-patterns/delete))。

## 模型評估頁是可信度的主戰場：信賴區間、自然頻率與研究用途聲明

對臨床使用者來說，最需要注意的 AI 味其實不在視覺上，而是**過度宣稱**。系統性回顧顯示，醫療人員普遍誤解敏感度、特異度與 PPV，而且常高估檢驗後機率，在盛行率低時更嚴重；改用**自然頻率**表達可以提升判讀正確率與速度 ([PMC4521525](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4521525/))。TRIPOD+AI 是取代 TRIPOD 2015 的 27 項報告清單；據次級來源描述，它要求同時報告校準與鑑別力，也就是說單看 AUROC 不夠，並且要附信賴區間 ([BMJ](https://www.bmj.com/node/1095803); [PMC12627258](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12627258/))。然而，TRIPOD+AI 發布後，骨科 AI 摘要的信賴區間報告率仍只有 **18.7%** ([PMC12627258](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12627258/))。這說明介面應該**預設就顯示**信賴區間，不能指望使用者自己想到。FDA 2026 年修訂的臨床決策支援指引明確提到自動化偏誤，並強調要讓臨床人員能獨立評估建議的依據 ([Cooley](https://www.cooley.com/news/insight/2026/2026-01-20-automation-bias-and-clinical-practice-fda-makes-incremental-updates-to-clinical-decision-support-software-guidance); [Faegre Drinker](https://faegredrinker.com/en/insights/publications/2026/1/key-updates-in-fdas-2026-general-wellness-and-clinical-decision-support-software-guidance))。本工作台雖然只用於研究，這個原則仍然適用於模型輸出的呈現方式。

具體規格如下。每個指標都寫成「敏感度 0.87（95% CI 0.81–0.92，n=312）」，並註明使用的閾值，以及數字來自內部驗證還是外部驗證。混淆矩陣旁附一句自然頻率說明，例如「每 100 張陽性影像，模型標出 87 張；每 100 張陰性影像，誤報 9 張（本測試集盛行率 18%）」。ROC 旁邊並列校準圖或 Brier 分數。混淆矩陣的熱圖用單一色相漸層並在格內印出數字，不靠紅綠對比 ([Carbon](https://carbondesignsystem.com/patterns/status-indicator-pattern/); [W3C 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html))。數字最多三位有效數字，用 tabular-nums，數字與單位之間留空格 ([Vercel](https://vercel.com/design/guidelines))，不做跳動計數動畫，不加閃亮圖示或「AI 驅動」徽章。每個模型詳細頁放一個仿照 Sendak 等人「Model Facts」標籤的面板，內容包括預期用途、訓練資料族群、驗證結果與已知限制／警示，目的是讓第一線人員在一頁內就知道何時該用、何時不該用模型輸出 ([Sendak et al., arXiv 1911.08089](https://arxiv.org/pdf/1911.08089))。頁首常駐一行「僅供研究使用，非診斷用途」，用 `--info` 中性樣式而不是紅色，免得它變成另一種被習慣性忽略的警示。

文案也照同樣的標準處理：頁面標題用名詞，例如影像審查、訓練紀錄、稽核紀錄、垃圾桶；按鈕用「動詞＋受詞」，例如「開始訓練」「匯出 CSV」「永久刪除影像」；錯誤訊息說明怎麼修正，而不是怪罪使用者 ([Vercel](https://vercel.com/design/guidelines))。AUROC、Dice、IoU 這類縮寫保留英文，滑鼠移上去時顯示中文定義。空狀態要寫出下一步，例如「垃圾桶是空的。刪除的影像會在此保留 30 天」或「沒有符合篩選條件的影像　［清除篩選］」，因為漏掉空狀態與鍵盤操作是 AI 產出介面最常見的缺口 ([Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c); [Vercel](https://vercel.com/design/guidelines))。

## 結論

這項研究讓問題的重心移動了：「去 AI 味」本質上不是美學問題，而是**歸屬問題**，也就是每個視覺決定是否有人負責。所以最有效的落實方式不是再調一輪樣式，而是把上述 token 表、四級狀態規則、刪除摩擦表與禁用清單（KPI 卡片列、英文 eyebrow、大於 8px 的圓角、漸層／光暈、emoji、每格徽章、含中文時的 500／600 字重）寫進專案的 CLAUDE.md 或 AGENTS.md，讓每一次 AI 輔助開發都從同一份簡報出發。以後再出現「看起來很像 AI 做的」頁面，只需要問一個問題：這個顏色、圓角或徽章，對應到規格中的哪一條？對應不到就刪掉。

對臨床研究工具來說，可信度最終取決於數字怎麼呈現，而不是畫面多精緻。一個視覺樸素、但每個指標都附信賴區間、樣本數與自然頻率說明的評估頁，比任何精心設計的儀表板更能抵抗自動化偏誤。仍有幾項不確定：中文介面特有的 AI 跡象、正黑體 UI 的行距特性與 `tnum` 支援、Carbon 中間灰階與淺色狀態底色的確切色值，都沒有在本次研究中驗證；建議在第一版完成後，以實際的醫院螢幕與色覺模擬工具做一輪檢查，用量測結果取代這些推論。

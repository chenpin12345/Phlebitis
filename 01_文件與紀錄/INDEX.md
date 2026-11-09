# 文件索引

第一次接手請從 [交接說明 HANDOVER](操作與交付說明/HANDOVER.md) 開始。

## 操作與交付說明

| 文件 | 內容 |
|---|---|
| [HANDOVER.md](操作與交付說明/HANDOVER.md) | **接手人員先讀**：現況、第一天清單、架構、名詞、安全規則、常見任務 |
| [WORKBENCH.md](操作與交付說明/WORKBENCH.md) | 工作台手冊：各頁功能、參數、匯入與備份、保存政策 |
| [DATA.md](操作與交付說明/DATA.md) | 資料管理：任務與標籤、岡山高醫檔名規則、每日補入照片 |
| [TRAINING.md](操作與交付說明/TRAINING.md) | 訓練與評估：快照、五種模型、指標判讀、外部模型匯入 |
| [LINE.md](操作與交付說明/LINE.md) | LINE 金鑰、HTTPS、圖文選單 |
| [RESEARCH_INTAKE.md](操作與交付說明/RESEARCH_INTAKE.md) | LINE 研究收件：同意、保存、撤回 |
| [DATA_REVIEW.md](操作與交付說明/DATA_REVIEW.md) | 2026-09 的資料核對待辦快照（最新狀態看工作台） |

其他資料夾的說明：[04_備份](../04_備份/README.md)、[05_匯入區](../05_匯入區/README.md)、[03_模型與影像資料](../03_模型與影像資料/README.md)、[02_主程式碼（開發說明）](../02_主程式碼/README.md)。

## 變更紀錄

[變更紀錄.md](變更紀錄.md)：依日期列出每次的主要變更。程式的逐筆修改看 git 紀錄（工作區根目錄執行 `git log`）。

## 驗證報告

結構說明見 [驗證報告/README.md](驗證報告/README.md)。

- [工作台驗收紀錄](驗證報告/WORKBENCH_ACCEPTANCE.md)、[效能驗收](驗證報告/PERFORMANCE_RESULTS.md)
- [補入紀錄（2026-10-13）](驗證報告/verification/2026-10-13_岡山高醫補入/gangshan-import-2026-10-13.md)
- [功能批次 1–5（2026-10-17）](驗證報告/verification/2026-10-17_功能批次1-5/batches-1-5-2026-10-17.md)
- [交接整理驗收（2026-10-17）](驗證報告/verification/2026-10-17_交接整理/驗收紀錄.md)、[資料搬移紀錄](驗證報告/verification/2026-10-17_交接整理/data-moves.json)
- 資料夾整理（2026-10-14）：[路徑改寫紀錄](驗證報告/verification/2026-10-14_資料夾整理/workspace-path-rewrite.json)

## 研究報告

- [去除 AI 味的 UI 設計](研究報告/reports/去除%20AI%20味的%20UI%20設計.md)（介面規則的依據；研究筆記在 `研究報告/research_notes/`）
- 原成果報告：`研究報告/成果報告NEW.docx`（可能含病人影像，不納入 git）

## 改版計畫與決策

- [計畫與決策](計畫與決策/README.md)：2026-11 改版的實作企劃、決策紀錄與里程碑報告。
- [研究決策](研究決策/README.md)：改版依據的深度研究報告；研究過程在 `研究筆記/`。
- 簡報：`簡報/靜脈炎影像研究工作台_簡報.pptx`。

## 歷史紀錄

舊需求、實作紀錄與階段性狀態，只供追溯，內容可能已過時：`歷史紀錄/`（[執行紀錄](歷史紀錄/IMPLEMENTATION.md)、[效能與匯入](歷史紀錄/PERFORMANCE_IMPORTS.md)、[垃圾桶實作](歷史紀錄/TRASH_IMPLEMENTATION.md)、[工作台七項改善](歷史紀錄/WORKBENCH_SEVEN_ITEMS.md) 等）。

## LINE 選單

圖文選單素材：`LINE選單/rich-menu.png`、`rich-menu.json`（由 `python -m src menu` 產生）。

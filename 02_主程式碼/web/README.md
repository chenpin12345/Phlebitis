# web：工作台介面

React 19＋TypeScript，Vite 建置。`src/` 是原始碼；`dist/` 是建置輸出（由 `python -m src workbench` 提供），不要直接修改。

```powershell
cd web
npm ci            # 第一次或 package-lock.json 變更後
npm run build     # 型別檢查＋建置；改完介面一定要跑
npx prettier --check "src/**/*.{ts,tsx}" "*.mjs"   # 排版（scripts\check.ps1 會做）
```

## 結構

| 位置 | 內容 |
|---|---|
| `src/main.tsx`、`src/app/App.tsx` | 進入點、hash 路由、側邊導覽、全域通知 |
| `src/features/overview/` | 總覽 |
| `src/features/data-review/` | 資料審查（分類、品質與重複旗標） |
| `src/features/data-trust/` | 資料可信度（來源檢查、資料盤點、醫師核准） |
| `src/features/imports/` | 匯入對話框（05_匯入區照片／模型包、岡山高醫外部來源） |
| `src/features/models/` | 模型與實驗（目錄、快照、建立實驗、工作監測、評估比較、模型版本、曲線） |
| `src/features/simulator/` | LINE 模擬器 |
| `src/features/intake/` | LINE 研究收件 |
| `src/features/maintenance/` | 設定與維護（環境檢查、每日備份、完整備份、磁碟用量、通知） |
| `src/features/trash/` | 垃圾桶 |
| `src/shared/` | API client（`ui.tsx`）、對話框、選取、提示、頁首搜尋與通知 |
| `src/style.css` | 設計 token 與全部樣式；開頭註解是介面規則 |

介面規則：只有一個強調色；狀態一定用「形狀＋文字」；中文字重只用 400／700；圓角 ≤ 8px；頁面標題用名詞。

## 瀏覽器回歸測試

`workbench-regression.mjs`、`trash-regression.mjs`、`cleanup-regression.mjs`、`features-regression.mjs`、`import-regression.mjs`、`query-lifecycle-regression.mjs`，以及效能量測 `performance-check.mjs`、`navigation-performance.mjs`、`startup-performance.mjs`：都只操作 8877 的合成 fixture；量測輸出位置由 `output-dir.mjs` 決定。



# LINE 研究收件

`Intake.tsx` 對應後端 `src/workbench/intake.py` 與 `src/workbench/routes/intake.py`。

- 清單採伺服器端分頁，可依來源、處理狀態、授權、標籤與日期篩選。
- 詳情可做人工確認、轉入資料審查、記錄撤回，或移入垃圾桶。
- 送出時有防止重複提交的保護；模型預測標示為僅供參考。

政策與流程說明見 `docs/RESEARCH_INTAKE.md`。原「案例與回歸」頁面已停用（回歸測試分頁亦已移除），`#cases` 會轉到「模型與實驗」。

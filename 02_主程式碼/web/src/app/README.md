# app：進入點與導覽

`App.tsx` 管理會話（CSRF）、hash 路由（`#overview`、`#data`、`#models`、`#simulator`、`#intake`、`#settings`、`#trash`）、側邊導覽與背景操作完成通知。舊網址 `#cases`（已停用的「案例與回歸」）會轉到 `#models`。`main.tsx` 只負責啟動 React。

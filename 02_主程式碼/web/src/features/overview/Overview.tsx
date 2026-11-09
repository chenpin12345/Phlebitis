type Obj = Record<string, any>;
import {Badge, Empty, Heading} from '../../shared/app-ui';
import {useData} from '../../shared/ui';
const AREA_ROWS = [['cls', '照片分類', '岡山高醫照片依檔名自動分類']];

/** Things that need a person (D2). Shown only when there is something to do. */
function NextSteps() {
  const state = useData('/next-steps', 15000);
  const items: Obj[] = state.data?.items || [];
  return (
    <section className="panel next-steps" aria-label="下一步">
      <h2>下一步</h2>
      {state.error && !state.data ? (
        <p role="alert">{state.error}</p>
      ) : !state.data ? (
        <p className="muted">整理待辦…</p>
      ) : !items.length ? (
        <p className="muted">目前沒有待辦。</p>
      ) : (
        <ul>
          {items.map(i => (
            <li key={i.key} className={i.level === 'error' ? 'urgent' : ''}>
              <span className="mark" aria-hidden="true" />
              <span className="text">{i.text}</span>
              <a className="button secondary" href={i.href}>
                {i.action}
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Finished photos by label. Counts only completed rows, so the row adds up to 已完成. */
function Content({a}: {a: Obj}) {
  const l = a.confirmed_labels || {};
  return (
    <>
      正常 {l.normal || 0}・第一期 {l.stage1 || 0}・第二期 {l.stage2 || 0}
      {l.positive_unstaged ? <>・陽性未分期 {l.positive_unstaged}</> : null}
    </>
  );
}

export function Overview({data, error}: any) {
  return (
    <>
      <Heading title="總覽">資料、模型與工作的目前狀態。</Heading>
      {error && <div className="notice error">{error}</div>}
      <NextSteps />
      {!data ? (
        <Empty>載入中…</Empty>
      ) : (
        <>
          <section className="panel">
            <div className="panel-head">
              <h2>資料進度</h2>
              <a href="#data">前往資料審查</a>
            </div>
            {data.areas ? (
              <div className="table-wrap area-overview">
                <table>
                  <thead>
                    <tr>
                      <th>工作區</th>
                      <th className="num">已完成</th>
                      <th className="num">待處理</th>
                      <th className="num">排除</th>
                      <th>進度</th>
                      <th>已完成內容</th>
                    </tr>
                  </thead>
                  <tbody>
                    {AREA_ROWS.map(([k, t, s]) => {
                      const a = data.areas[k];
                      const usable = a.progress.total - a.progress.excluded;
                      const ratio = a.progress.ratio ? Math.round(a.progress.ratio * 100) : 0;
                      return (
                        <tr key={k}>
                          <td>
                            <a className="area-card" href={'#data?area=' + k}>
                              {t}
                            </a>
                            <small>{s}</small>
                          </td>
                          <td className="num">{a.progress.confirmed}</td>
                          <td className="num">{a.counts.pending}</td>
                          <td className="num">{a.progress.excluded}</td>
                          <td>
                            <div className="meter" role="img" aria-label={`已完成 ${ratio}%`}>
                              <span style={{width: ratio + '%'}} />
                            </div>
                            <small>
                              {a.progress.confirmed} / {usable}（{ratio}%）
                            </small>
                          </td>
                          <td>
                            <Content a={a} />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty>資料索引建立中。</Empty>
            )}
          </section>
          <div className="two-col">
            <section className="panel">
              <h2>可用於訓練</h2>
              <table className="kv">
                <tbody>
                  <tr>
                    <th>二分類</th>
                    <td className="num">{data.task_counts?.binary_classification ?? 0}</td>
                    <td>
                      陽性 {data.approved_labels.positive || 0}・正常 {data.approved_labels.negative || 0}
                    </td>
                  </tr>
                  <tr>
                    <th>分期</th>
                    <td className="num">{data.task_counts?.stage_classification ?? 0}</td>
                    <td>
                      正常 {data.stage_labels?.normal || 0}・第一期 {data.stage_labels?.stage1 || 0}・第二期{' '}
                      {data.stage_labels?.stage2 || 0}
                    </td>
                  </tr>
                </tbody>
              </table>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>最近工作</h2>
                <a href="#models?tab=jobs">全部工作</a>
              </div>
              {data.jobs.length ? (
                <table>
                  <tbody>
                    {data.jobs.slice(0, 6).map((j: Obj) => (
                      <tr key={j.id}>
                        <td>
                          {j.config.name || j.config.model || j.kind}
                          <small className="mono">{j.id.slice(0, 8)}</small>
                        </td>
                        <td>
                          <Badge value={j.state} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <Empty>尚無工作。先建立資料快照，再開始第一個實驗。</Empty>
              )}
              <p className="muted">已登錄 {data.artifacts} 個模型版本；新模型不會自動用於 LINE。</p>
            </section>
          </div>
        </>
      )}
    </>
  );
}

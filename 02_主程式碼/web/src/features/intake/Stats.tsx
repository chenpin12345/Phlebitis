import {useState} from 'react';
import {useData, Empty, names} from '../../shared/ui';
type Obj = Record<string, any>;
const pct = (v: number | null | undefined) => (v == null ? '—' : (v * 100).toFixed(1) + '%');
const STATUS: Obj = {
  suspected: '疑似陽性',
  not_detected: '未達門檻',
  needs_review: '需人工確認',
  quality_rejected: '品質不足',
};

/** C3: LINE usage over 7 days, 30 days or everything. */
export function UsageStats() {
  const [period, setPeriod] = useState('30'),
    [source, setSource] = useState('line');
  const state = useData('/intake/stats?period=' + period + '&source=' + source, 30000);
  const d = state.data;
  const max = Math.max(1, ...(d?.series || []).map((x: Obj) => x.analyses));
  return (
    <section className="panel usage-stats">
      <div className="panel-head">
        <h2>使用統計</h2>
        <div className="toolbar">
          <div className="segmented" role="radiogroup" aria-label="期間">
            {[
              ['7', '7 天'],
              ['30', '30 天'],
              ['all', '全部'],
            ].map(([k, v]) => (
              <button
                key={k}
                role="radio"
                aria-checked={period === k}
                className={period === k ? 'active' : ''}
                onClick={() => setPeriod(k)}
              >
                {v}
              </button>
            ))}
          </div>
          <select aria-label="資料來源" value={source} onChange={e => setSource(e.target.value)}>
            <option value="line">LINE</option>
            <option value="simulator">模擬器（測試）</option>
            <option value="">LINE 與模擬器</option>
          </select>
        </div>
      </div>
      {state.error ? (
        <p role="alert">{state.error}</p>
      ) : !d ? (
        <Empty>統計中…</Empty>
      ) : (
        <>
          <div className="stats">
            <div className="stat">
              <small>完成分析</small>
              <strong>{d.analyses}</strong>
            </div>
            <div className="stat">
              <small>研究收件數</small>
              <strong>{d.received}</strong>
            </div>
            <div className="stat">
              <small>同意率</small>
              <strong>{pct(d.consent_rate)}</strong>
              <small>
                同意 {d.accepted}・不同意 {d.declined}
              </small>
            </div>
            <div className="stat">
              <small>品質不足比例</small>
              <strong>{pct(d.quality_rejected_rate)}</strong>
              <small>{d.quality_rejected} 張</small>
            </div>
          </div>
          <div className="two-col">
            <div>
              <h3>預測分布</h3>
              {!d.analyses ? (
                <Empty>這段期間沒有完成的分析。</Empty>
              ) : (
                <table className="usage">
                  <tbody>
                    {Object.entries(d.status).map(([k, v]: any) => (
                      <tr key={k}>
                        <th>{STATUS[k] || k}</th>
                        <td>
                          <div className="meter" role="img" aria-label={(STATUS[k] || k) + ' ' + v}>
                            <span style={{width: Math.round((v / d.analyses) * 100) + '%'}} />
                          </div>
                        </td>
                        <td className="num">
                          {v}（{pct(v / d.analyses)}）
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {Object.keys(d.classes || {}).length > 0 && (
                <>
                  <h4>分期模型的判斷</h4>
                  <table className="usage">
                    <tbody>
                      {Object.entries(d.classes).map(([k, v]: any) => (
                        <tr key={k}>
                          <th>{names[k] || k}</th>
                          <td />
                          <td className="num">{v}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>
            <div>
              <h3>研究同意與撤回</h3>
              <table className="kv">
                <tbody>
                  <tr>
                    <th>詢問同意</th>
                    <td className="num">{d.consent_offered}</td>
                    <td>完成分析後提供研究同意選項的次數</td>
                  </tr>
                  <tr>
                    <th>撤回</th>
                    <td className="num">{d.withdrawals}</td>
                    <td>這段期間撤回研究同意的次數</td>
                  </tr>
                  {Object.entries(d.intake_states || {}).map(([k, v]: any) => (
                    <tr key={k}>
                      <th>{names[k] || k}</th>
                      <td className="num">{v}</td>
                      <td>研究收件處理狀態</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <h3>每日分析數（{d.series_days} 天）</h3>
          <div className="daily-bars" role="img" aria-label={'每日分析數，共 ' + d.analyses + ' 張'}>
            {d.series.map((x: Obj, i: number) => (
              <span
                key={i}
                title={new Date(x.start * 1000 + 86400000).toLocaleDateString('zh-TW') + '：' + x.analyses}
                style={{height: Math.max(2, (x.analyses / max) * 100) + '%'}}
                className={x.analyses ? '' : 'zero'}
              />
            ))}
          </div>
          <p className="muted">
            {d.note}
            {source === 'simulator' ? ' 模擬器同意不等於真人研究授權。' : ''}
          </p>
        </>
      )}
    </section>
  );
}

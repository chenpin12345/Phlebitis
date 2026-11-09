import {useEffect, useState} from 'react';
import {api, useData, when, Empty, names} from '../../shared/ui';
type Obj = Record<string, any>;
const pct = (v: number | null | undefined) => (v == null ? '—' : (v * 100).toFixed(1) + '%');

/** LINE actions on a model card: use for LINE (needs a complete evaluation) and shadow mode (C2). */
export function LineActions({artifact, ready, act}: {artifact: Obj; ready: boolean; act: any}) {
  const shadow = useData('/shadow');
  const isShadow = shadow.data?.shadow?.artifact === artifact.id;
  return (
    <>
      <button
        type="button"
        className="secondary"
        disabled={!ready}
        onClick={() =>
          act(
            () => api('/artifacts/activate', 'POST', {artifact: artifact.id, target: 'line'}),
            'LINE 模型引用已更新（LINE 重新啟動後使用）'
          )
        }
      >
        用於 LINE
      </button>
      <button
        type="button"
        className="secondary"
        onClick={() =>
          act(
            () =>
              api('/shadow', 'POST', {artifact: isShadow ? null : artifact.id}).then(r => {
                shadow.refresh();
                return r;
              }),
            isShadow
              ? '已停止影子模式（LINE 下次啟動時生效）'
              : '已設為 LINE 影子模型（LINE 重新啟動後開始比較，不會回覆病患）'
          )
        }
      >
        {isShadow ? '停止影子模式' : '設為影子模型'}
      </button>
    </>
  );
}

/** C2: which model runs in shadow, and how often it agrees with the LINE model. */
export function ShadowPanel() {
  const [period, setPeriod] = useState('30'),
    [source, setSource] = useState('');
  const state = useData('/shadow?period=' + period + '&source=' + source, 30000);
  const d = state.data;
  if (!d || (!d.shadow && !d.total)) return null;
  const status = (v: string) =>
    (({suspected: '疑似', not_detected: '未達門檻', quality_rejected: '品質不足', needs_review: '需人工確認'}) as Obj)[
      v
    ] ||
    v ||
    '—';
  return (
    <section className="panel shadow-panel">
      <div className="panel-head">
        <h2>影子模式</h2>
        <div className="toolbar">
          <select aria-label="影子比較期間" value={period} onChange={e => setPeriod(e.target.value)}>
            <option value="7">近 7 天</option>
            <option value="30">近 30 天</option>
            <option value="all">全部</option>
          </select>
          <select aria-label="影子比較來源" value={source} onChange={e => setSource(e.target.value)}>
            <option value="">LINE 與模擬器</option>
            <option value="line">只看 LINE</option>
            <option value="simulator">只看模擬器</option>
          </select>
        </div>
      </div>
      <p>
        {d.shadow ? (
          <>
            影子模型：<span className="mono break">{d.shadow.artifact}</span>（{when(d.shadow.since)}{' '}
            起）。影子模型在回覆送出後才分析同一張照片，只記錄比較結果，不會回覆病患。LINE
            需重新啟動才會載入或卸除影子模型。
          </>
        ) : (
          '目前沒有影子模型；以下為先前的比較紀錄。'
        )}
      </p>
      {!d.total ? (
        <Empty>尚無比較紀錄。可在「LINE 模擬」傳送照片測試。</Empty>
      ) : (
        <>
          <div className="stats compact">
            <div className="stat">
              <small>比較張數</small>
              <strong>{d.compared}</strong>
            </div>
            <div className="stat">
              <small>判斷一致</small>
              <strong>{pct(d.agreement)}</strong>
            </div>
            <div className="stat">
              <small>不一致</small>
              <strong>{d.compared - d.agreed}</strong>
            </div>
            <div className="stat">
              <small>影子失敗</small>
              <strong>{d.failed}</strong>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>LINE 模型</th>
                  <th>影子模型</th>
                  <th className="num">張數</th>
                </tr>
              </thead>
              <tbody>
                {d.pairs.map((p: Obj, i: number) => (
                  <tr key={i}>
                    <td>{status(p.main_status)}</td>
                    <td>{status(p.shadow_status)}</td>
                    <td className="num">{p.n}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {d.disagreements.length > 0 && (
            <details>
              <summary>最近不一致的分析（{d.disagreements.length}）</summary>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>時間</th>
                      <th>來源</th>
                      <th>LINE 模型</th>
                      <th>影子模型</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.disagreements.map((r: Obj, i: number) => (
                      <tr key={i}>
                        <td>{when(r.at)}</td>
                        <td>{r.source === 'line' ? 'LINE' : '模擬器'}</td>
                        <td>
                          {status(r.main_status)}
                          {r.main_class ? ' · ' + (names[r.main_class] || r.main_class) : ''}
                        </td>
                        <td>
                          {r.shadow_error
                            ? '失敗：' + r.shadow_error
                            : status(r.shadow_status) +
                              (r.shadow_class ? ' · ' + (names[r.shadow_class] || r.shadow_class) : '')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </>
      )}
    </section>
  );
}

/** Scroll to the model card named in ?artifact= (links from search). */
export function ScrollToArtifact({id, ready}: {id: string; ready: boolean}) {
  useEffect(() => {
    if (id && ready) {
      const t = setTimeout(() => document.getElementById('artifact-' + id)?.scrollIntoView({block: 'start'}), 100);
      return () => clearTimeout(t);
    }
  }, [id, ready]);
  return null;
}

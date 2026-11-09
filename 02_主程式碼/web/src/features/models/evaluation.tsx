import React, {useState} from 'react';
import {useData, useHash, route, names, when, Empty} from '../../shared/ui';
import {Dialog} from '../../shared/dialog';
type Obj = Record<string, any>;
export const pct = (v: number | null | undefined) => (v == null ? '—' : (v * 100).toFixed(1) + '%');
const ci = (c: number[] | null | undefined) =>
  c ? `${(c[0] * 100).toFixed(0)}–${(c[1] * 100).toFixed(0)}%` : '樣本不足';

/** B2: ① summary — key metrics with 95% intervals and plain sentences. */
export function SummaryPanel({summary, title = '摘要'}: {summary: Obj | null | undefined; title?: string}) {
  if (!summary) return <Empty>計算摘要…</Empty>;
  return (
    <section className="report-section summary-panel">
      <h4>① {title}</h4>
      {summary.lines?.length > 0 && (
        <ul className="plain-lines">
          {summary.lines.map((l: string) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      )}
      <div className="table-wrap">
        <table className="ci-table">
          <thead>
            <tr>
              <th>指標</th>
              <th className="num">數值</th>
              <th>95% 信賴區間</th>
              <th className="num">張數</th>
            </tr>
          </thead>
          <tbody>
            {summary.metrics.map((m: Obj) => (
              <tr key={m.key}>
                <th>{m.name}</th>
                <td className="num">{pct(m.value)}</td>
                <td>
                  <CiBar value={m.value} ci={m.ci} />
                </td>
                <td className="num">{m.count || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {summary.cautions?.map((c: string) => (
        <p className="callout" key={c}>
          {c}
        </p>
      ))}
      <small>{summary.method}</small>
    </section>
  );
}
function CiBar({value, ci: c}: {value: number | null; ci: number[] | null}) {
  if (value == null) return <span className="muted">不適用</span>;
  return (
    <span className="ci-bar" role="img" aria-label={'信賴區間 ' + ci(c)}>
      <span className="track">
        {c && (
          <span className="range" style={{left: c[0] * 100 + '%', width: Math.max(0.5, (c[1] - c[0]) * 100) + '%'}} />
        )}
        <span className="point" style={{left: value * 100 + '%'}} />
      </span>
      <span>{ci(c)}</span>
    </span>
  );
}

/** B2: ② confusion matrix (binary or multiclass). */
export function Matrix({matrix}: {matrix: Obj | undefined}) {
  if (!matrix) return null;
  if (matrix.kind === 'binary')
    return (
      <section className="report-section">
        <h4>② 混淆矩陣（列：人工標籤，欄：模型判斷）</h4>
        <div className="table-wrap">
          <table className="confusion">
            <thead>
              <tr>
                <th></th>
                <th>判為陽性</th>
                <th>判為正常</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th>實際陽性</th>
                <td className="diag">{matrix.tp}</td>
                <td>{matrix.fn}</td>
              </tr>
              <tr>
                <th>實際正常</th>
                <td>{matrix.fp}</td>
                <td className="diag">{matrix.tn}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    );
  return (
    <section className="report-section">
      <h4>② 混淆矩陣（列：人工標籤，欄：模型判斷）</h4>
      <div className="table-wrap">
        <table className="confusion">
          <thead>
            <tr>
              <th></th>
              {matrix.classes.map((c: string) => (
                <th key={c}>判為{names[c] || c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.confusion_matrix.map((row: number[], i: number) => (
              <tr key={i}>
                <th>實際{names[matrix.classes[i]] || matrix.classes[i]}</th>
                {row.map((v, j) => (
                  <td key={j} className={i === j ? 'diag' : ''}>
                    {v}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/** B3 + B4: ③ error gallery that links back to data review; ④ optional heat maps (EfficientNet). */
export function ErrorGallery({path, heatmaps}: {path: string; heatmaps: boolean}) {
  const state = useData(path);
  const [heat, setHeat] = useState(false),
    [zoom, setZoom] = useState<Obj | null>(null);
  const d = state.data;
  const src = (i: Obj) => '/api/v1/reports/' + i.report + '/' + (heat ? 'heatmaps' : 'images') + '/' + i.image_id;
  return (
    <section className="report-section">
      <div className="panel-head">
        <h4>③ 錯誤分析圖庫{d ? `（${d.total}）` : ''}</h4>
        {heatmaps && (
          <label className="check inline">
            <input type="checkbox" checked={heat} onChange={e => setHeat(e.target.checked)} />④ 顯示熱區圖
          </label>
        )}
      </div>
      {heatmaps && heat && (
        <ol className="muted">
          <li>熱區有沒有落在手臂皮膚上。</li>
          <li>有沒有落在膠帶、針具、床單或背景。</li>
          <li>落在背景的照片，判斷結果不要當成看懂病灶。</li>
        </ol>
      )}
      {heatmaps && heat && (
        <p className="callout info">
          熱區圖顯示模型做出這次判斷時較依賴的區域（EfficientNet 用 Grad-CAM，DINOv2
          用注意力圖），不是病灶位置，只供研究端檢查。第一次開啟每張圖需要幾秒計算。
        </p>
      )}
      {!heatmaps && <p className="muted">④ 熱區圖：{'基線沒有熱區圖'}</p>}
      {state.error ? (
        <p role="alert">{state.error}</p>
      ) : !d ? (
        <Empty>整理錯誤案例…</Empty>
      ) : !d.total ? (
        <Empty>沒有判斷錯誤的照片。</Empty>
      ) : (
        d.groups.map((g: Obj) => (
          <div key={g.key}>
            <h5>
              {g.title}（{g.items.length}）
            </h5>
            <div className="error-grid">
              {g.items.map((i: Obj) => (
                <figure key={i.report + i.image_id}>
                  {i.error ? (
                    <div className="report-image empty">{i.error}</div>
                  ) : (
                    <button
                      type="button"
                      className="image-button"
                      aria-label={'放大 ' + i.image_id}
                      onClick={() => setZoom(i)}
                    >
                      <img loading="lazy" src={src(i)} alt={g.title + ' ' + i.image_id} />
                    </button>
                  )}
                  <figcaption>
                    <span className="break">{i.image_id}</span>
                    {i.fold != null && (
                      <small>
                        fold {i.fold}
                        {i.score != null ? ` · 分數 ${Number(i.score).toFixed(2)}` : ''}
                      </small>
                    )}
                    {i.review_href ? <a href={i.review_href}>在資料審查開啟 →</a> : <small>此照片已不在資料清單</small>}
                  </figcaption>
                </figure>
              ))}
            </div>
          </div>
        ))
      )}
      {zoom && (
        <Dialog title={'評估圖片 ' + zoom.image_id} onClose={() => setZoom(null)}>
          <img className="report-image" src={src(zoom)} alt={zoom.image_id} />
          {zoom.review_href && (
            <a className="button secondary" href={zoom.review_href} onClick={() => setZoom(null)}>
              在資料審查開啟 →
            </a>
          )}
        </Dialog>
      )}
    </section>
  );
}

/** B1: three-fold aggregates. */
/** #24: shown only; nothing is recalibrated. */
function Calibration({value}: {value: Obj | null | undefined}) {
  if (!value?.bins?.length) return null;
  const x = (v: number) => 24 + v * 176,
    y = (v: number) => 184 - v * 176;
  return (
    <section className="report-section">
      <h4>校準（Brier {value.brier.toFixed(3)}，越小越好）</h4>
      <p className="muted">點越靠近對角線，分數越接近實際比例。這裡只呈現，不做再校準；分數不是疾病機率。</p>
      <svg viewBox="0 0 208 208" width="208" height="208" role="img" aria-label="可靠度圖">
        <rect x="24" y="8" width="176" height="176" fill="none" stroke="var(--border-subtle)" />
        <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="var(--border-control)" strokeDasharray="4 4" />
        {value.bins.map((b: Obj) => (
          <circle
            key={b.low}
            cx={x(b.score)}
            cy={y(b.observed)}
            r={Math.min(9, 3 + Math.sqrt(b.n))}
            fill="var(--accent)"
          >
            <title>{`分數 ${b.score.toFixed(2)}，實際 ${b.observed.toFixed(2)}，${b.n} 次預測`}</title>
          </circle>
        ))}
        <text x="112" y="202" textAnchor="middle" fontSize="11" fill="currentColor">
          模型分數
        </text>
        <text x="10" y="96" textAnchor="middle" fontSize="11" fill="currentColor" transform="rotate(-90 10 96)">
          實際比例
        </text>
      </svg>
    </section>
  );
}

export function GroupList({model}: {model: string}) {
  const {params} = useHash();
  const state = useData('/report-groups?model=' + encodeURIComponent(model), 5000);
  const items: Obj[] = state.data?.items || [];
  const selected = params.get('group') || items[0]?.cv_group || '';
  const set = (v: Obj) => route('models', {...Object.fromEntries(params), tab: 'compare', mode: 'groups', ...v});
  if (state.error) return <Empty>{state.error}</Empty>;
  if (!state.data) return <Empty>載入交叉驗證彙總…</Empty>;
  if (!items.length)
    return <Empty>還沒有交叉驗證的結果。在「建立實驗」勾選「全部折都執行」，完成後會出現在這裡。</Empty>;
  const current = items.find(g => g.cv_group === selected) || items[0];
  return (
    <>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>實驗／模型</th>
              <th>病人／照片</th>
              <th>敏感度（95% 區間）</th>
              <th>正常誤報率（95% 區間）</th>
              <th>平衡準確率／Macro F1</th>
              <th>完成折數</th>
            </tr>
          </thead>
          <tbody>
            {items.map(g => {
              const metric = (key: string) => g.pooled.metrics.find((m: Obj) => m.key === key);
              const sens = metric('sensitivity'),
                fpr = metric('false_positive_rate');
              return (
                <tr key={g.cv_group} className={g.cv_group === current.cv_group ? 'selected-row' : ''}>
                  <td>
                    <button className="plain" onClick={() => set({group: g.cv_group})}>
                      {g.name || g.model}
                    </button>
                    <small>
                      {g.baseline ? '基線 · ' : ''}
                      {names[g.task] || g.task} · {g.model}
                    </small>
                    {g.removed_photos > 0 && <small className="chip no">待驗證</small>}
                  </td>
                  <td>
                    {g.pooled.patients ?? '—'} 位／{g.pooled.photos} 張
                  </td>
                  <td>
                    {pct(sens?.value)}
                    <small>{ci(sens?.ci)}</small>
                  </td>
                  <td>
                    {pct(fpr?.value)}
                    <small>{ci(fpr?.ci)}</small>
                  </td>
                  <td>
                    {g.key_metric === 'macro_f1' ? 'Macro F1' : '平衡準確率'} {pct(g.mean)}
                    {g.sd != null ? ` ± ${(g.sd * 100).toFixed(1)}` : ''}
                  </td>
                  <td>
                    {g.fold_count}／{g.expected_folds ?? '?'}
                    {!g.complete && <small>尚未全部完成</small>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <GroupDetail key={current.cv_group} group={current} />
    </>
  );
}
function GroupDetail({group}: {group: Obj}) {
  return (
    <section className="report-detail">
      <h3>{group.name || group.model} · 交叉驗證彙總</h3>
      <p>
        {names[group.task] || group.task}・快照 {group.snapshot}・{group.fold_count} 折合併 {group.pooled.photos} 張照片
        {group.repeats > 1 ? `，重複切分 ${group.repeats} 次，共 ${group.pooled.n} 次預測` : ''}。
        {group.ledger && ` 這個快照已試 ${group.ledger.settings} 種設定。`}
      </p>
      <SummaryPanel summary={group.pooled} title="摘要（合併各折）" />
      <Matrix matrix={group.pooled.matrix} />
      <Calibration value={group.pooled.calibration} />
      <section className="report-section">
        <h4>各折結果</h4>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>fold</th>
                <th>準確率</th>
                <th>{group.key_metric === 'macro_f1' ? 'Macro F1' : '平衡準確率'}</th>
                <th>報告</th>
              </tr>
            </thead>
            <tbody>
              {group.folds.map((f: Obj) => (
                <tr key={f.fold}>
                  <td>{f.fold}</td>
                  <td>{f.accuracy_display}</td>
                  <td>{pct(f.value)}</td>
                  <td>
                    <a href={'#models?tab=compare&report=' + f.report_id}>開啟單折報告</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <ErrorGallery path={'/report-groups/' + group.cv_group + '/errors'} heatmaps={!group.baseline} />
    </section>
  );
}

/** B7: what changed between two snapshots. */
export function SnapshotDiff({a, b, onClose}: {a: string; b: string; onClose: () => void}) {
  const state = useData('/snapshots/' + encodeURIComponent(a) + '/diff/' + encodeURIComponent(b));
  const d = state.data;
  const label = (v: string) => names[v] || v || '—';
  return (
    <Dialog title="快照差異" onClose={onClose}>
      {state.error ? (
        <p role="alert">{state.error}</p>
      ) : !d ? (
        <Empty>比較中…</Empty>
      ) : (
        <>
          <p>
            {d.a.name || d.a.version}（{d.a.count} 張）→ {d.b.name || d.b.version}（{d.b.count} 張）
            {!d.same_task && <b>・兩個快照的任務不同，標籤意義不同</b>}
          </p>
          <div className="stats compact">
            <div className="stat">
              <small>新增</small>
              <strong>{d.added.length}</strong>
            </div>
            <div className="stat">
              <small>移除</small>
              <strong>{d.removed.length}</strong>
            </div>
            <div className="stat">
              <small>標籤改變</small>
              <strong>{d.changed.length}</strong>
            </div>
            <div className="stat">
              <small>相同</small>
              <strong>{d.unchanged}</strong>
            </div>
          </div>
          {[
            ['added', '新增的照片'],
            ['removed', '移除的照片'],
            ['changed', '標籤改變的照片'],
          ].map(
            ([k, t]) =>
              d[k].length > 0 && (
                <details key={k} open={d[k].length <= 20}>
                  <summary>
                    {t}（{d[k].length}）
                  </summary>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>照片</th>
                          <th>原本</th>
                          <th>之後</th>
                        </tr>
                      </thead>
                      <tbody>
                        {d[k].map((i: Obj) => (
                          <tr key={i.image_id}>
                            <td>
                              <span className="break">{i.display_name || i.image_id}</span>
                              {i.display_name && <small className="mono">{i.image_id}</small>}
                            </td>
                            <td>{label(i.before)}</td>
                            <td>{label(i.after)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              )
          )}
          {!d.added.length && !d.removed.length && !d.changed.length && <Empty>兩個快照的照片與標籤完全相同。</Empty>}
        </>
      )}
    </Dialog>
  );
}

/** B8: model card. */
export function ModelCard({id}: {id: string}) {
  const state = useData('/artifacts/' + id + '/card');
  const c = state.data;
  if (state.error) return <p role="alert">{state.error}</p>;
  if (!c) return <Empty>整理模型說明…</Empty>;
  const s = c.evaluation?.summary;
  const main = s?.metrics?.[0];
  const t = c.independent_test?.summary?.metrics?.[0];
  return (
    <div className="model-card-body">
      <a className="button secondary" href={'/api/v1/artifacts/' + id + '/card.md'} download="模型卡.md">
        匯出模型卡
      </a>
      <dl className="facts">
        <dt>使用狀態</dt>
        <dd>
          {[c.in_use.local && '本地模擬使用中', c.in_use.line && 'LINE 使用中', c.in_use.shadow && 'LINE 影子模式']
            .filter(Boolean)
            .join('・') || '未使用'}
        </dd>
        <dt>評估</dt>
        <dd>
          {c.evaluation ? (
            <>
              {main ? `${main.name} ${pct(main.value)}（95% 區間 ${ci(main.ci)}）` : c.evaluation.accuracy_display}
              ・驗證 fold {c.evaluation.fold}{' '}
              <a href={'#models?tab=compare&report=' + c.evaluation.report_id}>完整報告 →</a>
            </>
          ) : (
            '尚未完成評估'
          )}
        </dd>
        {(c.holdout || c.independent_test) && (
          <>
            <dt>流程煙霧測試</dt>
            <dd>
              {c.independent_test ? (
                <>
                  {t ? `${t.name} ${pct(t.value)}（95% 區間 ${ci(t.ci)}）` : c.independent_test.accuracy_display}{' '}
                  <a href={'#models?tab=compare&report=' + c.independent_test.report_id}>完整報告 →</a>
                </>
              ) : (
                '訓練完成後評估；尚無結果。'
              )}
            </dd>
          </>
        )}
      </dl>
      <details>
        <summary>用途與限制</summary>
        <p>{c.intended_use}</p>
        <ul className="limits">
          {c.limitations.map((l: string) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </details>
      <details>
        <summary>訓練資料</summary>
        {c.data ? (
          <p>
            {c.data.name || c.data.snapshot}・fold {c.data.fold}（共 {c.data.folds} 折）・訓練{' '}
            {c.data.counts?.train ?? '?'} 張／驗證 {c.data.counts?.val ?? '?'} 張
            {c.data.classes?.train && (
              <small>
                訓練組：
                {Object.entries(c.data.classes.train)
                  .map(([k, v]) => `${names[k] || k} ${v}`)
                  .join('・')}
              </small>
            )}
          </p>
        ) : (
          <p>未記錄</p>
        )}
      </details>
      <details>
        <summary>訓練設定</summary>
        <p className="break">
          {Object.keys(c.training).length
            ? Object.entries(c.training)
                .map(([k, v]) => `${k}=${v}`)
                .join('・')
            : '未記錄'}
          {c.experiment_name && <small>實驗：{c.experiment_name}</small>}
        </p>
      </details>
      {s?.lines?.length > 0 && (
        <details>
          <summary>評估說明</summary>
          <ul className="limits">
            {s.lines.map((l: string) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

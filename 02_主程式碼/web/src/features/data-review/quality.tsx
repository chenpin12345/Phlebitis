import {useEffect, useRef, useState} from 'react';
import {api, useData, names, operatorName, Empty} from '../../shared/ui';
import {invalidate} from '../../shared/query';
import {Dialog} from '../../shared/dialog';
import {showToast} from '../../shared/toast';
type Obj = Record<string, any>;
const changed = () =>
  dispatchEvent(
    new CustomEvent('workbench-resources-changed', {
      detail: {scopes: ['data', '/overview', '/next-steps', '/flags/summary', '/source-watch/new', '/spot-check']},
    })
  );

/** A4: shown only when the 岡山高醫 folder has photos that are not in the project yet. */
export function SourceNewButton({autoOpen, onClosed}: {autoOpen: boolean; onClosed: () => void}) {
  const state = useData('/source-watch/new', 60000);
  const n = state.data?.count || 0;
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (autoOpen) setOpen(true);
  }, [autoOpen]);
  if (!n && !open) return null;
  return (
    <>
      <button type="button" className="secondary new-photos" onClick={() => setOpen(true)}>
        岡山高醫新照片 <b>{n}</b>
      </button>
      {open && (
        <Dialog
          title="匯入岡山高醫新照片"
          onClose={() => {
            setOpen(false);
            onClosed();
            state.refresh();
          }}
        >
          <QuickImport
            source={state.data?.source || 'gangshan'}
            expected={n}
            onDone={() => {
              state.refresh();
              changed();
            }}
          />
        </Dialog>
      )}
    </>
  );
}

const CATEGORY_TEXT: Obj = {
  addable: '可補入',
  near_duplicate: '近似重複（仍補入，之後在「疑似重複」確認）',
  same_name: '同名不同內容（獨立保存）',
  existing: '已在專案中（只補記來源名稱）',
  duplicate_in_source: '來源內重複（記為別名）',
  pixel_duplicate: '像素相同（隔離待人工決定）',
  label_conflict: '標籤衝突（不覆蓋既有標籤）',
  unsupported: '不支援的檔案',
  corrupt: '損毀或無法解碼',
};
/** Scan → one confirmation button → import. A backup of the dataset records is taken first. */
function QuickImport({source, expected, onDone}: {source: string; expected: number; onDone: () => void}) {
  const [id, setId] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  const started = useRef(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    api('/imports/external-previews', 'POST', {source})
      .then(r => setId(r.id))
      .catch(e => setError((e as Error).message));
  }, []);
  const detail = useData(
    '/imports/operations/' + id + '?size=100',
    800,
    d => ['ready', 'completed', 'failed', 'needs_check'].includes(d?.state),
    {enabled: !!id}
  );
  const d = detail.data;
  const notified = useRef(false);
  useEffect(() => {
    if (d?.state === 'completed' && !notified.current) {
      notified.current = true;
      invalidate(['data', '/overview']);
      onDone();
    }
  }, [d?.state]);
  if (error)
    return (
      <p role="alert" className="notice error">
        {error}
      </p>
    );
  if (!d) return <Empty>正在比對岡山高醫資料夾（唯讀）…</Empty>;
  const adds = (d.items || []).filter((i: Obj) => i.action === 'add').length,
    aliases = (d.items || []).filter((i: Obj) => i.action === 'alias').length;
  if (d.state === 'scanning')
    return (
      <Empty>
        正在比對（{d.processed ?? 0} / {d.total ?? '…'}）{d.phase ? '・' + d.phase : ''}
      </Empty>
    );
  if (d.state === 'failed' || d.state === 'needs_check')
    return (
      <>
        <p role="alert" className="notice error">
          {d.error || '比對或匯入未完成'}
        </p>
        <button
          type="button"
          className="secondary"
          onClick={() =>
            api('/imports/operations/' + id + '/retry', 'POST')
              .then(() => detail.refresh())
              .catch(e => setError(e.message))
          }
        >
          重試
        </button>
      </>
    );
  if (['queued', 'running'].includes(d.state)) return <Empty>匯入中…{d.phase ? '（' + d.phase + '）' : ''}</Empty>;
  if (d.state === 'completed')
    return (
      <div className="callout">
        <b>匯入完成</b>
        <p>
          新增 {(d.items || []).filter((i: Obj) => i.action === 'add' && i.image_id).length} 張
          {d.rule_summary ? `；自動完成分類 ${d.rule_summary['cls:applied'] || 0} 張` : ''}
          。匯入前已自動備份資料清單與標註。
        </p>
        <div className="actions">
          <a className="button secondary" href="#data?area=cls&view=confirmed&source=gangshan">
            查看分類結果 →
          </a>
        </div>
      </div>
    );
  return (
    <>
      <p>只讀取岡山高醫資料夾，不搬移、改名或刪除來源檔案。偵測到 {expected} 張新照片；比對結果如下。</p>
      <div className="table-wrap">
        <table>
          <tbody>
            {Object.entries(d.summary || {})
              .filter(([, n]) => (n as number) > 0)
              .map(([k, n]) => (
                <tr key={k}>
                  <th>{CATEGORY_TEXT[k] || d.category_names?.[k] || k}</th>
                  <td className="num">{n as number}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <details>
        <summary>逐檔明細（{(d.items || []).length}）</summary>
        <ul>
          {(d.items || []).map((i: Obj, k: number) => (
            <li key={k} className="break">
              {i.name} — {CATEGORY_TEXT[i.category] || i.category}
              {i.label ? '・檔名分期 ' + (names[i.label.value] || i.label.value) : ''}
            </li>
          ))}
        </ul>
      </details>
      {adds + aliases === 0 ? (
        <p className="muted">沒有需要匯入的照片。</p>
      ) : (
        <div className="actions">
          <button
            type="button"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await api('/imports/external-operations', 'POST', {
                  preview_id: id,
                  idempotency_key: 'source-quick:' + id,
                  confirmation: '確認匯入',
                });
                await detail.refresh();
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? '送出中…' : adds ? `匯入 ${adds} 張` : `補記 ${aliases} 個來源名稱`}
          </button>
        </div>
      )}
    </>
  );
}

/** Conditional filters (A3, A6): shown only when the count is above zero. */
export function FlagPills({
  counts,
  flag,
  onFlag,
}: {
  counts: Obj | undefined;
  flag: string;
  onFlag: (f: string) => void;
}) {
  const items = [
    ['quality', '⚠', '品質待確認'],
    ['duplicate', '⧉', '疑似重複'],
  ].filter(([k]) => (counts?.[k] || 0) > 0 || flag === k);
  if (!items.length) return null;
  return (
    <div className="flag-pills" role="group" aria-label="需要確認的照片">
      {items.map(([k, icon, label]) => (
        <button
          key={k}
          type="button"
          aria-pressed={flag === k}
          className={'flag-pill ' + (flag === k ? 'active' : '')}
          onClick={() => onFlag(flag === k ? '' : k)}
        >
          <span aria-hidden="true">{icon}</span>
          {label}
          <b>{counts?.[k] || 0}</b>
        </button>
      ))}
    </div>
  );
}

export function ThumbMarks({flags}: {flags?: string[]}) {
  if (!flags?.length) return null;
  return (
    <span className="thumb-marks">
      {flags.includes('quality') && (
        <span className="mark-q" title="品質待確認">
          ⚠<span className="sr">品質待確認</span>
        </span>
      )}
      {flags.includes('duplicate') && (
        <span className="mark-d" title="疑似重複">
          ⧉<span className="sr">疑似重複</span>
        </span>
      )}
    </span>
  );
}

/** Editor notes: automatic quality measurements and suspected duplicates of this photo. */
export function FlagNotes({ident, onChanged}: {ident: string; onChanged: () => void}) {
  const state = useData('/data/' + ident + '/flags');
  const d = state.data;
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  if (!d) return null;
  const q = d.quality,
    dups = (d.duplicates || []).filter((p: Obj) => !p.decision);
  if (!q?.pending && !dups.length) return null;
  const run = async (fn: () => Promise<any>, message: string) => {
    if (!operatorName()) {
      setError('請先在「設定與維護」填寫操作者名稱。');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await fn();
      showToast({text: message});
      await state.refresh();
      changed();
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flag-notes">
      {q?.pending && (
        <div className="callout warning">
          <b>⚠ 品質待確認（自動檢查，僅供參考）</b>
          <ul>
            {q.reasons.map((r: string) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
          <p className="muted">可在分類區設定「影像品質」，或確認沒有問題。</p>
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={() =>
              run(() => api('/data/' + ident + '/quality-ack', 'POST', {reviewer: operatorName()}), '已標記品質可接受')
            }
          >
            品質沒有問題
          </button>
        </div>
      )}
      {dups.slice(0, 3).map((p: Obj) => (
        <div key={p.key} className="callout warning duplicate-pair">
          <b>⧉ 疑似重複：{p.kind === 'pixel' ? '像素完全相同' : '內容非常相似（差異 ' + p.distance + '）'}</b>
          <div className="pair">
            <figure>
              <img src={'/api/v1/data/' + ident + '/image?thumbnail=true'} alt="這張照片" />
              <figcaption>這張</figcaption>
            </figure>
            <figure>
              <a href={'#data?area=cls&view=all&image=' + p.other}>
                <img src={'/api/v1/data/' + p.other + '/image?thumbnail=true'} alt={'另一張 ' + p.other} />
              </a>
              <figcaption className="break">{p.other}</figcaption>
            </figure>
          </div>
          <div className="actions">
            <button
              type="button"
              className="secondary"
              disabled={busy}
              onClick={() =>
                run(
                  () =>
                    api('/duplicates/decision', 'POST', {
                      a: p.a,
                      b: p.b,
                      decision: 'not_duplicate',
                      reviewer: operatorName(),
                    }),
                  '已記錄：不是重複'
                )
              }
            >
              不是重複
            </button>
            <button
              type="button"
              className="secondary"
              disabled={busy}
              onClick={() =>
                run(
                  () =>
                    api('/duplicates/decision', 'POST', {
                      a: p.a,
                      b: p.b,
                      decision: 'duplicate',
                      keep: ident,
                      reviewer: operatorName(),
                    }),
                  '已排除另一張重複照片'
                )
              }
            >
              是重複，保留這張
            </button>
            <button
              type="button"
              className="secondary"
              disabled={busy}
              onClick={() =>
                run(
                  () =>
                    api('/duplicates/decision', 'POST', {
                      a: p.a,
                      b: p.b,
                      decision: 'duplicate',
                      keep: p.other,
                      reviewer: operatorName(),
                    }),
                  '已排除這張重複照片'
                )
              }
            >
              是重複，保留另一張
            </button>
          </div>
          <small>「是重複」會把不保留的那張在兩個工作區都設為排除，並留下審查紀錄。</small>
        </div>
      ))}
      {dups.length > 3 && <p className="muted">另有 {dups.length - 3} 組疑似重複；處理完上面幾組後會接著顯示。</p>}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
    </div>
  );
}

/** A5: one photo at a time, 「正確」 or 「有誤」. */
export function SpotCheckButton({autoOpen, onClosed}: {autoOpen: boolean; onClosed: () => void}) {
  const state = useData('/spot-check', 30000);
  const d = state.data;
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (autoOpen) setOpen(true);
  }, [autoOpen]);
  const n = d ? d.pending || d.unsampled : 0;
  if (!d?.enabled) return null;
  return (
    <>
      <button type="button" className="secondary" onClick={() => setOpen(true)}>
        抽查岡山高醫分期{n > 0 && <b className="count-chip">{d.pending || '新'}</b>}
      </button>
      {open && (
        <Dialog
          title="抽查岡山高醫自動分類"
          onClose={() => {
            setOpen(false);
            onClosed();
            changed();
          }}
        >
          <SpotCheck initial={d} onChanged={state.refresh} />
        </Dialog>
      )}
    </>
  );
}

function SpotCheck({initial, onChanged}: {initial: Obj | null; onChanged: () => void}) {
  const [d, setD] = useState<Obj | null>(initial),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [done, setDone] = useState(0);
  useEffect(() => {
    if (!initial || (!initial.pending && initial.unsampled)) {
      setBusy(true);
      api('/spot-check/start', 'POST')
        .then(setD)
        .catch(e => setError(e.message))
        .finally(() => setBusy(false));
    }
  }, []);
  const item = d?.items?.[0];
  const answer = async (correct: boolean) => {
    if (!item || busy) return;
    if (!operatorName()) {
      setError('請先在「設定與維護」填寫操作者名稱。');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const r = await api('/spot-check/' + item.image_id, 'POST', {
        correct,
        reviewer: operatorName(),
        revision: item.revision,
      });
      setD(r);
      setDone(n => n + 1);
      onChanged();
      if (!correct) showToast({text: '已退回分類區待處理，請重新分類'});
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if ((e.target as Element)?.tagName === 'INPUT') return;
      if (e.key === '1' || e.key.toLowerCase() === 'y') {
        e.preventDefault();
        answer(true);
      }
      if (e.key === '2' || e.key.toLowerCase() === 'n') {
        e.preventDefault();
        answer(false);
      }
    };
    addEventListener('keydown', f);
    return () => removeEventListener('keydown', f);
  });
  if (error && !d)
    return (
      <p role="alert" className="notice error">
        {error}
      </p>
    );
  if (!d) return <Empty>抽出本批照片…</Empty>;
  if (!item)
    return (
      <>
        <p>
          {done ? `本批已完成 ${done} 張。` : ''}目前沒有待抽查的照片。
          {d.auto_total
            ? `自動分類共 ${d.auto_total} 張，已抽查 ${d.checked} 張，其中 ${d.wrong} 張有誤。`
            : '目前沒有依檔名自動分類的照片。'}
        </p>
        {d.unsampled > 0 && (
          <button
            type="button"
            disabled={busy}
            onClick={() =>
              api('/spot-check/start', 'POST')
                .then(setD)
                .catch(e => setError(e.message))
            }
          >
            抽出下一批
          </button>
        )}
      </>
    );
  const total = done + d.items.length;
  return (
    <div className="spot-check">
      <p className="muted">
        第 {done + 1} / {total} 張・本批從 {d.items[0]?.batch} 起新增的自動分類照片中抽出。只確認分期是否正確。
      </p>
      <figure className="preview">
        <img src={'/api/v1/data/' + item.image_id + '/image'} alt="抽查照片" />
      </figure>
      <p>
        <b>自動分類：{names[item.stage] || item.stage}</b>
        {item.display_name && <small className="break">檔名：{item.display_name}</small>}
      </p>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <div className="actions">
        <button type="button" disabled={busy} aria-keyshortcuts="1" onClick={() => answer(true)}>
          正確<kbd aria-hidden="true">1</kbd>
        </button>
        <button
          type="button"
          className="secondary danger"
          disabled={busy}
          aria-keyshortcuts="2"
          onClick={() => answer(false)}
        >
          有誤<kbd aria-hidden="true">2</kbd>
        </button>
      </div>
      <small>「有誤」會把這張照片的分類退回待處理，由你在分類區重新選擇分期。</small>
    </div>
  );
}

import {PhotoTrash} from './PhotoTrash';
import React, {useState, useEffect, useRef} from 'react';
import {api, useData, useHash, route, Fields, Empty, Pager, when} from '../../shared/ui';
import {Dialog} from '../../shared/dialog';
import {useSelection, SelectAllBox, SelectionStatus} from '../../shared/selection';
import {trackOperation} from '../../shared/background-ops';
import {showToast} from '../../shared/toast';

export type Target = {type: 'job' | 'model' | 'research_photo' | 'legacy_run' | 'snapshot'; id: string};
type Capacity = {
  status: string;
  calculated_at?: number;
  file_bytes?: number | null;
  known_file_bytes?: number;
  exclusive_file_bytes?: number;
  estimated_release_bytes?: number | null;
  retained_file_bytes?: number | null;
  database_content_estimate_bytes?: number | null;
  basis?: string;
  limitations?: string[];
};
type FileInfo = {path: string; bytes: number | null; reason?: string};
type PreviewItem = Target & {
  name: string;
  revision: number;
  blockers: string[];
  warnings: string[];
  relations: unknown[];
  files: FileInfo[];
  retained: FileInfo[];
  file_count?: number;
  retained_count?: number;
  capacity: Capacity;
};
type Preview = {
  id: string;
  state: string;
  expires: number;
  blocked: boolean;
  confirmation: string;
  items: PreviewItem[];
  capacity: Capacity;
  error?: string;
  page: number;
  progress?: {done: number; total: number};
};
type Operation = {
  id: string;
  state: string;
  action: string;
  created: number;
  updated: number;
  removed_files: number;
  removed_logical_bytes: number;
  result: Array<Target & {state: string; errors?: string[]; retained?: FileInfo[]; retained_count?: number}>;
  page: number;
  size: number;
  step_count: number;
  steps: Array<{path: string; state: string; error?: string}>;
  plan: {items: PreviewItem[]};
};
type TrashItem = Target & {
  state: string;
  moved: number;
  actor: string | null;
  summary: Record<string, unknown>;
  capacity: Capacity;
  operation?: string;
  can_restore: boolean;
  can_purge: boolean;
};
const typeNames: Record<string, string> = {
  job: '工作紀錄',
  model: '模型版本',
  research_photo: 'LINE 研究照片',
  legacy_run: '歷史產物',
  snapshot: '資料快照',
};
export const MAX_TARGETS = 1000;
const stateNames: Record<string, string> = {
  trashed: '已移入',
  purging: '永久刪除中',
  purged: '已永久刪除',
  partial_failed: '部分失敗',
  needs_check: '待檢查',
  preparing: '準備中',
  running: '執行中',
  completed: '完成',
  succeeded: '成功',
  failed: '失敗',
  pending: '未處理',
  intent: '已記錄刪除意圖',
  removed: '已確認移除',
  ready: '已準備',
  calculating: '計算中',
  expired: '已失效',
};
const capacityNames: Record<string, string> = {
  pending: '計算中／尚未取得',
  estimated: '估計值',
  unable: '無法完整計算',
  stale: '過期',
};
export function bytes(n: number | null | undefined) {
  if (n == null) return '未知';
  if (n < 1024) return `${n} bytes`;
  const units = ['KiB', 'MiB', 'GiB', 'TiB'];
  let i = -1,
    v = n;
  do {
    v /= 1024;
    i++;
  } while (v >= 1024 && i < 3);
  return `${v.toFixed(2)} ${units[i]}`;
}
// A trash action can change any list (jobs, models, snapshots, trash), so every open query refreshes.
function changed() {
  dispatchEvent(new CustomEvent('workbench-resources-changed', {detail: {scopes: ['*']}}));
}

export function CapacityDetails({value}: {value: Capacity}) {
  return (
    <div className="capacity-detail">
      <p>
        計算狀態：{capacityNames[value.status] || value.status} · {when(value.calculated_at)}
      </p>
      <dl>
        <dt>資料容量（檔案邏輯大小）</dt>
        <dd>{bytes(value.file_bytes)}</dd>
        <dt>已確認的部分檔案容量</dt>
        <dd>{bytes(value.known_file_bytes)}</dd>
        <dt>獨占可清理檔案</dt>
        <dd>{bytes(value.exclusive_file_bytes)}</dd>
        <dt>預估可釋放容量</dt>
        <dd>{bytes(value.estimated_release_bytes)}</dd>
        <dt>仍保留檔案容量</dt>
        <dd>{bytes(value.retained_file_bytes)}</dd>
        <dt>資料庫欄位內容估計</dt>
        <dd>{bytes(value.database_content_estimate_bytes)}</dd>
      </dl>
      <p>{value.basis || '容量尚待計算。'}</p>
      <p>資料庫內容刪除後空間可由資料庫重用，立即可釋放磁碟空間不保證；不自動壓縮資料庫。</p>
      {value.limitations?.map((v, i) => (
        <p className="callout" key={i}>
          {v}
        </p>
      ))}
    </div>
  );
}

export function OperationResult({id, onChanged}: {id: string; onChanged?: () => void}) {
  const [page, setPage] = useState(1);
  const state = useData(
    '/trash/operations/' + id + '?page=' + page,
    1000,
    d => !['preparing', 'running'].includes(d.state)
  );
  const d = state.data as Operation | null;
  const notified = useRef('');
  const [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    if (d && !['preparing', 'running'].includes(d.state) && notified.current !== d.state) {
      notified.current = d.state;
      changed();
      onChanged?.();
    }
  }, [d?.state]);
  if (state.error) return <Empty>{state.error}</Empty>;
  if (!d) return <Empty>讀取操作紀錄…</Empty>;
  return (
    <section aria-live="polite">
      <h3>{stateNames[d.state] || d.state}</h3>
      <Fields value={{id: d.id, created: d.created, updated: d.updated}} />
      {['preparing', 'running'].includes(d.state) ? (
        <p className="callout info">已在背景執行，可以關閉此視窗；完成時會在頁面上方通知。</p>
      ) : (
        <p>完成範圍以本次核准清單為準。</p>
      )}
      <p>
        項目結果：{d.result.filter(r => r.state === 'succeeded').length} 成功／
        {d.result.filter(r => r.state === 'failed').length} 失敗／{Math.max(0, d.plan.items.length - d.result.length)}{' '}
        未處理。
      </p>
      <p>
        已確認移除 {d.removed_files} 個檔案，邏輯大小 {bytes(d.removed_logical_bytes)}
        。磁碟實際回收量未量測；備份及外部副本未刪除。
      </p>
      {d.result.map((r, i) => (
        <section key={i}>
          <h4>
            {typeNames[r.type] || '操作'} · {r.id} · {stateNames[r.state]}
          </h4>
          {r.errors?.map((v, j) => (
            <p className="notice error" key={j}>
              {v}
            </p>
          ))}
          {!!r.retained?.length && (
            <details>
              <summary>仍保留 {r.retained_count ?? r.retained.length} 份內容</summary>
              <FileTable rows={r.retained} />
            </details>
          )}
        </section>
      ))}
      <details>
        <summary>逐檔執行紀錄</summary>
        <Pager
          page={d.page}
          total={Math.max(d.step_count, ...d.result.map(r => r.retained_count || 0))}
          size={d.size}
          onPage={setPage}
        />
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>檔案</th>
                <th>狀態</th>
                <th>診斷</th>
              </tr>
            </thead>
            <tbody>
              {d.steps.map((s, i) => (
                <tr key={i}>
                  <td className="break">{s.path}</td>
                  <td>{stateNames[s.state] || s.state}</td>
                  <td>{s.error || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      {error && <p role="alert">{error}</p>}
      {['partial_failed', 'needs_check'].includes(d.state) && (
        <>
          <p>重試會重新檢查原計畫尚未完成的內容；無法確認的缺檔需先人工檢查，不會自動視為成功。</p>
          <button
            type="button"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              setError('');
              try {
                await api('/trash/operations/' + id + '/retry', 'POST');
                notified.current = '';
                await state.refresh();
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            重新檢查並重試剩餘項目
          </button>
        </>
      )}
    </section>
  );
}

function FileTable({rows}: {rows: FileInfo[]}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>檔案</th>
            <th>邏輯容量</th>
            <th>說明</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((f, i) => (
            <tr key={i}>
              <td className="break">{f.path}</td>
              <td>{bytes(f.bytes)}</td>
              <td>{f.reason || '核准範圍候選'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function PreviewContent({
  id,
  action,
  onDone,
  onRetarget,
}: {
  id: string;
  action: string;
  onDone?: () => void;
  onRetarget?: (targets: Target[]) => void;
}) {
  const [page, setPage] = useState(1),
    [confirmation, setConfirmation] = useState(''),
    [operation, setOperation] = useState(''),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const key = useRef(crypto.randomUUID());
  const state = useData('/trash/previews/' + id + '?page=' + page, 1000, d => d.state !== 'calculating');
  const d = state.data as Preview | null;
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  if (operation) return <OperationResult id={operation} onChanged={onDone} />;
  if (state.error) return <Empty>{state.error}</Empty>;
  if (!d) return <Empty>取得伺服器影響預覽…</Empty>;
  if (d.state === 'calculating')
    return (
      <Empty>
        正在核對相依性及計算容量（{d.progress ? `${d.progress.done} / ${d.progress.total}` : '準備中'}），尚未執行操作…
      </Empty>
    );
  const expired = d.expires * 1000 <= now || d.state === 'expired';
  const items = [...(d.items || [])].sort((a, b) => Number(!a.blockers.length) - Number(!b.blockers.length));
  const blockedItems = items.filter(i => i.blockers.length),
    rest = items.filter(i => !i.blockers.length);
  const many = items.length > 20;
  return (
    <>
      <p className="callout">
        {action === 'purge'
          ? '永久刪除後無法由垃圾桶還原。'
          : action === 'move'
            ? '移至垃圾桶保留原 ID 與內容，可還原；此步驟不釋放空間。'
            : '還原後工作不重新執行、模型不自動啟用，稽核保留原時間。'}
      </p>
      <p>
        明確選取 {d.items?.length || 0} 個項目 · 預覽有效至 {when(d.expires)}
      </p>
      {d.error && <p className="notice error">{d.error}</p>}
      {expired && (
        <p role="alert" className="notice error">
          預覽已失效，請關閉後重新取得。
        </p>
      )}
      {(many ? blockedItems : items).map(item => (
        <section className="preview-item" key={item.type + item.id}>
          <h3>
            {typeNames[item.type]} · {item.name}
          </h3>
          <p className="break">{item.id}</p>
          {item.blockers.map((b, i) => (
            <p role="alert" className="notice error" key={i}>
              {b}
            </p>
          ))}
          {item.warnings.map((b, i) => (
            <p className="callout" key={i}>
              {b}
            </p>
          ))}
          <details>
            <summary>關聯對象與影響（{item.relations.length}）</summary>
            <Fields value={item.relations} />
          </details>
          <details>
            <summary>容量與計算限制</summary>
            <CapacityDetails value={item.capacity} />
          </details>
          <details>
            <summary>
              可清理檔案（{item.file_count || 0}）及保留內容（{item.retained_count || 0}）
            </summary>
            <h4>可清理檔案</h4>
            <FileTable rows={item.files} />
            <h4>保留內容</h4>
            <FileTable rows={item.retained} />
          </details>
        </section>
      ))}
      {many && (
        <details>
          <summary>其餘 {rest.length} 個可處理項目（展開查看逐項明細）</summary>
          {rest.map(item => (
            <p key={item.type + item.id} className="break">
              {typeNames[item.type]} · {item.name} · {item.id}
            </p>
          ))}
        </details>
      )}
      {d.items?.some(i => Math.max(i.file_count || 0, i.retained_count || 0) > 100) && (
        <Pager
          page={page}
          total={Math.max(...d.items.map(i => Math.max(i.file_count || 0, i.retained_count || 0)))}
          size={100}
          onPage={setPage}
        />
      )}
      <details>
        <summary>選取集合去重後容量</summary>
        <CapacityDetails value={d.capacity} />
      </details>
      {d.blocked && (
        <>
          <p>有 {blockedItems.length} 個項目受阻（列在最上方）。</p>
          {onRetarget && rest.length > 0 && (
            <button
              type="button"
              className="secondary"
              onClick={() => onRetarget(rest.map(({type, id}) => ({type, id})))}
            >
              略過 {blockedItems.length} 個受阻項目，重新取得預覽
            </button>
          )}
        </>
      )}
      {d.confirmation && (
        <label className="field">
          請輸入「{d.confirmation}」
          <input
            aria-label="永久刪除確認文字"
            autoComplete="off"
            value={confirmation}
            onChange={e => setConfirmation(e.target.value)}
          />
        </label>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <button
        type="button"
        className={action === 'purge' ? 'danger' : ''}
        disabled={busy || expired || d.blocked || d.state !== 'ready' || confirmation !== (d.confirmation || '')}
        onClick={async () => {
          setBusy(true);
          setError('');
          try {
            const op = await api(
              '/trash/operations',
              'POST',
              {preview_id: id, confirmation},
              {'Idempotency-Key': key.current}
            );
            setOperation(op.id);
            if (['preparing', 'running'].includes(op.state)) trackOperation({id: op.id, action, count: d.items.length});
            changed();
            onDone?.();
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? '提交中…' : action === 'purge' ? '確認永久刪除' : action === 'restore' ? '確認還原' : '確認移至垃圾桶'}
      </button>
    </>
  );
}

// ---- One-step trash actions (2026-10-17) ----------------------------------------------
// Move: no preview dialog; protected items stop the batch and are explained; undo via toast.
// Purge: one confirmation dialog (no typing). Restore keeps its preview dialog.
async function pollPreview(id: string, auto: boolean): Promise<Preview & {operation?: string}> {
  const deadline = Date.now() + 180000;
  for (;;) {
    const d = await api('/trash/previews/' + id);
    const waiting = d.state === 'calculating' || (auto && d.state === 'ready' && !d.blocked);
    if (!waiting) return d;
    if (Date.now() > deadline) throw Error('處理逾時，請稍後到垃圾桶確認結果');
    await new Promise(r => setTimeout(r, 400));
  }
}
async function oneStep(action: 'move' | 'restore' | 'purge', targets: Target[]) {
  if (targets.length > MAX_TARGETS) throw Error(`單次最多處理 ${MAX_TARGETS} 筆，請縮小篩選範圍。`);
  const p = await api('/trash/previews', 'POST', {action, targets, auto_commit: true});
  return pollPreview(p.id, true);
}
const blockedOf = (d: Preview) => (d.items || []).filter(i => i.blockers.length);
const restOf = (d: Preview) => (d.items || []).filter(i => !i.blockers.length).map(({type, id}) => ({type, id}));
function undoToast(moved: Target[], onDone?: () => void) {
  showToast({
    text: `已移至垃圾桶 ${moved.length} 項`,
    action: {
      label: '復原',
      run: async () => {
        try {
          const d = await oneStep('restore', moved);
          if (d.state === 'consumed') {
            showToast({text: `已還原 ${moved.length} 項`});
            changed();
            onDone?.();
          } else
            showToast({
              tone: 'error',
              text: '無法還原：' + (blockedOf(d)[0]?.blockers[0] || d.error || '請到垃圾桶處理'),
            });
        } catch (e) {
          showToast({tone: 'error', text: (e as Error).message});
        }
      },
    },
  });
}
/** Protected items: always shown with their reasons; nothing in the batch was changed. */
function BlockedNotice({
  d,
  action,
  onRest,
  onCancel,
}: {
  d: Preview;
  action: string;
  onRest: () => void;
  onCancel: () => void;
}) {
  const blocked = blockedOf(d),
    rest = restOf(d);
  const verb = action === 'purge' ? '永久刪除' : '移入垃圾桶';
  return (
    <>
      <p className="callout warning">
        以下 {blocked.length} 項是重要項目，不能{verb}。這一批目前沒有任何變更。
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>項目</th>
              <th>原因</th>
            </tr>
          </thead>
          <tbody>
            {blocked.map(i => (
              <tr key={i.type + i.id}>
                <td>
                  {typeNames[i.type]}
                  <br />
                  <small className="break">{i.name}</small>
                </td>
                <td>
                  {i.blockers.map((b, k) => (
                    <div key={k}>{b.replace('（模型引用保護）', '')}</div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="actions">
        {rest.length > 0 && (
          <button type="button" className={action === 'purge' ? 'danger' : ''} onClick={onRest}>
            只{verb}其餘 {rest.length} 項
          </button>
        )}
        <button type="button" className="secondary" onClick={onCancel}>
          取消
        </button>
      </div>
    </>
  );
}
function PurgeConfirm({
  d,
  onConfirm,
  onCancel,
  busy,
}: {
  d: Preview;
  onConfirm: () => void;
  onCancel: () => void;
  busy: boolean;
}) {
  const n = d.items.length;
  const warnings = [...new Set(d.items.flatMap(i => i.warnings))];
  return (
    <>
      <p>
        永久刪除 {n} 項（預估可釋放 {bytes(d.capacity?.estimated_release_bytes)}）？此動作無法復原。
      </p>
      {warnings.length > 0 && (
        <details>
          <summary>注意事項（{warnings.length}）</summary>
          <ul>
            {warnings.map(w => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </details>
      )}
      <div className="actions">
        <button type="button" className="danger" disabled={busy} onClick={onConfirm}>
          {busy ? '送出中…' : `永久刪除 ${n} 項`}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          取消
        </button>
      </div>
    </>
  );
}

export function TrashAction({
  targets,
  action = 'move',
  disabled = false,
  onDone,
}: {
  targets: Target[];
  action?: 'move' | 'restore' | 'purge';
  disabled?: boolean;
  onDone?: () => void;
}) {
  const [open, setOpen] = useState(false),
    [id, setId] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [checked, setChecked] = useState<Preview | null>(null),
    [progress, setProgress] = useState('');
  const generation = useRef(0);
  const label = action === 'move' ? '移至垃圾桶' : action === 'restore' ? '還原' : '永久刪除';
  const reset = () => {
    ++generation.current;
    setOpen(false);
    setChecked(null);
    setId('');
    setError('');
    setBusy(false);
  };
  // Restore keeps the full preview dialog (unchanged).
  const requestRestore = async (list: Target[]) => {
    setOpen(true);
    setError('');
    setId('');
    const token = ++generation.current;
    try {
      const p = await api('/trash/previews', 'POST', {action, targets: list});
      if (token === generation.current) setId(p.id);
    } catch (e) {
      if (token === generation.current) setError((e as Error).message);
    }
  };
  const move = async (list: Target[]) => {
    setBusy(true);
    setError('');
    try {
      const d = await oneStep('move', list);
      if (d.state === 'consumed') {
        reset();
        changed();
        onDone?.();
        undoToast(restOf(d).length ? restOf(d) : list, onDone);
      } else if (d.blocked) {
        setChecked(d);
        setOpen(true);
      } else throw Error(d.error || '移入失敗，請稍後再試');
    } catch (e) {
      setOpen(true);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const purgeCheck = async (list: Target[]) => {
    setOpen(true);
    setChecked(null);
    setError('');
    setProgress('');
    const token = ++generation.current;
    try {
      if (list.length > MAX_TARGETS) throw Error(`單次最多處理 ${MAX_TARGETS} 筆，請縮小篩選範圍。`);
      const p = await api('/trash/previews', 'POST', {action: 'purge', targets: list});
      for (;;) {
        const d = await api('/trash/previews/' + p.id);
        if (token !== generation.current) return;
        if (d.state !== 'calculating') {
          setChecked(d);
          return;
        }
        setProgress(d.progress ? `${d.progress.done} / ${d.progress.total}` : '');
        await new Promise(r => setTimeout(r, 400));
      }
    } catch (e) {
      if (token === generation.current) setError((e as Error).message);
    }
  };
  const purgeRun = async (d: Preview, only?: Target[]) => {
    setBusy(true);
    setError('');
    try {
      let opId = '',
        count = d.items.length;
      if (only) {
        count = only.length;
        const r = await oneStep('purge', only);
        if (r.state !== 'consumed' || !r.operation)
          throw Error(blockedOf(r)[0]?.blockers[0] || r.error || '無法送出永久刪除');
        opId = r.operation;
      } else {
        const op = await api(
          '/trash/operations',
          'POST',
          {preview_id: d.id, confirmation: ''},
          {'Idempotency-Key': 'purge:' + d.id}
        );
        opId = op.id;
      }
      trackOperation({id: opId, action: 'purge', count});
      showToast({text: `已開始永久刪除 ${count} 項，完成後會通知`});
      reset();
      changed();
      onDone?.();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const click = () =>
    action === 'move' ? move(targets) : action === 'purge' ? purgeCheck(targets) : requestRestore(targets);
  const body = error ? (
    <p role="alert" className="notice error">
      {error}
    </p>
  ) : action === 'restore' ? (
    id ? (
      <PreviewContent key={id} id={id} action={action} onDone={onDone} onRetarget={requestRestore} />
    ) : (
      <Empty>取得影響範圍…</Empty>
    )
  ) : !checked ? (
    <Empty>正在檢查{progress ? `（${progress}）` : ''}…</Empty>
  ) : checked.blocked ? (
    <BlockedNotice
      d={checked}
      action={action}
      onCancel={reset}
      onRest={() => {
        const rest = restOf(checked);
        if (action === 'move') {
          setChecked(null);
          move(rest);
        } else purgeRun(checked, rest);
      }}
    />
  ) : (
    <PurgeConfirm d={checked} busy={busy} onCancel={reset} onConfirm={() => purgeRun(checked)} />
  );
  return (
    <>
      <button
        type="button"
        className="secondary"
        disabled={disabled || !targets.length || busy || open}
        onClick={click}
      >
        {busy && action === 'move' ? '處理中…' : label}
      </button>
      {open && (
        <Dialog
          title={checked?.blocked ? '無法' + (action === 'purge' ? '永久刪除' : '移入') + '的項目' : label}
          onClose={reset}
        >
          {body}
        </Dialog>
      )}
    </>
  );
}

export function TrashPage() {
  const {params} = useHash();
  const [operation, setOperation] = useState(''),
    [error, setError] = useState('');
  const query = new URLSearchParams(params);
  const state = useData('/trash?' + query.toString(), 4000);
  const d = state.data as {
    items: TrashItem[];
    total: number;
    all_count: number;
    page: number;
    size: number;
    actors: string[];
  } | null;
  const set = (k: string, v: string) => {
    const p = Object.fromEntries(params);
    p[k] = v;
    if (k !== 'page') p.page = '1';
    route('trash', p);
  };
  const filters = new URLSearchParams(Object.fromEntries([...params].filter(([k]) => k !== 'page')));
  const selection = useSelection(filters.toString());
  const key = (r: Target) => r.type + ':' + r.id;
  const selected: Target[] = selection.selected.map(k => {
    const i = k.indexOf(':');
    return {type: k.slice(0, i) as Target['type'], id: k.slice(i + 1)};
  });
  const clear = () => selection.clear();
  return (
    <>
      <div className="heading">
        <div>
          <h1>垃圾桶</h1>
          <p>集中管理資料照片、工作、模型版本、LINE 研究照片、資料快照與歷史產物。永久刪除須先取得影響預覽。</p>
        </div>
      </div>
      <PhotoTrash />
      <section className="panel">
        <div className="form-grid">
          <label className="field">
            類型
            <select value={params.get('type') || ''} onChange={e => set('type', e.target.value)}>
              <option value="">全部</option>
              {Object.entries(typeNames).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            搜尋名稱、摘要或 ID
            <input value={params.get('search') || ''} onChange={e => set('search', e.target.value)} />
          </label>
          {[
            ['start', '移入開始日期'],
            ['end', '移入結束日期'],
          ].map(([k, v]) => (
            <label className="field" key={k}>
              {v}
              <input type="date" value={params.get(k) || ''} onChange={e => set(k, e.target.value)} />
            </label>
          ))}
          <label className="field">
            操作者（自填身分）
            <select value={params.get('actor') || ''} onChange={e => set('actor', e.target.value)}>
              <option value="">全部</option>
              <option value="__unknown__">未記錄</option>
              {d?.actors.filter(a => a && a !== 'local_operator').map(a => <option key={a}>{a}</option>)}
            </select>
          </label>
          <label className="field">
            排序欄位
            <select value={params.get('sort') || 'moved'} onChange={e => set('sort', e.target.value)}>
              <option value="moved">移入時間</option>
              <option value="file_bytes">檔案資料容量</option>
              <option value="estimated_release_bytes">預估可釋放容量</option>
            </select>
          </label>
          <label className="field">
            排序方向
            <select value={params.get('direction') || 'desc'} onChange={e => set('direction', e.target.value)}>
              <option value="desc">由大到小／由新到舊</option>
              <option value="asc">由小到大／由舊到新</option>
            </select>
          </label>
        </div>
        <p>日期採臺北時間，結束日期包含當日。未知容量排在最後。</p>
        <div className="toolbar selection-bar">
          <SelectionStatus selection={selection} total={d?.total || 0} />
          <TrashAction
            targets={selected}
            action="restore"
            onDone={() => {
              clear();
              state.refresh();
            }}
          />
          <TrashAction
            targets={selected}
            action="purge"
            onDone={() => {
              clear();
              state.refresh();
            }}
          />
          <button
            className="secondary"
            disabled={!selected.length}
            onClick={async () => {
              try {
                await api('/trash/capacity', 'POST', selected);
                await state.refresh();
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            重新計算選取項目容量
          </button>
        </div>
        {error && <p role="alert">{error}</p>}
        {state.error ? (
          <Empty>{state.error}</Empty>
        ) : !d ? (
          <Empty>載入垃圾桶…</Empty>
        ) : (
          <>
            <Pager page={d.page} total={d.total} size={d.size} onPage={(v: number) => set('page', String(v))} />
            {!d.items.length ? (
              <Empty>{d.all_count ? '沒有符合篩選條件的項目。' : '垃圾桶目前是空的。'}</Empty>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>
                        <SelectAllBox
                          selection={selection}
                          total={d.total}
                          label="選取全部符合條件的項目"
                          fetchAll={() => api('/trash/ids?' + filters.toString())}
                        />
                      </th>
                      <th>類型／名稱／原 ID</th>
                      <th>移入時間／操作者</th>
                      <th>資料容量</th>
                      <th>預估可釋放容量</th>
                      <th>狀態／操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.items.map(r => (
                      <tr key={r.type + r.id}>
                        <td>
                          <input
                            type="checkbox"
                            aria-label={'選取 ' + r.id}
                            checked={selection.has(key(r))}
                            onChange={e => selection.toggle(key(r), e.target.checked)}
                          />
                        </td>
                        <td>
                          {typeNames[r.type]}
                          <br />
                          {String(r.summary.model || r.summary.kind || r.summary.name || '未記錄')}
                          <small className="break">{r.id}</small>
                          <details>
                            <summary>資源明細</summary>
                            <Fields value={r.summary} />
                            <CapacityDetails value={r.capacity} />
                          </details>
                        </td>
                        <td>
                          {when(r.moved)}
                          <br />
                          {r.actor && r.actor !== 'local_operator' ? r.actor : '未記錄'}
                        </td>
                        <td>
                          {bytes(r.capacity.file_bytes)}
                          <small>{capacityNames[r.capacity.status] || r.capacity.status}</small>
                        </td>
                        <td>
                          {bytes(r.capacity.estimated_release_bytes)}
                          <small>估計值；提交前重新檢查</small>
                        </td>
                        <td>
                          {stateNames[r.state] || r.state}
                          <div className="actions">
                            <TrashAction
                              targets={[{type: r.type, id: r.id}]}
                              action="restore"
                              disabled={!r.can_restore}
                              onDone={state.refresh}
                            />
                            <TrashAction
                              targets={[{type: r.type, id: r.id}]}
                              action="purge"
                              disabled={!r.can_purge}
                              onDone={state.refresh}
                            />
                            {r.operation && (
                              <button className="secondary" onClick={() => setOperation(r.operation!)}>
                                操作紀錄
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </section>
      <OperationHistory onOpen={setOperation} />
      {operation && (
        <Dialog title="操作結果與恢復" onClose={() => setOperation('')}>
          <OperationResult id={operation} onChanged={state.refresh} />
        </Dialog>
      )}
    </>
  );
}

type Chain = {
  target: string;
  revision: string | null;
  nodes: Array<{index: number; artifact: string; updated?: string; current: boolean}>;
};
export function ReferenceManager() {
  const state = useData('/references');
  const [preview, setPreview] = useState<{id: string; affected: unknown[]; confirmation: string} | null>(null),
    [text, setText] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  return (
    <section className="panel">
      <h2>歷史回復引用</h2>
      <p>解除歷史節點會改變可回復的版本，不切換目前模型，也不會自動移至垃圾桶。</p>
      {error && <p role="alert">{error}</p>}
      {state.error ? (
        <Empty>{state.error}</Empty>
      ) : (
        ((state.data as Chain[]) || []).map(c => (
          <section key={c.target}>
            <h3>{c.target === 'line' ? 'LINE' : '本地模擬'}</h3>
            {!c.nodes.length ? (
              <Empty>未設定引用</Empty>
            ) : (
              <ol>
                {c.nodes.map(n => (
                  <li key={n.index}>
                    <span className="break">
                      {n.current ? '目前使用' : '歷史節點 ' + n.index}：{n.artifact}
                    </span>{' '}
                    · {when(n.updated)}{' '}
                    {!n.current && (
                      <button
                        className="secondary"
                        onClick={async () => {
                          setError('');
                          setText('');
                          try {
                            setPreview(
                              await api('/references/' + c.target + '/preview', 'POST', {
                                revision: c.revision,
                                indices: [n.index],
                              })
                            );
                          } catch (e) {
                            setError((e as Error).message);
                          }
                        }}
                      >
                        預覽解除此引用
                      </button>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>
        ))
      )}
      {preview && (
        <Dialog title="確認解除歷史回復引用" onClose={() => setPreview(null)}>
          <p>解除後無法再透過此節點回復。其他歷史節點保留；目前模型不變。</p>
          <Fields value={preview.affected} />
          <label className="field">
            請輸入「解除回復引用」
            <input value={text} onChange={e => setText(e.target.value)} />
          </label>
          {error && <p role="alert">{error}</p>}
          <button
            type="button"
            disabled={busy || text !== preview.confirmation}
            onClick={async () => {
              setBusy(true);
              try {
                await api('/references/commit', 'POST', {preview_id: preview.id, confirmation: text});
                setPreview(null);
                state.refresh();
                changed();
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            確認解除
          </button>
        </Dialog>
      )}
    </section>
  );
}

const actionNames: Record<string, string> = {move: '移至垃圾桶', restore: '還原', purge: '永久刪除'};
function OperationHistory({onOpen}: {onOpen: (id: string) => void}) {
  const [page, setPage] = useState(1),
    [type, setType] = useState(''),
    [action, setAction] = useState(''),
    [confirming, setConfirming] = useState(false);
  const filter = new URLSearchParams({type, action}).toString();
  const state = useData('/trash/operation-history?page=' + page + '&' + filter, 4000);
  const d = state.data;
  const selection = useSelection(filter);
  return (
    <section className="panel">
      <h2>管理操作紀錄</h2>
      <p>項目刪除後仍可查看逐項結果；未完成操作可在明細中重新檢查。</p>
      <div className="form-grid">
        <label className="field">
          資源類型
          <select
            value={type}
            onChange={e => {
              setType(e.target.value);
              setPage(1);
            }}
          >
            <option value="">全部</option>
            {Object.entries(typeNames).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          動作
          <select
            value={action}
            onChange={e => {
              setAction(e.target.value);
              setPage(1);
            }}
          >
            <option value="">全部</option>
            {Object.entries(actionNames).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="toolbar selection-bar">
        <SelectionStatus selection={selection} total={d?.total || 0} />
        <button
          type="button"
          className="secondary"
          disabled={!selection.selected.length}
          onClick={() => setConfirming(true)}
        >
          永久刪除選取紀錄
        </button>
      </div>
      {state.error ? (
        <Empty>{state.error}</Empty>
      ) : !d ? (
        <Empty>載入操作…</Empty>
      ) : (
        <>
          <Pager page={d.page} total={d.total} size={d.size} onPage={setPage} />
          {!d.items.length ? (
            <Empty>{type || action ? '沒有符合篩選條件的操作。' : '尚無管理操作'}</Empty>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>
                      <SelectAllBox
                        selection={selection}
                        total={d.total}
                        label="選取全部符合條件的操作紀錄"
                        fetchAll={() => api('/trash/operation-history/ids?' + filter)}
                      />
                    </th>
                    <th>時間／操作 ID</th>
                    <th>動作</th>
                    <th>資源類型</th>
                    <th>狀態</th>
                    <th>操作者</th>
                    <th>明細</th>
                  </tr>
                </thead>
                <tbody>
                  {d.items.map((o: any) => (
                    <tr key={o.id}>
                      <td>
                        <input
                          type="checkbox"
                          aria-label={'選取操作 ' + o.id}
                          checked={selection.has(o.id)}
                          onChange={e => selection.toggle(o.id, e.target.checked)}
                        />
                      </td>
                      <td>
                        {when(o.created)}
                        <small className="break">{o.id}</small>
                      </td>
                      <td>{actionNames[o.action] || o.action}</td>
                      <td>{(o.types || []).map((t: string) => typeNames[t] || t).join('、') || '—'}</td>
                      <td>{stateNames[o.state] || o.state}</td>
                      <td>{o.actor && o.actor !== 'local_operator' ? o.actor : '未記錄'}</td>
                      <td>
                        <button className="secondary" onClick={() => onOpen(o.id)}>
                          查看操作結果
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      {confirming && (
        <Dialog title="永久刪除操作紀錄" onClose={() => setConfirming(false)}>
          <RecordDelete
            ids={selection.selected}
            onDone={() => {
              selection.clear();
              setConfirming(false);
              state.refresh();
            }}
          />
        </Dialog>
      )}
    </section>
  );
}

function RecordDelete({ids, onDone}: {ids: string[]; onDone: () => void}) {
  const [preview, setPreview] = useState<any>(null),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    api('/trash/operation-history/delete', 'POST', {ids})
      .then(setPreview)
      .catch(e => setError((e as Error).message));
  }, []);
  if (error && !preview) return <p role="alert">{error}</p>;
  if (!preview) return <Empty>檢查可刪除的紀錄…</Empty>;
  return (
    <>
      <p>
        永久刪除 {preview.deletable}{' '}
        筆管理操作紀錄？只刪除紀錄本身，不影響垃圾桶項目、模型或工作；刪除後無法再查看這些操作的逐項結果。
      </p>
      {!!preview.blocked.length && (
        <details open>
          <summary>{preview.blocked.length} 筆不可刪除（將略過）</summary>
          {preview.blocked.map((b: any) => (
            <p key={b.id} className="break">
              <small>{b.id}</small>：{b.reason}
            </p>
          ))}
        </details>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <div className="actions">
        <button
          type="button"
          className="danger"
          disabled={busy || !preview.deletable}
          onClick={async () => {
            setBusy(true);
            setError('');
            try {
              await api('/trash/operation-history/delete', 'POST', {ids, execute: true});
              changed();
              onDone();
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          永久刪除 {preview.deletable} 筆紀錄
        </button>
      </div>
    </>
  );
}

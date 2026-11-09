import {ImportPanel, ExternalImport} from '../imports/ImportPanel';
import {Dialog} from '../../shared/dialog';
import {SourceNewButton, FlagPills, ThumbMarks, FlagNotes, SpotCheckButton} from './quality';
import {DeletePhotos} from './delete';
import {ReviewHistory} from '../../shared/readable';
import React, {useEffect, useRef, useState} from 'react';
import {api, useData, useHash, route, names, when, Empty, operatorName, DisplayName} from '../../shared/ui';

type Obj = Record<string, any>;
const AREA: Obj = {
  title: '照片分類',
  desc: '給 EfficientNet、DINOv2 等整張照片分類模型使用。岡山高醫照片已依檔名自動分類，可在此修正。',
  labels: [
    ['normal', '正常'],
    ['stage1', '第一期'],
    ['stage2', '第二期'],
    ['positive_unstaged', '陽性・分期未知'],
    ['unknown', '未確認'],
  ],
};
const VIEWS: [string, string][] = [
  ['pending', '待處理'],
  ['confirmed', '已完成'],
  ['excluded', '排除'],
  ['all', '全部'],
];
const STATE_NAMES: Obj = {pending: '待處理', confirmed: '已完成', excluded: '排除'};
const SOURCE_NAMES: Obj = {gangshan: '岡山高醫', line: 'LINE', other: '其他'};
// Upper row: photo source (show-all last). Lower row: processing state. 'all' stays reachable by URL only.
const SOURCE_TABS: [string, string][] = [
  ['gangshan', '岡山高醫'],
  ['line', 'LINE'],
  ['other', '其他'],
  ['', '顯示全部'],
];
const STATE_TABS = VIEWS.filter(([k]) => k !== 'all');
// Label filter options follow the list: pending/excluded lists have no confirmed label to filter by,
// and completed lists never contain the 'not yet decided' value.
const UNDECIDED = ['unknown'];
const labelOptions = (view: string) =>
  view === 'pending' || view === 'excluded'
    ? []
    : AREA.labels.filter(([k]: any) => view === 'all' || !UNDECIDED.includes(k));
/** Research-intake facts for a LINE photo (prediction is reference only, never a label). */
function LineIntakeInfo({ident}: {ident: string}) {
  const info = useData('/intake/by-image/' + ident, 0, undefined, {enabled: ident.startsWith('line_')});
  const d = info.data;
  if (!ident.startsWith('line_')) return null;
  if (info.error) return <p className="callout">LINE 收件資訊無法取得：{info.error}</p>;
  if (!d) return null;
  const p = d.prediction || {};
  return (
    <div className="callout info line-intake">
      <b>LINE 上傳{d.simulated ? '（模擬）' : ''}</b>
      <span>
        收件 {new Date(d.received_at * 1000).toLocaleString()}・同意書 {d.version}
      </span>
      <span>
        收件時模型預測：
        {p.status
          ? (
              {
                suspected: '疑似陽性',
                not_detected: '未達門檻',
                quality_rejected: '品質不足',
                needs_review: '需人工確認',
              } as Obj
            )[p.status] || p.status
          : '無'}
        （僅供參考，不作為標籤）
      </span>
      <a href="#intake">查看研究收件紀錄</a>
    </div>
  );
}
const labelName = (value: string) => Object.fromEntries(AREA.labels)[value] || value;
const typing = (t: EventTarget | null) =>
  t instanceof Element &&
  (['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName) ||
    (t as HTMLElement).isContentEditable ||
    !!t.closest('svg,[role=radiogroup]'));
// Single-key shortcuts are ignored only while typing into a field.
function plainTyping(t: EventTarget | null) {
  return (
    t instanceof Element &&
    (['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName) || (t as HTMLElement).isContentEditable)
  );
}
/** A2: editor shortcuts. Keys are matched case-insensitively; Ctrl+Enter saves as done. */
function useKeys(map: Record<string, () => void>, deps: any[]) {
  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if (document.querySelector('dialog[open]')) return;
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        if (map['ctrl+enter']) {
          e.preventDefault();
          map['ctrl+enter']();
        }
        return;
      }
      if (plainTyping(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;
      const fn = map[e.key.toLowerCase()];
      if (fn) {
        e.preventDefault();
        fn();
      }
    };
    addEventListener('keydown', f);
    return () => removeEventListener('keydown', f);
  }, deps);
}
const SHORTCUTS: Obj = {
  common: [
    ['← / →', '上一張／下一張照片'],
    ['Ctrl + Enter', '儲存並完成'],
    ['?', '開啟這份說明'],
    ['/', '全域搜尋'],
  ],
  cls: [
    ['1', '正常'],
    ['2', '第一期'],
    ['3', '第二期'],
    ['4', '陽性・分期未知'],
  ],
};
function ShortcutHelp() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if (e.key === '?' && !plainTyping(e.target) && !document.querySelector('dialog[open]')) {
        e.preventDefault();
        setOpen(true);
      }
    };
    addEventListener('keydown', f);
    return () => removeEventListener('keydown', f);
  }, []);
  return (
    <>
      <button
        type="button"
        className="secondary icon-btn"
        title="快捷鍵（?）"
        aria-label="快捷鍵說明"
        aria-keyshortcuts="?"
        onClick={() => setOpen(true)}
      >
        ⌨
      </button>
      {open && (
        <Dialog title="快捷鍵" onClose={() => setOpen(false)}>
          <div className="table-wrap">
            <table className="shortcuts">
              <tbody>
                {[...SHORTCUTS.cls, ...SHORTCUTS.common].map(([k, v]: string[]) => (
                  <tr key={k}>
                    <th>
                      <kbd>{k}</kbd>
                    </th>
                    <td>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="muted">在輸入欄位中打字時，單鍵快捷鍵不會作用。</p>
        </Dialog>
      )}
    </>
  );
}

function useOperator() {
  const [name, setName] = useState(operatorName());
  useEffect(() => {
    const f = () => setName(operatorName());
    addEventListener('storage', f);
    addEventListener('focus', f);
    return () => {
      removeEventListener('storage', f);
      removeEventListener('focus', f);
    };
  }, []);
  return name;
}

function Progress({progress}: {progress: Obj | undefined}) {
  if (!progress) return null;
  const usable = progress.total - progress.excluded;
  const pct = progress.ratio == null ? 0 : Math.round(progress.ratio * 100);
  return (
    <div className="area-progress" role="group" aria-label="完成進度">
      <div
        className="bar"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={usable}
        aria-valuenow={progress.confirmed}
      >
        <span style={{width: pct + '%'}} />
      </div>
      <small>
        已完成 {progress.confirmed} / {usable} 張（{progress.ratio == null ? '—' : pct + '%'}）
        {progress.excluded ? ` · 另有 ${progress.excluded} 張排除` : ''}
      </small>
    </div>
  );
}

function IndexBadge({index, onRecheck}: {index: Obj | undefined; onRecheck: () => void}) {
  if (!index) return null;
  const state =
    ({ready: '已檢查', checking: '檢查中', pending: '待檢查', stale: '待更新', failed: '檢查失敗'} as Obj)[
      index.state
    ] || index.state;
  return (
    <span
      className={'status-pill ' + index.state}
      title={'完整性檢查：' + state + (index.checked_at ? ' · ' + when(index.checked_at) : '')}
    >
      <span className="dot" aria-hidden="true" />
      {state}
      {index.state === 'checking' && index.total != null ? ` ${index.processed ?? 0}/${index.total}` : ''}
      {index.state === 'ready' && index.checked_at
        ? ' · ' +
          new Date(index.checked_at * 1000).toLocaleTimeString('zh-TW', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          })
        : ''}
      <button className="plain" onClick={onRecheck} aria-label="重新檢查完整性">
        ↻
      </button>
    </span>
  );
}

function Reasons({tasks}: {tasks: Obj | null | undefined}) {
  if (!tasks) return <p className="muted">訓練資格待背景檢查完成。</p>;
  return (
    <ul className="eligibility">
      {Object.entries(tasks).map(([k, v]: any) => (
        <li key={k} className={v.eligible ? 'ok' : 'no'}>
          <b>{names[k] || k}</b>
          {v.eligible ? '：可用於訓練' : '：' + v.reasons.join('；')}
        </li>
      ))}
    </ul>
  );
}

function SaveBar({busy, disabled, reason, setReason, onSave, operator, hint}: any) {
  return (
    <div className="save-bar">
      <label className="field">
        審查原因（必填）
        <input maxLength={1000} value={reason} onChange={e => setReason(e.target.value)} />
      </label>
      {!operator && <p className="muted">請先在「設定與維護」填寫操作者名稱。</p>}
      {hint && <p className="muted">{hint}</p>}
      <div className="actions">
        <button
          disabled={busy || disabled || !reason.trim() || !operator}
          aria-keyshortcuts="Control+Enter"
          title="Ctrl + Enter"
          onClick={() => onSave('approve')}
        >
          儲存並完成
        </button>
        <button
          className="secondary"
          disabled={busy || !reason.trim() || !operator}
          onClick={() => onSave('needs_changes')}
        >
          存為待處理
        </button>
        <button
          className="secondary danger"
          disabled={busy || !reason.trim() || !operator}
          onClick={() => onSave('exclude')}
        >
          此區排除
        </button>
      </div>
    </div>
  );
}

function EditorHead({d, ident}: any) {
  return (
    <header className="image-title">
      <div className="title-row">
        <h2 className="break">
          <DisplayName row={d} fallback={ident} />
        </h2>
        <div className="title-tools">
          <ShortcutHelp />
        </div>
      </div>
      <div className="meta-row">
        <span className={'state-badge ' + d.state}>{STATE_NAMES[d.state]}</span>
        {d.rule_applied && <span className="source-badge">依岡山高醫檔名自動分類（授權規則）</span>}
        <small>image_id：{ident}</small>
      </div>
      {d.aliases?.length > 0 && (
        <details>
          <summary>來源檔名（{d.aliases.length}）</summary>
          <ul>
            {d.aliases.map((a: any, i: number) => (
              <li key={i}>
                {a.relative_path}
                <small> · {a.source}</small>
              </li>
            ))}
          </ul>
        </details>
      )}
      {d.name_variants?.length > 0 && (
        <p className="muted">
          另有同名但內容不同的版本：{d.name_variants.join('、')}（兩個版本都保留，可能是同一次拍攝）。
        </p>
      )}
    </header>
  );
}

function History({d}: {d: Obj}) {
  return (
    <details>
      <summary>此區的證據與審查歷程</summary>
      {d.evidence?.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>時間</th>
                <th>來源</th>
                <th>內容</th>
              </tr>
            </thead>
            <tbody>
              {d.evidence.map((e: any, i: number) => (
                <tr key={i}>
                  <td>{when(e.at)}</td>
                  <td>
                    {(
                      {
                        rule_prefill: '檔名預填',
                        rule_applied: '授權檔名規則',
                        review: '人工審查',
                        intake_review: '收件確認',
                      } as Obj
                    )[e.method] || e.method}
                    {e.rule_version ? ' · ' + e.rule_version : ''}
                  </td>
                  <td>
                    {[e.value && names[e.value], e.stage && names[e.stage], e.detection && names[e.detection]]
                      .filter(Boolean)
                      .join(' · ') || '—'}
                    {e.relative_path ? ' · ' + e.relative_path : ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {d.history.length ? (
        d.history.map((h: any, i: number) => (
          <section key={i}>
            <h4>
              {when(h.after?.updated_at)} ·{' '}
              {h.source === 'authorized_filename_rule' ? '授權檔名規則' : h.after?.reviewer || '未記錄'}
            </h4>
            <p>{h.after?.reason}</p>
            <ReviewHistory history={h} />
          </section>
        ))
      ) : (
        <Empty>此區尚無審查歷程</Empty>
      )}
    </details>
  );
}

function ClassifyEditor({ident, act, onSaved}: any) {
  const info = useData('/data/' + ident + '/annotation?area=cls');
  const operator = useOperator();
  const [stage, setStage] = useState('unknown'),
    [quality, setQuality] = useState(''),
    [subject, setSubject] = useState(''),
    [reason, setReason] = useState('人工確認分類'),
    [busy, setBusy] = useState(false),
    [failed, setFailed] = useState(false);
  useEffect(() => {
    if (info.data) {
      const l = info.data.labels;
      setStage(l.stage || 'unknown');
      setQuality(l.quality || '');
      setSubject(info.data.row.subject_id || '');
      setFailed(false);
    }
  }, [info.data?.revision]);
  const keys = useRef<Record<string, () => void>>({});
  useKeys(
    {
      '1': () => setStage('normal'),
      '2': () => setStage('stage1'),
      '3': () => setStage('stage2'),
      '4': () => setStage('positive_unstaged'),
      'ctrl+enter': () => keys.current.save?.(),
    },
    []
  );
  if (info.error)
    return (
      <p role="alert">
        {info.error} <button onClick={() => info.refresh()}>重試</button>
      </p>
    );
  if (!info.data) return <Empty>載入照片與分類…</Empty>;
  const d = info.data;
  const hint = d.stage_suggestion;
  const binary =
    ({normal: 'negative', stage1: 'positive', stage2: 'positive', positive_unstaged: 'positive'} as Obj)[stage] ||
    'unknown';
  const save = (decision: string) => {
    setBusy(true);
    act(
      () =>
        api('/data/' + ident + '/classification', 'PUT', {
          decision,
          label: binary,
          stage,
          quality,
          reviewer: operator,
          reason,
          revision: d.revision,
          subject_id: subject,
          clear_subject: !!d.row.subject_id && !subject,
          category: '',
        }).then(r => {
          onSaved(decision === 'approve');
          return r;
        }),
      '分類已儲存'
    ).finally(() => setBusy(false));
  };
  keys.current = {
    save: () => {
      if (!busy && !failed && stage !== 'unknown' && reason.trim() && operator) save('approve');
    },
  };
  return (
    <>
      <EditorHead d={d} ident={ident} />
      <LineIntakeInfo ident={ident} />
      <FlagNotes
        ident={ident}
        onChanged={() => {
          info.refresh();
          onSaved(false);
        }}
      />
      <figure className="preview">
        {failed ? (
          <Empty>圖片無法載入，請重新整理或檢查原檔。</Empty>
        ) : (
          <img
            src={'/api/v1/data/' + ident + '/image'}
            alt="待分類照片（已校正方向，不顯示任何框）"
            onError={() => setFailed(true)}
          />
        )}
      </figure>
      {hint && !hint.confirmed && (
        <div className={'callout ' + (hint.conflict ? 'warning' : '')}>
          <b>檔名預填：{names[hint.value]}</b>（{hint.rule}）
          {hint.conflict ? (
            <ul>
              {hint.conflict_reasons.map((r: string, i: number) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          ) : (
            <button className="secondary" onClick={() => setStage(hint.value)}>
              套用預填
            </button>
          )}
        </div>
      )}
      <div className="segmented" role="radiogroup" aria-label="分類標籤">
        {AREA.labels.map(([k, v]: any, i: number) => (
          <button
            key={k}
            role="radio"
            aria-checked={stage === k}
            aria-keyshortcuts={i < 4 ? String(i + 1) : undefined}
            className={stage === k ? 'active' : ''}
            onClick={() => setStage(k)}
          >
            {v}
            {i < 4 && <kbd aria-hidden="true">{i + 1}</kbd>}
          </button>
        ))}
      </div>
      <div className="form-grid compact">
        <label className="field">
          影像品質
          <select value={quality} onChange={e => setQuality(e.target.value)}>
            <option value="">未評估</option>
            <option value="acceptable">可用</option>
            <option value="limited">勉強可用</option>
            <option value="unusable">不可用</option>
          </select>
        </label>
        <label className="field">
          個案研究編號（化名）
          <input value={subject} maxLength={100} onChange={e => setSubject(e.target.value)} />
          <small>不可由檔名代碼推定，請勿填姓名。</small>
        </label>
      </div>
      <SaveBar
        busy={busy}
        operator={operator}
        reason={reason}
        setReason={setReason}
        onSave={save}
        disabled={failed || stage === 'unknown'}
        hint={
          stage === 'unknown'
            ? '選擇分類後才能完成；也可存為待處理。'
            : '二分類由分期推得：正常＝陰性，第一／二期與陽性未分期＝陽性。'
        }
      />
      <Reasons tasks={d.tasks} />
      <History d={d} />
    </>
  );
}

function StageBatch({items, act, onDone}: any) {
  const candidates = items.filter(
    (r: any) =>
      r.stage_suggestion && !r.stage_suggestion.conflict && !r.stage_suggestion.confirmed && r.state !== 'excluded'
  );
  const operator = useOperator();
  const [picked, setPicked] = useState<string[]>([]),
    [reason, setReason] = useState('確認檔名預填分期'),
    [result, setResult] = useState<any[] | null>(null);
  if (!candidates.length) return null;
  return (
    <details className="slot-note">
      <summary>批次確認檔名預填（本頁 {candidates.length} 張，非岡山高醫來源）</summary>
      <div className="batch-list">
        {candidates.map((r: any) => (
          <label className="check" key={r.image_id}>
            <input
              type="checkbox"
              checked={picked.includes(r.image_id)}
              onChange={e =>
                setPicked(e.target.checked ? [...picked, r.image_id] : picked.filter(x => x !== r.image_id))
              }
            />
            <DisplayName row={r} /> → {names[r.stage_suggestion.value]}
          </label>
        ))}
      </div>
      <div className="toolbar">
        <button className="secondary" onClick={() => setPicked(candidates.map((r: any) => r.image_id))}>
          全選本頁
        </button>
        <input aria-label="確認原因" value={reason} onChange={e => setReason(e.target.value)} />
        <button
          disabled={!picked.length || !reason.trim() || !operator}
          onClick={() =>
            act(async () => {
              const map = Object.fromEntries(candidates.map((r: any) => [r.image_id, r]));
              const res = await api('/data/stage-confirm', 'POST', {
                reviewer: operator,
                reason,
                items: picked.map(id => ({
                  image_id: id,
                  revision: map[id].revision,
                  stage: map[id].stage_suggestion.value,
                  approve: true,
                })),
              });
              setResult(res.results);
              setPicked([]);
              onDone();
              return res;
            }, '批次確認已處理')
          }
        >
          確認 {picked.length} 張
        </button>
      </div>
      {result && (
        <ul>
          {result.map((r: any) => (
            <li key={r.image_id}>
              {r.image_id}：{r.ok ? '已確認' : '未處理 — ' + r.error}
            </li>
          ))}
        </ul>
      )}
    </details>
  );
}

export function DataReview({act}: any) {
  const {params} = useHash();
  const area = 'cls';
  const view = VIEWS.some(v => v[0] === params.get('view')) ? params.get('view')! : 'pending';
  const label = params.get('label') || '',
    source = params.get('source') || '',
    reviewer = params.get('reviewer') || '',
    page = Math.max(1, Number(params.get('page')) || 1),
    selected = params.get('image') || '';
  const flag = ['duplicate', 'quality'].includes(params.get('flag') || '') ? params.get('flag')! : '';
  const query = new URLSearchParams({area, view, page: String(page), size: '24'});
  if (label) query.set('label', label);
  if (source) query.set('source', source);
  if (reviewer) query.set('reviewer', reviewer);
  if (flag) query.set('flag', flag);
  const rows = useData(
    '/data-area?' + query.toString(),
    1000,
    d => d?.index?.state === 'ready' || d?.index?.state === 'failed'
  );
  const go = (next: Obj, keep = true) => {
    const base: Obj = keep ? {area, view, label, source, reviewer, flag, page: String(page), image: selected} : {area};
    const merged = {...base, ...next};
    route('data', Object.fromEntries(Object.entries(merged).filter(([, v]) => v !== '' && v != null)) as Obj);
  };
  const items: Obj[] = rows.data?.items || [];
  const select = (id: string) => go({image: id});
  const [picking, setPicking] = useState(false),
    [picked, setPicked] = useState<string[]>([]),
    [asking, setAsking] = useState(false);
  const stopPicking = () => {
    setPicking(false);
    setPicked([]);
    setAsking(false);
  };
  const step = (delta: number) => {
    if (!items.length) return;
    const i = items.findIndex(x => x.image_id === selected);
    const next = items[Math.min(items.length - 1, Math.max(0, i < 0 ? 0 : i + delta))];
    if (next) select(next.image_id);
  };
  const nextPending = () => {
    const i = items.findIndex(x => x.image_id === selected);
    const after = [...items.slice(i + 1), ...items.slice(0, Math.max(0, i))].find(
      x => x.state === 'pending' && x.image_id !== selected
    );
    if (after) select(after.image_id);
    else if (rows.data && page * rows.data.size < rows.data.total) go({page: String(page + 1), image: ''});
    else go({image: ''});
  };
  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if (typing(e.target) || e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        step(1);
      }
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        step(-1);
      }
    };
    addEventListener('keydown', f);
    return () => removeEventListener('keydown', f);
  });
  const counts = rows.data?.counts || {};
  const labelCounts = rows.data?.labels || {};
  const options = labelOptions(view);
  useEffect(() => {
    if (label && !options.some(([k]: any) => k === label)) go({label: '', page: '1'});
  }, [view, label]);
  const sources = rows.data?.sources || {},
    pendingBySource = rows.data?.source_pending || {};
  const snapshotTask = 'stage_classification';
  return (
    <div className="area-page">
      {picking && (
        <p className="notice picking-bar">
          點選要刪除的照片，已選 {picked.length} 張。
          <button type="button" className="secondary danger" disabled={!picked.length} onClick={() => setAsking(true)}>
            移到垃圾桶…
          </button>
        </p>
      )}
      {asking && (
        <DeletePhotos
          ids={picked}
          onClose={() => setAsking(false)}
          onDone={() => {
            stopPicking();
            go({image: ''});
            rows.refresh();
          }}
        />
      )}
      <section className="panel area-header">
        <div className="area-title">
          <h2>{AREA.title}</h2>
          <p>{AREA.desc}</p>
        </div>
        <Progress progress={rows.data?.progress} />
        <div className="source-tabs" role="tablist" aria-label="照片來源">
          {SOURCE_TABS.map(([k, v]) => (
            <button
              key={k || 'all'}
              role="tab"
              aria-selected={source === k}
              className={source === k ? 'active' : ''}
              onClick={() => go({source: k, page: '1', image: ''})}
            >
              {v}
              <span>{k ? (sources[k] ?? 0) : Object.values(sources).reduce((a: number, b: any) => a + b, 0)}</span>
              {k === 'line' && pendingBySource.line > 0 && <em>待處理 {pendingBySource.line}</em>}
            </button>
          ))}
        </div>
        <div className="state-row">
          <div className="view-pills" role="tablist" aria-label="處理狀態">
            {STATE_TABS.map(([k, v]) => (
              <button
                key={k}
                role="tab"
                aria-selected={view === k && !flag}
                className={view === k && !flag ? 'active' : ''}
                onClick={() => go({view: k, flag: '', page: '1', image: ''})}
              >
                {v}
                <span>{counts[k] ?? '…'}</span>
              </button>
            ))}
          </div>
          <FlagPills
            counts={rows.data?.flag_counts}
            flag={flag}
            onFlag={f => go({flag: f, view: f ? 'all' : 'pending', page: '1', image: ''})}
          />
        </div>
      </section>
      <section className="panel toolbar-card">
        <div className="filters">
          {options.length > 0 && (
            <label className="field">
              分類標籤
              <select value={label} onChange={e => go({label: e.target.value, page: '1', image: ''})}>
                <option value="">全部</option>
                {options.map(([k, v]: any) => (
                  <option key={k} value={k}>
                    {v}（{labelCounts[k] ?? 0}）
                  </option>
                ))}
              </select>
            </label>
          )}
          <label className="field">
            最近審查者
            <select value={reviewer} onChange={e => go({reviewer: e.target.value, page: '1', image: ''})}>
              <option value="">全部</option>
              <option value="__unknown__">未記錄</option>
              {(rows.data?.reviewers || []).map((r: string) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="tool-actions">
          <IndexBadge
            index={rows.data?.index}
            onRecheck={() => api('/data-index/rebuild', 'POST').then(rows.refresh)}
          />
          <SourceNewButton
            autoOpen={params.get('source_new') === '1'}
            onClosed={() => {
              if (params.get('source_new')) go({source_new: ''});
              rows.refresh();
            }}
          />
          <SpotCheckButton
            autoOpen={params.get('spot') === '1'}
            onClosed={() => {
              if (params.get('spot')) go({spot: ''});
              rows.refresh();
            }}
          />
          <ImportPanel kind="photos" />
          <ExternalImport />
          <a className="button secondary" href={'#models?tab=snapshots&task=' + snapshotTask}>
            建立訓練快照 →
          </a>
          <button type="button" className="secondary" onClick={() => (picking ? stopPicking() : setPicking(true))}>
            {picking ? '取消選取' : '刪除照片'}
          </button>
        </div>
      </section>
      <section className="panel list-card">
        <div className="list-head">
          <span>
            共 <b>{rows.data?.total ?? '…'}</b> 筆{label ? ' · ' + labelName(label) : ''}
            {source ? ' · ' + SOURCE_NAMES[source] : ''}
            {flag ? ' · ' + (flag === 'duplicate' ? '疑似重複' : '品質待確認') : ''}
          </span>
          <div className="pager">
            <button
              className="secondary"
              disabled={!rows.data?.items?.some((x: Obj) => x.state === 'pending')}
              onClick={nextPending}
            >
              下一張待處理
            </button>
            <span>
              第 {page} / {Math.max(1, Math.ceil((rows.data?.total || 0) / 24))} 頁
            </span>
            <button
              className="secondary icon-btn"
              aria-label="上一頁"
              disabled={page <= 1}
              onClick={() => go({page: String(page - 1), image: ''})}
            >
              ‹
            </button>
            <button
              className="secondary icon-btn"
              aria-label="下一頁"
              disabled={!rows.data || page * 24 >= rows.data.total}
              onClick={() => go({page: String(page + 1), image: ''})}
            >
              ›
            </button>
          </div>
        </div>
        <StageBatch items={items} act={act} onDone={rows.refresh} />
        {rows.error && (
          <p role="alert">
            <span>{rows.error}</span> <button onClick={() => rows.refresh()}>重試</button>
          </p>
        )}
        {!rows.data ? (
          !rows.error && <Empty>載入資料…</Empty>
        ) : (
          <div className="review-layout">
            <section className="gallery" aria-label="照片清單">
              {items.map(r => (
                <button
                  data-image-id={r.image_id}
                  className={
                    'thumb ' +
                    (picking
                      ? picked.includes(r.image_id)
                        ? 'picked'
                        : ''
                      : selected === r.image_id
                        ? 'selected'
                        : '')
                  }
                  aria-pressed={picking ? picked.includes(r.image_id) : undefined}
                  key={r.image_id}
                  onClick={() =>
                    picking
                      ? setPicked(
                          picked.includes(r.image_id) ? picked.filter(x => x !== r.image_id) : [...picked, r.image_id]
                        )
                      : select(r.image_id)
                  }
                >
                  <img
                    loading="lazy"
                    src={'/api/v1/data/' + r.image_id + '/image?thumbnail=true'}
                    width={160}
                    height={120}
                    alt={r.display_name || r.image_id}
                  />
                  <div>
                    <b>
                      <DisplayName row={r} />
                    </b>
                    <span className="card-meta">
                      <span className={'state-badge ' + r.state}>{STATE_NAMES[r.state]}</span>
                      <span className="chip">{labelName(r.labels.stage)}</span>
                      <span className="chip source">{SOURCE_NAMES[r.source]}</span>
                      <ThumbMarks flags={r.flags} />
                    </span>
                  </div>
                </button>
              ))}
              {!items.length && (
                <Empty>
                  {flag
                    ? '目前沒有需要確認的照片。'
                    : view === 'pending'
                      ? '此區目前沒有待處理的照片。'
                      : '這個分類目前沒有符合條件的照片。'}
                </Empty>
              )}
            </section>
            <section className="panel editor-panel">
              {selected ? (
                <ClassifyEditor
                  key={'cls' + selected}
                  ident={selected}
                  act={act}
                  onSaved={(done: boolean) => {
                    rows.refresh();
                    if (done) nextPending();
                  }}
                />
              ) : (
                <Empty>選擇左側照片開始分類。可用鍵盤 ← → 切換照片。</Empty>
              )}
            </section>
          </div>
        )}
      </section>
    </div>
  );
}

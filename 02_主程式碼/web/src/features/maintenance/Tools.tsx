import React, {useEffect, useState} from 'react';
import {api, useData, useHash, when, Empty} from '../../shared/ui';
import {Dialog} from '../../shared/dialog';
import {TrashAction, bytes, Target} from '../trash/Trash';
import {useSelection, SelectionStatus} from '../../shared/selection';
import {showToast} from '../../shared/toast';
type Obj = Record<string, any>;

/** Scroll to ?section=… once the panel exists (links from 下一步 and notifications). */
export function useSectionScroll() {
  const {params} = useHash();
  const section = params.get('section') || '';
  useEffect(() => {
    if (!section) return;
    const t = setTimeout(() => document.getElementById('section-' + section)?.scrollIntoView({block: 'start'}), 150);
    return () => clearTimeout(t);
  }, [section]);
}

function usePrefs() {
  const state = useData('/settings/workbench');
  const [error, setError] = useState('');
  const save = async (section: string, value: Obj, message: string) => {
    setError('');
    try {
      await api('/settings/workbench', 'PUT', {...state.data, [section]: {...state.data[section], ...value}});
      await state.refresh();
      showToast({text: message});
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return {data: state.data as Obj | null, load: state.error, save, error};
}

/** D1: daily automatic backup, manual backup and restore. */
export function BackupPanel() {
  const state = useData('/backups', 30000);
  const prefs = usePrefs();
  const d = state.data;
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [restore, setRestore] = useState<Obj | null>(null),
    [dir, setDir] = useState<string | null>(null);
  const now = async () => {
    setBusy(true);
    setError('');
    try {
      const b = await api('/backups', 'POST');
      showToast({text: `已備份 ${b.file_count} 個檔案`});
      await state.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const b = prefs.data?.backup;
  return (
    <section className="panel" id="section-backup">
      <div className="panel-head">
        <h2>每日自動備份</h2>
        <button type="button" className="secondary" disabled={busy} onClick={now}>
          {busy ? '備份中…' : '立即備份'}
        </button>
      </div>
      <p>
        工作台開著時每天備份一次：資料清單、標註、審查紀錄、標籤證據、來源名稱、資料庫與設定，存在
        04_備份/工作台紀錄。照片與模型權重請用下方的「完整備份」複製到外接硬碟。
      </p>
      {state.error ? (
        <p role="alert">{state.error}</p>
      ) : !d ? (
        <Empty>讀取備份…</Empty>
      ) : (
        <>
          <p className={d.due && d.enabled ? 'callout warning' : 'muted'}>
            {!d.enabled
              ? '自動備份已關閉。'
              : d.last_auto
                ? `上次自動備份：${when(d.last_auto)}`
                : '尚未有自動備份；工作台開啟約 1 分鐘後會自動執行。'}
            　位置：<span className="break">{d.directory}</span>
          </p>
          {!d.items.length ? (
            <Empty>目前沒有備份。</Empty>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>時間</th>
                    <th>種類</th>
                    <th className="num">檔案</th>
                    <th className="num">大小</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {d.items.slice(0, 20).map((x: Obj) => (
                    <tr key={x.name}>
                      <td>
                        {when(x.created)}
                        <small className="break">{x.name}</small>
                      </td>
                      <td>{x.kind_name}</td>
                      <td className="num">{x.file_count ?? '—'}</td>
                      <td className="num">{bytes(x.bytes)}</td>
                      <td>
                        {!x.damaged && (
                          <button type="button" className="secondary" onClick={() => setRestore(x)}>
                            還原…
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {b && (
        <details>
          <summary>備份設定</summary>
          <div className="form-grid">
            <label className="check">
              <input
                type="checkbox"
                checked={b.enabled}
                onChange={e =>
                  prefs.save(
                    'backup',
                    {enabled: e.target.checked},
                    e.target.checked ? '已開啟每日自動備份' : '已關閉每日自動備份'
                  )
                }
              />
              每天自動備份
            </label>
            <label className="field">
              每種備份保留份數
              <input
                type="number"
                min={1}
                max={90}
                value={b.keep}
                onChange={e =>
                  prefs.save('backup', {keep: Math.max(1, Math.min(90, +e.target.value || 14))}, '保留份數已更新')
                }
              />
            </label>
            <label className="field">
              備份位置（建議外接硬碟；留空使用預設）
              <input
                value={dir ?? b.directory}
                placeholder="例如 E:\靜脈炎備份"
                onChange={e => setDir(e.target.value)}
              />
            </label>
            <div>
              <button
                type="button"
                className="secondary"
                disabled={dir === null || dir === b.directory}
                onClick={async () => {
                  await prefs.save('backup', {directory: (dir || '').trim()}, '備份位置已更新');
                  setDir(null);
                  state.refresh();
                }}
              >
                儲存位置
              </button>
            </div>
          </div>
          {prefs.error && <p role="alert">{prefs.error}</p>}
        </details>
      )}
      {restore && (
        <Dialog title="從備份還原" onClose={() => setRestore(null)}>
          <RestoreConfirm
            item={restore}
            onDone={() => {
              setRestore(null);
              state.refresh();
            }}
          />
        </Dialog>
      )}
    </section>
  );
}

const FULL_ACTIONS: Obj = {backup: '完整備份', verify: '核對', restore: '還原'};

/** Full backup of photos, models and records to an external drive; old versions are kept for keep_days. */
export function FullBackupPanel() {
  const state = useData('/full-backups', 2000, d => d?.progress?.state !== 'running');
  const prefs = usePrefs();
  const d = state.data;
  const [error, setError] = useState(''),
    [dir, setDir] = useState<string | null>(null),
    [restore, setRestore] = useState<Obj | null>(null);
  const f = prefs.data?.full_backup;
  const p = d?.progress;
  const running = p?.state === 'running';
  const last = d?.status?.last_success;
  const start = async (path: string, message: string) => {
    setError('');
    try {
      await api(path, 'POST');
      showToast({text: message});
      await state.refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <section className="panel" id="section-full-backup">
      <div className="panel-head">
        <h2>完整備份</h2>
        <div className="actions">
          <button
            type="button"
            className="secondary"
            disabled={running || !d?.available || !d?.runs?.length}
            onClick={() => start('/full-backups/verify', '已開始核對完整備份')}
          >
            核對備份
          </button>
          <button
            type="button"
            disabled={running || !f?.directory}
            onClick={() => start('/full-backups', '已開始完整備份')}
          >
            {running && p.action === 'backup' ? '備份中…' : '立即完整備份'}
          </button>
        </div>
      </div>
      <p>
        把照片與標註、模型權重、原始資料封存、05_匯入區（含岡山高醫原始照片）、資料庫、設定與每日備份複製到外接硬碟。每次只複製新增或變更的檔案；被修改或刪除的檔案，舊版本保留{' '}
        {f?.keep_days ?? 30} 天，這段期間內的每一次備份都能還原。
      </p>
      {state.error ? (
        <p role="alert">{state.error}</p>
      ) : !d ? (
        <Empty>讀取完整備份…</Empty>
      ) : (
        <>
          {!f?.directory ? (
            <p className="callout warning">尚未設定完整備份位置。請接上外接硬碟，在下方「完整備份設定」填入資料夾。</p>
          ) : !d.available ? (
            <p className="callout warning">
              {d.reason}：<span className="break">{f.directory}</span>
            </p>
          ) : (
            <p className={d.due ? 'callout warning' : 'muted'}>
              {last ? `上次完整備份：${when(last)}` : '尚未做過完整備份。'}
              {d.due && last ? `（已超過 ${f.remind_days} 天）` : ''}　位置：
              <span className="break">{f.directory}</span>
            </p>
          )}
          {d.same_drive && (
            <p className="callout warning">備份位置和資料在同一顆硬碟：硬碟故障時兩者會一起損失，建議改用外接硬碟。</p>
          )}
          {d.last_import && (!last || d.last_import > last) && (
            <p className="callout info">{when(d.last_import)} 匯入了新照片，尚未做完整備份。</p>
          )}
          {running && (
            <p role="status">
              {FULL_ACTIONS[p.action]}中：{p.phase}
              {p.files_total ? `（${p.files_done ?? 0}／${p.files_total} 個檔案）` : ''}
            </p>
          )}
          {p?.state === 'failed' && (
            <p role="alert" className="callout warning">
              {FULL_ACTIONS[p.action]}失敗：{p.error}
            </p>
          )}
          {p?.state === 'done' && p.action === 'verify' && (
            <p role="status" className={p.result.ok ? 'muted' : 'callout warning'}>
              核對 {p.result.checked} 個檔案：
              {p.result.ok
                ? '全部相符。'
                : `缺少 ${p.result.missing_count} 個、內容不符 ${p.result.damaged_count} 個。`}
            </p>
          )}
          {p?.state === 'done' && p.action === 'restore' && (
            <p role="status">
              已還原 {p.result.restored} 個檔案到 <span className="break">{p.result.output}</span>
              {p.result.missing_count ? `；${p.result.missing_count} 個檔案找不到` : ''}
              。核對無誤後，請依 04_備份/README.md 的步驟手動替換。
            </p>
          )}
          {d.runs.length > 0 && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>備份時間</th>
                    <th className="num">新增或更新</th>
                    <th className="num">移入舊版本</th>
                    <th className="num">檔案總數</th>
                    <th className="num">總大小</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {d.runs.map((r: Obj) => (
                    <tr key={r.run}>
                      <td>
                        {when(r.finished)}
                        <small className="mono">{r.run}</small>
                      </td>
                      <td className="num">{r.copied}</td>
                      <td className="num">{r.moved_to_old}</td>
                      <td className="num">{r.total_files}</td>
                      <td className="num">{bytes(r.total_bytes)}</td>
                      <td>
                        <button type="button" className="secondary" disabled={running} onClick={() => setRestore(r)}>
                          還原…
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
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {f && (
        <details open={!f.directory}>
          <summary>完整備份設定</summary>
          <div className="form-grid">
            <label className="field">
              備份位置（外接硬碟上的資料夾）
              <input
                value={dir ?? f.directory}
                placeholder="例如 E:\靜脈炎完整備份"
                onChange={e => setDir(e.target.value)}
              />
            </label>
            <div>
              <button
                type="button"
                className="secondary"
                disabled={dir === null || dir === f.directory}
                onClick={async () => {
                  await prefs.save('full_backup', {directory: (dir || '').trim()}, '完整備份位置已更新');
                  setDir(null);
                  state.refresh();
                }}
              >
                儲存位置
              </button>
            </div>
            <NumberSetting
              label="舊版本保留天數"
              props={{min: 7, max: 365, step: 1}}
              value={f.keep_days}
              onSave={v => prefs.save('full_backup', {keep_days: Math.round(v)}, '保留天數已更新')}
            />
            <NumberSetting
              label="超過幾天沒做完整備份就提醒"
              props={{min: 1, max: 90, step: 1}}
              value={f.remind_days}
              onSave={v => prefs.save('full_backup', {remind_days: Math.round(v)}, '提醒天數已更新')}
            />
            <label className="check">
              <input
                type="checkbox"
                checked={f.include_runs}
                onChange={e =>
                  prefs.save(
                    'full_backup',
                    {include_runs: e.target.checked},
                    e.target.checked ? '完整備份將包含訓練輸出' : '完整備份不含訓練輸出'
                  )
                }
              />
              也備份訓練與評估輸出（runs，約數 GB，可重新產生）
            </label>
          </div>
          {prefs.error && <p role="alert">{prefs.error}</p>}
        </details>
      )}
      {restore && (
        <Dialog title="還原完整備份" onClose={() => setRestore(null)}>
          <FullRestore
            item={restore}
            onDone={() => {
              setRestore(null);
              state.refresh();
            }}
          />
        </Dialog>
      )}
    </section>
  );
}

function FullRestore({item, onDone}: {item: Obj; onDone: () => void}) {
  const [output, setOutput] = useState(''),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  return (
    <>
      <p>
        把 {when(item.finished)} 的備份內容組回當時的狀態，寫到一個<strong>空資料夾</strong>
        。正式資料不會被覆蓋；核對無誤後，再依 04_備份/README.md 的步驟手動替換。
      </p>
      <label className="field">
        還原到（完整路徑，必須是空資料夾或尚不存在）
        <input value={output} placeholder="例如 E:\還原_20261017" onChange={e => setOutput(e.target.value)} />
      </label>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <div className="actions">
        <button
          type="button"
          disabled={busy || !output.trim()}
          onClick={async () => {
            setBusy(true);
            setError('');
            try {
              await api('/full-backups/' + encodeURIComponent(item.run) + '/restore-to', 'POST', {
                output: output.trim(),
              });
              showToast({text: '已開始還原，完成後會通知'});
              onDone();
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? '開始還原…' : '還原到這個資料夾'}
        </button>
      </div>
    </>
  );
}

function RestoreConfirm({item, onDone}: {item: Obj; onDone: () => void}) {
  const [database, setDatabase] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  return (
    <>
      <p>
        把資料清單、標註、審查紀錄與標籤證據還原到 {when(item.created)}{' '}
        的狀態？備份之後新增的審查紀錄會移除；還原前會先自動備份目前狀態，可再還原回來。
      </p>
      <ul>
        <li>照片檔案不會刪除；備份後才匯入的照片會從資料清單移除。</li>
        <li>模型引用（本地模擬、LINE 使用中的模型）與設定檔不會被改動。</li>
      </ul>
      {item.database && (
        <label className="check">
          <input type="checkbox" checked={database} onChange={e => setDatabase(e.target.checked)} />
          同時還原資料庫（工作紀錄、垃圾桶與研究收件紀錄也會回到當時狀態）
        </label>
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
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError('');
            try {
              const r = await api('/backups/' + encodeURIComponent(item.name) + '/restore', 'POST', {
                include_database: database,
              });
              showToast({text: `已還原 ${r.restored} 個檔案；還原前狀態另存為備份`});
              dispatchEvent(new CustomEvent('workbench-resources-changed', {detail: {scopes: ['*']}}));
              onDone();
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? '還原中…' : '還原此備份'}
        </button>
      </div>
    </>
  );
}

/** D5: disk usage by area; old outputs go to the trash (never deleted here). */
export function DiskUsagePanel() {
  const state = useData('/disk-usage', 2000, d => d?.state !== 'calculating');
  const d = state.data;
  const recalc = async () => {
    try {
      await api('/disk-usage?refresh=true');
    } catch {
      /* shown by the next poll */
    }
    await state.refresh();
  };
  const selection = useSelection('disk');
  const items: Obj[] = d?.cleanable || [];
  const max = Math.max(1, ...(d?.areas || []).map((a: Obj) => a.bytes));
  const targets: Target[] = selection.selected.map(k => {
    const i = k.indexOf(':');
    return {type: k.slice(0, i) as Target['type'], id: k.slice(i + 1)};
  });
  const chosen = items.filter(i => selection.has(i.type + ':' + i.id)).reduce((n, i) => n + i.bytes, 0);
  return (
    <section className="panel" id="section-disk">
      <div className="panel-head">
        <h2>磁碟用量</h2>
        <button type="button" className="secondary" disabled={d?.state === 'calculating'} onClick={recalc}>
          重新計算
        </button>
      </div>
      {!d ? (
        <Empty>計算磁碟用量…</Empty>
      ) : d.state === 'failed' ? (
        <p role="alert">{d.error}</p>
      ) : (
        <>
          {d.state === 'calculating' && <p className="muted">計算中…{d.areas ? '（以下為上次結果）' : ''}</p>}
          {d.disk && (
            <p>
              磁碟可用 {bytes(d.disk.free)}／共 {bytes(d.disk.total)}
              {d.calculated_at ? `・計算於 ${when(d.calculated_at)}` : ''}
            </p>
          )}
          {d.areas && (
            <table className="usage">
              <tbody>
                {d.areas.map((a: Obj) => (
                  <tr key={a.key}>
                    <th>
                      {a.name}
                      <small>{a.note}</small>
                    </th>
                    <td>
                      <div className="meter" role="img" aria-label={a.name + ' ' + bytes(a.bytes)}>
                        <span style={{width: Math.max(1, Math.round((a.bytes / max) * 100)) + '%'}} />
                      </div>
                    </td>
                    <td className="num">{bytes(a.bytes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {d.cleanable && (
            <>
              <h3>可清理的舊輸出</h3>
              <p>
                失敗、取消或中斷的工作、模擬預測暫存與完成超過 30 天的工作輸出。清理一律先移至垃圾桶；本地模擬或 LINE
                使用中的模型、執行中的工作會被擋下並說明原因。
              </p>
              {!items.length ? (
                <Empty>目前沒有可清理的舊輸出。</Empty>
              ) : (
                <>
                  <div className="toolbar selection-bar">
                    <SelectionStatus selection={selection} total={items.length} />
                    {selection.selected.length > 0 && <span className="muted">約 {bytes(chosen)}</span>}
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => selection.setSelected(items.map(i => i.type + ':' + i.id))}
                    >
                      全選
                    </button>
                    <TrashAction
                      targets={targets}
                      onDone={() => {
                        selection.clear();
                        void recalc();
                      }}
                    />
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th></th>
                          <th>項目</th>
                          <th>原因</th>
                          <th>更新時間</th>
                          <th className="num">大小</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map(i => (
                          <tr key={i.type + i.id}>
                            <td>
                              <input
                                type="checkbox"
                                aria-label={'選取 ' + i.name}
                                checked={selection.has(i.type + ':' + i.id)}
                                onChange={e => selection.toggle(i.type + ':' + i.id, e.target.checked)}
                              />
                            </td>
                            <td>
                              {i.name}
                              <small className="mono">{i.id.slice(0, 12)}</small>
                            </td>
                            <td>{i.reason}</td>
                            <td>{when(i.updated)}</td>
                            <td className="num">{bytes(i.bytes)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}

function NumberSetting({
  label,
  props,
  value,
  onSave,
}: {
  label: string;
  props: Obj;
  value: number;
  onSave: (v: number) => void;
}) {
  const [text, setText] = useState(String(value));
  useEffect(() => setText(String(value)), [value]);
  const commit = () => {
    const v = Number(text);
    if (text.trim() !== '' && Number.isFinite(v) && v !== value) onSave(v);
    else setText(String(value));
  };
  return (
    <label className="field">
      {label}
      <input
        type="number"
        {...props}
        value={text}
        onChange={e => setText(e.target.value)}
        onBlur={commit}
        onKeyDown={e => {
          if (e.key === 'Enter') commit();
        }}
      />
    </label>
  );
}

/** D3 / A5 preferences. */
export function PreferencePanels() {
  const prefs = usePrefs();
  const p = prefs.data;
  const [permission, setPermission] = useState(
    typeof Notification === 'undefined' ? 'unsupported' : Notification.permission
  );
  if (prefs.load)
    return (
      <section className="panel">
        <p role="alert">{prefs.load}</p>
      </section>
    );
  if (!p) return null;
  const num = (section: string, key: string, label: string, props: Obj, pct = false) => (
    <NumberSetting
      key={section + key}
      label={label}
      props={props}
      value={pct ? Math.round(p[section][key] * 1000) / 10 : p[section][key]}
      onSave={v => prefs.save(section, {[key]: pct ? v / 100 : v}, '設定已儲存')}
    />
  );
  return (
    <>
      <section className="panel" id="section-notifications">
        <h2>通知設定</h2>
        <p>訓練、評估完成或失敗、垃圾桶操作完成、每日備份結果與岡山高醫新照片，都會出現在頁首的「通知」。</p>
        <label className="check">
          <input
            type="checkbox"
            checked={p.notifications.system}
            onChange={async e => {
              const on = e.target.checked;
              if (on && typeof Notification !== 'undefined' && Notification.permission === 'default') {
                const r = await Notification.requestPermission();
                setPermission(r);
              }
              prefs.save('notifications', {system: on}, on ? '已開啟 Windows 系統通知' : '已關閉 Windows 系統通知');
            }}
          />
          同時顯示 Windows 系統通知（工作台分頁開著時）
        </label>
        {p.notifications.system && permission !== 'granted' && (
          <p className="callout warning">
            {permission === 'unsupported'
              ? '這個瀏覽器不支援系統通知。'
              : '瀏覽器尚未允許通知；請在網址列左側的網站設定中允許「通知」。'}
          </p>
        )}
      </section>
      <section className="panel" id="section-spot">
        <h2>抽查設定</h2>
        <p>岡山高醫照片依檔名自動分類；每批自動分類的照片會抽出一部分，由人工逐張確認「正確」或「有誤」。</p>
        <label className="check">
          <input
            type="checkbox"
            checked={!!prefs.data?.spot_check?.enabled}
            onChange={e =>
              prefs.save('spot_check', {enabled: e.target.checked}, e.target.checked ? '已開啟抽查' : '已關閉抽查')
            }
          />
          開啟抽查（預設關閉：標籤已由醫師核准）
        </label>
        <div className="form-grid">
          {num('spot_check', 'ratio', '抽查比例（%）', {min: 1, max: 100, step: 1}, true)}
        </div>
        {prefs.error && <p role="alert">{prefs.error}</p>}
      </section>
    </>
  );
}

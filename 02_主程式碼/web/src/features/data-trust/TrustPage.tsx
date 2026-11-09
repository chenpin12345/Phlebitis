import {useState} from 'react';
import {api, operatorName, route, useData, useHash} from '../../shared/ui';
import {Empty, Field, Heading} from '../../shared/app-ui';

type Obj = Record<string, any>;

const TABS = [
  ['source', '來源檢查'],
  ['inventory', '資料盤點'],
  ['prospective', '前瞻名單'],
];

function Score({label, value}: {label: string; value: Obj | null}) {
  return (
    <tr>
      <th scope="row">{label}</th>
      <td>{value ? value.balanced_accuracy.toFixed(2) : '資料不足'}</td>
      <td>{value?.shuffled_labels != null ? value.shuffled_labels.toFixed(2) : '—'}</td>
    </tr>
  );
}

function SourceCheck({data, refresh}: {data: Obj; refresh: () => void}) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const audit = data.audit;
  const run = async () => {
    setBusy(true);
    setError('');
    try {
      await api('/data-trust/source-check', 'POST');
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>來源檢查</h2>
        <button type="button" className="secondary" disabled={busy} onClick={run}>
          {busy ? '檢查中…' : '重新檢查'}
        </button>
      </div>
      <p>檢查標籤是否能被照片的來源或檔案資訊解釋。分數接近打亂標籤的數值，代表分不出來。</p>
      {error && <p role="alert">{error}</p>}
      {!audit ? (
        <Empty>還沒有檢查紀錄，請按「重新檢查」。</Empty>
      ) : (
        <>
          {!data.fresh && <p className="notice">資料在上次檢查後有變更，結果可能已過期。</p>}
          {audit.findings.map((text: string) => (
            <p key={text} className={audit.level === 'high' || audit.level === 'watch' ? 'notice error' : 'notice'}>
              {text}
            </p>
          ))}
          {audit.level === 'none' && <p className="notice">沒有發現來源與標籤的明顯關聯。</p>}
          <h3>來源與類別</h3>
          <table>
            <thead>
              <tr>
                <th scope="col">來源</th>
                <th scope="col">正常</th>
                <th scope="col">陽性</th>
                <th scope="col">待處理</th>
                <th scope="col">已排除</th>
              </tr>
            </thead>
            <tbody>
              {audit.crosstab.map((row: Obj) => (
                <tr key={row.source}>
                  <th scope="row">{row.name}</th>
                  <td>{row.normal}</td>
                  <td>{row.positive}</td>
                  <td>{row.pending}</td>
                  <td>{row.excluded}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h3>照片尺寸與類別</h3>
          <table>
            <thead>
              <tr>
                <th scope="col">尺寸（像素）</th>
                <th scope="col">正常</th>
                <th scope="col">陽性</th>
              </tr>
            </thead>
            <tbody>
              {audit.sizes.map((row: Obj) => (
                <tr key={row.size}>
                  <th scope="row">{row.size}</th>
                  <td>{row.normal}</td>
                  <td>{row.positive}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h3>分開類別的能力（平衡準確率）</h3>
          <table>
            <thead>
              <tr>
                <th scope="col">檢查</th>
                <th scope="col">實際標籤</th>
                <th scope="col">打亂標籤</th>
              </tr>
            </thead>
            <tbody>
              <Score label="只看檔案資訊分類別" value={audit.label_from_metadata} />
              <Score label="只看色彩分類別" value={audit.label_from_colour} />
              <Score label="只看檔案資訊認來源" value={audit.source_from_metadata} />
              <Score label="只看色彩認來源" value={audit.source_from_colour} />
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}

function Inventory({data}: {data: Obj}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>資料盤點</h2>
        <a className="button secondary" href="/api/v1/data-card.md" download="資料卡.md">
          匯出資料卡
        </a>
      </div>
      {data.warnings.map((text: string) => (
        <p key={text} className="notice error">
          {text}
        </p>
      ))}
      <dl>
        <dt>已核准照片</dt>
        <dd>{data.approved} 張</dd>
        <dt>病人數</dt>
        <dd>{data.patients} 位</dd>
        <dt>正常照片</dt>
        <dd>
          {data.normal_photos} 張，來自 {data.normal_patients} 位病人
        </dd>
        <dt>沒有分組</dt>
        <dd>{data.unassigned} 張</dd>
      </dl>
      {data.rows.length === 0 ? (
        <Empty>還沒有已分組的病人。</Empty>
      ) : (
        <table>
          <thead>
            <tr>
              <th scope="col">病人</th>
              <th scope="col">照片</th>
              <th scope="col">正常</th>
              <th scope="col">第一期</th>
              <th scope="col">第二期</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row: Obj) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                <td>{row.photos}</td>
                <td>{row.normal}</td>
                <td>{row.stage1}</td>
                <td>{row.stage2}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

const ROLES: Obj = {development: '開發', test: '測試', calibration: '校準'};

/** #21, #22: decide what a new patient is for before any result exists. */
function Prospective() {
  const state = useData('/prospective');
  const [name, setName] = useState(''),
    [codes, setCodes] = useState(''),
    [role, setRole] = useState('test'),
    [asking, setAsking] = useState(''),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const run = async (work: () => Promise<unknown>) => {
    setBusy(true);
    setError('');
    try {
      await work();
      await state.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const seal = () =>
    run(async () => {
      await api('/prospective', 'POST', {name, codes: codes.split('\n'), role, reviewer: operatorName()});
      setName('');
      setCodes('');
    });
  const items: Obj[] = state.data?.items || [];
  return (
    <section className="panel">
      <h2>前瞻名單</h2>
      <p>
        新病人要先決定角色再看結果。測試與校準的病人不會進訓練快照；名單封存後只能解鎖一次。系統只存雜湊，不存病歷號。
      </p>
      {error && <p role="alert">{error}</p>}
      {items.length === 0 ? (
        <Empty>還沒有前瞻名單。</Empty>
      ) : (
        <table>
          <thead>
            <tr>
              <th scope="col">名單</th>
              <th scope="col">角色</th>
              <th scope="col">病人</th>
              <th scope="col">狀態</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id}>
                <th scope="row">{item.name}</th>
                <td>{item.role_name}</td>
                <td>{item.count} 位</td>
                <td>
                  {item.unlocked_at ? (
                    '已解鎖'
                  ) : asking === item.id ? (
                    <button
                      type="button"
                      className="secondary danger"
                      disabled={busy}
                      onClick={() =>
                        run(() => api('/prospective/' + item.id + '/unlock', 'POST', {reviewer: operatorName()}))
                      }
                    >
                      確認解鎖（只能一次）
                    </button>
                  ) : (
                    <button type="button" className="secondary" onClick={() => setAsking(item.id)}>
                      解鎖
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <h3>新增名單</h3>
      <div className="form-grid">
        <Field label="名單名稱">
          <input value={name} maxLength={60} onChange={e => setName(e.target.value)} />
        </Field>
        <Field label="角色">
          <select value={role} onChange={e => setRole(e.target.value)}>
            {Object.entries(ROLES).map(([key, label]) => (
              <option key={key} value={key}>
                {label as string}
              </option>
            ))}
          </select>
        </Field>
        <Field label="病歷號（一行一位）">
          <textarea rows={4} value={codes} onChange={e => setCodes(e.target.value)} />
        </Field>
      </div>
      <div className="actions">
        <button type="button" disabled={busy || !name.trim() || !codes.trim()} onClick={seal}>
          封存名單
        </button>
      </div>
    </section>
  );
}

export function TrustPage() {
  const {params} = useHash();
  const tab = params.get('tab') || 'source';
  const state = useData('/data-trust');
  const d = state.data as Obj | null;
  return (
    <>
      <Heading title="資料可信度">訓練前確認照片的來源與病人分組。</Heading>
      <div className="tabs main-tabs">
        {TABS.map(([key, name]) => (
          <button key={key} className={tab === key ? 'active' : ''} onClick={() => route('trust', {tab: key})}>
            {name}
          </button>
        ))}
      </div>
      {tab === 'prospective' ? (
        <Prospective />
      ) : state.error ? (
        <p role="alert">{state.error}</p>
      ) : !d ? (
        <Empty>讀取資料…</Empty>
      ) : tab === 'inventory' ? (
        <Inventory data={d.inventory} />
      ) : (
        <SourceCheck data={d} refresh={state.refresh} />
      )}
    </>
  );
}

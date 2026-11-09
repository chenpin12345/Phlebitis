import {ImportPanel} from '../imports/ImportPanel';
import {useState, useEffect, useRef} from 'react';
import {
  PolicyFields,
  ArtifactPolicy,
  ParameterOptions,
  FineTuneSource,
  PARAM_HINTS,
  IndependentEvaluation,
} from './extras';
type Obj = Record<string, any>;
import {api, useData, Pager, useHash, route} from '../../shared/ui';
import {JobDetail, ArtifactDetails, TrainingCurves} from './monitor';
import {TrashAction} from '../trash/Trash';
import {useSelection, SelectAllBox, SelectionStatus} from '../../shared/selection';
import {Comparison} from './comparison';
import {SnapshotCreator, ExperimentPreview} from '../../shared/readable';
import {Badge, Empty, Field, download, Heading} from '../../shared/app-ui';
import {names} from '../../shared/ui';
import {SnapshotDiff, ModelCard} from './evaluation';
import {LineActions, ShadowPanel, ScrollToArtifact} from './release';
const MODEL_LIST = [
  'efficientnet_b0',
  'dinov2_small',
  'dinov2_base',
  'baseline_majority',
  'baseline_colour',
  'baseline_dino_knn',
];
const TASK_MODELS: Obj = {
  binary_classification: MODEL_LIST,
  stage_classification: MODEL_LIST,
};
const PURPOSES: Obj = {independent_test: '流程煙霧測試（不用於訓練）', holdout_training: '訓練用：已保留獨立測試集'};
const snapshotFits = (s: Obj, task: string) => s.task === task;
export function ModelsPage({act}: any) {
  const {params} = useHash();
  const validTabs = ['catalog', 'snapshots', 'new', 'jobs', 'compare', 'registry', 'curves'];
  const tab = validTabs.includes(params.get('tab') || '') ? params.get('tab')! : 'catalog';
  const kind = params.get('kind') || '',
    jobPage = Math.max(1, Number(params.get('job_page')) || 1);
  const setKind = (kind: string) => route('models', {tab: 'jobs', kind, job_page: '1'});
  const models = useData('/models', 0, undefined, {enabled: tab === 'catalog'}),
    snapshots = useData('/snapshot-options', 0, undefined, {enabled: ['snapshots', 'new', 'registry'].includes(tab)}),
    artifacts = useData('/artifacts', 5000, d => d.every((a: Obj) => !a.active_evaluation), {
      enabled: tab === 'registry',
    }),
    jobsList = useData(
      '/jobs-query?kind=' + encodeURIComponent(kind) + '&page=' + jobPage,
      3000,
      d => d?.active_count === 0,
      {enabled: tab === 'jobs'}
    );
  const setTab = (tab: string) => route('models', {tab});
  const [model, setModel] = useState('efficientnet_b0');
  const job = params.get('job') || '';
  const setJob = (job: string) => route('models', {tab: 'jobs', job});
  return (
    <>
      <Heading title="模型與實驗">
        建立快照、訓練、評估與版本管理。準確率只在完成評估後顯示，新模型不會自動用於 LINE。
      </Heading>
      <ImportPanel kind="models" />
      <div className="tabs main-tabs">
        {[
          ['catalog', '模型目錄'],
          ['snapshots', '新增快照'],
          ['new', '建立實驗'],
          ['jobs', '工作監測'],
          ['compare', '評估比較'],
          ['registry', '模型版本'],
          ['curves', '訓練曲線'],
        ].map(([k, v]) => (
          <button key={k} className={tab === k ? 'active' : ''} onClick={() => setTab(k)}>
            {v}
          </button>
        ))}
      </div>
      {tab === 'catalog' && !models.data && <Empty>載入模型目錄…</Empty>}
      {tab === 'catalog' && models.data?.length === 0 && <Empty>尚無模型方案，請檢查環境設定。</Empty>}
      {tab === 'catalog' && (
        <div className="model-grid">
          {(models.data || []).map((m: Obj) => (
            <section className="panel model-card" key={m.id}>
              <small className="meta">整圖分類</small>
              <h2>{m.name}</h2>
              <Badge value={m.state} />
              <p>{'以整張照片分類：二分類（正常／陽性）或分期（正常／第一期／第二期）；不提供病灶位置、不需框。'}</p>
              <dl>
                <dt>所需標註</dt>
                <dd>{m.labels}</dd>
                <dt>方案準確率</dt>
                <dd>依每個訓練產物的評估結果顯示</dd>
                <dt>總參數 / 可訓練參數（最近實驗）</dt>
                <dd>
                  {m.measured
                    ? `${m.measured.total_parameters?.toLocaleString()} / ${m.measured.trainable_parameters?.toLocaleString()}`
                    : '尚未實測'}
                </dd>
                <dt>續訓</dt>
                <dd>{m.resume ? '完成 checkpoint 後可續訓' : '分類器重新擬合，不提供 checkpoint 續訓'}</dd>
              </dl>
              <details>
                <summary>預訓練來源</summary>
                <p className="break">{m.source}</p>
              </details>
              <div className="actions">
                {
                  <button
                    className="secondary"
                    onClick={() => act(() => api('/models/' + m.id + '/prepare', 'POST'), '權重準備工作已排入佇列')}
                  >
                    {m.state === 'ready' ? '核對官方權重來源' : '準備官方權重'}
                  </button>
                }
                <button
                  onClick={() => {
                    setModel(m.id);
                    setTab('new');
                  }}
                >
                  建立實驗 →
                </button>
              </div>
            </section>
          ))}
        </div>
      )}
      {tab === 'new' && (
        <NewExperiment
          model={model}
          setModel={setModel}
          snapshots={snapshots.data || []}
          refreshSnapshots={snapshots.refresh}
          act={act}
          onJob={(id: string) => {
            setJob(id);
          }}
        />
      )}
      {tab === 'jobs' && (
        <div className="two-col jobs-layout">
          <JobsList jobsList={jobsList} jobPage={jobPage} kind={kind} setKind={setKind} job={job} setJob={setJob} />
          <section className="panel">
            {job ? <JobDetail id={job} act={act} /> : <Empty>選擇工作查看進度、有效參數與紀錄。</Empty>}
          </section>
        </div>
      )}
      {tab === 'snapshots' && <SnapshotsTab snapshots={snapshots} act={act} />}
      {tab === 'curves' && <TrainingCurves />}
      {tab === 'compare' && <Comparison />}
      {tab === 'registry' && (
        <>
          <ShadowPanel />
          <ScrollToArtifact id={params.get('artifact') || ''} ready={!!artifacts.data} />
        </>
      )}
      {tab === 'registry' && (
        <div className="model-grid">
          {(artifacts.data || []).map((a: Obj) => {
            const r = a.reports?.filter((x: Obj) => x.applicable !== false && x.purpose !== 'independent_test').at(-1);
            return (
              <section
                className={'panel model-card-panel' + (params.get('artifact') === a.id ? ' highlighted' : '')}
                id={'artifact-' + a.id}
                key={a.id}
              >
                <small className="meta">
                  {a.model} · {names[a.task] || a.task} · {names[a.label_scheme] || a.label_scheme}
                </small>
                <h2 className="break">模型說明卡 · {a.id}</h2>
                {a.attention && (
                  <div className="callout warning">
                    <b>需重新評估或重訓</b>
                    <p>{a.attention.reason}</p>
                  </div>
                )}
                {a.extra?.source === 'external' && (
                  <div className="callout warning">
                    <b>外部訓練的模型</b>
                    <p>
                      {a.extra.note} 訓練資料：{a.extra.training_data}
                    </p>
                  </div>
                )}
                <div className="metric-big">{r?.metrics?.accuracy_display || '尚無可驗證準確率'}</div>
                <p>
                  {r
                    ? `驗證 fold ${r.fold} · ${r.demo_only ? '流程展示' : '正式'}`
                    : '待評估或評估失敗，請查看工作紀錄。'}
                </p>
                <ModelCard id={a.id} />
                <div className="actions">
                  <button
                    disabled={!r?.metrics?.complete}
                    onClick={() =>
                      act(
                        () => api('/artifacts/activate', 'POST', {artifact: a.id, target: 'local'}),
                        '已選為本地模擬模型'
                      )
                    }
                  >
                    用於本地模擬
                  </button>
                  <LineActions artifact={a} ready={!!r?.metrics?.complete} act={act} />
                  <button
                    className="secondary"
                    onClick={() =>
                      act(
                        () =>
                          api('/artifacts/' + a.id + '/evaluate', 'POST', {
                            dataset: a.extra?.dataset || snapshots.data?.[0]?.folds[0].dataset,
                            device: '0',
                          }),
                        '評估工作已排入佇列'
                      )
                    }
                  >
                    重新評估
                  </button>
                </div>
                <p>
                  評估狀態：
                  {
                    (
                      {
                        pending: '待評估',
                        evaluating: '評估中',
                        succeeded: '評估成功',
                        failed: '評估失敗',
                        not_applicable: '報告不適用',
                      } as Obj
                    )[a.evaluation_status]
                  }
                </p>
                <ArtifactPolicy artifact={a} act={act} api={api} />
                <IndependentEvaluation artifact={a} snapshots={snapshots.data || []} act={act} api={api} />
                <TrashAction targets={[{type: 'model', id: a.id}]} onDone={artifacts.refresh} />
                <ArtifactDetails id={a.id} />
              </section>
            );
          })}
        </div>
      )}
    </>
  );
}
const JOB_KINDS = [
  ['train', '訓練'],
  ['predict', '預測'],
  ['evaluate', '評估'],
  ['regression', '回歸測試'],
  ['prepare', '權重準備'],
];
function JobsList({jobsList, jobPage, kind, setKind, job, setJob}: any) {
  const selection = useSelection(kind);
  const items: Obj[] = jobsList.data?.items || [],
    total = jobsList.data?.total || 0;
  return (
    <section className="panel">
      <h2>工作紀錄</h2>
      {jobsList.error && (
        <p role="alert">
          {jobsList.error}
          <button onClick={() => jobsList.refresh()}>重試</button>
        </p>
      )}
      <Pager
        page={jobPage}
        total={total}
        size={30}
        onPage={(p: number) => route('models', {tab: 'jobs', kind, job_page: String(p)})}
      />
      <label className="field">
        工作類型
        <select value={kind} onChange={e => setKind(e.target.value)}>
          <option value="">全部</option>
          {JOB_KINDS.map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </label>
      <div className="selection-bar">
        <label className="check inline">
          <SelectAllBox
            selection={selection}
            total={total}
            label="選取全部符合條件的工作"
            fetchAll={() => api('/jobs-query/ids?kind=' + encodeURIComponent(kind))}
          />
          全選
        </label>
        <SelectionStatus selection={selection} total={total} />
        <TrashAction
          targets={selection.selected.map(id => ({type: 'job', id}))}
          onDone={() => {
            selection.clear();
            jobsList.refresh();
          }}
        />
      </div>
      {grouped(items).map((row: Obj) =>
        row.job ? (
          <JobRow key={row.job.id} j={row.job} selection={selection} job={job} setJob={setJob} />
        ) : (
          <FoldGroup key={row.group} row={row} selection={selection} job={job} setJob={setJob} />
        )
      )}
      {!items.length && <Empty>尚無工作，請先建立實驗。</Empty>}
      <p className="muted">執行中的工作無法移入垃圾桶；預覽時可一鍵略過。</p>
    </section>
  );
}
function JobRow({j, selection, job, setJob}: any) {
  return (
    <div className="job-row-wrap">
      <input
        type="checkbox"
        aria-label={'選取工作 ' + j.id}
        checked={selection.has(j.id)}
        onChange={e => selection.toggle(j.id, e.target.checked)}
      />
      <button className={'job-row ' + (job === j.id ? 'selected' : '')} onClick={() => setJob(j.id)}>
        <div>
          <b>
            {j.config.name ? j.config.name + ' · ' : ''}
            {j.config.model || j.kind}
          </b>
          <small>
            {j.id.slice(0, 12)} · {new Date(j.created * 1000).toLocaleString()}
          </small>
        </div>
        <Badge value={j.state} />
      </button>
    </div>
  );
}
/** B1: the jobs of one three-fold run are listed together and can be expanded. */
function grouped(items: Obj[]) {
  const rows: Obj[] = [];
  const seen: Record<string, Obj> = {};
  for (const j of items) {
    const g = j.config.cv_group;
    if (!g) {
      rows.push({job: j});
      continue;
    }
    if (!seen[g]) {
      seen[g] = {group: g, jobs: []};
      rows.push(seen[g]);
    }
    seen[g].jobs.push(j);
  }
  for (const r of rows)
    if (r.jobs)
      r.jobs.sort(
        (a: Obj, b: Obj) => a.created - b.created || (a.config.name || '').localeCompare(b.config.name || '')
      );
  return rows;
}
function FoldGroup({row, selection, job, setJob}: any) {
  const jobs: Obj[] = row.jobs;
  const done = jobs.filter(j => j.state === 'succeeded').length,
    failed = jobs.filter(j => ['failed', 'interrupted', 'cancelled'].includes(j.state)).length,
    running = jobs.find(j => ['running', 'cancelling'].includes(j.state));
  const first = jobs[0];
  const name = (first.config.name || '').replace(/ · fold \d+$/, '').replace(/^fold \d+$/, '');
  const state = failed ? 'failed' : done === jobs.length ? 'succeeded' : running ? 'running' : 'queued';
  return (
    <details className="fold-group" open={jobs.some(j => j.id === job)}>
      <summary>
        <span>
          <b>
            交叉驗證 · {name ? name + ' · ' : ''}
            {first.config.model}
          </b>
          <small>
            {jobs
              .map(
                (j, i) =>
                  `${i + 1}/${jobs.length} ${({succeeded: '完成', running: '執行中', queued: '等待資源', failed: '失敗', cancelled: '已取消', interrupted: '中斷', cancelling: '停止中'} as Obj)[j.state] || j.state}`
              )
              .join('・')}
          </small>
        </span>
        <span className="fold-progress">
          完成 {done}/{jobs.length}
          <Badge value={state} />
        </span>
      </summary>
      {jobs.map(j => (
        <JobRow key={j.id} j={j} selection={selection} job={job} setJob={setJob} />
      ))}
    </details>
  );
}
const SNAPSHOT_STATES: Obj = {withdrawn: '已撤回', superseded: '已被取代'};
const SNAPSHOT_REASONS: Obj = {
  'Human review changed labels, eligibility or grouping': '人工審查變更了標籤、可用資格或分組，需重新建立快照',
};
function SnapshotsTab({snapshots, act}: any) {
  const {params} = useHash();
  const task = TASK_MODELS[params.get('task') || ''] ? params.get('task') : '';
  const list: Obj[] = snapshots.data || [];
  const selection = useSelection('snapshots');
  const ids = list.map((s: Obj) => s.version);
  const [diff, setDiff] = useState<string[] | null>(null);
  return (
    <>
      <SnapshotCreator act={act} onCreated={snapshots.refresh} defaultTask={task || undefined} />
      <section className="panel">
        <h2>既有快照</h2>
        <p>
          建立實驗只會列出狀態為「有效」的快照；已被取代或撤回的快照保留供追溯，不需要時可勾選後移至垃圾桶。執行中訓練使用的快照不能移除。
        </p>
        <div className="toolbar selection-bar">
          <SelectionStatus selection={selection} total={ids.length} />
          <TrashAction
            targets={selection.selected.map(id => ({type: 'snapshot', id}))}
            onDone={() => {
              selection.clear();
              snapshots.refresh();
            }}
          />
        </div>
        {snapshots.error ? (
          <Empty>{snapshots.error}</Empty>
        ) : !snapshots.data ? (
          <Empty>載入快照…</Empty>
        ) : !list.length ? (
          <Empty>尚無快照。</Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>
                    <SelectAllBox
                      selection={selection}
                      total={ids.length}
                      label="選取全部快照"
                      fetchAll={async () => ({ids, total: ids.length, limit: ids.length})}
                    />
                  </th>
                  <th>名稱／版本</th>
                  <th>任務</th>
                  <th>各 fold（訓練／驗證）</th>
                  <th>狀態</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {list.map((s: Obj) => (
                  <tr key={s.version}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={'選取快照 ' + s.version}
                        checked={selection.has(s.version)}
                        onChange={e => selection.toggle(s.version, e.target.checked)}
                      />
                    </td>
                    <td className="break">
                      {s.name && <b>{s.name}</b>}
                      <div>{s.version}</div>
                      {s.purpose && <small>{PURPOSES[s.purpose] || s.purpose}</small>}
                      {s.demo_only && <small>流程展示</small>}
                    </td>
                    <td>{s.legacy ? '二分類／偵測（舊版）' : names[s.task] || s.task}</td>
                    <td>
                      {s.folds.map((f: Obj) => (
                        <div key={f.dataset}>
                          fold {f.fold}：{f.counts.train}／{f.counts.val}
                        </div>
                      ))}
                    </td>
                    <td>
                      {s.state ? (
                        <>
                          {SNAPSHOT_STATES[s.state] || s.state}
                          {s.state_reason && <small>{SNAPSHOT_REASONS[s.state_reason] || s.state_reason}</small>}
                        </>
                      ) : (
                        '有效'
                      )}
                    </td>
                    <td>
                      <div className="row-actions">
                        <select
                          aria-label={'與其他快照比較 ' + s.version}
                          className="compare-select"
                          value=""
                          onChange={e => {
                            if (e.target.value) setDiff([e.target.value, s.version]);
                          }}
                        >
                          <option value="">與…比較</option>
                          {list
                            .filter((o: Obj) => o.version !== s.version)
                            .map((o: Obj) => (
                              <option key={o.version} value={o.version}>
                                {o.name || o.version}
                              </option>
                            ))}
                        </select>
                        {!s.state && !s.legacy && !s.purpose && (
                          <a className="button secondary" href={'#models?tab=new&task=' + s.task}>
                            建立實驗 →
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      {diff && <SnapshotDiff a={diff[0]} b={diff[1]} onClose={() => setDiff(null)} />}
    </>
  );
}
export function NewExperiment({model, setModel, snapshots, refreshSnapshots, act, onJob}: any) {
  const {params: hashParams} = useHash();
  const requested = hashParams.get('task') || '';
  const [task, setTask] = useState(TASK_MODELS[requested] ? requested : 'binary_classification');
  useEffect(() => {
    if (TASK_MODELS[requested]) {
      setTask(requested);
      if (!TASK_MODELS[requested].includes(model)) setModel(TASK_MODELS[requested][0]);
    }
  }, [requested]);
  useEffect(() => {}, [model]);
  const [allFolds, setAllFolds] = useState(true),
    [dataset, setDataset] = useState(''),
    [epochs, setEpochs] = useState(30),
    [batch, setBatch] = useState(4),
    [device, setDevice] = useState('0'),
    [demo, setDemo] = useState(false),
    [control, setControl] = useState(false),
    [adjustment, setAdjustment] = useState('threshold'),
    [params, setParams] = useState<Obj>({}),
    [threshold, setThreshold] = useState(0.5),
    [seed, setSeed] = useState(42),
    [patience, setPatience] = useState(5),
    [compare, setCompare] = useState<string[]>([]),
    [policy, setPolicy] = useState<Obj>({
      quality_mode: 'advisory',
      blur_threshold: 30,
      dark_fraction: 0.85,
      bright_fraction: 0.85,
    });
  const templates = useData('/templates');
  const [templateName, setTemplateName] = useState('');
  const [expName, setExpName] = useState('');
  const [holdout, setHoldout] = useState(false);
  const [baseImport, setBaseImport] = useState('');
  const basePackages = useData('/imports/packages?purpose=base&model=' + encodeURIComponent(model));
  const [initial, setInitial] = useState('');
  const requestKeys = useRef<Record<string, string>>({});
  const submitting = useRef(false);
  const dino = model.startsWith('dinov2');
  const neural = model === 'efficientnet_b0';
  useEffect(() => {
    setParams({});
    setInitial('');
    setBaseImport('');
    setEpochs(20);
    setPatience(5);
  }, [model]);
  const fitting = snapshots.filter((s: Obj) => !s.purpose && snapshotFits(s, task));
  const usableSnapshots = fitting.filter((s: Obj) => !s.state);
  const hiddenSnapshots = fitting.length - usableSnapshots.length;
  useEffect(() => {
    if (dataset && !usableSnapshots.some((s: Obj) => s.folds.some((f: Obj) => f.dataset === dataset))) setDataset('');
  }, [snapshots, task]);
  const stageTask = task === 'stage_classification';
  const named = (suffix = '') => (expName.trim() ? {name: (expName.trim() + suffix).slice(0, 60)} : {});
  const adjusted = (p: Obj) => (['class_weight', 'both'].includes(adjustment) ? {...p, class_weight: 'balanced'} : p);
  const thresholdPolicy = !stageTask && ['threshold', 'both'].includes(adjustment) ? 'sensitivity_090' : 'fixed';
  const config = () => ({
    ...named(),
    model,
    task,
    dataset,
    device,
    demo,
    control: control ? 'shuffled_labels' : '',
    holdout,
    epochs,
    batch,
    seed,
    patience,
    imgsz: 224,
    parameters: adjusted(params),
    threshold_policy: thresholdPolicy,
    initial_artifact: initial || null,
    ...(baseImport ? {base_import: baseImport} : {}),
    inference: {...policy, threshold, imgsz: 224},
  });
  const change = (key: string, value: any) => setParams({...params, [key]: value});
  const fields = dino ? ['C', 'max_iter'] : neural ? ['learning_rate', 'weight_decay', 'rotation'] : [];
  const queueConfigs = () =>
    (compare.length ? compare : [model]).map(m =>
      m === model
        ? config()
        : {
            ...named(' · ' + m),
            model: m,
            task,
            dataset,
            device,
            demo,
            control: control ? 'shuffled_labels' : '',
            holdout,
            seed,
            batch,
            epochs: 20,
            patience: 5,
            imgsz: 224,
            parameters: adjusted({}),
            threshold_policy: thresholdPolicy,
            inference: {threshold: 0.5, imgsz: 224},
          }
    );
  const snap = usableSnapshots.find((s: Obj) => s.folds.some((f: Obj) => f.dataset === dataset));
  const crossValidation = allFolds && !!snap && snap.folds.length > 1;
  const submit = async () => {
    if (submitting.current) throw Error('正在送出，請稍候');
    submitting.current = true;
    try {
      if (!dataset) throw Error(allFolds ? '請選擇資料快照' : '請選擇資料快照與 fold');
      const body = queueConfigs(),
        key = JSON.stringify([crossValidation, body]);
      requestKeys.current[key] ??= crypto.randomUUID();
      // B1: one job per fold, queued in order; each fold is evaluated on its own validation set.
      const list = crossValidation
        ? await api(
            '/experiments/cross-validation',
            'POST',
            {snapshot: snap.version, configs: body},
            {'Idempotency-Key': requestKeys.current[key]}
          )
        : await api('/experiments/batch', 'POST', body, {'Idempotency-Key': requestKeys.current[key]});
      onJob((crossValidation ? list[0] : list.at(-1)).id);
      return list;
    } finally {
      submitting.current = false;
    }
  };
  const load = (c: Obj) => {
    setExpName(c.name || '');
    setModel(c.model);
    setTask(c.task || 'binary_classification');
    setDataset(c.dataset);
    setEpochs(c.epochs);
    setBatch(c.batch);
    setDevice(c.device);
    setDemo(c.demo);
    setControl(c.control === 'shuffled_labels');
    const weighted = c.parameters?.class_weight === 'balanced',
      moved = c.threshold_policy === 'sensitivity_090';
    setAdjustment(weighted && moved ? 'both' : weighted ? 'class_weight' : moved ? 'threshold' : 'none');
    setHoldout(!!c.holdout);
    setThreshold(c.inference.threshold);
    setSeed(c.seed);
    setPatience(c.patience);
    setPolicy(c.inference);
    setTimeout(() => {
      setParams(c.parameters);
      setEpochs(c.epochs);
      setPatience(c.patience);
      setInitial(c.initial_artifact || '');
      setBaseImport(c.base_import || '');
    }, 0);
  };
  return (
    <section className="panel">
      <h2>建立可重現的訓練實驗</h2>
      <div className="form-grid">
        <Field label="實驗名稱（選填）" hint="顯示在工作紀錄與訓練曲線；不影響訓練結果。">
          <input
            maxLength={60}
            placeholder="例如：EfficientNet 二分類 fold0 加權"
            value={expName}
            onChange={e => setExpName(e.target.value)}
          />
        </Field>
        <Field label="訓練任務" hint="任務決定可用模型、快照與標籤方案；不同任務的結果不可直接比較。">
          <select
            value={task}
            onChange={e => {
              const t = e.target.value;
              setTask(t);
              setDataset('');
              setCompare([]);
              if (!TASK_MODELS[t].includes(model)) setModel(TASK_MODELS[t][0]);
            }}
          >
            {[
              ['binary_classification', '二分類（正常／陽性）'],
              ['stage_classification', '分期（正常／第一期／第二期）'],
            ].map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </Field>
        <Field label="模型方案">
          <select value={model} onChange={e => setModel(e.target.value)}>
            {TASK_MODELS[task].map((v: string) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </Field>
        <Field label="已匯入官方基礎權重">
          <select
            value={baseImport}
            onChange={e => {
              setBaseImport(e.target.value);
              setInitial('');
            }}
          >
            <option value="">使用既有官方權重流程</option>
            {(basePackages.data || []).map((p: Obj) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </Field>
        <FineTuneSource
          model={model}
          value={initial}
          setValue={(v: string) => {
            setInitial(v);
            setBaseImport('');
          }}
          api={api}
        />
        <label className="check wide-check">
          <input type="checkbox" checked={allFolds} onChange={e => setAllFolds(e.target.checked)} />
          全部折都執行（依序訓練快照的每一折，完成後可在「評估比較 → 交叉驗證彙總」看合併結果）
        </label>
        <label className="check wide-check">
          <input type="checkbox" checked={holdout} onChange={e => setHoldout(e.target.checked)} />
          流程煙霧測試（只確認流程跑得通，不是獨立成績；從快照固定保留約 20%
          的照片，以整位個案為單位，個案少時比例會略高；這些照片完全不參與訓練與交叉驗證，每個模型訓練完成後在這批照片上評估一次。未勾選則不保留、不評估）
        </label>
        <Field
          label={allFolds ? '資料快照' : '資料快照與驗證折'}
          hint={
            <>
              {hiddenSnapshots
                ? `已隱藏 ${hiddenSnapshots} 個已失效（已被取代或撤回）的快照；訓練不接受失效快照。`
                : usableSnapshots.length
                  ? '只列出與此任務相符、仍有效的快照。'
                  : '此任務尚無可用快照。'}{' '}
              <a href={'#models?tab=snapshots&task=' + task}>前往新增快照 →</a>
            </>
          }
        >
          <select value={allFolds && snap ? snap.folds[0].dataset : dataset} onChange={e => setDataset(e.target.value)}>
            <option value="">
              {usableSnapshots.length ? '請選擇資料快照' : '尚無可用快照，請先到「新增快照」建立'}
            </option>
            {allFolds
              ? usableSnapshots.map((s: Obj) => (
                  <option key={s.version} value={s.folds[0].dataset}>
                    {s.name ? s.name + '（' + s.version + '）' : s.version}・{s.folds.length} 折（每折驗證{' '}
                    {s.folds.map((f: Obj) => f.counts.val).join('／')} 張）
                  </option>
                ))
              : usableSnapshots.flatMap((s: Obj) =>
                  s.folds.map((f: Obj) => (
                    <option key={f.dataset} value={f.dataset}>
                      {s.name ? s.name + '（' + s.version + '）' : s.version} / fold {f.fold}（訓練 {f.counts.train}
                      、驗證 {f.counts.val}）
                    </option>
                  ))
                )}
          </select>
        </Field>
        <Field label="計算裝置">
          <select value={device} onChange={e => setDevice(e.target.value)}>
            <option value="0">本地 NVIDIA GPU</option>
            <option value="cpu">CPU（明確選用，速度較慢）</option>
          </select>
        </Field>
        <Field
          label="判斷門檻"
          hint={
            stageTask
              ? '分期模型以最高分類別判定；此門檻不影響分期類別。'
              : '模型分數不是疾病機率；不同模型的門檻數值不可直接相比。'
          }
        >
          <input
            type="number"
            min=".01"
            max=".99"
            step=".01"
            value={threshold}
            onChange={e => setThreshold(+e.target.value)}
          />
        </Field>
        {neural && (
          <>
            <Field label="固定 epochs" hint="跑滿固定輪數，不用驗證折挑模型。">
              <input type="number" min="1" max="500" value={epochs} onChange={e => setEpochs(+e.target.value)} />
            </Field>
            <Field label="Batch size">
              <input type="number" min="1" max="64" value={batch} onChange={e => setBatch(+e.target.value)} />
            </Field>
          </>
        )}
        <Field label="隨機種子">
          <input type="number" value={seed} onChange={e => setSeed(+e.target.value)} />
        </Field>
        <Field label="實驗對照" hint="門檻只用訓練折決定，評估時不會重挑；分期不使用門檻。">
          <select value={adjustment} onChange={e => setAdjustment(e.target.value)}>
            <option value="none">標準</option>
            <option value="class_weight">類別權重</option>
            <option value="threshold">移動門檻（敏感度 ≥ 90%）</option>
            <option value="both">類別權重＋移動門檻</option>
          </select>
        </Field>
      </div>
      <label className="check">
        <input type="checkbox" checked={demo} onChange={e => setDemo(e.target.checked)} />
        我了解流程展示快照不能當正式成績
      </label>
      <label className="check">
        <input type="checkbox" checked={control} onChange={e => setControl(e.target.checked)} />
        隨機標籤對照：打亂訓練組標籤，只用來驗證流程，模型不能啟用
      </label>
      <details>
        <summary>進階參數 · 僅顯示此模型已支援的設定</summary>
        <div className="form-grid">
          {neural && (
            <Field label="Optimizer">
              <select value={params.optimizer || 'AdamW'} onChange={e => change('optimizer', e.target.value)}>
                {['AdamW', 'SGD'].map(v => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </Field>
          )}
          {neural && (
            <>
              <Field label="凍結策略">
                <select value={params.freeze || 'backbone'} onChange={e => change('freeze', e.target.value)}>
                  <option value="backbone">固定骨幹，只訓練分類頭</option>
                  <option value="last_stage">解凍最後階段</option>
                </select>
              </Field>
              <Field label="Scheduler">
                <select value={params.scheduler || 'none'} onChange={e => change('scheduler', e.target.value)}>
                  <option>none</option>
                  <option>cosine</option>
                </select>
              </Field>
            </>
          )}
          {dino && (
            <Field label="Logistic solver" hint={stageTask ? '三類分期只支援 lbfgs（多項式）。' : undefined}>
              <select value={params.solver || 'lbfgs'} onChange={e => change('solver', e.target.value)}>
                <option>lbfgs</option>
                {!stageTask && <option>liblinear</option>}
              </select>
            </Field>
          )}
          {dino && (
            <>
              <Field label="特徵">
                <select value={params.pooling || 'cls'} onChange={e => change('pooling', e.target.value)}>
                  <option value="cls">CLS</option>
                  <option value="cls_mean">CLS＋平均 patch</option>
                </select>
              </Field>
              <Field label="解析度">
                <select value={params.resolution || 224} onChange={e => change('resolution', +e.target.value)}>
                  <option value={224}>224</option>
                  <option value={518}>518</option>
                </select>
              </Field>
              {stageTask && (
                <Field label="分期方式" hint="階層式是描述性分析，不當正式分期結果。">
                  <select value={params.strategy || 'flat'} onChange={e => change('strategy', e.target.value)}>
                    <option value="flat">平面三類</option>
                    <option value="hierarchical">先判陽性再分期</option>
                  </select>
                </Field>
              )}
            </>
          )}
          {fields.map(k => (
            <Field key={k} label={k} hint={PARAM_HINTS[k]}>
              <input
                type="number"
                step="any"
                value={params[k] ?? ''}
                placeholder="沿用預設"
                onChange={e => {
                  const p = {...params};
                  if (e.target.value === '') delete p[k];
                  else p[k] = +e.target.value;
                  setParams(p);
                }}
              />
            </Field>
          ))}
        </div>
        <p>分類使用完整圖片與固定前處理。</p>
      </details>
      <ParameterOptions model={model} params={params} setParams={setParams} />
      <PolicyFields policy={policy} setPolicy={setPolicy} model={model} />
      <details>
        <summary>有限模型比較佇列</summary>
        <p>共用所選資料切分，依序執行。其他方案沿用各自預設參數；不進行自動調參。</p>
        {TASK_MODELS[task].map((m: string) => (
          <label className="check inline" key={m}>
            <input
              type="checkbox"
              checked={compare.includes(m)}
              onChange={e => setCompare(e.target.checked ? [...compare, m] : compare.filter(x => x !== m))}
            />
            {m}
          </label>
        ))}
      </details>
      <div className="callout">
        將建立 {(compare.length || 1) * (crossValidation ? snap.folds.length : 1)} 個訓練／擬合工作
        {crossValidation ? `（${compare.length || 1} 個模型方案 × ${snap.folds.length} 折）` : ''}，完成後自動排入驗證
        {holdout ? '，並做一次流程煙霧測試' : ''}。所有工作共用單一計算資源；請先停止正在接案的 LINE 服務。
      </div>
      <div className="toolbar">
        <button onClick={() => act(submit, '實驗已建立')}>開始本地訓練</button>
        <details>
          <summary>送出前檢視每個工作設定</summary>
          <ExperimentPreview configs={queueConfigs()} />
        </details>
        <button className="secondary" onClick={() => download('experiment.json', config())}>
          匯出設定
        </button>
        <label className="button secondary">
          匯入設定
          <input
            type="file"
            accept=".json"
            hidden
            onChange={e => {
              const f = e.target.files?.[0];
              if (f)
                act(async () => {
                  load(JSON.parse(await f.text()));
                }, '設定已匯入，尚未執行');
            }}
          />
        </label>
      </div>
      <details>
        <summary>設定模板</summary>
        <div className="toolbar">
          <input
            aria-label="模板名稱"
            placeholder="模板名稱"
            value={templateName}
            onChange={e => setTemplateName(e.target.value)}
          />
          <button
            className="secondary"
            disabled={!templateName}
            onClick={() =>
              act(
                () =>
                  api('/templates', 'PUT', [...(templates.data || []), {name: templateName, config: config()}]).then(
                    templates.refresh
                  ),
                '模板已儲存'
              )
            }
          >
            儲存模板
          </button>
          {(templates.data || []).map((t: Obj, i: number) => (
            <button className="secondary" key={i} onClick={() => load(t.config)}>
              {t.name}
            </button>
          ))}
        </div>
      </details>
    </section>
  );
}

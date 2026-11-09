import {useState, useEffect} from 'react';
type Obj = Record<string, any>;
import {api, useData, setCSRF} from '../shared/ui';
import {Settings} from '../features/maintenance/Settings';
import {TrashPage} from '../features/trash/Trash';
import {Empty} from '../shared/app-ui';
import {Overview} from '../features/overview/Overview';
import {DataPage} from '../features/data-review/DataPage';
import {TrustPage} from '../features/data-trust/TrustPage';
import {ModelsPage} from '../features/models/ModelsPage';
import {Simulator} from '../features/simulator/Simulator';
import {Intake} from '../features/intake/Intake';
import {trackedOperations, untrackOperation, ACTION_NAMES} from '../shared/background-ops';
import {Toasts} from '../shared/toasts';
import {GlobalSearch, NotificationBell} from '../shared/topbar';
// Old bookmarks to the retired "案例與回歸" page (regression tools are no longer offered) land on Models.
function legacy() {
  if (location.hash.slice(1).split('?')[0] === 'cases') {
    location.replace('#models');
    return true;
  }
  return false;
}
export function App() {
  const moved = legacy();
  const [page, setPage] = useState(location.hash.slice(1).split('?')[0] || 'overview'),
    [notice, setNotice] = useState(
      moved ? '「案例與回歸」已停用；模型比較請用 模型與實驗 → 評估比較，LINE 研究照片請改用「LINE 研究收件」。' : ''
    ),
    [error, setError] = useState(''),
    [ready, setReady] = useState(false);
  useEffect(() => {
    const fn = () => {
      if (legacy())
        setNotice('「案例與回歸」已停用；模型比較請用 模型與實驗 → 評估比較，LINE 研究照片請改用「LINE 研究收件」。');
    };
    addEventListener('hashchange', fn);
    return () => removeEventListener('hashchange', fn);
  }, []);
  const overview = useData('/overview', 4000, undefined, {enabled: ready && page === 'overview'});
  useEffect(() => {
    const fn = (e: Event) => setError((e as CustomEvent).detail);
    addEventListener('workbench-error', fn);
    return () => removeEventListener('workbench-error', fn);
  }, []);
  useEffect(() => {
    api('/session')
      .then(x => {
        setCSRF(x.csrf);
        setReady(true);
      })
      .catch(e => setError(e.message));
    const fn = () => setPage(location.hash.slice(1).split('?')[0] || 'overview');
    addEventListener('hashchange', fn);
    return () => removeEventListener('hashchange', fn);
  }, []);
  // Background trash operations: announced here when they finish, whichever page is open.
  useEffect(() => {
    let busy = false;
    const tick = async () => {
      if (busy || !ready) return;
      busy = true;
      try {
        for (const op of trackedOperations()) {
          try {
            const d = await api('/trash/operations/' + op.id + '?size=1');
            if (['preparing', 'running'].includes(d.state)) continue;
            untrackOperation(op.id);
            const ok = d.result.filter((r: Obj) => r.state === 'succeeded').length,
              bad = d.result.filter((r: Obj) => r.state === 'failed').length;
            const text = `${ACTION_NAMES[op.action] || '操作'}${d.state === 'completed' ? '已完成' : '未全部完成'}：${ok} 成功／${bad} 失敗。結果可在 垃圾桶 → 管理操作紀錄 查看。`;
            if (d.state === 'completed') setNotice(text);
            else setError(text);
            dispatchEvent(new CustomEvent('workbench-resources-changed', {detail: {scopes: ['*']}}));
          } catch {
            untrackOperation(op.id);
          }
        }
      } finally {
        busy = false;
      }
    };
    const t = setInterval(tick, 2000);
    return () => clearInterval(t);
  }, [ready]);
  const act = async (fn: () => Promise<any>, message = '已完成') => {
    setError('');
    setNotice('處理中…');
    try {
      const value = await fn();
      setNotice(message);
      overview.refresh();
      return value;
    } catch (e) {
      setNotice('');
      setError((e as Error).message);
      return null;
    }
  };
  const nav = [
    ['overview', '總覽'],
    ['data', '資料審查'],
    ['trust', '資料可信度'],
    ['models', '模型與實驗'],
    ['simulator', 'LINE 模擬'],
    ['intake', 'LINE 研究收件'],
    ['settings', '設定與維護'],
    ['trash', '垃圾桶'],
  ];
  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="#overview">
          靜脈炎研究工作台
        </a>
        <nav aria-label="主要功能">
          {nav.map(([id, label]) => (
            <a
              key={id}
              href={'#' + id}
              aria-current={page === id ? 'page' : undefined}
              className={page === id ? 'current' : ''}
            >
              {label}
            </a>
          ))}
        </nav>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span className="crumb">{nav.find(x => x[0] === page)?.[1]}</span>
          {ready && (
            <>
              <GlobalSearch />
              <NotificationBell />
            </>
          )}
        </header>
        <main>
          <div role="alert" className={error ? 'notice error' : 'notice'} hidden={!error && !notice}>
            {error || notice}
            <button
              className="plain"
              onClick={() => {
                setError('');
                setNotice('');
              }}
              aria-label="關閉通知"
            >
              ×
            </button>
          </div>
          {!ready ? (
            <Empty>
              {error ? (
                <>
                  本地服務尚未連接。
                  <button
                    onClick={() =>
                      api('/session')
                        .then(x => {
                          setCSRF(x.csrf);
                          setReady(true);
                          setError('');
                        })
                        .catch(e => setError(e.message))
                    }
                  >
                    重新連接
                  </button>
                </>
              ) : (
                <>正在連接本地服務…</>
              )}
            </Empty>
          ) : (
            <>
              {page === 'overview' && <Overview data={overview.data} error={overview.error} />}
              {page === 'data' && <DataPage act={act} />} {page === 'trust' && <TrustPage />}{' '}
              {page === 'models' && <ModelsPage act={act} />} {page === 'simulator' && <Simulator act={act} />}{' '}
              {page === 'intake' && <Intake act={act} />} {page === 'settings' && <Settings act={act} />}{' '}
              {page === 'trash' && <TrashPage />}
            </>
          )}
        </main>
        <Toasts />
      </div>
    </div>
  );
}

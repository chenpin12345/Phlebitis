import {useState} from 'react';
import {api, operatorName, useData} from '../../shared/ui';
import {Dialog} from '../../shared/dialog';
import {showToast} from '../../shared/toast';

type Obj = Record<string, any>;

/** Project photos in the trash.  Purging removes the photo and every copy of it. */
export function PhotoTrash() {
  const state = useData('/photo-trash');
  const items: Obj[] = state.data?.items || [];
  const [picked, setPicked] = useState<string[]>([]),
    [confirm, setConfirm] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const run = async (path: string, text: (r: Obj) => string) => {
    setBusy(true);
    setError('');
    try {
      const r = await api('/photo-trash/' + path, 'POST', {ids: picked, reviewer: operatorName()});
      showToast({text: text(r)});
      setPicked([]);
      setConfirm(false);
      await state.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  if (!items.length) return null;
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>資料照片（{items.length}）</h2>
        <div className="actions">
          <button
            type="button"
            className="secondary"
            disabled={busy || !picked.length}
            onClick={() => run('restore', r => `已還原 ${r.restored} 張照片`)}
          >
            還原
          </button>
          <button
            type="button"
            className="secondary danger"
            disabled={busy || !picked.length}
            onClick={() => setConfirm(true)}
          >
            永久刪除…
          </button>
        </div>
      </div>
      {error && <p role="alert">{error}</p>}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">
                <input
                  type="checkbox"
                  aria-label="全選資料照片"
                  checked={picked.length === items.length}
                  ref={box => {
                    if (box) box.indeterminate = picked.length > 0 && picked.length < items.length;
                  }}
                  onChange={e => setPicked(e.target.checked ? items.map(item => item.image_id) : [])}
                />
              </th>
              <th scope="col">檔名</th>
              <th scope="col">移入者</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.image_id}>
                <td>
                  <input
                    type="checkbox"
                    aria-label={'選取 ' + item.name}
                    checked={picked.includes(item.image_id)}
                    onChange={e =>
                      setPicked(e.target.checked ? [...picked, item.image_id] : picked.filter(x => x !== item.image_id))
                    }
                  />
                </td>
                <th scope="row">{item.name}</th>
                <td>{item.moved_by}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {confirm && (
        <Dialog title="永久刪除照片" onClose={() => setConfirm(false)}>
          <p>
            會永久刪除這 {picked.length}{' '}
            張照片，以及它們的審查紀錄、快照與報告裡的副本、快取，無法復原。報告的數字會保留，用過這些照片的快照不能再訓練。
          </p>
          <p>`05_匯入區` 的原檔和備份不受影響。</p>
          <div className="actions">
            <button
              type="button"
              className="danger"
              disabled={busy}
              onClick={() => run('purge', r => `已永久刪除 ${r.deleted} 張照片`)}
            >
              永久刪除 {picked.length} 張照片
            </button>
          </div>
        </Dialog>
      )}
    </section>
  );
}

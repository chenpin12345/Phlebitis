import {useEffect, useState} from 'react';
import {api, operatorName} from '../../shared/ui';
import {Dialog} from '../../shared/dialog';
import {showToast} from '../../shared/toast';

type Obj = Record<string, any>;
const size = (n: number) => (n / 1024 / 1024).toFixed(1) + ' MB';

/** Shows what a deletion touches before anything moves. */
export function DeletePhotos({ids, onClose, onDone}: {ids: string[]; onClose: () => void; onDone: () => void}) {
  const [plan, setPlan] = useState<Obj | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  useEffect(() => {
    api('/photo-trash/preview', 'POST', {ids})
      .then(setPlan)
      .catch(e => setError(e.message));
  }, []);
  const move = async () => {
    setBusy(true);
    setError('');
    try {
      await api('/photo-trash/move', 'POST', {ids, reviewer: operatorName()});
      showToast({text: `已把 ${ids.length} 張照片移到垃圾桶`});
      onDone();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  };
  return (
    <Dialog title="刪除照片" onClose={onClose}>
      {error && <p role="alert">{error}</p>}
      {!plan ? (
        !error && <p>計算影響範圍…</p>
      ) : (
        <>
          <dl>
            <dt>照片</dt>
            <dd>
              {plan.photos} 張（其中已完成 {plan.approved} 張）
            </dd>
            <dt>會失去的病人</dt>
            <dd>{plan.patients_lost} 位</dd>
            <dt>受影響的快照</dt>
            <dd>{plan.snapshots} 個，之後不能再訓練</dd>
            <dt>受影響的報告</dt>
            <dd>{plan.reports} 份，數字保留，照片不再顯示</dd>
            <dt>受影響的模型</dt>
            <dd>{plan.models} 個，會標示需重新評估</dd>
            <dt>永久刪除後可釋放</dt>
            <dd>{size(plan.bytes)}</dd>
          </dl>
          <p>現在只會移到垃圾桶，可以還原。`05_匯入區` 的原檔不會被刪除，也不會再被提示匯入。</p>
          {plan.busy && <p role="alert">有工作正在執行，請等工作結束後再刪除。</p>}
          <div className="actions">
            <button type="button" className="secondary danger" disabled={busy || plan.busy} onClick={move}>
              移到垃圾桶
            </button>
          </div>
        </>
      )}
    </Dialog>
  );
}

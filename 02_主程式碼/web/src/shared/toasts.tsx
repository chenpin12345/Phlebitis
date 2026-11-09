import {useEffect, useState} from 'react';
import {TOAST_EVENT, Toast} from './toast';

/** Renders toasts dispatched with showToast(); each stays 12 seconds unless dismissed. */
export function Toasts() {
  const [items, setItems] = useState<Toast[]>([]);
  useEffect(() => {
    const add = (e: Event) => {
      const t = (e as CustomEvent).detail as Toast;
      setItems(list => [...list.slice(-2), t]);
      setTimeout(() => setItems(list => list.filter(x => x.id !== t.id)), 12000);
    };
    addEventListener(TOAST_EVENT, add);
    return () => removeEventListener(TOAST_EVENT, add);
  }, []);
  const close = (id: number) => setItems(list => list.filter(x => x.id !== id));
  return (
    <div className="toasts" role="status" aria-live="polite">
      {items.map(t => (
        <div key={t.id} className={'toast ' + (t.tone || 'info')}>
          <span>{t.text}</span>
          {t.action && (
            <button
              type="button"
              className="plain"
              onClick={() => {
                close(t.id);
                t.action!.run();
              }}
            >
              {t.action.label}
            </button>
          )}
          <button type="button" className="plain" aria-label="關閉通知" onClick={() => close(t.id)}>
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

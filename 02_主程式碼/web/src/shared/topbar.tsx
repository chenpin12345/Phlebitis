import React, {useEffect, useRef, useState} from 'react';
import {api, useData, when} from './ui';
type Obj = Record<string, any>;
type Hit = {id: string; title: string; detail?: string; href: string; trash?: string | null};
type Group = {key: string; name: string; items: Hit[]; more?: boolean};

const typing = (t: EventTarget | null) =>
  t instanceof Element && (['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName) || (t as HTMLElement).isContentEditable);

/** Header search (D4): photos, jobs, model versions and snapshots, trash included. Shortcut: / */
export function GlobalSearch() {
  const [q, setQ] = useState(''),
    [result, setResult] = useState<{query: string; groups: Group[]; total: number} | null>(null),
    [open, setOpen] = useState(false),
    [active, setActive] = useState(0),
    [error, setError] = useState('');
  const input = useRef<HTMLInputElement>(null),
    box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if (
        e.key === '/' &&
        !typing(e.target) &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey &&
        !document.querySelector('dialog[open]')
      ) {
        e.preventDefault();
        input.current?.focus();
        input.current?.select();
      }
    };
    addEventListener('keydown', f);
    return () => removeEventListener('keydown', f);
  }, []);
  useEffect(() => {
    const text = q.trim();
    if (!text) {
      setResult(null);
      setError('');
      return;
    }
    const controller = new AbortController();
    const t = setTimeout(() => {
      api('/search?q=' + encodeURIComponent(text), 'GET', undefined, {}, controller.signal)
        .then(r => {
          setResult(r);
          setActive(0);
          setError('');
        })
        .catch(e => {
          if (e.name !== 'AbortError') setError(e.message);
        });
    }, 200);
    return () => {
      clearTimeout(t);
      controller.abort();
    };
  }, [q]);
  useEffect(() => {
    const f = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    addEventListener('mousedown', f);
    return () => removeEventListener('mousedown', f);
  }, []);
  const flat = (result?.groups || []).flatMap(g => g.items);
  const go = (hit: Hit) => {
    location.hash = hit.href.replace(/^#/, '');
    setOpen(false);
    setQ('');
    input.current?.blur();
  };
  const key = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setOpen(false);
      input.current?.blur();
      return;
    }
    if (!flat.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setOpen(true);
      setActive(a => (a + 1) % flat.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive(a => (a - 1 + flat.length) % flat.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      go(flat[active]);
    }
  };
  let index = -1;
  return (
    <div className="global-search" ref={box}>
      <input
        ref={input}
        type="search"
        role="combobox"
        aria-label="搜尋照片、工作、模型與快照"
        aria-expanded={open && !!q.trim()}
        aria-controls="global-search-results"
        placeholder="搜尋照片、工作、模型　/"
        value={q}
        onFocus={() => setOpen(true)}
        onChange={e => {
          setQ(e.target.value);
          setOpen(true);
        }}
        onKeyDown={key}
      />
      {open && q.trim() && (
        <div className="search-results" id="global-search-results" role="listbox" aria-label="搜尋結果">
          {error ? (
            <p className="muted">{error}</p>
          ) : !result || result.query !== q.trim().toLowerCase().replace(/\s+/g, ' ') ? (
            <p className="muted">搜尋中…</p>
          ) : !result.total ? (
            <p className="muted">找不到符合「{q.trim()}」的項目。</p>
          ) : (
            result.groups.map(g => (
              <section key={g.key}>
                <h3>
                  {g.name}
                  {g.more && <small>（只列前 8 筆）</small>}
                </h3>
                {g.items.map(hit => {
                  index++;
                  const i = index;
                  return (
                    <a
                      key={g.key + hit.id}
                      role="option"
                      aria-selected={i === active}
                      className={i === active ? 'active' : ''}
                      href={hit.href}
                      onMouseEnter={() => setActive(i)}
                      onClick={e => {
                        e.preventDefault();
                        go(hit);
                      }}
                    >
                      <span className="break">{hit.title}</span>
                      <small>
                        {hit.detail}
                        {hit.trash && <span className="chip trash-chip">{hit.trash}</span>}
                      </small>
                    </a>
                  );
                })}
              </section>
            ))
          )}
        </div>
      )}
    </div>
  );
}

/** Bell with unread count (D3). New notices can also be shown as Windows system notifications. */
export function NotificationBell() {
  const state = useData('/notifications?limit=30', 15000);
  const prefs = useData('/settings/workbench');
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const d = state.data as {items: Obj[]; unread: number; latest: number} | null;
  useEffect(() => {
    const f = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    addEventListener('mousedown', f);
    return () => removeEventListener('mousedown', f);
  }, []);
  useEffect(() => {
    if (!d) return;
    let seen = 0;
    try {
      seen = Number(sessionStorage.getItem('workbench.notice-seen') || 0);
    } catch {}
    if (
      seen &&
      prefs.data?.notifications?.system &&
      'Notification' in window &&
      Notification.permission === 'granted'
    ) {
      for (const n of d.items.filter(n => n.id > seen && !n.read).slice(0, 3))
        try {
          new Notification(n.title, {body: n.body || '', tag: 'workbench-' + n.id});
        } catch {
          /* unsupported */
        }
    }
    try {
      sessionStorage.setItem('workbench.notice-seen', String(d.latest || 0));
    } catch {}
  }, [d?.latest]);
  const read = async (ids?: number[]) => {
    await api('/notifications/read', 'POST', {ids: ids ?? null}).catch(() => {});
    state.refresh();
  };
  const unread = d?.unread || 0;
  return (
    <div className="bell" ref={box}>
      <button
        type="button"
        className="secondary bell-button"
        aria-expanded={open}
        aria-haspopup="true"
        onClick={() => setOpen(!open)}
        aria-label={unread ? `通知，${unread} 則未讀` : '通知'}
      >
        通知
        {unread > 0 && (
          <span className="count" aria-hidden="true">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>
      {open && (
        <div className="notice-panel" role="region" aria-label="通知">
          <div className="notice-head">
            <b>通知</b>
            <button type="button" className="plain" disabled={!unread} onClick={() => read()}>
              全部標為已讀
            </button>
          </div>
          {!d ? (
            <p className="muted">載入中…</p>
          ) : !d.items.length ? (
            <p className="muted">目前沒有通知。訓練、評估、垃圾桶操作完成，或偵測到岡山高醫新照片時會出現在這裡。</p>
          ) : (
            <ul>
              {d.items.map(n => (
                <li key={n.id} className={(n.read ? '' : 'unread ') + 'level-' + n.level}>
                  <a
                    href={n.href || '#overview'}
                    onClick={() => {
                      setOpen(false);
                      if (!n.read) read([n.id]);
                    }}
                  >
                    <span className="mark" aria-hidden="true" />
                    <span>
                      <b>{n.title}</b>
                      {n.body && <small className="break">{n.body}</small>}
                      <small>
                        {when(n.at)}
                        {n.read ? '' : '・未讀'}
                      </small>
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

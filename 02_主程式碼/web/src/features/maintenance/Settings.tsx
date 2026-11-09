import {ReferenceManager} from '../trash/Trash';
import React, {useState, useEffect} from 'react';
import {api, useData, Fields, TechnicalDetails, Empty, Pager, when, names, Operator} from '../../shared/ui';
import {LineControl} from '../models/extras';
import {BackupPanel, DiskUsagePanel, FullBackupPanel, PreferencePanels, useSectionScroll} from './Tools';

export function Settings({act}: any) {
  useSectionScroll();
  const doctor = useData('/doctor'),
    retention = useData('/retention');
  const d = doctor.data,
    r = retention.data;
  return (
    <>
      <div className="heading">
        <div>
          <h1>設定與維護</h1>
          <p>本機環境、資料保存與模型引用。</p>
        </div>
      </div>
      <section className="panel">
        <h2>操作者設定</h2>
        <Operator />
        <p>研究代稱只用於追溯，不是經登入驗證的身分，也不是管理員授權。</p>
      </section>
      <BackupPanel />
      <FullBackupPanel />
      <DiskUsagePanel />
      <PreferencePanels />
      <div className="two-col">
        <section className="panel">
          <h2>環境檢查</h2>
          {doctor.error ? (
            <Empty>{doctor.error}</Empty>
          ) : !d ? (
            <Empty>檢查中…</Empty>
          ) : (
            <>
              <Fields
                value={{
                  運算資源:
                    d.compute_available == null
                      ? '未知'
                      : d.compute_available
                        ? '可取得運算鎖'
                        : '使用中或目前無法取得運算鎖',
                  'CUDA 可用': d.cuda,
                  GPU: d.gpu ?? '未取得／無 CUDA 裝置',
                  'GPU 記憶體（GB）': d.vram == null ? null : d.vram / 1024 ** 3,
                  '可用磁碟（GB）': d.free_disk_gb,
                  前端已建置: d.frontend_ready,
                }}
              />
              {d.workspace && (
                <>
                  <h3>工作區</h3>
                  <table>
                    <tbody>
                      {d.workspace.map((w: any) => (
                        <tr key={w.key}>
                          <th>{w.name}</th>
                          <td>
                            <span className={'status ' + (w.ok === true ? 'ok' : w.ok === false ? 'bad' : 'neutral')}>
                              <i />
                              {w.ok === true ? '正常' : w.ok === false ? '需處理' : '未設定'}
                            </span>
                          </td>
                          <td className="break">
                            {w.detail}
                            {w.action && <small>{w.action}</small>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
              {d.check_errors?.map((e: string) => (
                <p className="callout" key={e}>
                  {e}
                </p>
              ))}
              <h3>套件版本</h3>
              <table>
                <thead>
                  <tr>
                    <th>套件</th>
                    <th>已安裝版本</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(d.packages).map(([k, v]: any) => (
                    <tr key={k}>
                      <th>{k}</th>
                      <td>{v ?? '未安裝或無法取得'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p>此表確認安裝版本；跨套件相容性尚未完整驗證。</p>
              <details>
                <summary>安裝與修復說明</summary>
                <p>{d.repair}</p>
              </details>
              <TechnicalDetails
                label="服務位置與檢查資訊"
                value={{
                  ports: d.ports,
                  frontend_ready: d.frontend_ready,
                  line_credentials_required: d.line_credentials_required,
                }}
              />
            </>
          )}
          <button className="secondary" onClick={doctor.refresh}>
            重新檢查
          </button>
        </section>
        <section className="panel">
          <h2>資料保存與清理預覽</h2>
          <dl>
            <dt>LINE 原圖</dt>
            <dd>不永久保存，不自動加入訓練</dd>
            <dt>LINE 結果／模擬暫存</dt>
            <dd>一小時</dd>
            <dt>新授權研究回收</dt>
            <dd>預設 30 天，可明確撤回</dd>
            <dt>既有資料／封存／使用中模型</dt>
            <dd>保護，不套用研究回收期限</dd>
          </dl>
          {retention.error ? (
            <Empty>{retention.error}</Empty>
          ) : !r ? (
            <Empty>取得清理範圍…</Empty>
          ) : (
            <>
              <h3>已到期 {r.assets.length} 份</h3>
              {!r.assets.length ? (
                <Empty>目前沒有到期資料</Empty>
              ) : (
                r.assets.map((a: any) => (
                  <details key={a.id}>
                    <summary>
                      {a.id} · {a.category} · {when(a.expires)}
                    </summary>
                    <Fields value={{id: a.id, expires: a.expires, category: a.category, impact: a.impact}} />
                  </details>
                ))
              )}
              <details>
                <summary>受保護的資料</summary>
                <ul>
                  {r.protected.map((s: string) => (
                    <li key={s}>{s}：不適用此工作台回收期限</li>
                  ))}
                </ul>
                <p>{r.note}</p>
              </details>
              <p>清理不會刪除 LINE 或其他外部副本。</p>
              <button
                className="danger secondary"
                disabled={!r.assets.length}
                onClick={() => {
                  if (
                    confirm(
                      `將刪除目前預覽的 ${r.assets.length} 份到期資料及各明細所列受管理副本。請先展開核對範圍，是否繼續？`
                    )
                  )
                    act(
                      () =>
                        api('/retention/cleanup', 'POST', {ids: r.assets.map((a: any) => a.id)}).then(
                          retention.refresh
                        ),
                      '到期資料已清理'
                    );
                }}
              >
                清理預覽項目
              </button>
            </>
          )}
          <button className="secondary" onClick={retention.refresh}>
            重新預覽
          </button>
        </section>
      </div>
      <LineControl act={act} api={api} />
      <section className="panel">
        <h2>模型引用</h2>
        <p>回復會換回前一次選定的版本。解除會停用目前的模型，之後要重新選定才能預測；解除後這個模型才能移到垃圾桶。</p>
        {['local', 'line'].map(t => (
          <button
            className="secondary"
            key={t}
            onClick={() => act(() => api('/artifacts/rollback/' + t, 'POST'), '模型引用已回復')}
          >
            回復 {t === 'local' ? '本地模擬' : 'LINE'} 模型
          </button>
        ))}
        {['local', 'line'].map(t => (
          <button
            className="secondary danger"
            key={t}
            onClick={() => act(() => api('/references/' + t + '/clear', 'POST'), '已解除模型引用')}
          >
            解除 {t === 'local' ? '本地模擬' : 'LINE'} 模型
          </button>
        ))}
      </section>
      <ReferenceManager />
    </>
  );
}

// Trash operations keep running on the server after their dialog is closed.
// Submitted operation ids are remembered here (per browser tab) so the app shell can
// poll them and announce completion wherever the user currently is.
const KEY = 'workbench-background-operations';
export const BACKGROUND_EVENT = 'workbench-background-operations';
export type BackgroundOp = {id: string; action: string; count: number; started: number};

export function trackedOperations(): BackgroundOp[] {
  try {
    return JSON.parse(sessionStorage.getItem(KEY) || '[]');
  } catch {
    return [];
  }
}
function save(list: BackgroundOp[]) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    /* storage unavailable: tracking lasts until reload */
  }
  dispatchEvent(new Event(BACKGROUND_EVENT));
}
export function trackOperation(op: Omit<BackgroundOp, 'started'>) {
  const list = trackedOperations().filter(x => x.id !== op.id);
  save([...list, {...op, started: Date.now()}]);
}
export function untrackOperation(id: string) {
  save(trackedOperations().filter(x => x.id !== id));
}
export const ACTION_NAMES: Record<string, string> = {move: '移至垃圾桶', restore: '還原', purge: '永久刪除'};

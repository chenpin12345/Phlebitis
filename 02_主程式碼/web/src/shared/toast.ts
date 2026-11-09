// Short-lived message at the bottom of the window, optionally with one action (e.g. 復原).
// Used for reversible actions so they need no confirmation dialog.
export const TOAST_EVENT = 'workbench-toast';
export type Toast = {id: number; text: string; tone?: 'info' | 'error'; action?: {label: string; run: () => void}};
let next = 1;
export function showToast(toast: Omit<Toast, 'id'>) {
  dispatchEvent(new CustomEvent(TOAST_EVENT, {detail: {...toast, id: next++}}));
}

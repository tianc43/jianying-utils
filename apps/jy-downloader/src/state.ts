import { atom } from "jotai";

export type LogLevel = "info" | "success" | "error";

export interface LogEntry {
  id: number;
  level: LogLevel;
  message: string;
}

export interface InstallResult {
  targetDir: string;
  placeholderId: string;
  draftName: string;
}

export const sourceAtom = atom("");
export const draftsDirAtom = atom("");
export const draftNameAtom = atom("");
export const placeholderIdAtom = atom("");
export const overwriteAtom = atom(false);
export const installingAtom = atom(false);
export const resultAtom = atom<InstallResult | null>(null);
export const logsAtom = atom<LogEntry[]>([]);

export const canInstallAtom = atom((get) => {
  return get(sourceAtom).trim().length > 0 && get(draftsDirAtom).trim().length > 0 && !get(installingAtom);
});

let nextLogId = 1;

export const appendLogAtom = atom(null, (_get, set, entry: Omit<LogEntry, "id">) => {
  set(logsAtom, (logs) => [...logs, { ...entry, id: nextLogId++ }]);
});

export const clearRunStateAtom = atom(null, (_get, set) => {
  set(resultAtom, null);
  set(logsAtom, []);
});

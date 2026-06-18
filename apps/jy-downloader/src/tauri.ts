import { invoke } from "@tauri-apps/api/core";

export interface EnvironmentInfo {
  defaultDraftsDir: string | null;
  detectedPlaceholderId: string | null;
}

export interface InstallDraftRequest {
  source: string;
  draftsDir: string;
  draftName?: string;
  placeholderId?: string;
  overwrite: boolean;
}

export interface InstallDraftResult {
  targetDir: string;
  placeholderId: string;
  draftName: string;
}

export async function getEnvironmentInfo(): Promise<EnvironmentInfo> {
  return invoke<EnvironmentInfo>("get_environment_info");
}

export async function installDraft(request: InstallDraftRequest): Promise<InstallDraftResult> {
  return invoke<InstallDraftResult>("install_draft", { request });
}

import { API_ROUTES, postJson, requestJson } from '../../core/api/client';
import type { PromptDraft, PromptService } from '../../core/types';

export interface PromptUpdateResponse {
  status: string;
  message: string;
}

/** Fetches the list of prompt services available in the system. */
export function fetchPromptServices(): Promise<PromptService[]> {
  return requestJson<PromptService[]>(API_ROUTES.prompts.list);
}

/** Updates the content of a prompt. */
export function updatePrompt(draft: PromptDraft): Promise<PromptUpdateResponse> {
  return postJson<PromptDraft, PromptUpdateResponse>(API_ROUTES.prompts.update, draft);
}

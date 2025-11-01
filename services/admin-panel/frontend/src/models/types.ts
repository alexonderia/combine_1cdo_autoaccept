export type Service = {
  name: string;
  status: string;
  url: string;
  version?: string;
  details?: Record<string, string>;
};

export type Prompt = {
  service : string;
  name: string;
  content: string;
};

export type PromptService = {
  name: string;
  prompts: Prompt[];
};

export type ConfigService = {
  name: string;
  config: Record<string, string>;
};
/**
 * Describes a service that is monitored by the admin panel.
 */
export interface Service {
  /** Unique name of the service. */
  name: string;
  /** Current status reported by the backend. */
  status: string;
  /** Base URL where the service is deployed. */
  url: string;
  /** Optional semantic version string. */
  version?: string;
  /** Additional metadata returned by the service health check. */
  details?: Record<string, string>;
}

/**
 * Represents a single prompt file belonging to a service.
 */
export interface Prompt {
  /** Identifier of the owning service. */
  service: string;
  /** File name of the prompt. */
  name: string;
  /** Prompt content. */
  content: string;
}

/**
 * A group of prompts associated with the same service.
 */
export interface PromptService {
  /** Display name of the service. */
  name: string;
  /** Collection of prompts available for editing. */
  prompts: Prompt[];
}

/**
 * Configuration entries returned for a specific service.
 */
export interface ConfigService {
  /** Service name. */
  name: string;
  /** Key-value configuration map. */
  config: Record<string, string>;
}

/**
 * Draft of a prompt used while editing the content in the UI.
 */
export interface PromptDraft {
  service: string;
  name: string;
  content: string;
}

export interface ProviderCapabilities {
  plan_mode: boolean;
  resume: boolean;
  streaming: boolean;
  autonomous: boolean;
  autonomous_flag: string | null;
  models: string[];
}

export interface Provider {
  name: string;
  display_name: string;
  description: string;
  capabilities: ProviderCapabilities;
  is_available: boolean;
  executable_path: string | null;
}

export interface ProviderSummary {
  name: string;
  display_name: string;
  is_available: boolean;
  supports_plan_mode: boolean;
}

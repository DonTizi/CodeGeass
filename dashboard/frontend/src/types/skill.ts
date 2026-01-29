export interface Skill {
  name: string;
  path: string;
  description: string;
  allowed_tools: string[];
  context: 'inline' | 'fork';
  agent: string | null;
  disable_model_invocation: boolean;
  content: string;
  dynamic_commands: string[];
}

export interface SkillSummary {
  name: string;
  description: string;
  context: 'inline' | 'fork';
  has_agent: boolean;
}

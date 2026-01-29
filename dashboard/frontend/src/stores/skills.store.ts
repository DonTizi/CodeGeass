import { create } from 'zustand';
import type { Skill, SkillSummary } from '@/types';
import { api } from '@/lib/api';

interface SkillsState {
  skills: SkillSummary[];
  selectedSkill: Skill | null;
  loading: boolean;
  error: string | null;

  fetchSkills: () => Promise<void>;
  fetchSkill: (name: string) => Promise<void>;
  reloadSkills: () => Promise<void>;
  selectSkill: (skill: Skill | null) => void;
}

export const useSkillsStore = create<SkillsState>((set) => ({
  skills: [],
  selectedSkill: null,
  loading: false,
  error: null,

  fetchSkills: async () => {
    set({ loading: true, error: null });
    try {
      const skills = await api.skills.list();
      set({ skills, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch skills', loading: false });
    }
  },

  fetchSkill: async (name: string) => {
    set({ loading: true, error: null });
    try {
      const skill = await api.skills.get(name);
      set({ selectedSkill: skill, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch skill', loading: false });
    }
  },

  reloadSkills: async () => {
    set({ loading: true, error: null });
    try {
      const skills = await api.skills.reload();
      set({ skills, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to reload skills', loading: false });
    }
  },

  selectSkill: (skill: Skill | null) => {
    set({ selectedSkill: skill });
  },
}));

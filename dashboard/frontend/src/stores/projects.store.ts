import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Project, ProjectCreate, ProjectUpdate, TaskWithProject, SkillWithSource } from '@/types';
import { api } from '@/lib/api';

interface ProjectsState {
  projects: Project[];
  selectedProjectId: string | null; // null = all projects
  loading: boolean;
  error: string | null;

  // Actions
  fetchProjects: () => Promise<void>;
  selectProject: (projectId: string | null) => void;
  addProject: (data: ProjectCreate) => Promise<Project>;
  updateProject: (projectId: string, data: ProjectUpdate) => Promise<Project>;
  removeProject: (projectId: string) => Promise<void>;
  setDefaultProject: (projectId: string) => Promise<void>;
  enableProject: (projectId: string) => Promise<void>;
  disableProject: (projectId: string) => Promise<void>;
  getProjectTasks: (projectId: string) => Promise<TaskWithProject[]>;
  getAllTasks: () => Promise<TaskWithProject[]>;
  getProjectSkills: (projectId: string) => Promise<SkillWithSource[]>;

  // Computed
  getSelectedProject: () => Project | null;
  getDefaultProject: () => Project | null;
}

export const useProjectsStore = create<ProjectsState>()(
  persist(
    (set, get) => ({
      projects: [],
      selectedProjectId: null,
      loading: false,
      error: null,

      fetchProjects: async () => {
        set({ loading: true, error: null });
        try {
          const projects = await api.projects.list();
          set({ projects, loading: false });
        } catch (e) {
          set({
            error: e instanceof Error ? e.message : 'Failed to fetch projects',
            loading: false,
          });
        }
      },

      selectProject: (projectId: string | null) => {
        set({ selectedProjectId: projectId });
      },

      addProject: async (data: ProjectCreate) => {
        set({ loading: true, error: null });
        try {
          const project = await api.projects.add(data);
          set((state) => ({
            projects: [...state.projects, project],
            loading: false,
          }));
          return project;
        } catch (e) {
          const error = e instanceof Error ? e.message : 'Failed to add project';
          set({ error, loading: false });
          throw e;
        }
      },

      updateProject: async (projectId: string, data: ProjectUpdate) => {
        set({ loading: true, error: null });
        try {
          const project = await api.projects.update(projectId, data);
          set((state) => ({
            projects: state.projects.map((p) =>
              p.id === projectId ? project : p
            ),
            loading: false,
          }));
          return project;
        } catch (e) {
          const error = e instanceof Error ? e.message : 'Failed to update project';
          set({ error, loading: false });
          throw e;
        }
      },

      removeProject: async (projectId: string) => {
        set({ loading: true, error: null });
        try {
          await api.projects.remove(projectId);
          set((state) => ({
            projects: state.projects.filter((p) => p.id !== projectId),
            selectedProjectId:
              state.selectedProjectId === projectId
                ? null
                : state.selectedProjectId,
            loading: false,
          }));
        } catch (e) {
          const error = e instanceof Error ? e.message : 'Failed to remove project';
          set({ error, loading: false });
          throw e;
        }
      },

      setDefaultProject: async (projectId: string) => {
        try {
          await api.projects.setDefault(projectId);
          set((state) => ({
            projects: state.projects.map((p) => ({
              ...p,
              is_default: p.id === projectId,
            })),
          }));
        } catch (e) {
          throw e;
        }
      },

      enableProject: async (projectId: string) => {
        try {
          await api.projects.enable(projectId);
          set((state) => ({
            projects: state.projects.map((p) =>
              p.id === projectId ? { ...p, enabled: true } : p
            ),
          }));
        } catch (e) {
          throw e;
        }
      },

      disableProject: async (projectId: string) => {
        try {
          await api.projects.disable(projectId);
          set((state) => ({
            projects: state.projects.map((p) =>
              p.id === projectId ? { ...p, enabled: false } : p
            ),
          }));
        } catch (e) {
          throw e;
        }
      },

      getProjectTasks: async (projectId: string) => {
        return api.projects.getTasks(projectId);
      },

      getAllTasks: async () => {
        return api.projects.getAllTasks();
      },

      getProjectSkills: async (projectId: string) => {
        return api.projects.getSkills(projectId);
      },

      getSelectedProject: () => {
        const state = get();
        if (!state.selectedProjectId) return null;
        return state.projects.find((p) => p.id === state.selectedProjectId) || null;
      },

      getDefaultProject: () => {
        const state = get();
        return state.projects.find((p) => p.is_default) || null;
      },
    }),
    {
      name: 'codegeass-projects',
      partialize: (state) => ({
        selectedProjectId: state.selectedProjectId,
      }),
    }
  )
);

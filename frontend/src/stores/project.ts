import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Project } from '../types'

interface AnalysisState {
  test_data_id?: number
  sampling_rate: number
  interpolation_method: 'linear' | 'spline' | 'step'
}

interface AnalysisResult {
  id: number
  indicator_id: string
  indicator_name: string
  result_value: number | string | object
  result_status: 'pass' | 'warning' | 'fail' | 'error'
  calculated_at: string
}

interface SignalSummary {
  min: number
  max: number
  mean: number
  std: number
  count: number
}

interface ProjectState {
  currentProject: Project | null
  projects: Project[]
  analysisConfig: AnalysisState
  analysisResults: AnalysisResult[]
  signalSummary: Record<string, SignalSummary>
  hasAnalyzed: boolean
  setCurrentProject: (project: Project | null) => void
  setProjects: (projects: Project[]) => void
  addProject: (project: Project) => void
  updateProject: (project: Project) => void
  removeProject: (id: number) => void
  setAnalysisConfig: (config: Partial<AnalysisState>) => void
  setAnalysisResults: (results: AnalysisResult[]) => void
  setSignalSummary: (summary: Record<string, SignalSummary>) => void
  setHasAnalyzed: (value: boolean) => void
  clearAnalysis: () => void
}

const defaultAnalysisConfig: AnalysisState = {
  sampling_rate: 100,
  interpolation_method: 'linear'
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      currentProject: null,
      projects: [],
      analysisConfig: defaultAnalysisConfig,
      analysisResults: [],
      signalSummary: {},
      hasAnalyzed: false,
      setCurrentProject: (project) => set({ currentProject: project }),
      setProjects: (projects) => set({ projects }),
      addProject: (project) =>
        set((state) => ({
          projects: [...state.projects, project],
        })),
      updateProject: (project) =>
        set((state) => ({
          projects: state.projects.map((p) => (p.id === project.id ? project : p)),
          currentProject: state.currentProject?.id === project.id ? project : state.currentProject,
        })),
      removeProject: (id) =>
        set((state) => ({
          projects: state.projects.filter((p) => p.id !== id),
          currentProject: state.currentProject?.id === id ? null : state.currentProject,
        })),
      setAnalysisConfig: (config) =>
        set((state) => ({
          analysisConfig: { ...state.analysisConfig, ...config }
        })),
      setAnalysisResults: (results) => set({ analysisResults: results, hasAnalyzed: true }),
      setSignalSummary: (summary) => set({ signalSummary: summary }),
      setHasAnalyzed: (value) => set({ hasAnalyzed: value }),
      clearAnalysis: () => set({
        analysisConfig: defaultAnalysisConfig,
        analysisResults: [],
        signalSummary: {},
        hasAnalyzed: false
      }),
    }),
    {
      name: 'project-storage',
    }
  )
)

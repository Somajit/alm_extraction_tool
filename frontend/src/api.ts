import axios, { AxiosResponse } from 'axios'

const API_BASE = (import.meta as any).env.VITE_API_BASE || 'http://localhost:8000'
const api = axios.create({
  baseURL: API_BASE,
  validateStatus: () => true, // Don't throw on any status code, handle manually
})

export interface AuthPayload {
  username: string
  password: string
}

export interface AuthResponse {
  ok: boolean
  message?: string
}

export interface Domain {
  name: string
  id: string
}

export interface Project {
  name: string
  id: string
}

export interface TreeNode {
  id: string
  label: string
  children?: TreeNode[]
}

export interface TreeResponse {
  tree: TreeNode[]
}

export interface Defect {
  id: string
  summary: string
  status: string
  priority: string
  project: string
}

export const authenticate = (username: string, password: string): Promise<AxiosResponse<AuthResponse>> =>
  api.post('/auth', { username, password })

export const getDomains = (): Promise<AxiosResponse<Domain[]>> =>
  api.get('/domains')

export const getProjects = (domain: string): Promise<AxiosResponse<Project[]>> =>
  api.get('/projects', { params: { domain } })

export const getTree = (project: string, type: string): Promise<AxiosResponse<TreeResponse>> =>
  api.get('/tree', { params: { project, type } })

export const getDefects = (project: string): Promise<AxiosResponse<Defect[]>> =>
  api.get('/defects', { params: { project } })

export const initSample = (): Promise<AxiosResponse> =>
  api.post('/init')

export default api

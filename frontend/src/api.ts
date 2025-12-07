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
  type?: string
  folder_id?: string
  test_id?: string
  testset_id?: string
  release_id?: string
  cycle_id?: string
  run_id?: string
  attachment_id?: string
  has_children?: boolean
  children?: TreeNode[]
  json_data?: any
  status?: string
}

export interface TreeResponse {
  tree: TreeNode[]
}

export interface TestDetails {
  id: string
  name: string
  [key: string]: any  // Allow any additional fields from ALM
  design_steps?: any[]
  attachments?: {
    id: string
    name: string
    sanitized_name: string
  }[]
}

export interface Defect {
  id: string
  name: string
  status: string
  severity?: string
  priority?: string
  'detected-by'?: string
  owner?: string
  description?: string
  'creation-time'?: string
  'last-modified'?: string
  'has-attachments'?: string
  [key: string]: any  // Allow any additional fields
}

export interface DefectsResponse {
  defects: Defect[]
  total: number
}

export interface DefectDetails extends Defect {
  attachments?: {
    id: string
    name: string
    'file-size'?: number
  }[]
}

export const authenticate = (username: string, password: string): Promise<AxiosResponse<AuthResponse>> =>
  api.post('/auth', { username, password })

export const logout = (username: string): Promise<AxiosResponse> =>
  api.post('/logout', { username })

export const getDomains = (username: string): Promise<AxiosResponse<Domain[]>> =>
  api.get('/domains', { params: { username } })

export const getProjects = (domain: string, username: string): Promise<AxiosResponse<Project[]>> =>
  api.get('/projects', { params: { domain, username } })

// ============================================================================
// NEW RATIONALIZED API METHODS
// Following pattern: Frontend → Backend → ALM → Store MongoDB → Query MongoDB → Return
// ============================================================================

export interface AuthenticateRequest {
  username: string
  password: string
}

export interface AuthenticateResponse {
  success: boolean
  message: string
  username: string
}

export interface DomainsResponse {
  success: boolean
  domains: Domain[]
}

export interface ProjectsResponse {
  success: boolean
  projects: Project[]
}

export interface LoginRequest {
  username: string
  domain: string
  project: string
}

export interface LoginResponse {
  success: boolean
  testplan_root_folders: number
  testlab_releases: number
  defects: number
}

export interface LogoutRequest {
  username: string
}

export interface LogoutResponse {
  success: boolean
  message: string
}

/**
 * New authentication API methods using rationalized endpoints
 */
export const authApi = {
  /**
   * Authenticate with ALM server (username/password only)
   * Flow: Call ALM auth → Store credentials in MongoDB → Return from MongoDB
   */
  authenticate: (username: string, password: string): Promise<AxiosResponse<AuthenticateResponse>> =>
    api.post('/api/authenticate', { username, password }),

  /**
   * Fetch and store available domains from ALM
   * Flow: Call ALM → Store in domains collection → Query MongoDB → Return
   */
  getDomains: (username: string): Promise<AxiosResponse<DomainsResponse>> =>
    api.get('/api/get_domains', { params: { username } }),

  /**
   * Fetch and store projects for a domain from ALM
   * Flow: Call ALM → Store in projects collection → Query MongoDB → Return
   */
  getProjects: (username: string, domain: string): Promise<AxiosResponse<ProjectsResponse>> =>
    api.get('/api/get_projects', { params: { username, domain } }),

  /**
   * Complete login after domain/project selection, load initial tree data
   * Flow: Store selection → Fetch root folders, releases, defects → Store all → Return counts
   */
  login: (username: string, domain: string, project: string, project_group: string = 'default'): Promise<AxiosResponse<LoginResponse>> =>
    api.post('/api/login', { username, domain, project, project_group }),

  /**
   * Logout from ALM server
   * Flow: Call ALM logout → Clear cookies → Update MongoDB
   */
  logout: (username: string): Promise<AxiosResponse<LogoutResponse>> =>
    api.post('/api/logout', { username }),
}


export const getTree = (
  project: string, 
  username: string,
  domain: string,
  type: string, 
  parent_id: number = 0,
  folder_id?: string
): Promise<AxiosResponse<TreeResponse>> =>
  api.get('/tree', { params: { project, username, domain, type, parent_id, folder_id } })

export const getTestChildren = (
  username: string,
  domain: string,
  project: string,
  test_id: string
): Promise<AxiosResponse<TreeResponse>> =>
  api.get('/test-children', { params: { username, domain, project, test_id } })

export const getTestDetails = (
  username: string,
  domain: string,
  project: string,
  test_id: string
): Promise<AxiosResponse<TestDetails>> =>
  api.get('/test-details', { params: { username, domain, project, test_id } })

export const getRunChildren = (
  username: string,
  domain: string,
  project: string,
  run_id: string
): Promise<AxiosResponse<TreeResponse>> =>
  api.get('/run-children', { params: { username, domain, project, run_id } })

export const getRunJson = (
  username: string,
  domain: string,
  project: string,
  run_id: string
): Promise<AxiosResponse<any>> =>
  api.get('/run-json', { params: { username, domain, project, run_id } })

export const extractFolderRecursive = (
  folder_id: string
): Promise<AxiosResponse<any>> =>
  api.post('/extract-folder-recursive', { node_type: 'folder', node_id: folder_id })

export const getTestSetDetails = (
  username: string,
  domain: string,
  project: string,
  testset_id: string
): Promise<AxiosResponse<any>> =>
  api.get('/testset-details', { params: { username, domain, project, testset_id } })

export const getTestSetChildren = (
  username: string,
  domain: string,
  project: string,
  testset_id: string
): Promise<AxiosResponse<TreeResponse>> =>
  api.get('/testset-children', { params: { username, domain, project, testset_id } })

export const extractTestLabRecursive = (
  username: string,
  domain: string,
  project: string,
  node_id: string,
  node_type: string
): Promise<AxiosResponse<any>> =>
  api.post('/extract-testlab-recursive', null, { params: { username, domain, project, node_id, node_type } })

export const getDefects = (
  username: string,
  domain: string,
  project: string,
  start_index: number = 1,
  page_size: number = 100,
  query_filter?: string
): Promise<AxiosResponse<DefectsResponse>> =>
  api.get('/defects', { params: { username, domain, project, start_index, page_size, query_filter } })

export const getDefectDetails = (
  username: string,
  domain: string,
  project: string,
  defect_id: string
): Promise<AxiosResponse<DefectDetails>> =>
  api.get('/defect-details', { params: { username, domain, project, defect_id } })

export const downloadAttachment = (
  username: string,
  domain: string,
  project: string,
  attachment_id: string,
  filename: string
): string =>
  `${API_BASE}/download-attachment?username=${username}&domain=${domain}&project=${project}&attachment_id=${attachment_id}&filename=${encodeURIComponent(filename)}`

export const initSample = (): Promise<AxiosResponse> =>
  api.post('/init')

export default api

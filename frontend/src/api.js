import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const api = axios.create({ baseURL: API_BASE })

export async function authenticate(username, password){
  return api.post('/auth', { username, password })
}

export async function getDomains(){
  return api.get('/domains')
}

export async function getProjects(domain){
  return api.get('/projects', { params: { domain } })
}

export async function getTree(project, type){
  return api.get('/tree', { params: { project, type } })
}

export async function getDefects(project){
  return api.get('/defects', { params: { project } })
}

export async function initSample(){
  return api.post('/init')
}

export default api

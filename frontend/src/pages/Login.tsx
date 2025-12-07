import React, { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  FormControl,
  FormHelperText,
  MenuItem,
  Select,
  SelectChangeEvent,
  TextField,
  Typography,
} from '@mui/material'
import { authenticate, getDomains, getProjects, Domain, Project } from '../api'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

interface LoginPageState {
  step: number
  username: string
  password: string
  projectGroup: string
  projectGroups: string[]
  domains: Domain[]
  projects: Project[]
  selectedDomain: string
  selectedProject: string
  error: string
  loading: boolean
}

interface LoginProps {
  onLogin: (role: string) => void
}

const LoginPage: React.FC<LoginProps> = ({ onLogin }) => {
  const [state, setState] = useState<LoginPageState>({
    step: 1,
    username: '',
    password: '',
    projectGroup: 'default',
    projectGroups: ['default'],
    domains: [],
    projects: [],
    selectedDomain: '',
    selectedProject: '',
    error: '',
    loading: false,
  })

  React.useEffect(() => {
    // Load existing project groups
    loadProjectGroups()
  }, [])

  const loadProjectGroups = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/users/project-groups`)
      setState(prev => ({ 
        ...prev, 
        projectGroups: response.data.project_groups || ['default']
      }))
    } catch (err) {
      console.error('Failed to load project groups:', err)
    }
  }

  const handleAuthSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setState(prev => ({ ...prev, loading: true, error: '' }))

    try {
      // First, try ALM authentication
      const res = await authenticate(state.username, state.password)
      if (res.data.ok) {
        // ALM authentication successful - now register/update user
        try {
          await axios.post(`${API_BASE}/api/users/register`, null, {
            params: {
              username: state.username,
              password: state.password,
              project_group: state.projectGroup
            }
          })
        } catch (regErr) {
          console.error('User registration failed:', regErr)
          // Continue anyway if user exists
        }

        // Check if admin - skip domain/project selection
        const role = state.username.toLowerCase() === 'admin' ? 'admin' : 'user'
        if (role === 'admin') {
          localStorage.setItem('user', state.username)
          localStorage.setItem('role', 'admin')
          localStorage.setItem('project_group', state.projectGroup)
          onLogin('admin')
          return
        }

        // Load domains for regular users
        const domainsRes = await getDomains(state.username)
        setState(prev => ({
          ...prev,
          step: 2,
          domains: domainsRes.data,
          loading: false,
        }))
      } else {
        setState(prev => ({
          ...prev,
          error: res.data.message || 'Authentication failed',
          loading: false,
        }))
      }
    } catch (err: any) {
      setState(prev => ({
        ...prev,
        error: err.response?.data?.detail || 'Invalid username or password',
        loading: false,
      }))
    }
  }

  const handleDomainChange = async (e: SelectChangeEvent<string>) => {
    const domainName = e.target.value
    setState(prev => ({ ...prev, selectedDomain: domainName, loading: true, error: '' }))

    try {
      const res = await getProjects(domainName, state.username)
      if (res.data.length === 0) {
        setState(prev => ({
          ...prev,
          error: `No projects found for domain: ${domainName}`,
          loading: false,
        }))
      } else {
        setState(prev => ({
          ...prev,
          step: 3,
          projects: res.data,
          loading: false,
        }))
      }
    } catch (err: any) {
      setState(prev => ({
        ...prev,
        error: 'Failed to load projects',
        loading: false,
      }))
    }
  }

  const handleProjectChange = (e: SelectChangeEvent<string>) => {
    const project = e.target.value
    setState(prev => ({ ...prev, selectedProject: project }))
  }

  const handleLogin = async () => {
    setState(prev => ({ ...prev, loading: true }))
    
    try {
      // Call backend to load initial data (testplan, testlab, defects)
      const response = await axios.post(`${API_BASE}/api/login`, {
        username: state.username,
        domain: state.selectedDomain,
        project: state.selectedProject,
        project_group: state.projectGroup
      })
      
      console.log('Login successful:', response.data)
      
      // Store session data
      localStorage.setItem('user', state.username)
      localStorage.setItem('domain', state.selectedDomain)
      localStorage.setItem('project', state.selectedProject)
      localStorage.setItem('project_group', state.projectGroup)
      
      // Determine role
      const role = state.username.toLowerCase() === 'admin' ? 'admin' : 'user'
      localStorage.setItem('role', role)
      
      onLogin(role)
    } catch (err: any) {
      console.error('Login failed:', err)
      setState(prev => ({
        ...prev,
        error: err.response?.data?.detail || 'Login failed. Please try again.',
        loading: false
      }))
    }
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Card sx={{ width: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
              <img src="/logo.svg" alt="ReleaseCraft Logo" style={{ height: '80px' }} />
            </Box>

            {state.step === 1 && (
              <form onSubmit={handleAuthSubmit}>
                <Typography variant="h5" align="center" gutterBottom>
                  Sign In
                </Typography>
                
                <TextField
                  fullWidth
                  label="Username"
                  margin="normal"
                  value={state.username}
                  onChange={e => setState(prev => ({ ...prev, username: e.target.value }))}
                  disabled={state.loading}
                  required
                />
                <TextField
                  fullWidth
                  label="Password"
                  type="password"
                  margin="normal"
                  value={state.password}
                  onChange={e => setState(prev => ({ ...prev, password: e.target.value }))}
                  disabled={state.loading}
                  required
                />
                
                <FormControl fullWidth margin="normal">
                  <Typography variant="body2" gutterBottom>
                    Project Group
                  </Typography>
                  <Select
                    value={state.projectGroup}
                    onChange={(e) => setState(prev => ({ ...prev, projectGroup: e.target.value }))}
                    disabled={state.loading}
                  >
                    {state.projectGroups.map((group) => (
                      <MenuItem key={group} value={group}>
                        {group}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>Select or use 'default' for new users</FormHelperText>
                </FormControl>

                {state.error && <FormHelperText error>{state.error}</FormHelperText>}
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{ mt: 2 }}
                  disabled={state.loading}
                >
                  {state.loading ? 'Authenticating...' : 'Authenticate'}
                </Button>
              </form>
            )}

            {state.step === 2 && (
              <>
                <FormControl fullWidth margin="normal">
                  <Typography variant="body2" gutterBottom>
                    Select Domain
                  </Typography>
                  <Select
                    value={state.selectedDomain}
                    onChange={handleDomainChange}
                    disabled={state.loading}
                    displayEmpty
                  >
                    <MenuItem value="" disabled>
                      Select a domain...
                    </MenuItem>
                    {state.domains.map(domain => (
                      <MenuItem key={domain.id} value={domain.name}>
                        {domain.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                {state.error && <FormHelperText error>{state.error}</FormHelperText>}
              </>
            )}

            {state.step === 3 && (
              <>
                <FormControl fullWidth margin="normal">
                  <Typography variant="body2" gutterBottom>
                    Domain: {state.selectedDomain}
                  </Typography>
                </FormControl>
                <FormControl fullWidth margin="normal">
                  <Typography variant="body2" gutterBottom>
                    Select Project
                  </Typography>
                  <Select 
                    value={state.selectedProject} 
                    onChange={handleProjectChange}
                    displayEmpty
                  >
                    <MenuItem value="" disabled>
                      Select a project...
                    </MenuItem>
                    {state.projects.map(project => (
                      <MenuItem key={project.id} value={project.name}>
                        {project.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                  fullWidth
                  variant="contained"
                  sx={{ mt: 2 }}
                  onClick={handleLogin}
                  disabled={!state.selectedProject}
                >
                  Login
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </Box>
    </Container>
  )
}

export default LoginPage

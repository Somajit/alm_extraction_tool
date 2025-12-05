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

interface LoginPageState {
  step: number
  username: string
  password: string
  domains: Domain[]
  projects: Project[]
  selectedDomain: string
  selectedProject: string
  error: string
  loading: boolean
}

interface LoginProps {
  onLogin: () => void
}

const LoginPage: React.FC<LoginProps> = ({ onLogin }) => {
  const [state, setState] = useState<LoginPageState>({
    step: 1,
    username: '',
    password: '',
    domains: [],
    projects: [],
    selectedDomain: '',
    selectedProject: '',
    error: '',
    loading: false,
  })

  const handleAuthSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setState(prev => ({ ...prev, loading: true, error: '' }))

    try {
      const res = await authenticate(state.username, state.password)
      if (res.data.ok) {
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
        error: err.response?.data?.detail || err.message || 'Connection error',
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

  const handleLogin = () => {
    localStorage.setItem('user', state.username)
    localStorage.setItem('domain', state.selectedDomain)
    localStorage.setItem('project', state.selectedProject)
    onLogin()
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
                <TextField
                  fullWidth
                  label="Username"
                  margin="normal"
                  value={state.username}
                  onChange={e => setState(prev => ({ ...prev, username: e.target.value }))}
                  disabled={state.loading}
                />
                <TextField
                  fullWidth
                  label="Password"
                  type="password"
                  margin="normal"
                  value={state.password}
                  onChange={e => setState(prev => ({ ...prev, password: e.target.value }))}
                  disabled={state.loading}
                />
                {state.error && <FormHelperText error>{state.error}</FormHelperText>}
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{ mt: 2 }}
                  disabled={state.loading}
                >
                  Sign In
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

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
import { useNavigate } from 'react-router-dom'
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

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
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
        const domainsRes = await getDomains()
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
    const domain = e.target.value
    setState(prev => ({ ...prev, selectedDomain: domain, loading: true }))

    try {
      const res = await getProjects(domain)
      setState(prev => ({
        ...prev,
        step: 3,
        projects: res.data,
        loading: false,
      }))
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
    navigate('/home')
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Card sx={{ width: '100%' }}>
          <CardContent>
            <Typography variant="h5" component="h1" gutterBottom sx={{ mb: 3 }}>
              ALM Extraction Tool
            </Typography>

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
                  >
                    {state.domains.map(domain => (
                      <MenuItem key={domain.id} value={domain.id}>
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
                  <Select value={state.selectedProject} onChange={handleProjectChange}>
                    {state.projects.map(project => (
                      <MenuItem key={project.id} value={project.id}>
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

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, TextField, Typography, MenuItem, Select, FormControl, InputLabel } from '@mui/material'
import { authenticate, getDomains, getProjects } from '../api'

export default function Login(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [domains, setDomains] = useState([])
  const [projects, setProjects] = useState([])
  const [domain, setDomain] = useState('')
  const [project, setProject] = useState('')
  const [authed, setAuthed] = useState(false)
  const navigate = useNavigate()

  const doAuth = async () => {
    try{
      await authenticate(username, password)
      setAuthed(true)
      const res = await getDomains()
      setDomains(res.data)
    }catch(e){
      alert('Authentication failed')
    }
  }

  const chooseDomain = async (d) => {
    setDomain(d)
    setProject('')
    const res = await getProjects(d)
    setProjects(res.data)
  }

  const login = () => {
    localStorage.setItem('alm_user', username)
    localStorage.setItem('alm_project', project)
    navigate('/home')
  }

  return (
    <Box sx={{maxWidth:480, mx:'auto', mt:8, p:4, boxShadow:3, borderRadius:2}}>
      <Typography variant="h5" gutterBottom>ALM - Sign In</Typography>
      <TextField fullWidth label="Username" value={username} onChange={e=>setUsername(e.target.value)} sx={{mb:2}} />
      <TextField fullWidth label="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} sx={{mb:2}} />
      <Button variant="contained" onClick={doAuth} sx={{mr:2}}>Authenticate</Button>

      {authed && (
        <Box sx={{mt:3}}>
          <FormControl fullWidth sx={{mb:2}}>
            <InputLabel>Domain</InputLabel>
            <Select value={domain} label="Domain" onChange={(e)=>chooseDomain(e.target.value)}>
              {domains.map(d=> <MenuItem key={d.name} value={d.name}>{d.name}</MenuItem>)}
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{mb:2}}>
            <InputLabel>Project</InputLabel>
            <Select value={project} label="Project" onChange={(e)=>setProject(e.target.value)}>
              {projects.map(p=> <MenuItem key={p.name} value={p.name}>{p.name}</MenuItem>)}
            </Select>
          </FormControl>

          <Button variant="contained" color="primary" disabled={!project} onClick={login}>Login</Button>
        </Box>
      )}
    </Box>
  )
}

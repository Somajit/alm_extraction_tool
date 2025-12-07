import React, { useState, useEffect } from 'react'
import {
  AppBar,
  Box,
  Button,
  Container,
  Typography,
  Toolbar,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Tabs,
  Tab,
  Chip
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import axios from 'axios'
import { LogsViewer } from '../components/LogsViewer'

const API_BASE = 'http://localhost:8000'

interface User {
  username: string
  email: string
  role: string
  project_groups: string[]
  created_at: string
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ width: '100%' }}>
    {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
  </div>
)

interface AdminDashboardProps {
  onLogout: () => void
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ onLogout }) => {
  const adminUsername = localStorage.getItem('user') || ''
  
  const [tabValue, setTabValue] = useState(0)
  const [users, setUsers] = useState<User[]>([])
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [roleDialogOpen, setRoleDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [cleanAllDialogOpen, setCleanAllDialogOpen] = useState(false)
  const [selectedProjectGroup, setSelectedProjectGroup] = useState<string>('')
  const [newRole, setNewRole] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [dbStats, setDbStats] = useState<any>(null)

  useEffect(() => {
    loadUsers()
    if (tabValue === 2) {
      loadDbStats()
    }
  }, [tabValue])

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/admin/users`, {
        params: { admin_username: adminUsername }
      })
      setUsers(response.data.users || [])
      setLoading(false)
    } catch (err: any) {
      console.error('Failed to load users:', err)
      setError(err.response?.data?.detail || 'Failed to load users')
      setLoading(false)
    }
  }

  const loadDbStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/admin/db/stats`, {
        params: { admin_username: adminUsername }
      })
      setDbStats(response.data)
    } catch (err: any) {
      console.error('Failed to load database stats:', err)
      setError(err.response?.data?.detail || 'Failed to load database stats')
    }
  }

  const handleCleanAllData = async () => {
    try {
      const response = await axios.delete(`${API_BASE}/api/admin/db/clean-all`, {
        params: { admin_username: adminUsername }
      })
      setSuccess('All data cleaned successfully!')
      setError('')
      setCleanAllDialogOpen(false)
      loadDbStats()
      loadUsers()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clean all data')
    }
  }

  const handleOpenRoleDialog = (user: User) => {
    setSelectedUser(user)
    setNewRole(user.role)
    setRoleDialogOpen(true)
  }

  const handleCloseRoleDialog = () => {
    setRoleDialogOpen(false)
    setSelectedUser(null)
    setNewRole('')
  }

  const handleUpdateRole = async () => {
    if (!selectedUser) return

    try {
      await axios.put(`${API_BASE}/api/admin/users/role`, null, {
        params: {
          admin_username: adminUsername,
          target_username: selectedUser.username,
          new_role: newRole
        }
      })
      
      setSuccess(`User role updated to ${newRole}`)
      setError('')
      handleCloseRoleDialog()
      loadUsers()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update role')
    }
  }

  const handleOpenDeleteDialog = (user: User) => {
    setSelectedUser(user)
    setSelectedProjectGroup('')
    setDeleteDialogOpen(true)
  }

  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false)
    setSelectedUser(null)
    setSelectedProjectGroup('')
  }

  const handleDeleteUserData = async () => {
    if (!selectedUser) return

    try {
      const params: any = {
        admin_username: adminUsername,
        target_username: selectedUser.username
      }
      
      if (selectedProjectGroup) {
        params.project_group = selectedProjectGroup
      }
      
      const response = await axios.delete(`${API_BASE}/api/admin/users/data`, { params })
      
      const message = selectedProjectGroup 
        ? `Data deleted for user ${selectedUser.username} in project group "${selectedProjectGroup}"`
        : `All data deleted for user ${selectedUser.username}`
      
      setSuccess(message)
      setError('')
      handleCloseDeleteDialog()
      loadUsers()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete user data')
    }
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleLogout = () => {
    onLogout()
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <img src="/logo.svg" alt="ReleaseCraft Logo" style={{ height: '50px' }} />
            <Typography variant="h6" sx={{ ml: 2 }}>
              Admin Dashboard
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ mr: 2 }}>Admin: {adminUsername}</Typography>
          <Button color="inherit" onClick={handleLogout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ flex: 1, py: 2 }}>
        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

        <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="User Management" />
          <Tab label="System Logs" />
          <Tab label="Database" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                All Users ({users.length})
              </Typography>
              
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Username</strong></TableCell>
                      <TableCell><strong>Email</strong></TableCell>
                      <TableCell><strong>Role</strong></TableCell>
                      <TableCell><strong>Project Groups</strong></TableCell>
                      <TableCell><strong>Created</strong></TableCell>
                      <TableCell align="right"><strong>Actions</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.username}>
                        <TableCell>{user.username}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <Chip
                            label={user.role}
                            color={user.role === 'admin' ? 'error' : 'primary'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {user.project_groups && user.project_groups.length > 0 ? (
                            <Box>
                              {user.project_groups.map((group, idx) => (
                                <Typography key={idx} variant="body2">
                                  {group}
                                </Typography>
                              ))}
                            </Box>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              No project groups
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          {new Date(user.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            onClick={() => handleOpenRoleDialog(user)}
                            disabled={user.username === adminUsername}
                            size="small"
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton
                            onClick={() => handleOpenDeleteDialog(user)}
                            disabled={user.username === adminUsername}
                            size="small"
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <LogsViewer isAdmin={true} />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Database Overview
                </Typography>
                <Button
                  variant="contained"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setCleanAllDialogOpen(true)}
                >
                  Clean All Data
                </Button>
              </Box>

              {dbStats ? (
                <Box>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    Collection Statistics
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Collection</strong></TableCell>
                          <TableCell align="right"><strong>Document Count</strong></TableCell>
                          <TableCell align="right"><strong>Size (bytes)</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(dbStats.collections || {}).map(([collection, stats]: [string, any]) => (
                          <TableRow key={collection}>
                            <TableCell>{collection}</TableCell>
                            <TableCell align="right">{stats.count?.toLocaleString() || 0}</TableCell>
                            <TableCell align="right">{stats.size?.toLocaleString() || 0}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Total Database Size
                    </Typography>
                    <Typography variant="h4" color="primary">
                      {((dbStats.total_size || 0) / (1024 * 1024)).toFixed(2)} MB
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Total Documents: {(dbStats.total_documents || 0).toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  Loading database statistics...
                </Typography>
              )}
            </CardContent>
          </Card>
        </TabPanel>
      </Container>

      {/* Role Update Dialog */}
      <Dialog open={roleDialogOpen} onClose={handleCloseRoleDialog}>
        <DialogTitle>Update User Role</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            Update role for user: <strong>{selectedUser?.username}</strong>
          </Typography>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Role</InputLabel>
            <Select
              value={newRole}
              label="Role"
              onChange={(e) => setNewRole(e.target.value)}
            >
              <MenuItem value="user">User</MenuItem>
              <MenuItem value="admin">Admin</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseRoleDialog}>Cancel</Button>
          <Button onClick={handleUpdateRole} variant="contained" color="primary">
            Update Role
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete User Data Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleCloseDeleteDialog}>
        <DialogTitle>Clean User Data</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will permanently delete data for user <strong>{selectedUser?.username}</strong>
          </Alert>
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <Typography variant="body2" gutterBottom>
              Project Group (Optional)
            </Typography>
            <Select
              value={selectedProjectGroup}
              onChange={(e) => setSelectedProjectGroup(e.target.value)}
              displayEmpty
            >
              <MenuItem value="">All Project Groups</MenuItem>
              {selectedUser?.project_groups?.map((group) => (
                <MenuItem key={group} value={group}>
                  {group}
                </MenuItem>
              ))}
            </Select>
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
              Leave empty to delete data from all project groups
            </Typography>
          </FormControl>
          
          <Typography variant="body2" component="div" sx={{ mb: 1 }}>
            This will delete:
          </Typography>
          <Typography variant="body2" component="ul" sx={{ ml: 2 }}>
            <li>All projects and domains</li>
            <li>TestPlan and TestLab data</li>
            <li>Defects and test runs</li>
            <li>All cached data</li>
            {selectedProjectGroup && (
              <li><strong>Only for project group: {selectedProjectGroup}</strong></li>
            )}
          </Typography>
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            This action cannot be undone!
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>Cancel</Button>
          <Button onClick={handleDeleteUserData} variant="contained" color="error">
            {selectedProjectGroup ? `Delete Data in "${selectedProjectGroup}"` : 'Delete All Data'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clean All Data Dialog */}
      <Dialog open={cleanAllDialogOpen} onClose={() => setCleanAllDialogOpen(false)}>
        <DialogTitle>Clean All Database Data</DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            <strong>WARNING:</strong> This will permanently delete ALL data from the database!
          </Alert>
          
          <Typography variant="body2" component="div" sx={{ mb: 2 }}>
            This action will:
          </Typography>
          <Typography variant="body2" component="ul" sx={{ ml: 2 }}>
            <li>Delete all user data (except admin accounts)</li>
            <li>Delete all projects, domains, and configurations</li>
            <li>Delete all TestPlan and TestLab data</li>
            <li>Delete all defects and test runs</li>
            <li>Delete all cached data and attachments</li>
            <li>Clear all extraction results</li>
          </Typography>
          
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone! Make sure you have backups if needed.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCleanAllDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCleanAllData} variant="contained" color="error">
            Confirm - Delete All Data
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AdminDashboard

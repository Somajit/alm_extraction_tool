import React, { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material'
import { ExpandLess, ExpandMore, InsertDriveFile, Folder, AttachFile, Close, Download } from '@mui/icons-material'
import { getTree, getTestChildren, getTestDetails, getRunChildren, getRunJson, extractFolderRecursive, extractTestLabRecursive, TreeNode, downloadAttachment } from '../api'

interface TestTreeProps {
  type: 'TestPlan' | 'TestLab'
  username: string
  domain: string
  project: string
}

interface TreeNodeState extends TreeNode {
  expanded: boolean
  loaded: boolean
  data?: any
}

const TestTree: React.FC<TestTreeProps> = ({ type, username, domain, project }) => {
  const [treeData, setTreeData] = useState<TreeNodeState[]>([])
  const [loading, setLoading] = useState(true)
  const [contextMenu, setContextMenu] = useState<{ 
    mouseX: number; 
    mouseY: number; 
    treenode: TreeNodeState | null 
  } | null>(null)
  const [jsonDialog, setJsonDialog] = useState<{ open: boolean; content: any; title: string }>({
    open: false,
    content: null,
    title: ''
  })
  const [extracting, setExtracting] = useState(false)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  })

  useEffect(() => {
    loadTree()
  }, [type, project])

  const loadTree = async (folderId?: string) => {
    try {
      setLoading(true)
      const res = await getTree(
        project, 
        username, 
        domain, 
        type === 'TestPlan' ? 'testplan' : 'testlab',
        0,
        folderId
      )
      const treeWithState = res.data.tree.map((treenode: TreeNode) => addExpandedState(treenode))
      if (!folderId) {
        setTreeData(treeWithState)
      }
      return treeWithState
    } catch (err) {
      console.error('Failed to load tree:', err)
      return []
    } finally {
      setLoading(false)
    }
  }

  const addExpandedState = (treenode: TreeNode): TreeNodeState => ({
    ...treenode,
    expanded: false,
    loaded: !!(treenode.children && treenode.children.length > 0), // Mark as loaded if children already present
    children: treenode.children?.map(addExpandedState) || [],
  })

  const toggleNode = async (treenode: TreeNodeState) => {
    // If treenode is being expanded and hasn't loaded children yet
    if (!treenode.expanded && !treenode.loaded && treenode.has_children) {
      let children: TreeNodeState[] = []
      
      if (type === 'TestPlan') {
        // TestPlan logic
        if (treenode.type === 'folder') {
          // Fetch folder's subfolders, tests, and attachments
          children = await loadTree(treenode.folder_id)
        } else if (treenode.type === 'test') {
          // Fetch test's attachments and test.json
          const res = await getTestChildren(username, domain, project, treenode.test_id!)
          children = res.data.tree.map(addExpandedState)
        }
      } else if (type === 'TestLab') {
        // TestLab logic: releases, cycles, testsets
        if (treenode.type === 'release') {
          // Fetch release cycles
          children = await loadTree(`release_${treenode.release_id}`)
        } else if (treenode.type === 'cycle') {
          // Fetch test sets
          children = await loadTree(`cycle_${treenode.cycle_id}`)
        } else if (treenode.type === 'testset') {
          // Fetch test runs and attachments
          children = await loadTree(`testset_${treenode.testset_id}`)
        } else if (treenode.type === 'run') {
          // Fetch run details (run.json and attachments)
          const res = await getRunChildren(username, domain, project, treenode.run_id!)
          children = res.data.tree.map(addExpandedState)
        }
      }
      
      // If no children found, remove the + icon by setting has_children to false
      const hasChildren = children.length > 0
      setTreeData(prevData => updateNodeChildren(prevData, treenode.id, children, hasChildren))
    } else {
      // Just toggle expanded state
      setTreeData(prevData => updateNodeExpanded(prevData, treenode.id))
    }
  }

  const handleNodeClick = async (treenode: TreeNodeState) => {
    if (treenode.type === 'attachment') {
      // Download attachment
      handleAttachmentDownload(treenode)
    } else if (treenode.type === 'test-json') {
      // Fetch and display test.json for TestPlan
      try {
        const res = await getTestDetails(username, domain, project, treenode.test_id!)
        setJsonDialog({
          open: true,
          content: res.data,
          title: `Test Details: ${treenode.test_id}`
        })
      } catch (err) {
        console.error('Failed to fetch test details:', err)
      }
    } else if (treenode.type === 'run-json') {
      // Display run.json for TestLab runs
      try {
        const run_id = treenode.id.replace('runjson_', '')
        const res = await getRunJson(username, domain, project, run_id)
        setJsonDialog({
          open: true,
          content: res.data,
          title: `Run Details: ${run_id}`
        })
      } catch (err) {
        console.error('Failed to fetch run details:', err)
      }
    } else if (treenode.type === 'testset_json') {
      // Display testset.json for TestLab
      if (treenode.json_data) {
        setJsonDialog({
          open: true,
          content: treenode.json_data,
          title: `Test Set Details: ${treenode.testset_id}`
        })
      }
    } else if (treenode.has_children) {
      // Toggle expand/collapse for nodes with children
      toggleNode(treenode)
    }
  }

  const handleAttachmentDownload = (treenode: TreeNodeState) => {
    if (!treenode.attachment_id) {
      console.error('No attachment_id found for treenode:', treenode)
      return
    }

    const filename = treenode.label || `attachment_${treenode.attachment_id}`
    const url = downloadAttachment(username, domain, project, treenode.attachment_id, filename)
    
    // Create a temporary link element and trigger download
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const findNode = (nodes: TreeNodeState[], nodeId: string): TreeNodeState | null => {
    for (const treenode of nodes) {
      if (treenode.id === nodeId) return treenode
      if (treenode.children && treenode.children.length > 0) {
        const found = findNode(treenode.children as TreeNodeState[], nodeId)
        if (found) return found
      }
    }
    return null
  }

  const updateNodeChildren = (
    nodes: TreeNodeState[], 
    nodeId: string, 
    children: TreeNodeState[],
    hasChildren?: boolean
  ): TreeNodeState[] => {
    return nodes.map(treenode => {
      if (treenode.id === nodeId) {
        return { 
          ...treenode, 
          expanded: children.length > 0, // Only expand if there are children
          loaded: true, 
          has_children: hasChildren !== undefined ? hasChildren : (children.length > 0), // Update has_children based on actual children
          children: children 
        }
      }
      if (treenode.children && treenode.children.length > 0) {
        return { 
          ...treenode, 
          children: updateNodeChildren(treenode.children as TreeNodeState[], nodeId, children, hasChildren) 
        }
      }
      return treenode
    })
  }

  const updateNodeExpanded = (nodes: TreeNodeState[], nodeId: string): TreeNodeState[] => {
    return nodes.map(treenode => {
      if (treenode.id === nodeId) {
        return { ...treenode, expanded: !treenode.expanded }
      }
      if (treenode.children && treenode.children.length > 0) {
        return { ...treenode, children: updateNodeExpanded(treenode.children as TreeNodeState[], nodeId) }
      }
      return treenode
    })
  }

  const handleContextMenu = (e: React.MouseEvent, treenode: TreeNodeState) => {
    e.preventDefault()
    
    if (type === 'TestPlan') {
      // Only show context menu for folder nodes in TestPlan
      if (treenode.type === 'folder') {
        setContextMenu({ 
          mouseX: e.clientX, 
          mouseY: e.clientY,
          treenode: treenode
        })
      }
    } else if (type === 'TestLab') {
      // Show context menu for release and cycle nodes in TestLab
      if (treenode.type === 'release' || treenode.type === 'cycle') {
        setContextMenu({ 
          mouseX: e.clientX, 
          mouseY: e.clientY,
          treenode: treenode
        })
      }
    }
  }

  const handleCloseContext = () => {
    setContextMenu(null)
  }

  const handleExtractFolder = async () => {
    if (!contextMenu?.treenode) return
    
    const treenode = contextMenu.treenode
    handleCloseContext()
    
    try {
      setExtracting(true)
      setSnackbar({
        open: true,
        message: `Extracting ${type === 'TestPlan' ? 'folder' : treenode.type}: ${treenode.label}. This may take a while...`,
        severity: 'success'
      })
      
      let response: any
      
      if (type === 'TestPlan') {
        // Extract folder recursively
        response = await extractFolderRecursive(
          treenode.folder_id!
        )
      } else if (type === 'TestLab') {
        // Extract release or cycle recursively
        const { extractTestLabRecursive } = await import('../api')
        const nodeType = treenode.type === 'release' ? 'release' : 'cycle'
        const nodeId = treenode.type === 'release' ? treenode.release_id! : treenode.cycle_id!
        
        response = await extractTestLabRecursive(
          username,
          domain,
          project,
          nodeId,
          nodeType
        )
      }
      
      if (response?.data?.success) {
        const stats = response.data.stats || {}
        let statsMessage = ''
        
        if (stats.total_items) {
          if (type === 'TestPlan') {
            // TestPlan stats: folders, tests, attachments
            statsMessage = ` (${stats.total_items} items: ${stats.folders || 0} folders, ${stats.tests || 0} tests, ${stats.attachments || 0} attachments)`
          } else if (type === 'TestLab') {
            // TestLab stats: cycles, testsets, runs, attachments
            if (treenode.type === 'release') {
              statsMessage = ` (${stats.total_items} items: ${stats.cycles || 0} cycles, ${stats.testsets || 0} test sets, ${stats.runs || 0} runs, ${stats.attachments || 0} attachments)`
            } else if (treenode.type === 'cycle') {
              statsMessage = ` (${stats.total_items} items: ${stats.testsets || 0} test sets, ${stats.runs || 0} runs, ${stats.attachments || 0} attachments)`
            }
          }
        }
        
        setSnackbar({
          open: true,
          message: `Successfully extracted and stored ${type === 'TestPlan' ? 'folder' : treenode.type}: ${treenode.label}${statsMessage}`,
          severity: 'success'
        })
      }
    } catch (error: any) {
      console.error('Extraction failed:', error)
      setSnackbar({
        open: true,
        message: `Extraction failed: ${error.response?.data?.detail || error.message}`,
        severity: 'error'
      })
    } finally {
      setExtracting(false)
    }
  }

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false })
  }

  const handleCloseJsonDialog = () => {
    setJsonDialog({ open: false, content: null, title: '' })
  }

  const handleExportToJSON = async () => {
    if (!contextMenu?.treenode) return
    
    const treenode = contextMenu.treenode
    handleCloseContext()
    
    try {
      setExtracting(true)
      
      let extractedData: any = null
      
      if (type === 'TestPlan') {
        // Extract folder hierarchy for TestPlan
        if (treenode.type === 'folder' && treenode.folder_id) {
          const response = await extractFolderRecursive(treenode.folder_id)
          extractedData = response.data
        } else {
          throw new Error('Can only export folder nodes in TestPlan')
        }
      } else if (type === 'TestLab') {
        // Extract release/cycle hierarchy for TestLab
        if (treenode.type === 'release' && treenode.release_id) {
          const response = await extractTestLabRecursive(username, domain, project, treenode.release_id, 'release')
          extractedData = response.data
        } else if (treenode.type === 'cycle' && treenode.cycle_id) {
          const response = await extractTestLabRecursive(username, domain, project, treenode.cycle_id, 'cycle')
          extractedData = response.data
        } else {
          throw new Error('Can only export release or cycle nodes in TestLab')
        }
      }
      
      if (!extractedData) {
        throw new Error('No data extracted')
      }
      
      // Create export package with metadata
      const exportPackage = {
        metadata: {
          exportType: type,
          nodeType: treenode.type,
          nodeId: treenode.id,
          nodeName: treenode.label,
          timestamp: new Date().toISOString(),
          domain: domain,
          project: project
        },
        statistics: extractedData.stats || {},
        data: extractedData.data || extractedData
      }
      
      // Create and download JSON file
      const dataStr = JSON.stringify(exportPackage, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${type}_${treenode.type}_${treenode.label.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      setSnackbar({
        open: true,
        message: `Tree exported successfully with ${extractedData.stats?.total_items || 0} items!`,
        severity: 'success'
      })
    } catch (error: any) {
      console.error('Export error:', error)
      setSnackbar({
        open: true,
        message: `Export failed: ${error.message || error}`,
        severity: 'error'
      })
    } finally {
      setExtracting(false)
    }
  }

  const handleDetailsClick = () => {
    if (!contextMenu?.treenode) return
    
    const treenode = contextMenu.treenode
    handleCloseContext()
    
    // Show treenode details in JSON dialog
    const nodeDetails = {
      id: treenode.id,
      name: treenode.label,
      type: treenode.type,
      hasChildren: treenode.children && treenode.children.length > 0,
      childrenCount: treenode.children ? treenode.children.length : 0,
      data: treenode.data || {}
    }
    
    setJsonDialog({
      open: true,
      content: nodeDetails,
      title: `${(treenode.type || 'treenode').charAt(0).toUpperCase() + (treenode.type || 'treenode').slice(1)} Details: ${treenode.label}`
    })
  }

  const getNodeIcon = (treenode: TreeNodeState) => {
    if (treenode.type === 'folder') {
      return <Folder fontSize="small" sx={{ mr: 1, color: '#FFA726' }} /> // Orange folder
    } else if (treenode.type === 'container') {
      if (treenode.label === 'Subfolders') {
        return <Folder fontSize="small" sx={{ mr: 1, color: '#42A5F5' }} /> // Blue folder
      } else if (treenode.label === 'Tests') {
        return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#66BB6A' }} /> // Green file
      } else if (treenode.label === 'Attachments') {
        return <AttachFile fontSize="small" sx={{ mr: 1, color: '#AB47BC' }} /> // Purple attachment
      }
      return <Folder fontSize="small" sx={{ mr: 1, color: '#64b5f6' }} />
    } else if (treenode.type === 'test') {
      return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#4CAF50' }} /> // Green test file
    } else if (treenode.type === 'attachment') {
      const filename = treenode.label?.toLowerCase() || ''
      if (filename.endsWith('.png') || filename.endsWith('.jpg') || filename.endsWith('.jpeg')) {
        return <AttachFile fontSize="small" sx={{ mr: 1, color: '#E91E63' }} /> // Pink image
      } else if (filename.endsWith('.pdf')) {
        return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#F44336' }} /> // Red PDF
      } else if (filename.endsWith('.csv') || filename.endsWith('.xlsx')) {
        return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#4CAF50' }} /> // Green spreadsheet
      } else if (filename.endsWith('.txt') || filename.endsWith('.log')) {
        return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#9E9E9E' }} /> // Gray text
      } else if (filename.endsWith('.json') || filename.endsWith('.xml')) {
        return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#FF9800' }} /> // Orange data
      } else if (filename.endsWith('.html')) {
        return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#2196F3' }} /> // Blue HTML
      } else if (filename.endsWith('.docx')) {
        return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#2196F3' }} /> // Blue document
      } else if (filename.endsWith('.sql')) {
        return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#00BCD4' }} /> // Cyan SQL
      }
      return <AttachFile fontSize="small" sx={{ mr: 1, color: '#AB47BC' }} /> // Default purple
    } else if (treenode.type === 'test-json' || treenode.type === 'testset_json' || treenode.type === 'run-json') {
      return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#FF9800' }} /> // Orange JSON
    } else if (treenode.type === 'release') {
      return <Folder fontSize="small" sx={{ mr: 1, color: '#9C27B0' }} /> // Purple release
    } else if (treenode.type === 'cycle') {
      return <Folder fontSize="small" sx={{ mr: 1, color: '#3F51B5' }} /> // Indigo cycle
    } else if (treenode.type === 'testset') {
      return <Folder fontSize="small" sx={{ mr: 1, color: '#00BCD4' }} /> // Cyan testset
    } else if (treenode.type === 'run') {
      return <InsertDriveFile fontSize="small" sx={{ mr: 1, color: '#66bb6a' }} /> // Green run
    }
    return null
  }

  const renderTreeNode = (treenode: TreeNodeState, depth: number = 0): React.ReactNode => (
    <Box key={treenode.id}>
      <ListItem disablePadding sx={{ pl: depth * 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          {treenode.has_children ? (
            <IconButton size="small" onClick={() => toggleNode(treenode)}>
              {treenode.expanded ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          ) : (
            <Box sx={{ width: 40 }} /> // Spacer for alignment
          )}
          <ListItemButton
            sx={{ 
              flex: 1, 
              display: 'flex', 
              alignItems: 'center',
              cursor: treenode.type === 'attachment' || treenode.type === 'test-json' || treenode.type === 'testset_json' || treenode.type === 'run-json' ? 'pointer' : 'default'
            }}
            onContextMenu={(e) => handleContextMenu(e, treenode)}
            onClick={() => handleNodeClick(treenode)}
          >
            {getNodeIcon(treenode)}
            <ListItemText 
              primary={treenode.label}
              sx={{
                '& .MuiTypography-root': {
                  fontWeight: treenode.type === 'folder' ? 600 : 400,
                  color: treenode.type === 'test-json' ? '#ffa726' : 
                         treenode.type === 'attachment' ? '#ab47bc' : 'inherit'
                }
              }}
            />
          </ListItemButton>
        </Box>
      </ListItem>
      {treenode.children && treenode.children.length > 0 && (
        <Collapse in={treenode.expanded} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {(treenode.children as TreeNodeState[]).map((child: TreeNodeState) => renderTreeNode(child, depth + 1))}
          </List>
        </Collapse>
      )}
    </Box>
  )

  if (loading) return <Typography>Loading {type}...</Typography>
  if (treeData.length === 0) return <Typography>No {type} data available</Typography>

  return (
    <Box>
      {extracting && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, p: 2, bgcolor: '#e3f2fd', borderRadius: 1 }}>
          <CircularProgress size={20} />
          <Typography>Extracting folder data recursively...</Typography>
        </Box>
      )}
      
      <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
        {treeData.map(treenode => renderTreeNode(treenode))}
      </List>

      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContext}
        anchorPosition={contextMenu ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined}
        anchorReference="anchorPosition"
      >
        <MenuItem onClick={handleExtractFolder} disabled={extracting}>
          Extract {contextMenu?.treenode?.type === 'folder' ? 'Folder' : 
                  contextMenu?.treenode?.type === 'release' ? 'Release' : 'Cycle'} (Recursive)
        </MenuItem>
        <MenuItem onClick={handleExportToJSON}>
          <Download fontSize="small" sx={{ mr: 1 }} />
          Export to JSON
        </MenuItem>
        <MenuItem onClick={handleDetailsClick}>View Details</MenuItem>
      </Menu>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* JSON Viewer Dialog */}
      <Dialog
        open={jsonDialog.open}
        onClose={handleCloseJsonDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {jsonDialog.title}
          <IconButton
            aria-label="close"
            onClick={handleCloseJsonDialog}
            sx={{
              color: (theme) => theme.palette.grey[500],
            }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Box
            component="pre"
            sx={{
              bgcolor: '#1e1e1e',
              color: '#d4d4d4',
              padding: 2,
              borderRadius: 1,
              overflow: 'auto',
              maxHeight: '70vh',
              fontFamily: 'Consolas, Monaco, "Courier New", monospace',
              fontSize: '0.875rem',
              lineHeight: 1.5,
            }}
          >
            {jsonDialog.content ? JSON.stringify(jsonDialog.content, null, 2) : ''}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseJsonDialog} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default TestTree

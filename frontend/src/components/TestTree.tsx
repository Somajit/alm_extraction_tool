import React, { useEffect, useState } from 'react'
import {
  Box,
  Collapse,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from '@mui/material'
import { ExpandLess, ExpandMore } from '@mui/icons-material'
import { getTree, TreeNode } from '../api'

interface TestTreeProps {
  type: 'TestPlan' | 'TestLab'
}

interface TreeNodeState extends TreeNode {
  expanded: boolean
}

const TestTree: React.FC<TestTreeProps> = ({ type }) => {
  const [treeData, setTreeData] = useState<TreeNodeState[]>([])
  const [loading, setLoading] = useState(true)
  const [contextMenu, setContextMenu] = useState<{ mouseX: number; mouseY: number } | null>(null)

  useEffect(() => {
    loadTree()
  }, [type])

  const loadTree = async () => {
    try {
      const project = localStorage.getItem('project') || ''
      const res = await getTree(project, type)
      const treeWithState = res.data.tree.map((node: TreeNode) => addExpandedState(node))
      setTreeData(treeWithState)
    } catch (err) {
      console.error('Failed to load tree:', err)
    } finally {
      setLoading(false)
    }
  }

  const addExpandedState = (node: TreeNode): TreeNodeState => ({
    ...node,
    expanded: false,
    children: node.children?.map(addExpandedState) || [],
  })

  const toggleNode = (nodeId: string) => {
    setTreeData(prevData => updateNodeExpanded(prevData, nodeId))
  }

  const updateNodeExpanded = (nodes: TreeNodeState[], nodeId: string): TreeNodeState[] => {
    return nodes.map(node => {
      if (node.id === nodeId) {
        return { ...node, expanded: !node.expanded }
      }
      if (node.children && node.children.length > 0) {
        return { ...node, children: updateNodeExpanded(node.children as TreeNodeState[], nodeId) }
      }
      return node
    })
  }

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault()
    setContextMenu({ mouseX: e.clientX, mouseY: e.clientY })
  }

  const handleCloseContext = () => {
    setContextMenu(null)
  }

  const renderTreeNode = (node: TreeNodeState, depth: number = 0): React.ReactNode => (
    <Box key={node.id}>
      <ListItem disablePadding sx={{ pl: depth * 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          {node.children && node.children.length > 0 && (
            <IconButton size="small" onClick={() => toggleNode(node.id)}>
              {node.expanded ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          )}
          <ListItemButton
            sx={{ flex: 1 }}
            onContextMenu={handleContextMenu}
          >
            <ListItemText primary={node.label} />
          </ListItemButton>
        </Box>
      </ListItem>
      {node.children && node.children.length > 0 && (
        <Collapse in={node.expanded} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {(node.children as TreeNodeState[]).map((child: TreeNodeState) => renderTreeNode(child, depth + 1))}
          </List>
        </Collapse>
      )}
    </Box>
  )

  if (loading) return <Typography>Loading {type}...</Typography>
  if (treeData.length === 0) return <Typography>No {type} data available</Typography>

  return (
    <Box>
      <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
        {treeData.map(node => renderTreeNode(node))}
      </List>

      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContext}
        anchorPosition={contextMenu ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined}
        anchorReference="anchorPosition"
      >
        <MenuItem onClick={handleCloseContext}>View Details</MenuItem>
        <MenuItem onClick={handleCloseContext}>Export</MenuItem>
      </Menu>
    </Box>
  )
}

export default TestTree

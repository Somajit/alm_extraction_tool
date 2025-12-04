import React, { useEffect, useState } from 'react'
import { Box, Menu, MenuItem, Paper, List, ListItemButton, ListItemText, Collapse, IconButton } from '@mui/material'
import ExpandLess from '@mui/icons-material/ExpandLess'
import ExpandMore from '@mui/icons-material/ExpandMore'
import FolderIcon from '@mui/icons-material/Folder'
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile'
import { getTree } from '../api'

function TreeNode({ node, onContext }){
  const [open, setOpen] = useState(true)
  const hasChildren = Array.isArray(node.children) && node.children.length > 0

  return (
    <>
      <ListItemButton onClick={()=> setOpen(!open)} onContextMenu={(e)=>onContext(e,node)}>
        <IconButton size="small" sx={{mr:1}}>
          {hasChildren ? <FolderIcon fontSize="small"/> : <InsertDriveFileIcon fontSize="small"/>}
        </IconButton>
        <ListItemText primary={node.label} />
        {hasChildren ? (open ? <ExpandLess/> : <ExpandMore/>) : null}
      </ListItemButton>

      {hasChildren && (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List component="div" disablePadding sx={{pl:4}}>
            {node.children.map(ch => (
              <TreeNode key={ch.id} node={ch} onContext={onContext} />
            ))}
          </List>
        </Collapse>
      )}
    </>
  )
}

export default function TestTree({project, type}){
  const [tree, setTree] = useState([])
  const [menu, setMenu] = useState(null)
  const [menuNode, setMenuNode] = useState(null)

  useEffect(()=>{
    if(project) load()
  },[project])

  async function load(){
    const res = await getTree(project, type)
    setTree(res.data.tree || [])
  }

  const handleContext = (event, node) => {
    event.preventDefault()
    setMenuNode(node)
    setMenu({ mouseX: event.clientX + 2, mouseY: event.clientY - 6 })
  }

  const handleClose = () => setMenu(null)

  return (
    <Paper sx={{p:2}}>
      <List>
        {tree.map(n => (
          <TreeNode key={n.id} node={n} onContext={handleContext} />
        ))}
      </List>

      <Menu open={Boolean(menu)} onClose={handleClose} anchorReference="anchorPosition" anchorPosition={menu ? {top: menu.mouseY, left: menu.mouseX} : undefined}>
        <MenuItem onClick={()=>{ alert('Extract: '+(menuNode?.label||'')); handleClose() }}>Extract</MenuItem>
        <MenuItem onClick={()=>{ handleClose() }}>Details</MenuItem>
      </Menu>
    </Paper>
  )
}

import React from 'react';
import {
  Box,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Collapse,
  Tooltip,
  Button
} from '@mui/material';
import FolderIcon from '@mui/icons-material/Folder';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import StorageIcon from '@mui/icons-material/Storage';
import LaunchIcon from '@mui/icons-material/Launch';

interface TreeNode {
  id: number;
  name: string;
  children: TreeNode[];
  artifact: Artifact[];
}

interface Artifact {
  name: string;
  type: string;
  file_path: string;
}

interface NodeTreeProps {
  node: TreeNode;
  depth?: number;
  workflowId: string | number;
  onNodeSelect: (node: TreeNode, navigate: boolean) => void;
}

const NodeTree: React.FC<NodeTreeProps> = ({ node, depth = 0, workflowId, onNodeSelect }) => {
  const [expanded, setExpanded] = React.useState(depth < 1);

  const hasChildren = node.children && node.children.length > 0;
  const hasArtifacts = node.artifact && node.artifact.length > 0;

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setExpanded(!expanded);
  };

  const handleNodeClick = () => {
    // Default action is to navigate to node details
    onNodeSelect(node, true);
  };

  const handleViewLogs = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Open drawer instead of navigating
    onNodeSelect(node, false);
  };

  // Indentation for tree levels
  const paddingLeft = depth * 2;

  return (
    <>
      <ListItem
        onClick={handleNodeClick}
        sx={{
          pl: paddingLeft,
          borderLeft: expanded && hasChildren ? `2px solid ${getColorForDepth(depth)}` : 'none',
          py: 0.5,
          '&:hover': {
            bgcolor: 'action.hover',
          },
        }}
        dense
      >
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          {hasChildren ? (
            <IconButton
              size="small"
              onClick={handleToggleExpand}
              edge="start"
              sx={{ mr: 0.5, p: 0.25 }}
            >
              {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
            </IconButton>
          ) : (
            <Box sx={{ width: 24 }} /> // Spacer for alignment
          )}

          {hasChildren ? (
            expanded ? <FolderOpenIcon fontSize="small" color="primary" /> : <FolderIcon fontSize="small" color="primary" />
          ) : (
            <InsertDriveFileIcon fontSize="small" color="action" />
          )}

          <ListItemText
            primary={node.name || `Node ${node.id}`}
            primaryTypographyProps={{
              variant: "body2",
              noWrap: true,
              sx: { ml: 1 },
            }}
          />

          {hasArtifacts && (
            <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
              <Button
                size="small"
                onClick={handleViewLogs}
                startIcon={<StorageIcon fontSize="small" color="secondary" />}
                sx={{ mr: 1, py: 0, minWidth: 0 }}
              >
                Logs
              </Button>
              <Tooltip title="Open node details">
                <LaunchIcon fontSize="small" color="action" />
              </Tooltip>
            </Box>
          )}
        </Box>
      </ListItem>

      {hasChildren && (
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <List disablePadding>
            {node.children.map(childNode => (
              <NodeTree
                key={childNode.id}
                node={childNode}
                depth={depth + 1}
                workflowId={workflowId}
                onNodeSelect={onNodeSelect}
              />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
};

// Helper function to get different colors based on depth
function getColorForDepth(depth: number): string {
  const colors = [
    '#2196f3', // primary blue
    '#00bcd4', // cyan
    '#4caf50', // green
    '#ff9800', // orange
    '#9c27b0', // purple
  ];
  return colors[depth % colors.length];
}

export default NodeTree;

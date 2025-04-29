import React, { useState } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Divider,
  Tabs,
  Tab,
  AppBar,
  Toolbar,
  Chip,
  Button
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import LogViewer from './LogViewer';

interface Artifact {
  name: string;
  type: string;
  file_path: string;
}

interface TreeNode {
  id: number;
  name: string;
  children: TreeNode[];
  artifact: Artifact[];
}

interface ArtifactDrawerProps {
  open: boolean;
  onClose: () => void;
  selectedNode: TreeNode | null;
}

const ArtifactDrawer: React.FC<ArtifactDrawerProps> = ({ open, onClose, selectedNode }) => {
  const [selectedTabIndex, setSelectedTabIndex] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTabIndex(newValue);
  };

  const artifacts = selectedNode?.artifact || [];
  const hasArtifacts = artifacts.length > 0;

  const handleOpenNodeDetails = () => {
    if (selectedNode) {
      window.location.href = `/workflows/${selectedNode.id}/nodes/${selectedNode.id}`;
    }
  };

  return (
    <Drawer
      anchor="bottom"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          height: { xs: '100%', sm: '70%', md: '60%' },
          overflow: 'hidden'
        },
      }}
    >
      <AppBar position="static" color="default" elevation={0}>
        <Toolbar variant="dense">
          <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center' }}>
            <Typography variant="subtitle1" component="div" sx={{ mr: 2 }}>
              {selectedNode?.name || 'Node Details'}
            </Typography>
            <Chip 
              label={`ID: ${selectedNode?.id}`} 
              size="small" 
              color="primary" 
              variant="outlined"
            />
          </Box>
          <Button
            size="small"
            startIcon={<OpenInNewIcon />}
            onClick={handleOpenNodeDetails}
            sx={{ mr: 2 }}
          >
            Open Details
          </Button>
          <IconButton edge="end" color="inherit" onClick={onClose} aria-label="close" size="small">
            <CloseIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {hasArtifacts ? (
        <>
          <AppBar position="static" color="default" elevation={0}>
            <Tabs
              value={selectedTabIndex}
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              variant="scrollable"
              scrollButtons="auto"
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              {artifacts.map((artifact, index) => (
                <Tab 
                  key={index} 
                  label={artifact.name} 
                  id={`artifact-tab-${index}`}
                  aria-controls={`artifact-tabpanel-${index}`}
                />
              ))}
            </Tabs>
          </AppBar>
          
          <Box sx={{ 
            overflow: 'auto', 
            height: 'calc(100% - 96px)',
            p: 2 
          }}>
            {artifacts.map((artifact, index) => (
              <div
                key={index}
                role="tabpanel"
                hidden={selectedTabIndex !== index}
                id={`artifact-tabpanel-${index}`}
                aria-labelledby={`artifact-tab-${index}`}
                style={{ height: '100%' }}
              >
                {selectedTabIndex === index && (
                  <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" component="div">
                        Type: {artifact.type} • Path: {artifact.file_path}
                      </Typography>
                    </Box>
                    <Divider sx={{ mb: 1 }} />
                    <Box sx={{ flexGrow: 1, height: 'calc(100% - 30px)' }}>
                      <LogViewer 
                        artifactPath={artifact.file_path}
                        artifactName={artifact.name}
                      />
                    </Box>
                  </Box>
                )}
              </div>
            ))}
          </Box>
        </>
      ) : (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="subtitle1" gutterBottom>
            No artifacts found for this node
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This node doesn't have any associated artifacts to display.
          </Typography>
        </Box>
      )}
    </Drawer>
  );
};

export default ArtifactDrawer;

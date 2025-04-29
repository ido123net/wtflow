import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  Paper,
  Breadcrumbs,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import HomeIcon from '@mui/icons-material/Home';
import FolderIcon from '@mui/icons-material/Folder';
import StorageIcon from '@mui/icons-material/Storage';
import LogViewer from '../components/LogViewer';

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

const fetchNodeData = async (workflowId: string, nodeId: string) => {
  console.log(`Fetching node: ${nodeId} from workflow: ${workflowId}`);
  
  // This is a simplified approach - in a real app, you'd want to get only this node data
  // For now, we're getting the whole tree and finding our node
  const { data } = await axios.get(`http://localhost:8000/api/v1/workflow/${workflowId}/tree`);
  
  const findNode = (node: TreeNode): TreeNode | null => {
    if (node.id === parseInt(nodeId)) {
      return node;
    }
    
    if (node.children) {
      for (const child of node.children) {
        const found = findNode(child);
        if (found) return found;
      }
    }
    
    return null;
  };
  
  const nodeData = findNode(data);
  if (!nodeData) {
    throw new Error(`Node ${nodeId} not found in workflow ${workflowId}`);
  }
  
  return { nodeData, workflowName: data.name, workflowId: data.id };
};

function NodeDetails() {
  const { workflowId, nodeId, artifactName } = useParams<{ 
    workflowId: string; 
    nodeId: string; 
    artifactName: string; 
  }>();
  const navigate = useNavigate();
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['node', workflowId, nodeId],
    queryFn: () => fetchNodeData(workflowId!, nodeId!),
    enabled: !!workflowId && !!nodeId,
  });
  
  const [selectedTab, setSelectedTab] = useState(0);
  
  // Update selected tab when the artifactName changes
  useEffect(() => {
    if (data?.nodeData.artifact && artifactName) {
      const index = data.nodeData.artifact.findIndex(a => a.name === artifactName);
      if (index >= 0) {
        setSelectedTab(index);
      }
    }
  }, [data, artifactName]);
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
    
    // Update URL with the selected artifact name
    if (data?.nodeData.artifact && data.nodeData.artifact[newValue]) {
      navigate(`/workflows/${workflowId}/nodes/${nodeId}/artifacts/${data.nodeData.artifact[newValue].name}`);
    }
  };
  
  if (isLoading) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error || !data) {
    return (
      <Container sx={{ py: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Error loading node: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
        <Button
          component={Link}
          to={`/workflows/${workflowId}`}
          startIcon={<ArrowBackIcon />}
          variant="outlined"
          size="small"
        >
          Back to workflow
        </Button>
      </Container>
    );
  }
  
  const { nodeData, workflowName } = data;
  const artifacts = nodeData.artifact || [];
  const hasArtifacts = artifacts.length > 0;
  
  return (
    <Box>
      <Container maxWidth="md" sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Breadcrumbs aria-label="breadcrumb">
            <Link to="/" style={{ display: 'flex', alignItems: 'center', color: 'inherit', textDecoration: 'none' }}>
              <HomeIcon sx={{ mr: 0.5 }} fontSize="small" />
              <Typography variant="body2">Workflows</Typography>
            </Link>
            <Link 
              to={`/workflows/${workflowId}`} 
              style={{ display: 'flex', alignItems: 'center', color: 'inherit', textDecoration: 'none' }}
            >
              <FolderIcon sx={{ mr: 0.5 }} fontSize="small" />
              <Typography variant="body2">{workflowName || `Workflow ${workflowId}`}</Typography>
            </Link>
            <Typography color="text.primary" variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
              <StorageIcon sx={{ mr: 0.5 }} fontSize="small" />
              {nodeData.name || `Node ${nodeId}`}
            </Typography>
          </Breadcrumbs>

          <Button
            component={Link}
            to={`/workflows/${workflowId}`}
            startIcon={<ArrowBackIcon />}
            variant="outlined"
            size="small"
          >
            Back
          </Button>
        </Box>

        <Paper variant="outlined" sx={{ mb: 2, py: 1, px: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 'medium' }}>
            {nodeData.name || `Node ${nodeId}`}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            ID: {nodeData.id}
          </Typography>
        </Paper>

        {hasArtifacts ? (
          <Paper variant="outlined">
            <Tabs
              value={selectedTab}
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              variant="scrollable"
              scrollButtons="auto"
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              {artifacts.map((artifact, index) => (
                <Tab 
                  key={artifact.name}
                  label={artifact.name}
                  id={`artifact-tab-${index}`}
                  aria-controls={`artifact-tabpanel-${index}`}
                />
              ))}
            </Tabs>
            
            <Box sx={{ height: 'calc(100vh - 250px)', p: 2 }}>
              {artifacts.map((artifact, index) => (
                <Box
                  key={artifact.name}
                  role="tabpanel"
                  hidden={selectedTab !== index}
                  id={`artifact-tabpanel-${index}`}
                  aria-labelledby={`artifact-tab-${index}`}
                  sx={{ height: '100%' }}
                >
                  {selectedTab === index && (
                    <Box sx={{ height: '100%' }}>
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" component="div">
                          Type: {artifact.type} • Path: {artifact.file_path}
                        </Typography>
                      </Box>
                      <Divider sx={{ mb: 2 }} />
                      <Box sx={{ height: 'calc(100% - 30px)' }}>
                        <LogViewer 
                          artifactPath={artifact.file_path}
                          artifactName={artifact.name}
                        />
                      </Box>
                    </Box>
                  )}
                </Box>
              ))}
            </Box>
          </Paper>
        ) : (
          <Alert severity="info">No artifacts found for this node</Alert>
        )}
      </Container>
    </Box>
  );
}

export default NodeDetails;

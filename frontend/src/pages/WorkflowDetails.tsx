import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";
import {
    Container,
    Typography,
    Box,
    CircularProgress,
    Alert,
    Button,
    Paper,
    List,
    IconButton,
    Breadcrumbs
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import HomeIcon from "@mui/icons-material/Home";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import RefreshIcon from "@mui/icons-material/Refresh";
import StorageIcon from "@mui/icons-material/Storage";
import NodeTree from "../components/NodeTree";
import ArtifactDrawer from "../components/ArtifactDrawer";

// Define interfaces
interface TreeNode {
    id: number;
    name: string;
    children: TreeNode[];
    artifact: Array<{
        name: string;
        type: string;
        file_path: string;
    }>;
}

const fetchWorkflow = async (id: string) => {
    console.log(`Fetching workflow: ${id}`);
    const { data } = await axios.get(`http://localhost:8000/api/v1/workflow/${id}/tree`);
    console.log("Workflow tree data:", data);
    return data;
};

function WorkflowDetails() {
    const { id } = useParams<{ id: string }>();
    const { data: workflowTree, isLoading, error, refetch } = useQuery({
        queryKey: ["workflow", id, "tree"],
        queryFn: () => fetchWorkflow(id!),
        enabled: !!id,
    });

    // State for the artifact drawer
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);

    // Handler for node selection
    const handleNodeSelect = (node: TreeNode, navigate: boolean) => {
        if (navigate) {
            window.location.href = `/workflows/${id}/nodes/${node.id}`;
            return;
        }
        setSelectedNode(node);
        setDrawerOpen(true);
    };

    // Function to open drawer with specific node
    const openArtifactDrawer = (node: TreeNode) => {
        setSelectedNode(node);
        setDrawerOpen(true);
    };

    if (isLoading) return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}
        >
            <CircularProgress />
        </Box>
    );

    if (error) return (
        <Container maxWidth="md" sx={{ py: 3 }}>
            <Alert severity="error" sx={{ mb: 2 }}>
                Error loading workflow
            </Alert>
            <Button
                component={Link}
                to="/"
                startIcon={<ArrowBackIcon />}
                variant="outlined"
                size="small"
            >
                Back to workflows
            </Button>
        </Container>
    );

    // Check if we have a valid tree
    if (!workflowTree) {
        return (
            <Container maxWidth="md" sx={{ py: 3 }}>
                <Alert severity="warning" sx={{ mb: 2 }}>
                    No workflow data found
                </Alert>
                <Button
                    component={Link}
                    to="/"
                    startIcon={<ArrowBackIcon />}
                    variant="outlined"
                    size="small"
                >
                    Back to workflows
                </Button>
            </Container>
        );
    }

    return (
        <Box>
            <Container maxWidth="md" sx={{ py: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Breadcrumbs aria-label="breadcrumb">
                        <Link to="/" style={{ display: 'flex', alignItems: 'center', color: 'inherit', textDecoration: 'none' }}>
                            <HomeIcon sx={{ mr: 0.5 }} fontSize="small" />
                            <Typography variant="body2">Workflows</Typography>
                        </Link>
                        <Typography color="text.primary" variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                            <AccountTreeIcon sx={{ mr: 0.5 }} fontSize="small" />
                            {workflowTree.name}
                        </Typography>
                    </Breadcrumbs>

                    <Box>
                        <IconButton
                            size="small"
                            onClick={() => refetch()}
                            title="Refresh workflow"
                            sx={{ mr: 1 }}
                        >
                            <RefreshIcon fontSize="small" />
                        </IconButton>
                        <Button
                            component={Link}
                            to="/"
                            startIcon={<ArrowBackIcon />}
                            variant="outlined"
                            size="small"
                        >
                            Back
                        </Button>
                    </Box>
                </Box>

                <Paper
                    variant="outlined"
                    sx={{ mb: 2, py: 1, px: 2 }}
                >
                    <Typography variant="h6" sx={{ fontWeight: 'medium' }}>
                        {workflowTree.name}
                    </Typography>
                </Paper>

                <Paper variant="outlined">
                    <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'medium', display: 'flex', alignItems: 'center' }}>
                            <AccountTreeIcon sx={{ mr: 0.5, fontSize: 18 }} />
                        </Typography>
                    </Box>

                    <List
                        dense
                        disablePadding
                        sx={{
                            overflow: 'auto',
                            maxHeight: 'calc(100vh - 220px)',
                            pt: 0,
                            pb: 1
                        }}
                    >
                        <NodeTree
                            node={workflowTree}
                            workflowId={id!}
                            onNodeSelect={handleNodeSelect}
                        />
                    </List>
                </Paper>
            </Container>

            {/* Artifact Drawer */}
            <ArtifactDrawer
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                selectedNode={selectedNode}
            />
        </Box>
    );
}

export default WorkflowDetails;

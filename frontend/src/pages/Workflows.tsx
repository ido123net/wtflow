import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  Container,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Paper
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { Fragment } from "react/jsx-runtime";

interface Workflow {
  id: number;
  name: string;
  description?: string;
  created_at?: string;
}

const fetchWorkflows = async () => {
  console.log("Fetching all workflows");
  const { data } = await axios.get("http://localhost:8000/api/v1/workflows");
  console.log("Workflows data:", data);
  return data;
};

function Workflows() {
  const { data: workflows, isLoading, error } = useQuery({
    queryKey: ["workflows"],
    queryFn: fetchWorkflows,
  });

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
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Alert severity="error">Error loading workflows</Alert>
    </Container>
  );

  return (
    <Box>
      <Container maxWidth="md" sx={{ py: 3 }}>
        {workflows && workflows.length === 0 ? (
          <Alert severity="info">No workflows found. Create one to get started!</Alert>
        ) : (
          <Paper variant="outlined">
            <List disablePadding>
              {workflows.map((workflow: Workflow, index: number) => (
                <Fragment key={workflow.id}>
                  {index > 0 && <Divider />}
                  <ListItem
                    component={Link}
                    to={`/workflows/${workflow.id}`}
                    sx={{ py: 1.5 }}
                    secondaryAction={
                      <IconButton edge="end" size="small">
                        <ChevronRightIcon />
                      </IconButton>
                    }
                  >
                    <ListItemText
                      primary={
                        <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                          {workflow.name}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary" sx={{ mr: 2 }}>
                          ID: {workflow.id}
                        </Typography>
                      }
                    />
                  </ListItem>
                </Fragment>
              ))}
            </List>
          </Paper>
        )}
      </Container>
    </Box>
  );
}

export default Workflows;
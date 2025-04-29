import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, Typography } from "@mui/material";
import Workflows from "./pages/Workflows";
import WorkflowDetails from "./pages/WorkflowDetails";
import NodeDetails from "./pages/NodeDetails";
import TimelineIcon from '@mui/icons-material/Timeline';

const queryClient = new QueryClient();

// Create a custom theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          textTransform: 'none',
        },
      },
    },
    // Make the overall UI more compact
    MuiToolbar: {
      styleOverrides: {
        dense: {
          minHeight: 48,
        },
      },
    },
    MuiListItem: {
      styleOverrides: {
        dense: {
          paddingTop: 2,
          paddingBottom: 2,
        },
      },
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppBar position="static" color="primary" elevation={0}>
          <Toolbar variant="dense">
            <TimelineIcon sx={{ mr: 1 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              WTFlow
            </Typography>
          </Toolbar>
        </AppBar>

        <Router>
          <Routes>
            <Route path="/" element={<Workflows />} />
            <Route path="/workflows/:id" element={<WorkflowDetails />} />
            <Route path="/workflows/:workflowId/nodes/:nodeId" element={<NodeDetails />} />
            <Route path="/workflows/:workflowId/nodes/:nodeId/artifacts/:artifactName" element={<NodeDetails />} />
          </Routes>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;


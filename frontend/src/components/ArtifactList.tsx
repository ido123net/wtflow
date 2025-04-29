import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Grid, 
  CircularProgress, 
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import JSONPretty from "react-json-pretty";
import 'react-json-pretty/themes/monikai.css';

interface Artifact {
  id: number;
  node_id: number;
  name: string;
  data_type: string;
  data: any;
}

interface ArtifactListProps {
  nodeId: number;
}

const fetchArtifacts = async (nodeId: number) => {
  console.log(`Fetching artifacts for node: ${nodeId}`);
  const { data } = await axios.get(`http://localhost:8000/api/v1/artifacts/${nodeId}`);
  console.log("Artifacts data:", data);
  return data;
};

function ArtifactList({ nodeId }: ArtifactListProps) {
  const { data: artifacts, isLoading, error } = useQuery({
    queryKey: ["artifacts", nodeId],
    queryFn: () => fetchArtifacts(nodeId),
    enabled: !!nodeId,
  });

  if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">Error loading artifacts</Alert>;
  if (!artifacts || artifacts.length === 0) return <Alert severity="info">No artifacts found for this node</Alert>;

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 'medium' }}>
        Node Artifacts ({artifacts.length})
      </Typography>
      <Grid container spacing={2}>
        {artifacts.map((artifact: Artifact) => (
          <Grid container key={artifact.id}>
            <Accordion defaultExpanded>
              <AccordionSummary 
                expandIcon={<ExpandMoreIcon />}
                sx={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {artifact.name}
                  </Typography>
                  <Chip 
                    label={artifact.data_type} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                    sx={{ ml: 2 }}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ p: 0 }}>
                <Card variant="outlined" sx={{ backgroundColor: '#272822' }}>
                  <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
                    <JSONPretty 
                      id={`json-${artifact.id}`} 
                      data={artifact.data}
                      mainStyle="padding:1em; line-height:1.3; font-size:13px; font-family: monospace;"
                    />
                  </CardContent>
                </Card>
              </AccordionDetails>
            </Accordion>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

export default ArtifactList;

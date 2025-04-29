import React from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FileIcon from '@mui/icons-material/InsertDriveFile';
import JSONPretty from 'react-json-pretty';
import 'react-json-pretty/themes/monikai.css';
import LogViewer from './LogViewer';

interface Artifact {
  name: string;
  type: string;
  file_path: string;
}

interface ArtifactDisplayProps {
  artifacts: Artifact[];
}

const ArtifactDisplay: React.FC<ArtifactDisplayProps> = ({ artifacts }) => {
  if (!artifacts || artifacts.length === 0) return null;

  return (
    <Box>
      <Typography variant="subtitle1" sx={{ mb: 1.5, fontWeight: 'medium' }}>
        Artifacts
      </Typography>
      <Grid container spacing={1}>
        {artifacts.map((artifact, index) => (
          <Grid container key={`${artifact.name}-${index}`}>
            <Accordion defaultExpanded={false}>
              <AccordionSummary 
                expandIcon={<ExpandMoreIcon />}
                sx={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <FileIcon sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                      {artifact.name}
                    </Typography>
                  </Box>
                  <Chip 
                    label={artifact.type} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                    sx={{ ml: 2 }}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ p: 0 }}>
                <Card variant="outlined" sx={{ backgroundColor: '#f5f5f5' }}>
                  <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
                    <Typography variant="caption" display="block" gutterBottom sx={{ color: 'text.secondary' }}>
                      File path: {artifact.file_path}
                    </Typography>
                    <LogViewer artifactName={artifact.name} artifactPath={artifact.file_path}></LogViewer>
                    
                    {/* If we have actual data to display */}
                    {artifact.type === 'json' && (
                      <Box sx={{ backgroundColor: '#272822', borderRadius: 1, mt: 1 }}>
                        <JSONPretty
                          data={{ message: "Artifact content would be displayed here" }}
                          mainStyle="padding:1em; line-height:1.3; font-size:13px; font-family: monospace;"
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </AccordionDetails>
            </Accordion>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ArtifactDisplay;

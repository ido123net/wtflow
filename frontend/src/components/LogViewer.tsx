import React, { useEffect, useRef, useState } from 'react';
import {
    Box,
    Paper,
    IconButton,
    Tooltip,
    Stack
} from '@mui/material';
import {
    VerticalAlignBottom as ScrollDownIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';
import AnsiToHtml from 'ansi-to-html';

const ansiConverter = new AnsiToHtml();

interface LogViewerProps {
    artifactPath: string;
    artifactName: string;
}

const LogViewer: React.FC<LogViewerProps> = ({ artifactPath, artifactName }) => {
    const [lines, setLines] = useState<string[]>([]);
    const [position, setPosition] = useState<number>(0);
    const [eventSource, setEventSource] = useState<EventSource | null>(null);
    const logContainerRef = useRef<HTMLDivElement | null>(null);

    const encodedPath = encodeURIComponent(artifactPath);

    const scrollToBottom = () => {
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    };

    const startStream = (startPosition: number = 0) => {
        if (eventSource) {
            eventSource.close();
        }

        const newSource = new EventSource(`http://localhost:8000/api/v1/artifacts/file?file_path=${encodedPath}&start_position=${startPosition}`);

        newSource.onmessage = (event) => {
            try {
                const parsed = JSON.parse(event.data);
                console.log("Parsed SSE data:", parsed);
                if (parsed.content) {
                    setLines((prev) => [...prev, parsed.content]);
                    console.log("Updated lines:", [...lines, parsed.content]);
                }
                if (parsed.position !== undefined) {
                    setPosition(parsed.position);
                }
            } catch (err) {
                console.error('Failed to parse SSE data:', err);
            }
        };

        newSource.onerror = (event) => {
            console.log("Stream ended or errored", event);
            newSource.close();
        };

        setEventSource(newSource);
    };

    const refreshStream = () => {
        startStream(position);
    };

    useEffect(() => {
        startStream(0);

        return () => {
            if (eventSource) {
                eventSource.close();
            }
        };
    }, []);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                <Tooltip title="Scroll to bottom">
                    <IconButton size="small" onClick={scrollToBottom}>
                        <ScrollDownIcon />
                    </IconButton>
                </Tooltip>

                <Tooltip title="Resume from last position">
                    <IconButton size="small" onClick={refreshStream}>
                        <RefreshIcon />
                    </IconButton>
                </Tooltip>
            </Stack>

            <Paper
                elevation={0}
                variant="outlined"
                sx={{
                    overflow: 'auto',
                    bgcolor: '#FFFFFF',
                    p: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                    position: 'relative',
                    flex: 1,
                }}
                ref={logContainerRef}
            >
                <div
                    style={{ margin: 0, color: '#000000', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                    dangerouslySetInnerHTML={{ __html: ansiConverter.toHtml(lines.join('')) }}
                />
            </Paper>
        </Box>
    );
};

export default LogViewer;
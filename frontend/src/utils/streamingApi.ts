/**
 * Utility for streaming content from the API
 */

// Stream content from the API with callback for updates
export const streamContent = (
    artifactPath: string,
    onData: (data: string) => void,
    onError: (error: Error) => void
) => {
    let abortController = new AbortController();
    let stopped = false;

    const fetchData = async () => {
        try {
            const response = await fetch(
                `http://localhost:8000/api/v1/artifacts/file?file_path=${artifactPath}&stream=true`,
                { signal: abortController.signal }
            );

            if (!response.ok) {
                throw new Error(`Error fetching artifact content: ${response.status} ${response.statusText}`);
            }

            if (!response.body) {
                throw new Error('ReadableStream not supported in this browser.');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (!stopped) {
                const { value, done } = await reader.read();

                if (done) {
                    break;
                }

                const chunk = decoder.decode(value, { stream: true });
                onData(chunk);
            }
        } catch (error) {
            if (!stopped && error instanceof Error && error.name !== 'AbortError') {
                onError(error);
            }
        }
    };

    // Start fetching data
    fetchData();

    // Return a function to stop streaming
    return () => {
        stopped = true;
        abortController.abort();
    };
};

// Fetch the entire content at once (non-streaming)
export const getFullContent = async (artifactPath: string) => {
    try {
        const response = await fetch(`http://localhost:8000/api/v1/artifacts/file?file_path=${artifactPath}&stream=true`);

        if (!response.ok) {
            throw new Error(`Error fetching artifact content: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        return data.content;
    } catch (error) {
        console.error('Error fetching full content:', error);
        throw error;
    }
};

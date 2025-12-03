// cloudflare-workers-fetcher-congress/src/index.ts

export interface Env {
  CONGRESS_API_KEY: string;
}

// Configurable delay between API requests (in milliseconds)
const REQUEST_DELAY_MS = 2000; // Example: 2 seconds delay to limit requests to 30 per minute (well within typical free tiers)

// Helper function for artificial delay
function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Helper function for fetching with exponential backoff retry logic
async function retryFetch(
  input: RequestInfo,
  init?: RequestInit,
  maxRetries: number = 3,
  delay: number = 1000 // Initial delay in ms
): Promise<Response> {
  for (let i = 0; i < maxRetries; i++) {
    // Implement rate limiting delay BEFORE each attempt (including retries)
    await sleep(REQUEST_DELAY_MS); 

    try {
      const response = await fetch(input, init);
      if (response.ok) {
        return response;
      } else if (response.status === 429 || response.status >= 500) {
        console.warn(`Attempt ${i + 1} failed with status ${response.status}. Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        delay *= 2; // Exponential backoff
      } else {
        throw new Error(`API request failed with status ${response.status}: ${response.statusText}`);
      }
    } catch (error: any) {
      if (i === maxRetries - 1) {
        throw error;
      }
      console.error(`Attempt ${i + 1} failed: ${error.message}. Retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= 2; // Exponential backoff
    }
  }
  throw new Error('Max retries exceeded');
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const apiEndpoint = url.searchParams.get('apiEndpoint');

    if (!apiEndpoint) {
      return new Response('Missing apiEndpoint query parameter', { status: 400 });
    }

    try {
      const congressApiUrl = `https://api.congress.gov/v3/${apiEndpoint}?api_key=${env.CONGRESS_API_KEY}`;
      const apiResponse = await retryFetch(congressApiUrl, {
        headers: {
          'Accept': 'application/json'
        }
      });

      const data = await apiResponse.json();
      return new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json' } });

    } catch (error: any) {
      console.error('Error fetching data from Congress.gov API (after retries and rate limiting):', error);
      return new Response(`Error fetching data: ${error.message}`, { status: 500 });
    }
  },
};
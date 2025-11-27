// cloudflare-workers-transformer-openstates/src/index.ts

export interface Env {
  // Any environment variables needed for transformation logic
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    try {
      const rawLegislatorsData: any = await request.json(); // Expecting raw data from Fetcher/Orchestrator

      if (!rawLegislatorsData || !Array.isArray(rawLegislatorsData.results)) { // OpenStates often uses 'results'
        return new Response('Invalid input data format', { status: 400 });
      }

      // --- Transformation Logic ---
      // This example transforms raw OpenStates legislator data into a structure
      // suitable for direct insertion into the 'openstates.people' table.
      const transformedLegislators = rawLegislatorsData.results.map((person: any) => ({
        legislator_id: person.id,
        state_code: person.jurisdiction_id, // Assuming jurisdiction_id maps to state_code
        first_name: person.first_name || null,
        last_name: person.last_name || null,
        email: person.email || null,
        phone: person.phone || null,
        // Add other fields as per your openstates.people schema
      }));

      return new Response(JSON.stringify(transformedLegislators), { headers: { 'Content-Type': 'application/json' } });

    } catch (error: any) {
      console.error('Error transforming data:', error);
      return new Response(`Error transforming data: ${error.message}`, { status: 500 });
    }
  },
};

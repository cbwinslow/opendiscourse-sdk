// cloudflare-workers-transformer-congress/src/index.ts

export interface Env {
  // Any environment variables needed for transformation logic
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    try {
      const rawMembersData: any = await request.json(); // Expecting raw data from Fetcher/Orchestrator

      if (!rawMembersData || !Array.isArray(rawMembersData.members)) {
        return new Response('Invalid input data format', { status: 400 });
      }

      // --- Transformation Logic ---
      // This example transforms raw Congress.gov member data into a structure
      // suitable for direct insertion into the 'congress.members' table.
      const transformedMembers = rawMembersData.members.map((member: any) => ({
        bioguide_id: member.bioguideId,
        first_name: member.firstName,
        last_name: member.lastName,
        gender: member.gender || null,
        birth_date: member.birthDate || null, // Assuming birthDate exists in raw data
        // Add other fields as per your congress.members schema
      }));

      return new Response(JSON.stringify(transformedMembers), { headers: { 'Content-Type': 'application/json' } });

    } catch (error: any) {
      console.error('Error transforming data:', error);
      return new Response(`Error transforming data: ${error.message}`, { status: 500 });
    }
  },
};

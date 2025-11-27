// cloudflare-workers-transformer-govinfo/src/index.ts

export interface Env {
  // Any environment variables needed for transformation logic
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    try {
      const rawCollectionsData: any = await request.json(); // Expecting raw data from Fetcher/Orchestrator

      if (!rawCollectionsData || !Array.isArray(rawCollectionsData.collections)) {
        return new Response('Invalid input data format', { status: 400 });
      }

      // --- Transformation Logic ---
      // This example transforms raw GovInfo collection data into a structure
      // suitable for direct insertion into the 'govinfo.collections' table.
      const transformedCollections = rawCollectionsData.collections.map((collection: any) => ({
        collection_code: collection.collectionCode,
        collection_name: collection.collectionName,
        package_count: collection.packageCount || null,
        granule_count: collection.granuleCount || null,
        description: collection.description || null,
        source_url: collection.sourceUrl || null,
        last_indexed_at: collection.lastIndexedAt ? new Date(collection.lastIndexedAt) : null,
        // Add other fields as per your govinfo.collections schema
      }));

      return new Response(JSON.stringify(transformedCollections), { headers: { 'Content-Type': 'application/json' } });

    } catch (error: any) {
      console.error('Error transforming data:', error);
      return new Response(`Error transforming data: ${error.message}`, { status: 500 });
    }
  },
};

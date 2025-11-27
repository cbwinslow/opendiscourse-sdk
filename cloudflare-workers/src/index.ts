// cloudflare-workers/src/index.ts
import { ProgressState } from './durable-objects/progress-tracker';
import postgres from 'postgres'; // Import postgres client
import { runDataQualityAgent, DataQualityAssessment } from './ai-agents/data-quality-agent'; // Import the DataQualityAgent
import { runOptimizationAgent, OptimizationRecommendation } from './ai-agents/optimization-agent'; // Import the OptimizationAgent

export interface Env {
  PROGRESS_TRACKER: DurableObjectNamespace;
  CONGRESS_FETCHER: Fetcher; // Binding for the Congress Fetcher Worker
  CONGRESS_TRANSFORMER: Fetcher; // Binding for the Congress Transformer Worker
  GOVINFO_FETCHER: Fetcher; // Binding for the GovInfo Fetcher Worker
  GOVINFO_TRANSFORMER: Fetcher; // Binding for the GovInfo Transformer Worker
  OPENSTATES_FETCHER: Fetcher; // New binding for the OpenStates Fetcher Worker
  OPENSTATES_TRANSFORMER: Fetcher; // New binding for the OpenStates Transformer Worker
  // Database credentials (set as Worker Secrets)
  DB_HOST: string;
  DB_USER: string;
  DB_PASSWORD: string;
  DB_NAME: string;
  // API keys (set as Worker Secrets)
  CONGRESS_API_KEY: string;
  GOVINFO_API_KEY: string;
  OPENSTATES_API_KEY: string;
  OPENROUTER_API_KEY: string; // OpenRouter API Key for AI Agents
  // ... other API keys
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    const durableObjectId = env.PROGRESS_TRACKER.idFromName('ingestion_job_1'); // Hardcoded for simplicity
    const durableObjectStub = env.PROGRESS_TRACKER.get(durableObjectId);

    try {
      let response: Response;
      let status: ProgressState;

      // Helper to check if ingestion can proceed
      const canIngest = async (source: string) => {
        const currentStatusResponse = await durableObjectStub.fetch(url.origin + '/get');
        const currentStatus: ProgressState = await currentStatusResponse.json();
        if (currentStatus.status === 'paused') {
          return { can: false, message: `Ingestion for ${source} is paused. Please resume first.` };
        }
        return { can: true };
      };

      switch (path) {
        case '/start-ingestion':
          const startBody = JSON.stringify({
            source: 'generic', // Source can be updated by specific ingestion endpoints
            startDate: new Date().toISOString(),
            endDate: new Date().toISOString(),
            totalRecords: 0,
            status: 'running' // Set to running on start
          });
          response = await durableObjectStub.fetch(
            new Request(url.origin + '/start', { method: 'POST', body: startBody, headers: { 'Content-Type': 'application/json' } })
          );
          status = await response.json() as ProgressState;
          return new Response(JSON.stringify({ message: 'Ingestion job started or updated.', status: status.status }), { status: response.status, headers: { 'Content-Type': 'application/json' } });

        case '/pause-ingestion':
          response = await durableObjectStub.fetch(url.origin + '/pause');
          status = await response.json() as ProgressState;
          return new Response(JSON.stringify({ message: 'Ingestion job paused.', status: status.status }), { status: response.status, headers: { 'Content-Type': 'application/json' } });
        
        case '/resume-ingestion':
          response = await durableObjectStub.fetch(url.origin + '/resume');
          status = await response.json() as ProgressState;
          return new Response(JSON.stringify({ message: 'Ingestion job resumed.', status: status.status }), { status: response.status, headers: { 'Content-Type': 'application/json' } });

        case '/get-status':
          response = await durableObjectStub.fetch(url.origin + '/get');
          status = await response.json() as ProgressState;
          return new Response(JSON.stringify(status, null, 2), { headers: { 'Content-Type': 'application/json' } });

        case '/reset-job':
          response = await durableObjectStub.fetch(url.origin + '/reset');
          status = await response.json() as ProgressState;
          return new Response(JSON.stringify({ message: 'Ingestion job reset.', status: status.status }), { status: response.status, headers: { 'Content-Type': 'application/json' } });

        case '/run-congress-ingestion':
          const congressIngestCheck = await canIngest('congress.gov');
          if (!congressIngestCheck.can) {
            return new Response(congressIngestCheck.message, { status: 403 });
          }

          // 1. Update DO status to indicate fetching
          await durableObjectStub.fetch(
            new Request(url.origin + '/update', {
              method: 'POST',
              body: JSON.stringify({ source: 'congress.gov', status: 'fetching', lastUpdate: new Date().toISOString() }),
              headers: { 'Content-Type': 'application/json' }
            })
          );

          // 2. Call Congress Fetcher Worker
          const congressApiEndpoint = url.searchParams.get('apiEndpoint') || 'member';
          let congressFetcherRawResponse: Response;
          try {
            congressFetcherRawResponse = await env.CONGRESS_FETCHER.fetch(
              new Request(`${url.origin}/?apiEndpoint=${congressApiEndpoint}`, request)
            );
          } catch (fetcherError: any) {
             await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `Congress Fetcher network error: ${fetcherError.message}` }), headers: { 'Content-Type': 'application/json' } }));
            return new Response(`Congress Fetcher Worker network error: ${fetcherError.message}`, { status: 500 });
          }
          if (!congressFetcherRawResponse.ok) {
            const errorText = await congressFetcherRawResponse.text();
            await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `Congress Fetcher failed: ${congressFetcherRawResponse.status} ${congressFetcherRawResponse.statusText}. Details: ${errorText}` }), headers: { 'Content-Type': 'application/json' } }));
            return new Response(`Congress Fetcher Worker failed: ${congressFetcherRawResponse.status} ${congressFetcherRawResponse.statusText}. Details: ${errorText}`, { status: congressFetcherRawResponse.status });
          }
          const congressFetchedData = await congressFetcherRawResponse.json();

          // 3. Update DO status to indicate transforming
          await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'transforming', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

          // 4. Call Congress Transformer Worker
          let congressTransformerRawResponse: Response;
          try {
            congressTransformerRawResponse = await env.CONGRESS_TRANSFORMER.fetch(new Request(url.origin, { method: 'POST', body: JSON.stringify(congressFetchedData), headers: { 'Content-Type': 'application/json' } }));
          } catch (transformerError: any) {
              await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `Congress Transformer network error: ${transformerError.message}` }), headers: { 'Content-Type': 'application/json' } }));
              return new Response(`Congress Transformer Worker network error: ${transformerError.message}`, { status: 500 });
          }
          if (!congressTransformerRawResponse.ok) {
            const errorText = await congressTransformerRawResponse.text();
            await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `Congress Transformer failed: ${congressTransformerRawResponse.status} ${congressTransformerRawResponse.statusText}. Details: ${errorText}` }), headers: { 'Content-Type': 'application/json' } }));
            return new Response(`Congress Transformer Worker failed: ${congressTransformerRawResponse.status} ${congressTransformerRawResponse.statusText}. Details: ${errorText}`, { status: congressTransformerRawResponse.status });
          }
          const congressTransformedData: any[] = await congressTransformerRawResponse.json();
          
          // --- AI Agent: Data Quality Check ---
          // For simplicity, checking only the first record
          if (congressTransformedData.length > 0) {
            await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'checking_quality', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));
            try {
              const qualityAssessment = await runDataQualityAgent(congressTransformedData[0], { OPENROUTER_API_KEY: env.OPENROUTER_API_KEY });
              console.log('Congress Data Quality Assessment:', qualityAssessment);
              // Need to get current metrics to avoid overwriting other fields
              const currentStatusResponse = await durableObjectStub.fetch(url.origin + '/get');
              const currentStatusData: ProgressState = await currentStatusResponse.json();
              const currentMetrics = currentStatusData?.metrics || { recordsPerSecond: 0, averageLatency: 0, errorRate: 0 }; 
              await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ metrics: { ...currentMetrics, dataQualityScore: qualityAssessment.score }, lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

            } catch (aiError: any) {
              console.error('AI Data Quality Agent failed:', aiError);
              await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ status: 'quality_check_failed', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));
            }
          }

          // 5. Update DO status to indicate persisting
          await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'persisting', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

          // 6. Persist data to PostgreSQL
          let congressInsertedCount = 0;
          try {
            if (congressTransformedData.length > 0) {
              const sql = postgres({ host: DB_HOST, port: 5432, username: DB_USER, password: DB_PASSWORD, database: DB_NAME, ssl: 'require', max: 1 });
              await sql`INSERT INTO congress.members ${sql(congressTransformedData, 'bioguide_id', 'first_name', 'last_name', 'gender', 'birth_date')} ON CONFLICT (bioguide_id) DO NOTHING;`
              congressInsertedCount = congressTransformedData.length; // Assuming all were attempted to insert
              await sql.end(); // Close the connection explicitly
            }
            // 7. Update DO status to completed
            await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'completed', successfulInserts: congressInsertedCount, processedRecords: congressTransformedData.length, lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

            // --- AI Agent: Optimization Recommendation ---
            const finalStatusResponse = await durableObjectStub.fetch(url.origin + '/get');
            const finalStatusData: ProgressState = await finalStatusResponse.json();
            try {
              const optimizationRecommendation = await runOptimizationAgent(finalStatusData.metrics, finalStatusData.status, { OPENROUTER_API_KEY: env.OPENROUTER_API_KEY });
              console.log('Congress Optimization Recommendation:', optimizationRecommendation);
              // Store the recommendation in the Durable Object or elsewhere for the dashboard
              // This could update a new field in ProgressState, e.g., lastOptimizationRecommendation: optimizationRecommendation
            } catch (aiError: any) {
              console.error('AI Optimization Agent failed:', aiError);
            }
            return new Response(`Congress Ingestion successful! Fetched, transformed, and inserted ${congressInsertedCount} members.`, { headers: { 'Content-Type': 'application/json' } });
          } catch (dbError: any) {
            console.error('Error persisting Congress data to PostgreSQL:', dbError);
            await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `Congress Persistence failed: ${dbError.message}` }), headers: { 'Content-Type': 'application/json' } }));
            return new Response(`Error persisting Congress data: ${dbError.message}`, { status: 500 });
          }
        
        case '/run-govinfo-ingestion':
            const govinfoIngestCheck = await canIngest('govinfo.gov');
            if (!govinfoIngestCheck.can) {
                return new Response(govinfoIngestCheck.message, { status: 403 });
            }

            // 1. Update DO status to indicate fetching
            await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ source: 'govinfo.gov', status: 'fetching', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

            // 2. Call GovInfo Fetcher Worker
            const govinfoApiEndpoint = url.searchParams.get('apiEndpoint') || 'collections'; // Example endpoint
            let govinfoFetcherRawResponse: Response;
            try {
                govinfoFetcherRawResponse = await env.GOVINFO_FETCHER.fetch(new Request(`${url.origin}/?apiEndpoint=${govinfoApiEndpoint}`, request));
            } catch (fetcherError: any) {
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `GovInfo Fetcher network error: ${fetcherError.message}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`GovInfo Fetcher Worker network error: ${fetcherError.message}`, { status: 500 });
            }
            if (!govinfoFetcherRawResponse.ok) {
                const errorText = await govinfoFetcherRawResponse.text();
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `GovInfo Fetcher failed: ${govinfoFetcherRawResponse.status} ${govinfoFetcherRawResponse.statusText}. Details: ${errorText}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`GovInfo Fetcher Worker failed: ${govinfoFetcherRawResponse.status} ${govinfoFetcherRawResponse.statusText}. Details: ${errorText}`, { status: govinfoFetcherRawResponse.status });
            }
            const govinfoFetchedData = await govinfoFetcherRawResponse.json();

            // 3. Update DO status to indicate transforming
            await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'transforming', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

            // 4. Call GovInfo Transformer Worker
            let govinfoTransformerRawResponse: Response;
            try {
                govinfoTransformerRawResponse = await env.GOVINFO_TRANSFORMER.fetch(new Request(url.origin, { method: 'POST', body: JSON.stringify(govinfoFetchedData), headers: { 'Content-Type': 'application/json' } }));
            } catch (transformerError: any) {
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `GovInfo Transformer network error: ${transformerError.message}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`GovInfo Transformer Worker network error: ${transformerError.message}`, { status: 500 });
            }
            if (!govinfoTransformerRawResponse.ok) {
                const errorText = await govinfoTransformerRawResponse.text();
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `GovInfo Transformer failed: ${govinfoTransformerRawResponse.status} ${govinfoTransformerRawResponse.statusText}. Details: ${errorText}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`GovInfo Transformer Worker failed: ${govinfoTransformerRawResponse.status} ${govinfoTransformerRawResponse.statusText}. Details: ${errorText}`, { status: govinfoTransformerRawResponse.status });
            }
            const govinfoTransformedData: any[] = await govinfoTransformerRawResponse.json();

            // --- AI Agent: Data Quality Check ---
            // For simplicity, checking only the first record
            if (govinfoTransformedData.length > 0) {
              await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'checking_quality', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));
              try {
                const qualityAssessment = await runDataQualityAgent(govinfoTransformedData[0], { OPENROUTER_API_KEY: env.OPENROUTER_API_KEY });
                console.log('GovInfo Data Quality Assessment:', qualityAssessment);
                // Update status to include dataQualityScore
                const currentStatusResponse = await durableObjectStub.fetch(url.origin + '/get');
                const currentStatusData: ProgressState = await currentStatusResponse.json();
                const currentMetrics = currentStatusData?.metrics || { recordsPerSecond: 0, averageLatency: 0, errorRate: 0 }; 
                await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ metrics: { ...currentMetrics, dataQualityScore: qualityAssessment.score }, lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

              } catch (aiError: any) {
                console.error('AI Data Quality Agent failed for GovInfo:', aiError);
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ status: 'quality_check_failed', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));
              }
            }


            // 5. Update DO status to indicate persisting
            await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'persisting', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

            // 6. Persist data to PostgreSQL (GovInfo collections example)
            let govinfoInsertedCount = 0;
            try {
                if (govinfoTransformedData.length > 0) {
                    const sql = postgres({ host: DB_HOST, port: 5432, username: DB_USER, password: DB_PASSWORD, database: DB_NAME, ssl: 'require', max: 1 });
                    await sql`INSERT INTO govinfo.collections ${sql(govinfoTransformedData, 'collection_code', 'collection_name', 'package_count', 'granule_count', 'description', 'source_url', 'last_indexed_at')} ON CONFLICT (collection_code) DO NOTHING;`
                    govinfoInsertedCount = govinfoTransformedData.length;
                    await sql.end();
                }
                // Update DO status to completed
                await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'completed', successfulInserts: govinfoInsertedCount, processedRecords: govinfoTransformedData.length, lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

                // --- AI Agent: Optimization Recommendation ---
                const finalStatusResponse = await durableObjectStub.fetch(url.origin + '/get');
                const finalStatusData: ProgressState = await finalStatusResponse.json();
                try {
                  const optimizationRecommendation = await runOptimizationAgent(finalStatusData.metrics, finalStatusData.status, { OPENROUTER_API_KEY: env.OPENROUTER_API_KEY });
                  console.log('GovInfo Optimization Recommendation:', optimizationRecommendation);
                } catch (aiError: any) {
                  console.error('AI Optimization Agent failed for GovInfo:', aiError);
                }

                return new Response(`GovInfo Ingestion successful! Fetched, transformed, and inserted ${govinfoInsertedCount} collections.`, { headers: { 'Content-Type': 'application/json' } });
            } catch (dbError: any) {
                console.error('Error persisting GovInfo data to PostgreSQL:', dbError);
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `GovInfo Persistence failed: ${dbError.message}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`Error persisting GovInfo data: ${dbError.message}`, { status: 500 });
            }

        case '/run-openstates-ingestion':
            const openstatesIngestCheck = await canIngest('openstates.org');
            if (!openstatesIngestCheck.can) {
                return new Response(openstatesIngestCheck.message, { status: 403 });
            }
            // 1. Update DO status to indicate fetching
            await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ source: 'openstates.org', status: 'fetching', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

            // 2. Call OpenStates Fetcher Worker
            const openstatesApiEndpoint = url.searchParams.get('apiEndpoint') || 'legislators'; // Example endpoint for legislators
            let openstatesFetcherRawResponse: Response;
            try {
                openstatesFetcherRawResponse = await env.OPENSTATES_FETCHER.fetch(new Request(`${url.origin}/?apiEndpoint=${openstatesApiEndpoint}`, request)
                );
            } catch (fetcherError: any) {
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `OpenStates Fetcher network error: ${fetcherError.message}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`OpenStates Fetcher Worker network error: ${fetcherError.message}`, { status: 500 });
            }
            if (!openstatesFetcherRawResponse.ok) {
                const errorText = await openstatesFetcherRawResponse.text();
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `OpenStates Fetcher failed: ${openstatesFetcherRawResponse.status} ${openstatesFetcherRawResponse.statusText}. Details: ${errorText}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`OpenStates Fetcher Worker failed: ${openstatesFetcherRawResponse.status} ${openstatesFetcherRawResponse.statusText}. Details: ${errorText}`, { status: openstatesFetcherRawResponse.status });
            }
            const openstatesFetchedData = await openstatesFetcherRawResponse.json();

            // 3. Update DO status to indicate transforming
            await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'transforming', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

            // 4. Call OpenStates Transformer Worker
            let openstatesTransformerRawResponse: Response;
            try {
                openstatesTransformerRawResponse = await env.OPENSTATES_TRANSFORMER.fetch(new Request(url.origin, { method: 'POST', body: JSON.stringify(openstatesFetchedData), headers: { 'Content-Type': 'application/json' } }));
            } catch (transformerError: any) {
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `OpenStates Transformer network error: ${transformerError.message}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`OpenStates Transformer Worker network error: ${transformerError.message}`, { status: 500 });
            }
            if (!openstatesTransformerRawResponse.ok) {
                const errorText = await openstatesTransformerRawResponse.text();
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `OpenStates Transformer failed: ${openstatesTransformerRawResponse.status} ${openstatesTransformerRawResponse.statusText}. Details: ${errorText}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`OpenStates Transformer Worker failed: ${openstatesTransformerRawResponse.status} ${openstatesTransformerRawResponse.statusText}. Details: ${errorText}`, { status: openstatesTransformerRawResponse.status });
            }
            const openstatesTransformedData: any[] = await openstatesTransformerRawResponse.json();

            // --- AI Agent: Data Quality Check ---
            // For simplicity, checking only the first record
            if (openstatesTransformedData.length > 0) {
              await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'checking_quality', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));
              try {
                const qualityAssessment = await runDataQualityAgent(openstatesTransformedData[0], { OPENROUTER_API_KEY: env.OPENROUTER_API_KEY });
                console.log('OpenStates Data Quality Assessment:', qualityAssessment);
                const currentStatusResponse = await durableObjectStub.fetch(url.origin + '/get');
                const currentStatusData: ProgressState = await currentStatusResponse.json();
                const currentMetrics = currentStatusData?.metrics || { recordsPerSecond: 0, averageLatency: 0, errorRate: 0 };
                await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ metrics: { ...currentMetrics, dataQualityScore: qualityAssessment.score }, lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));
              } catch (aiError: any) {
                console.error('AI Data Quality Agent failed for OpenStates:', aiError);
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ status: 'quality_check_failed', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));
              }
            }

            // 5. Update DO status to indicate persisting
            await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'persisting', lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

            // 6. Persist data to PostgreSQL (OpenStates legislators example)
            let openstatesInsertedCount = 0;
            try {
                if (openstatesTransformedData.length > 0) {
                    const sql = postgres({ host: DB_HOST, port: 5432, username: DB_USER, password: DB_PASSWORD, database: DB_NAME, ssl: 'require', max: 1 });
                    await sql`INSERT INTO openstates.people ${sql(openstatesTransformedData, 'legislator_id', 'state_code', 'first_name', 'last_name', 'email', 'phone')} ON CONFLICT (legislator_id) DO NOTHING;`
                    openstatesInsertedCount = openstatesTransformedData.length;
                    await sql.end();
                }
                // Update DO status to completed
                await durableObjectStub.fetch(new Request(url.origin + '/update', { method: 'POST', body: JSON.stringify({ status: 'completed', successfulInserts: openstatesInsertedCount, processedRecords: openstatesTransformedData.length, lastUpdate: new Date().toISOString() }), headers: { 'Content-Type': 'application/json' } }));

                // --- AI Agent: Optimization Recommendation ---
                const finalStatusResponse = await durableObjectStub.fetch(url.origin + '/get');
                const finalStatusData: ProgressState = await finalStatusResponse.json();
                try {
                  const optimizationRecommendation = await runOptimizationAgent(finalStatusData.metrics, finalStatusData.status, { OPENROUTER_API_KEY: env.OPENROUTER_API_KEY });
                  console.log('OpenStates Optimization Recommendation:', optimizationRecommendation);
                } catch (aiError: any) {
                  console.error('AI Optimization Agent failed for OpenStates:', aiError);
                }

                return new Response(`OpenStates Ingestion successful! Fetched, transformed, and inserted ${openstatesInsertedCount} legislators.`, { headers: { 'Content-Type': 'application/json' } });
            } catch (dbError: any) {
                console.error('Error persisting OpenStates data to PostgreSQL:', dbError);
                await durableObjectStub.fetch(new Request(url.origin + '/fail', { method: 'POST', body: JSON.stringify({ error: `OpenStates Persistence failed: ${dbError.message}` }), headers: { 'Content-Type': 'application/json' } }));
                return new Response(`Error persisting OpenStates data: ${dbError.message}`, { status: 500 });
            }

        case '/':
          return new Response('Orchestrator Worker is running. Try /start-ingestion, /get-status, /reset-job, /run-congress-ingestion?apiEndpoint=member, /run-govinfo-ingestion?apiEndpoint=collections, /run-openstates-ingestion?apiEndpoint=legislators, /pause-ingestion, /resume-ingestion, etc.');

        default:
          return new Response('Not found', { status: 404 });
      }
    } catch (error: any) {
      console.error('Orchestrator Worker error (Top Level):', error); // Catch any unexpected errors
      await durableObjectStub.fetch(
        new Request(url.origin + '/fail', {
          method: 'POST',
          body: JSON.stringify({ error: `Orchestrator failed (Top Level): ${error.message}` }),
          headers: { 'Content-Type': 'application/json' }
        })
      );
      return new Response(`Error: ${error.message}`, { status: 500 });
    }
  },
};

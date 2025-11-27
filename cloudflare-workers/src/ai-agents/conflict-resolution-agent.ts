// cloudflare-workers/src/ai-agents/conflict-resolution-agent.ts

import { getOpenRouterClient, createChatCompletion } from './openrouter-client';
import OpenAI from 'openai'; // Import OpenAI for types

export interface ConflictResolution {
  summary: string;
  conflicts: Array<{ 
    recordIndex: number; // Index in the transformedData array
    issue: string;
    suggestedResolution: string;
  }>;
  mergeStrategyRecommendation: string;
}

export async function runConflictResolutionAgent(
  transformedData: Record<string, any>[], // A batch of transformed data
  env: { OPENROUTER_API_KEY: string } // Pass only the relevant env variable
): Promise<ConflictResolution> {
  const client = getOpenRouterClient(env.OPENROUTER_API_KEY);
  const model = 'mistralai/mistral-7b-instruct-v0.2'; // Example free model from OpenRouter

  const sampleDataForAI = transformedData.slice(0, 5); // Send a sample to stay within token limits

  const promptMessages: OpenAI.Chat.Completions.ChatCompletionMessage[] = [
    {
      role: 'system',
      content: `You are a data conflict resolution agent. Your task is to analyze a batch of incoming transformed data for potential duplicate records or conflicting information. Identify any conflicts and suggest a merge or resolution strategy. If no conflicts are found, state that clearly. Respond in JSON format.`,
    },
    {
      role: 'user',
      content: `Analyze the following sample of transformed records for conflicts or duplicates:

${JSON.stringify(sampleDataForAI, null, 2)}

Provide your analysis in the following JSON format:
{
  "summary": "No significant conflicts found.",
  "conflicts": [],
  "mergeStrategyRecommendation": "Continue with standard upsert."
}`,
    },
  ];

  try {
    const rawResponse = await createChatCompletion(client, model, promptMessages, 0.2); // Lower temperature for more consistent output
    if (rawResponse) {
      const resolution: ConflictResolution = JSON.parse(rawResponse);
      return resolution;
    }
  } catch (error) {
    console.error('Conflict Resolution Agent failed to get a valid response from OpenRouter:', error);
  }
  
  // Fallback in case of API error or invalid response format
  return {
    summary: 'Failed to get AI conflict resolution.',
    conflicts: [],
    mergeStrategyRecommendation: 'Manual review required due to AI failure.',
  };
}

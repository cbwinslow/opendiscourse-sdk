// cloudflare-workers/src/ai-agents/data-quality-agent.ts

import { getOpenRouterClient, createChatCompletion } from './openrouter-client';
import OpenAI from 'openai'; // Import OpenAI for types

export interface DataQualityAssessment {
  score: number; // e.g., 0-100
  issues: string[];
  recommendations: string[];
}

export async function runDataQualityAgent(
  data: Record<string, any>,
  env: { OPENROUTER_API_KEY: string } // Pass only the relevant env variable
): Promise<DataQualityAssessment> {
  const client = getOpenRouterClient(env.OPENROUTER_API_KEY);
  const model = 'mistralai/mistral-7b-instruct-v0.2'; // Example free model from OpenRouter

  const promptMessages: OpenAI.Chat.Completions.ChatCompletionMessage[] = [
    {
      role: 'system',
      content: `You are a data quality assessment agent. Your task is to review the provided JSON data and identify any potential quality issues such as missing fields, incorrect data types, inconsistencies, or suspicious values. Provide a quality score (0-100), a list of identified issues, and recommendations for improvement. Respond in JSON format.`,
    },
    {
      role: 'user',
      content: `Assess the data quality of this record:\n\
```json\
${JSON.stringify(data, null, 2)}
\
```\
\nProvide your assessment in the following JSON format:\n{
  "score": 85,
  "issues": ["Field 'birthDate' is missing for some records"],
  "recommendations": ["Ensure 'birthDate' is always present or handle nulls explicitly"]
}`,
    },
  ];

  try {
    const rawResponse = await createChatCompletion(client, model, promptMessages, 0.2); // Lower temperature for more consistent output
    if (rawResponse) {
      // Attempt to parse the JSON response
      const assessment: DataQualityAssessment = JSON.parse(rawResponse);
      return assessment;
    }
  } catch (error) {
    console.error('Data Quality Agent failed to get a valid response from OpenRouter:', error);
  }
  
  // Fallback in case of API error or invalid response format
  return {
    score: 0,
    issues: ['Failed to get AI quality assessment'],
    recommendations: ['Check OpenRouter API key and model availability.'],
  };
}

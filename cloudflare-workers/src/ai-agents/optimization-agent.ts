// cloudflare-workers/src/ai-agents/optimization-agent.ts

import { getOpenRouterClient, createChatCompletion } from './openrouter-client';
import OpenAI from 'openai'; // Import OpenAI for types
import { ProgressState } from '../durable-objects/progress-tracker'; // Assuming this path

export interface OptimizationRecommendation {
  summary: string;
  recommendations: string[]; // e.g., ["Increase batch size to 500", "Adjust concurrency to 4"]
  priority: 'low' | 'medium' | 'high';
}

export async function runOptimizationAgent(
  currentMetrics: ProgressState['metrics'],
  ingestionStatus: ProgressState['status'],
  env: { OPENROUTER_API_KEY: string } // Pass only the relevant env variable
): Promise<OptimizationRecommendation> {
  const client = getOpenRouterClient(env.OPENROUTER_API_KEY);
  const model = 'mistralai/mistral-7b-instruct-v0.2'; // Example free model from OpenRouter

  const promptMessages: OpenAI.Chat.Completions.ChatCompletionMessage[] = [
    {
      role: 'system',
      content: `You are an ingestion pipeline optimization agent. Your task is to analyze the provided current ingestion metrics and status, and recommend adjustments to improve performance, efficiency, or error reduction. Focus on actionable advice related to batch size, concurrency, retries, or other pipeline parameters. Respond in JSON format.`,
    },
    {
      role: 'user',
      content: `Current Ingestion Status: ${ingestionStatus}\n\nMetrics:\n${JSON.stringify(currentMetrics, null, 2)}\n\nProvide your optimization recommendations in the following JSON format:\n{\n  "summary": "Overall good, but some latency.",\n  "recommendations": ["Consider increasing batch size to 500 records.", "Monitor API responsiveness for external calls."],\n  "priority": "medium"\n}`,
    },
  ];

  try {
    const rawResponse = await createChatCompletion(client, model, promptMessages, 0.3); // Slightly higher temperature for more creative recommendations
    if (rawResponse) {
      const recommendation: OptimizationRecommendation = JSON.parse(rawResponse);
      return recommendation;
    }
  } catch (error) {
    console.error('Optimization Agent failed to get a valid response from OpenRouter:', error);
  }
  
  // Fallback in case of API error or invalid response format
  return {
    summary: 'Failed to get AI optimization recommendations.',
    recommendations: ['Check OpenRouter API key and model availability.', 'Review network connectivity.'],
    priority: 'high',
  };
}

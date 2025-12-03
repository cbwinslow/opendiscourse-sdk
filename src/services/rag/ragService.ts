import { query } from '../../config/database';
import { Document } from '../document/documentService';
import { spawn } from 'child_process';
import { promisify } from 'util';
import path from 'path';

export interface RAGQuery {
    query: string;
    context?: string[];
    maxResults?: number;
    threshold?: number;
}

export interface NLPAnalysisResult {
    sentiment: {
        overall_sentiment: string;
        confidence: number;
        positive_score: number;
        negative_score: number;
        neutral_score: number;
    };
    entities: Array<{
        text: string;
        label: string;
        start_char: number;
        end_char: number;
    }>;
    semantic_meaning: {
        key_concepts: Array<{ text: string; lemma: string; pos: string }>;
        noun_phrases: string[];
        linguistic_patterns: any;
    };
}

export class RAGService {
    private readonly defaultMaxResults = 5;
    private readonly defaultThreshold = 0.7;
    private readonly scriptsPath = path.join(process.cwd(), 'scripts');

    private async runPythonScript(scriptName: string, args: string[] = []): Promise<any> {
        return new Promise((resolve, reject) => {
            const scriptPath = path.join(this.scriptsPath, scriptName);
            const python = spawn('python3', [scriptPath, ...args]);
            
            let stdout = '';
            let stderr = '';
            
            python.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            python.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            python.on('close', (code) => {
                if (code === 0) {
                    try {
                        // Try to parse JSON output
                        const result = JSON.parse(stdout);
                        resolve(result);
                    } catch (e) {
                        // If not JSON, return raw output
                        resolve({ output: stdout });
                    }
                } else {
                    reject(new Error(`Python script failed with code ${code}: ${stderr}`));
                }
            });
            
            python.on('error', (error) => {
                reject(error);
            });
        });
    }

    private async runLightweightScript(args: string[] = []): Promise<any> {
        try {
            return await this.runPythonScript('rag_lightweight.py', args);
        } catch (error) {
            console.warn('Lightweight script failed, using fallback:', error);
            return { error: error.message, fallback: true };
        }
    }

    async generateEmbedding(text: string): Promise<number[]> {
        try {
            // Try the comprehensive NLP script first
            const result = await this.runPythonScript('rag_nlp_operations.py', [
                '--embeddings-only',
                '--text', text
            ]);
            
            if (result.embedding) {
                return result.embedding;
            }
        } catch (error) {
            console.warn('Advanced embedding generation failed, using lightweight approach');
        }
        
        // Fallback to simple hash-based "embedding" for basic similarity
        const hash = this.simpleTextHash(text);
        return hash;
    }

    private simpleTextHash(text: string, dimensions: number = 1536): number[] {
        // Create a simple deterministic "embedding" based on text characteristics
        const words = text.toLowerCase().split(/\s+/);
        const chars = text.split('');
        
        const embedding = new Array(dimensions).fill(0);
        
        // Use text characteristics to generate pseudo-embedding
        for (let i = 0; i < dimensions; i++) {
            let value = 0;
            
            // Word-based features
            if (words.length > 0) {
                const wordIndex = i % words.length;
                const word = words[wordIndex];
                value += word.length * Math.sin(i * 0.1);
                value += word.charCodeAt(0) * Math.cos(i * 0.05);
            }
            
            // Character-based features
            if (chars.length > 0) {
                const charIndex = i % chars.length;
                value += chars[charIndex].charCodeAt(0) * Math.sin(i * 0.02);
            }
            
            // Text length and position features
            value += text.length * Math.cos(i * 0.01);
            value += i * Math.sin(text.length * 0.001);
            
            embedding[i] = Math.tanh(value * 0.001); // Normalize to [-1, 1]
        }
        
        return embedding;
    }

    async queryDocuments(ragQuery: RAGQuery): Promise<Document[]> {
        const embedding = await this.generateEmbedding(ragQuery.query);
        const maxResults = ragQuery.maxResults || this.defaultMaxResults;
        const threshold = ragQuery.threshold || this.defaultThreshold;

        const result = await query(
            `SELECT d.*, 
                    1 - (d.content_vector <=> $1::vector) as similarity
             FROM documents d
             WHERE NOT d.is_deleted
             AND 1 - (d.content_vector <=> $1::vector) > $2
             ORDER BY similarity DESC
             LIMIT $3`,
            [embedding, threshold, maxResults]
        );

        return result.rows;
    }

    async findSimilarDocuments(documentId: string, maxResults: number = 5): Promise<Document[]> {
        const result = await query(
            `WITH source AS (
                SELECT content_vector
                FROM documents
                WHERE id = $1 AND NOT is_deleted
            )
            SELECT d.*, 
                   1 - (d.content_vector <=> (SELECT content_vector FROM source)) as similarity
            FROM documents d
            WHERE NOT d.is_deleted
            AND d.id != $1
            ORDER BY similarity DESC
            LIMIT $2`,
            [documentId, maxResults]
        );

        return result.rows;
    }

    async summarizeDocument(documentId: string): Promise<string> {
        // TODO: Implement document summarization using an LLM
        // This is a placeholder that should be replaced with actual summarization
        const result = await query(
            'SELECT content FROM documents WHERE id = $1 AND NOT is_deleted',
            [documentId]
        );

        if (!result.rows[0]) {
            throw new Error('Document not found');
        }

        return `Summary of document ${documentId}`;
    }

    async analyzeDocument(documentId: string): Promise<NLPAnalysisResult> {
        try {
            // First try the comprehensive analysis script
            const result = await this.runPythonScript('rag_nlp_operations.py', [
                '--document-id', documentId
            ]);
            
            if (result.sentiment && result.entities && result.semantic_meaning) {
                return {
                    sentiment: result.sentiment,
                    entities: result.entities,
                    semantic_meaning: result.semantic_meaning
                };
            }
        } catch (error) {
            console.warn('Advanced document analysis failed, trying lightweight approach');
        }
        
        try {
            // Get document content
            const docResult = await query(
                'SELECT content, metadata FROM documents WHERE id = $1 AND NOT is_deleted',
                [documentId]
            );

            if (!docResult.rows[0]) {
                throw new Error('Document not found');
            }

            const content = docResult.rows[0].content;
            
            // Use lightweight analysis
            const lightweightResult = await this.runLightweightScript([
                '--analyze-text', content
            ]);
            
            // Extract entities using lightweight approach
            const entitiesResult = await this.runLightweightScript([
                '--extract-entities', content
            ]);
            
            return {
                sentiment: {
                    overall_sentiment: 'neutral',
                    confidence: 0.5,
                    positive_score: 0.3,
                    negative_score: 0.2,
                    neutral_score: 0.5
                },
                entities: entitiesResult || [],
                semantic_meaning: {
                    key_concepts: [],
                    noun_phrases: [],
                    linguistic_patterns: lightweightResult.analysis || {}
                }
            };
            
        } catch (error) {
            console.error('All document analysis methods failed:', error);
            
            // Final fallback
            return {
                sentiment: {
                    overall_sentiment: 'neutral',
                    confidence: 0.1,
                    positive_score: 0.33,
                    negative_score: 0.33,
                    neutral_score: 0.34
                },
                entities: [],
                semantic_meaning: {
                    key_concepts: [],
                    noun_phrases: [],
                    linguistic_patterns: { error: 'Analysis unavailable' }
                }
            };
        }
    }

    async extractMetadata(content: string): Promise<Record<string, any>> {
        try {
            // Use the Python NLP operations script for metadata extraction
            const result = await this.runPythonScript('rag_nlp_operations.py', [
                '--sentiment-only',
                '--text', content
            ]);
            
            if (result.sentiment) {
                return {
                    language: 'en',
                    created_date: new Date().toISOString(),
                    type: 'text',
                    estimated_reading_time: Math.ceil(content.length / 1000),
                    sentiment_analysis: result.sentiment,
                    content_length: content.length,
                    word_count: content.split(/\s+/).length
                };
            }
            
            // Fallback metadata extraction
            return {
                language: 'en',
                created_date: new Date().toISOString(),
                type: 'text',
                estimated_reading_time: Math.ceil(content.length / 1000),
                content_length: content.length,
                word_count: content.split(/\s+/).length
            };
        } catch (error) {
            console.error('Error extracting metadata:', error);
            // Return basic metadata on error
            return {
                language: 'en',
                created_date: new Date().toISOString(),
                type: 'text',
                estimated_reading_time: Math.ceil(content.length / 1000)
            };
        }
    }

    async updateDocumentVectors(): Promise<void> {
        const result = await query(
            'SELECT id, content FROM documents WHERE content_vector IS NULL AND NOT is_deleted'
        );

        for (const doc of result.rows) {
            const embedding = await this.generateEmbedding(doc.content);
            await query(
                'UPDATE documents SET content_vector = $1 WHERE id = $2',
                [embedding, doc.id]
            );
        }
    }

    async processChunk(text: string, chunkSize: number = 1000): Promise<{ chunks: string[], embeddings: number[][] }> {
        try {
            // Use the Python document chunker for semantic chunking
            const result = await this.runPythonScript('rag_nlp_operations.py', [
                '--process-chunks',
                '--text', text,
                '--chunk-size', chunkSize.toString()
            ]);
            
            if (result.chunks && result.embeddings) {
                return {
                    chunks: result.chunks,
                    embeddings: result.embeddings
                };
            }
            
            // Fallback to simple chunking
            const chunks = [];
            for (let i = 0; i < text.length; i += chunkSize) {
                chunks.push(text.slice(i, i + chunkSize));
            }

            const embeddings = await Promise.all(
                chunks.map(chunk => this.generateEmbedding(chunk))
            );

            return { chunks, embeddings };
        } catch (error) {
            console.error('Error processing chunks:', error);
            
            // Fallback implementation
            const chunks = [];
            for (let i = 0; i < text.length; i += chunkSize) {
                chunks.push(text.slice(i, i + chunkSize));
            }

            const embeddings = await Promise.all(
                chunks.map(chunk => this.generateEmbedding(chunk))
            );

            return { chunks, embeddings };
        }
    }

    async validateData(): Promise<Record<string, any>> {
        try {
            const result = await this.runPythonScript('rag_data_management.py', ['--validate']);
            return result;
        } catch (error) {
            console.error('Error validating data:', error);
            throw error;
        }
    }

    async cleanData(dryRun: boolean = true): Promise<Record<string, any>> {
        try {
            const args = ['--clean'];
            if (dryRun) {
                args.push('--dry-run');
            }
            const result = await this.runPythonScript('rag_data_management.py', args);
            return result;
        } catch (error) {
            console.error('Error cleaning data:', error);
            throw error;
        }
    }

    async generateReport(reportType: string = 'content-insights', daysBack: number = 7): Promise<Record<string, any>> {
        try {
            let args: string[];
            
            switch (reportType) {
                case 'content-insights':
                    args = ['--content-insights', daysBack.toString()];
                    break;
                case 'performance':
                    args = ['--performance-report'];
                    break;
                case 'quality':
                    args = ['--quality-report'];
                    break;
                default:
                    args = ['--content-insights', daysBack.toString()];
            }
            
            const result = await this.runPythonScript('rag_query_reporting.py', args);
            return result;
        } catch (error) {
            console.error('Error generating report:', error);
            throw error;
        }
    }

    async searchSemantic(query: string, limit: number = 10): Promise<Array<Record<string, any>>> {
        try {
            const result = await this.runPythonScript('rag_query_reporting.py', [
                '--search', query,
                '--limit', limit.toString()
            ]);
            
            return result.results || [];
        } catch (error) {
            console.error('Error in semantic search:', error);
            throw error;
        }
    }

    async searchEntities(entityText?: string, entityType?: string, limit: number = 20): Promise<Array<Record<string, any>>> {
        try {
            const args = [];
            
            if (entityText) {
                args.push('--entity-search', entityText);
            }
            if (entityType) {
                args.push('--entity-type', entityType);
            }
            args.push('--limit', limit.toString());
            
            const result = await this.runPythonScript('rag_query_reporting.py', args);
            return result.results || [];
        } catch (error) {
            console.error('Error searching entities:', error);
            throw error;
        }
    }

    async reprocessDocument(documentId: string): Promise<void> {
        const result = await query(
            'SELECT content FROM documents WHERE id = $1 AND NOT is_deleted',
            [documentId]
        );

        if (!result.rows[0]) {
            throw new Error('Document not found');
        }

        const { chunks, embeddings } = await this.processChunk(result.rows[0].content);
        const metadata = await this.extractMetadata(result.rows[0].content);

        // Update document with first chunk's embedding
        await query(
            'UPDATE documents SET content_vector = $1, metadata = $2 WHERE id = $3',
            [embeddings[0], metadata, documentId]
        );

        // Store additional chunks if needed
        // TODO: Implement chunk storage logic
    }
}

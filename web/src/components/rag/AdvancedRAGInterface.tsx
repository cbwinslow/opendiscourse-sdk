'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { 
  Search, 
  Brain, 
  Network, 
  FileText, 
  BarChart3, 
  MessageSquare,
  Sparkles,
  Target,
  Link,
  Users
} from 'lucide-react';

interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
  confidence: number;
}

interface Relationship {
  source: string;
  target: string;
  relation: string;
  confidence: number;
}

interface RAGResult {
  answer: string;
  confidence: number;
  sources: Array<{
    id: string;
    title: string;
    excerpt: string;
    relevance: number;
    url?: string;
  }>;
  entities: Entity[];
  relationships: Relationship[];
  sentiment: {
    label: string;
    score: number;
  };
  keywords: Array<{
    text: string;
    weight: number;
  }>;
}

export function AdvancedRAGInterface() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<RAGResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('answer');

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      // Simulate advanced RAG processing with NLP analysis
      await new Promise(resolve => setTimeout(resolve, 2000));

      const mockResult: RAGResult = {
        answer: `Based on comprehensive analysis of political documents, here's what I found regarding "${query}":

The Infrastructure Investment and Jobs Act represents a significant bipartisan effort to modernize America's infrastructure. Key provisions include:

• $110 billion for roads and bridges repair
• $65 billion for broadband internet expansion  
• $55 billion for water infrastructure improvements
• $39 billion for public transit modernization

This legislation demonstrates cross-party collaboration on critical infrastructure needs, with implications for economic growth, job creation, and technological advancement across multiple sectors.`,
        confidence: 0.92,
        sources: [
          {
            id: 'hr3684',
            title: 'Infrastructure Investment and Jobs Act (H.R.3684)',
            excerpt: 'This bill provides funding for infrastructure improvements including roads, bridges, broadband, and clean energy initiatives...',
            relevance: 0.95,
            url: 'https://congress.gov/bill/117th-congress/house-bill/3684'
          },
          {
            id: 'cbo-analysis',
            title: 'CBO Cost Estimate - Infrastructure Bill',
            excerpt: 'The Congressional Budget Office estimates the bill will add $256 billion to the deficit over 10 years...',
            relevance: 0.87
          },
          {
            id: 'committee-report',
            title: 'House Committee on Transportation Report',
            excerpt: 'The committee finds that the proposed infrastructure investments will create approximately 2 million jobs...',
            relevance: 0.83
          }
        ],
        entities: [
          { text: 'Infrastructure Investment and Jobs Act', label: 'LEGISLATION', start: 23, end: 58, confidence: 0.98 },
          { text: 'H.R.3684', label: 'BILL_NUMBER', start: 59, end: 67, confidence: 0.99 },
          { text: '$110 billion', label: 'MONETARY', start: 150, end: 162, confidence: 0.95 },
          { text: 'Congress', label: 'ORGANIZATION', start: 400, end: 408, confidence: 0.92 },
          { text: 'bipartisan', label: 'POLITICAL_CONCEPT', start: 85, end: 95, confidence: 0.88 }
        ],
        relationships: [
          { source: 'Infrastructure Investment and Jobs Act', target: '$110 billion', relation: 'ALLOCATES', confidence: 0.94 },
          { source: 'H.R.3684', target: 'roads and bridges', relation: 'FUNDS', confidence: 0.91 },
          { source: 'Congress', target: 'Infrastructure Investment and Jobs Act', relation: 'PASSED', confidence: 0.96 }
        ],
        sentiment: {
          label: 'POSITIVE',
          score: 0.73
        },
        keywords: [
          { text: 'infrastructure', weight: 0.95 },
          { text: 'bipartisan', weight: 0.82 },
          { text: 'investment', weight: 0.78 },
          { text: 'modernization', weight: 0.71 },
          { text: 'economic growth', weight: 0.69 }
        ]
      };

      setResult(mockResult);
    } catch (error) {
      console.error('RAG search error:', error);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const renderEntities = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <Target className="h-5 w-5" />
        Named Entity Recognition
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {result?.entities.map((entity, index) => (
          <Card key={index} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Badge variant="outline">{entity.label}</Badge>
              <span className="text-sm text-muted-foreground">
                {(entity.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <p className="font-medium">{entity.text}</p>
            <p className="text-sm text-muted-foreground">
              Position: {entity.start}-{entity.end}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderRelationships = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <Link className="h-5 w-5" />
        Entity Relationships
      </h3>
      <div className="space-y-3">
        {result?.relationships.map((rel, index) => (
          <Card key={index} className="p-4">
            <div className="flex items-center gap-2 text-sm">
              <Badge variant="secondary">{rel.source}</Badge>
              <span className="px-2 py-1 bg-primary/10 text-primary rounded text-xs">
                {rel.relation}
              </span>
              <Badge variant="secondary">{rel.target}</Badge>
              <span className="ml-auto text-muted-foreground">
                {(rel.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sentiment Analysis */}
        <Card className="p-4">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Sentiment Analysis
          </h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>{result?.sentiment.label}</span>
              <Badge variant={result?.sentiment.label === 'POSITIVE' ? 'default' : 'secondary'}>
                {((result?.sentiment.score || 0) * 100).toFixed(1)}%
              </Badge>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${(result?.sentiment.score || 0) * 100}%` }}
              />
            </div>
          </div>
        </Card>

        {/* Confidence Score */}
        <Card className="p-4">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            Answer Confidence
          </h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>Overall Confidence</span>
              <Badge variant="default">
                {((result?.confidence || 0) * 100).toFixed(1)}%
              </Badge>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all"
                style={{ width: `${(result?.confidence || 0) * 100}%` }}
              />
            </div>
          </div>
        </Card>
      </div>

      {/* Keywords */}
      <Card className="p-4">
        <h4 className="font-semibold mb-3 flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          Key Topics & Weights
        </h4>
        <div className="space-y-2">
          {result?.keywords.map((keyword, index) => (
            <div key={index} className="flex items-center gap-3">
              <span className="min-w-0 flex-1">{keyword.text}</span>
              <div className="flex items-center gap-2 min-w-[120px]">
                <div className="flex-1 bg-secondary rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: `${keyword.weight * 100}%` }}
                  />
                </div>
                <span className="text-sm text-muted-foreground w-12 text-right">
                  {(keyword.weight * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <Brain className="h-8 w-8 text-primary" />
          Advanced RAG Analysis Platform
        </h1>
        <p className="text-muted-foreground">
          AI-powered political document analysis with NLP, entity recognition, and knowledge graphs
        </p>
      </div>

      {/* Search Interface */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Ask a question about political documents, legislation, or policy..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="text-lg"
              />
            </div>
            <Button 
              onClick={handleSearch} 
              disabled={loading || !query.trim()}
              size="lg"
              className="flex items-center gap-2"
            >
              {loading ? (
                <LoadingSpinner />
              ) : (
                <Search className="h-4 w-4" />
              )}
              Analyze
            </Button>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => setQuery("What are the key provisions of the Infrastructure Investment and Jobs Act?")}>
              Infrastructure Bill
            </Button>
            <Button variant="outline" size="sm" onClick={() => setQuery("How does the Build Back Better Act address climate change?")}>
              Climate Policy
            </Button>
            <Button variant="outline" size="sm" onClick={() => setQuery("What voting patterns exist in congressional healthcare legislation?")}>
              Healthcare Voting
            </Button>
          </div>
        </div>
      </Card>

      {/* Results */}
      {result && (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="answer" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Answer
            </TabsTrigger>
            <TabsTrigger value="entities" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Entities
            </TabsTrigger>
            <TabsTrigger value="relationships" className="flex items-center gap-2">
              <Network className="h-4 w-4" />
              Relations
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="sources" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Sources
            </TabsTrigger>
          </TabsList>

          <TabsContent value="answer" className="space-y-4">
            <Card className="p-6">
              <CardHeader className="px-0 pt-0">
                <CardTitle className="flex items-center justify-between">
                  RAG Response
                  <Badge variant="default">
                    Confidence: {((result.confidence) * 100).toFixed(1)}%
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="px-0">
                <div className="prose prose-slate dark:prose-invert max-w-none">
                  {result.answer.split('\n').map((paragraph, index) => (
                    <p key={index} className="mb-4 last:mb-0">{paragraph}</p>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="entities">
            <Card className="p-6">
              {renderEntities()}
            </Card>
          </TabsContent>

          <TabsContent value="relationships">
            <Card className="p-6">
              {renderRelationships()}
            </Card>
          </TabsContent>

          <TabsContent value="analytics">
            <Card className="p-6">
              {renderAnalytics()}
            </Card>
          </TabsContent>

          <TabsContent value="sources">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Source Documents
              </h3>
              <div className="space-y-4">
                {result.sources.map((source, index) => (
                  <Card key={index} className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium">{source.title}</h4>
                      <Badge variant="outline">
                        {(source.relevance * 100).toFixed(1)}% relevant
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">{source.excerpt}</p>
                    {source.url && (
                      <Button variant="outline" size="sm" asChild>
                        <a href={source.url} target="_blank" rel="noopener noreferrer">
                          View Document
                        </a>
                      </Button>
                    )}
                  </Card>
                ))}
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
'use client';

import React, { useState, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { 
  Search, 
  FileText, 
  Network, 
  BarChart3,
  Download,
  Share2,
  Eye,
  Calendar,
  Tag,
  Users,
  MapPin,
  TrendingUp
} from 'lucide-react';

interface Document {
  id: string;
  title: string;
  content: string;
  metadata: {
    source: string;
    documentType: string;
    billNumber?: string;
    congressSession?: string;
    committee?: string;
    sponsor?: string;
    cosponsor?: string[];
    dateIntroduced?: string;
    dateOfAction?: string;
    status?: string;
    tags: string[];
  };
  analysis: {
    entities: Array<{
      text: string;
      label: string;
      confidence: number;
    }>;
    sentiment: {
      score: number;
      label: string;
    };
    complexity: number;
    readabilityScore: number;
    keyTopics: Array<{
      topic: string;
      weight: number;
    }>;
    politicalLean?: {
      score: number;
      label: string;
    };
  };
  connections: Array<{
    targetDocumentId: string;
    targetTitle: string;
    relationshipType: string;
    strength: number;
  }>;
}



export function AdvancedDocumentAnalysis() {
  const [searchQuery, setSearchQuery] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      // Simulate advanced document search and analysis
      await new Promise(resolve => setTimeout(resolve, 1500));

      const mockDocuments: Document[] = [
        {
          id: 'hr3684',
          title: 'Infrastructure Investment and Jobs Act',
          content: 'This bill provides funding for infrastructure improvements including roads, bridges, broadband, and clean energy initiatives. The legislation represents a comprehensive approach to modernizing America\'s infrastructure with bipartisan support.',
          metadata: {
            source: 'congress.gov',
            documentType: 'bill',
            billNumber: 'H.R.3684',
            congressSession: '117th Congress',
            committee: 'House Transportation and Infrastructure',
            sponsor: 'Rep. Peter DeFazio (D-OR)',
            cosponsor: ['Rep. Sam Graves (R-MO)', 'Rep. Eleanor Holmes Norton (D-DC)'],
            dateIntroduced: '2021-06-04',
            dateOfAction: '2021-11-15',
            status: 'Passed/Signed',
            tags: ['infrastructure', 'transportation', 'broadband', 'bipartisan']
          },
          analysis: {
            entities: [
              { text: 'Infrastructure Investment and Jobs Act', label: 'LEGISLATION', confidence: 0.98 },
              { text: 'Peter DeFazio', label: 'PERSON', confidence: 0.95 },
              { text: 'House Transportation', label: 'ORGANIZATION', confidence: 0.92 },
              { text: '$110 billion', label: 'MONEY', confidence: 0.94 }
            ],
            sentiment: { score: 0.72, label: 'POSITIVE' },
            complexity: 0.78,
            readabilityScore: 65,
            keyTopics: [
              { topic: 'Infrastructure', weight: 0.95 },
              { topic: 'Transportation', weight: 0.87 },
              { topic: 'Broadband', weight: 0.73 },
              { topic: 'Jobs', weight: 0.69 }
            ],
            politicalLean: { score: 0.15, label: 'SLIGHTLY_LEFT' }
          },
          connections: [
            {
              targetDocumentId: 'hr5376',
              targetTitle: 'Build Back Better Act',
              relationshipType: 'COMPLEMENTARY',
              strength: 0.84
            },
            {
              targetDocumentId: 'senate-amendment-2',
              targetTitle: 'Senate Infrastructure Amendment',
              relationshipType: 'AMENDMENT',
              strength: 0.92
            }
          ]
        },
        {
          id: 'hr5376',
          title: 'Build Back Better Act',
          content: 'A comprehensive social spending and climate change bill that aims to expand social programs and combat climate change through various initiatives.',
          metadata: {
            source: 'congress.gov',
            documentType: 'bill',
            billNumber: 'H.R.5376',
            congressSession: '117th Congress',
            committee: 'House Budget Committee',
            sponsor: 'Rep. John Yarmuth (D-KY)',
            dateIntroduced: '2021-09-27',
            status: 'House Passed',
            tags: ['climate', 'social programs', 'healthcare', 'childcare']
          },
          analysis: {
            entities: [
              { text: 'Build Back Better Act', label: 'LEGISLATION', confidence: 0.97 },
              { text: 'John Yarmuth', label: 'PERSON', confidence: 0.94 },
              { text: 'climate change', label: 'CONCEPT', confidence: 0.89 }
            ],
            sentiment: { score: 0.68, label: 'POSITIVE' },
            complexity: 0.85,
            readabilityScore: 58,
            keyTopics: [
              { topic: 'Climate', weight: 0.91 },
              { topic: 'Social Programs', weight: 0.86 },
              { topic: 'Healthcare', weight: 0.74 },
              { topic: 'Tax Policy', weight: 0.67 }
            ],
            politicalLean: { score: -0.45, label: 'LEFT' }
          },
          connections: [
            {
              targetDocumentId: 'hr3684',
              targetTitle: 'Infrastructure Investment and Jobs Act',
              relationshipType: 'COMPLEMENTARY',
              strength: 0.84
            }
          ]
        }
      ];

      setDocuments(mockDocuments);
      if (mockDocuments.length > 0) {
        setSelectedDocument(mockDocuments[0]);
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  const renderDocumentOverview = () => {
    if (!selectedDocument) return null;

    return (
      <div className="space-y-6">
        {/* Document Header */}
        <Card className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">{selectedDocument.title}</h2>
              <div className="flex flex-wrap gap-2 mb-3">
                <Badge variant="outline">
                  {selectedDocument.metadata.billNumber}
                </Badge>
                <Badge variant="secondary">
                  {selectedDocument.metadata.documentType}
                </Badge>
                <Badge variant="outline">
                  {selectedDocument.metadata.congressSession}
                </Badge>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <Share2 className="h-4 w-4 mr-2" />
                Share
              </Button>
            </div>
          </div>
          
          <p className="text-muted-foreground leading-relaxed">{selectedDocument.content}</p>
        </Card>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4 text-center">
            <BarChart3 className="h-8 w-8 mx-auto mb-2 text-blue-500" />
            <p className="text-sm text-muted-foreground">Complexity</p>
            <p className="text-2xl font-bold">
              {(selectedDocument.analysis.complexity * 100).toFixed(0)}%
            </p>
          </Card>
          
          <Card className="p-4 text-center">
            <TrendingUp className="h-8 w-8 mx-auto mb-2 text-green-500" />
            <p className="text-sm text-muted-foreground">Readability</p>
            <p className="text-2xl font-bold">
              {selectedDocument.analysis.readabilityScore}
            </p>
          </Card>
          
          <Card className="p-4 text-center">
            <Users className="h-8 w-8 mx-auto mb-2 text-purple-500" />
            <p className="text-sm text-muted-foreground">Sentiment</p>
            <p className="text-2xl font-bold">
              {selectedDocument.analysis.sentiment.label}
            </p>
          </Card>
          
          <Card className="p-4 text-center">
            <Network className="h-8 w-8 mx-auto mb-2 text-orange-500" />
            <p className="text-sm text-muted-foreground">Connections</p>
            <p className="text-2xl font-bold">
              {selectedDocument.connections.length}
            </p>
          </Card>
        </div>

        {/* Metadata */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Document Metadata
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Sponsor:</span>
                <span>{selectedDocument.metadata.sponsor}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Committee:</span>
                <span>{selectedDocument.metadata.committee}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Date Introduced:</span>
                <span>{selectedDocument.metadata.dateIntroduced}</span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Status:</span>
                <Badge variant="default">{selectedDocument.metadata.status}</Badge>
              </div>
              
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Tags:</span>
                <div className="flex flex-wrap gap-1">
                  {selectedDocument.metadata.tags.map((tag, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    );
  };

  const renderAnalytics = () => {
    if (!selectedDocument) return null;

    return (
      <div className="space-y-6">
        {/* Key Topics */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Key Topics Analysis</h3>
          <div className="space-y-3">
            {selectedDocument.analysis.keyTopics.map((topic, index) => (
              <div key={index} className="flex items-center gap-3">
                <span className="min-w-0 flex-1 font-medium">{topic.topic}</span>
                <div className="flex items-center gap-2 min-w-[150px]">
                  <div className="flex-1 bg-secondary rounded-full h-2">
                    <div 
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ width: `${topic.weight * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground w-12 text-right">
                    {(topic.weight * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Named Entities */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Named Entity Recognition</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {selectedDocument.analysis.entities.map((entity, index) => (
              <Card key={index} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="outline">{entity.label}</Badge>
                  <span className="text-sm text-muted-foreground">
                    {(entity.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="font-medium">{entity.text}</p>
              </Card>
            ))}
          </div>
        </Card>

        {/* Political Analysis */}
        {selectedDocument.analysis.politicalLean && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Political Lean Analysis</h3>
            <div className="flex items-center justify-between p-4 bg-secondary rounded-lg">
              <span className="font-medium">Political Orientation:</span>
              <div className="flex items-center gap-2">
                <Badge variant={
                  selectedDocument.analysis.politicalLean.label.includes('LEFT') ? 'default' :
                  selectedDocument.analysis.politicalLean.label.includes('RIGHT') ? 'secondary' :
                  'outline'
                }>
                  {selectedDocument.analysis.politicalLean.label}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Score: {selectedDocument.analysis.politicalLean.score.toFixed(2)}
                </span>
              </div>
            </div>
          </Card>
        )}
      </div>
    );
  };

  const renderConnections = () => {
    if (!selectedDocument) return null;

    return (
      <div className="space-y-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Network className="h-5 w-5" />
            Document Relationships
          </h3>
          
          <div className="space-y-4">
            {selectedDocument.connections.map((connection, index) => (
              <Card key={index} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{connection.targetTitle}</h4>
                  <Badge variant="outline">
                    {(connection.strength * 100).toFixed(0)}% similarity
                  </Badge>
                </div>
                
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">
                    {connection.relationshipType}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    Document ID: {connection.targetDocumentId}
                  </span>
                </div>
                
                <div className="mt-3">
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4 mr-2" />
                    View Document
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </Card>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <FileText className="h-8 w-8 text-primary" />
          Advanced Document Analysis
        </h1>
        <p className="text-muted-foreground">
          Comprehensive political document analysis with NLP, entity recognition, and relationship mapping
        </p>
      </div>

      {/* Search Interface */}
      <Card className="p-6">
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <Input
              placeholder="Search political documents, bills, legislation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="text-lg"
            />
          </div>
          <Button 
            onClick={handleSearch} 
            disabled={loading || !searchQuery.trim()}
            size="lg"
            className="flex items-center gap-2"
          >
            {loading ? <LoadingSpinner /> : <Search className="h-4 w-4" />}
            Analyze
          </Button>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={() => setSearchQuery("infrastructure spending")}>
            Infrastructure
          </Button>
          <Button variant="outline" size="sm" onClick={() => setSearchQuery("healthcare reform")}>
            Healthcare
          </Button>
          <Button variant="outline" size="sm" onClick={() => setSearchQuery("climate change policy")}>
            Climate Policy
          </Button>
          <Button variant="outline" size="sm" onClick={() => setSearchQuery("defense authorization")}>
            Defense
          </Button>
        </div>
      </Card>

      {/* Results */}
      {documents.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Document List */}
          <div className="lg:col-span-1">
            <Card className="p-4">
              <h3 className="font-semibold mb-4">Found Documents ({documents.length})</h3>
              <div className="space-y-2">
                {documents.map((doc) => (
                  <button
                    key={doc.id}
                    onClick={() => setSelectedDocument(doc)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedDocument?.id === doc.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-secondary'
                    }`}
                  >
                    <div className="font-medium text-sm mb-1">{doc.title}</div>
                    <div className="text-xs opacity-70">{doc.metadata.billNumber}</div>
                  </button>
                ))}
              </div>
            </Card>
          </div>

          {/* Document Analysis */}
          <div className="lg:col-span-3">
            {selectedDocument && (
              <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="analytics">Analytics</TabsTrigger>
                  <TabsTrigger value="connections">Connections</TabsTrigger>
                </TabsList>

                <TabsContent value="overview">
                  {renderDocumentOverview()}
                </TabsContent>

                <TabsContent value="analytics">
                  {renderAnalytics()}
                </TabsContent>

                <TabsContent value="connections">
                  {renderConnections()}
                </TabsContent>
              </Tabs>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
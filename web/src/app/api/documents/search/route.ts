import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { query, filters } = await request.json();

    // In a real app, this would search your document database with vector embeddings
    // For demo purposes, we'll return mock data
    const mockDocuments = [
      {
        id: '1',
        title: 'Infrastructure Investment and Jobs Act',
        content: 'This bill provides funding for infrastructure improvements including roads, bridges, broadband, and clean energy...',
        metadata: {
          source: 'congress.gov',
          documentType: 'bill',
          billNumber: 'H.R.3684',
          congressSession: '117th Congress',
          committee: 'House Transportation and Infrastructure',
          tags: ['infrastructure', 'transportation', 'broadband']
        },
        createdAt: new Date('2021-06-01'),
        updatedAt: new Date('2021-11-15'),
      },
      {
        id: '2',
        title: 'Build Back Better Act',
        content: 'A comprehensive social spending and climate change bill that aims to expand social programs and combat climate change...',
        metadata: {
          source: 'congress.gov',
          documentType: 'bill',
          billNumber: 'H.R.5376',
          congressSession: '117th Congress',
          committee: 'House Budget Committee',
          tags: ['climate', 'social programs', 'healthcare']
        },
        createdAt: new Date('2021-09-27'),
        updatedAt: new Date('2021-11-19'),
      }
    ];

    // Filter documents based on query (simple text match for demo)
    const results = mockDocuments.filter(doc => 
      doc.title.toLowerCase().includes(query.toLowerCase()) ||
      doc.content.toLowerCase().includes(query.toLowerCase()) ||
      doc.metadata.tags?.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
    );

    return NextResponse.json({
      success: true,
      data: {
        documents: results,
        totalCount: results.length,
        query,
        filters
      }
    });
  } catch (error) {
    console.error('Document search error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'SEARCH_ERROR',
          message: 'Failed to search documents',
        },
      },
      { status: 500 }
    );
  }
}
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');

    // Mock documents data
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
      },
      // Add more mock documents to test pagination
      ...Array.from({ length: 50 }, (_, i) => ({
        id: `${i + 3}`,
        title: `Sample Document ${i + 3}`,
        content: `This is sample content for document ${i + 3} to demonstrate pagination...`,
        metadata: {
          source: 'mock-source',
          documentType: 'legislative' as const,
          tags: ['sample', 'demo']
        },
        createdAt: new Date(2021, 0, i + 1),
        updatedAt: new Date(2021, 0, i + 1),
      }))
    ];

    // Implement pagination
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedDocuments = mockDocuments.slice(startIndex, endIndex);

    return NextResponse.json({
      success: true,
      data: {
        documents: paginatedDocuments,
        totalCount: mockDocuments.length,
        page,
        limit,
        totalPages: Math.ceil(mockDocuments.length / limit)
      }
    });
  } catch (error) {
    console.error('Document fetch error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'FETCH_ERROR',
          message: 'Failed to fetch documents',
        },
      },
      { status: 500 }
    );
  }
}
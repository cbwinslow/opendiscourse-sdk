import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Clear the authentication cookie
    const response = NextResponse.json({
      success: true,
      data: { message: 'Logged out successfully' },
    });

    response.cookies.delete('opendiscourse-token');

    return response;
  } catch (error) {
    console.error('Logout error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An error occurred during logout',
        },
      },
      { status: 500 }
    );
  }
}
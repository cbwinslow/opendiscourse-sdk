import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // In a real app, you would validate the JWT token or session
    const token = request.cookies.get('opendiscourse-token')?.value;

    if (token) {
      // Simulate getting user data from token
      const user = {
        id: '1',
        username: 'admin',
        email: 'admin@opendiscourse.com',
        role: 'admin' as const,
        lastLogin: new Date(),
      };

      return NextResponse.json({
        success: true,
        data: { user },
      });
    } else {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Not authenticated',
          },
        },
        { status: 401 }
      );
    }
  } catch (error) {
    console.error('Authentication check error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An error occurred while checking authentication',
        },
      },
      { status: 500 }
    );
  }
}
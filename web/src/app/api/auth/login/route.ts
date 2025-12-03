import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { username, password } = await request.json();

    // In a real app, you would validate against a database
    // For demo purposes, we'll simulate authentication
    if (username && password) {
      const user = {
        id: '1',
        username,
        email: `${username}@opendiscourse.com`,
        role: 'admin' as const,
        lastLogin: new Date(),
      };

      // In a real app, you would set secure HTTP-only cookies
      const response = NextResponse.json({
        success: true,
        data: { user, token: 'demo-token' },
      });

      // Set a demo cookie
      response.cookies.set('opendiscourse-token', 'demo-token', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days
      });

      return response;
    } else {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid username or password',
          },
        },
        { status: 401 }
      );
    }
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An error occurred during login',
        },
      },
      { status: 500 }
    );
  }
}
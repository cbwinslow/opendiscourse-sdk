import type { Metadata } from 'next';
import { ThemeProvider } from 'next-themes';
import { Toaster } from '@/components/ui/toaster';
import { AuthProvider } from '@/contexts/AuthContext';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: {
    default: 'OpenDiscourse - Political Document Analysis Platform',
    template: '%s | OpenDiscourse',
  },
  description: 'Enterprise-grade platform for government document analysis and retrieval with AI-powered semantic search, NLP processing, and comprehensive political data management.',
  keywords: [
    'political analysis',
    'document analysis',
    'government data',
    'semantic search',
    'NLP',
    'political intelligence',
    'legislative analysis',
    'RAG',
    'AI-powered research'
  ],
  authors: [{ name: 'OpenDiscourse Team' }],
  creator: 'OpenDiscourse',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://opendiscourse.com',
    title: 'OpenDiscourse - Political Document Analysis Platform',
    description: 'Enterprise-grade platform for government document analysis and retrieval',
    siteName: 'OpenDiscourse',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'OpenDiscourse Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'OpenDiscourse - Political Document Analysis Platform',
    description: 'Enterprise-grade platform for government document analysis and retrieval',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'your-google-verification-code',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <div className="relative flex min-h-screen flex-col">
              <div className="flex-1">{children}</div>
            </div>
            <Toaster />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
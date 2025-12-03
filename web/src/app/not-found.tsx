import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { FileQuestion, Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="flex items-center justify-center min-h-screen p-4">
        <Card className="w-full max-w-md p-8 text-center">
          <div className="flex justify-center mb-4">
            <FileQuestion className="h-12 w-12 text-slate-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            Page Not Found
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
          <div className="space-y-3">
            <Button asChild className="w-full">
              <Link href="/">
                <Home className="h-4 w-4 mr-2" />
                Go to homepage
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full">
              <Link href="/search">
                Search documents
              </Link>
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
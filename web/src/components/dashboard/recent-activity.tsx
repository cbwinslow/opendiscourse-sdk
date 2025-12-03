import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Clock, ExternalLink } from 'lucide-react';

interface QueryItem {
  query: string;
  time: string;
}

interface RecentActivityProps {
  queries: QueryItem[];
}

export function RecentActivity({ queries }: RecentActivityProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Clock className="h-5 w-5" />
          <span>Recent RAG Queries</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {queries.map((item, index) => (
            <div key={index} className="flex items-start justify-between py-3 border-b last:border-0">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100 line-clamp-2">
                  {item.query}
                </p>
                <p className="text-xs text-muted-foreground mt-1 flex items-center">
                  <Clock className="h-3 w-3 mr-1" />
                  {item.time}
                </p>
              </div>
              <Button variant="ghost" size="sm" className="ml-4 flex-shrink-0">
                <ExternalLink className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t">
          <Button variant="outline" size="sm" className="w-full">
            View All Queries
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
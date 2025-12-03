import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, BarChart3, Settings } from 'lucide-react';

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button asChild className="h-auto p-4 flex-col space-y-2">
            <a href="/upload">
              <Upload className="h-6 w-6" />
              <span className="font-medium">Upload Documents</span>
              <span className="text-xs opacity-90">Add new files for analysis</span>
            </a>
          </Button>
          <Button asChild variant="outline" className="h-auto p-4 flex-col space-y-2">
            <a href="/analytics">
              <BarChart3 className="h-6 w-6" />
              <span className="font-medium">View Analytics</span>
              <span className="text-xs opacity-70">Explore data insights</span>
            </a>
          </Button>
          <Button asChild variant="outline" className="h-auto p-4 flex-col space-y-2">
            <a href="/settings">
              <Settings className="h-6 w-6" />
              <span className="font-medium">Settings</span>
              <span className="text-xs opacity-70">Configure platform</span>
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
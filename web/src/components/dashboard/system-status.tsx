import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, CheckCircle, AlertCircle } from 'lucide-react';

interface ServiceItem {
  service: string;
  status: string;
  uptime: string;
}

interface SystemStatusProps {
  services: ServiceItem[];
}

function StatusBadge({ status }: { status: string }) {
  const isOperational = status.toLowerCase() === 'operational';
  return (
    <Badge
      variant={isOperational ? 'default' : 'destructive'}
      className={`${
        isOperational
          ? 'bg-green-100 text-green-800 hover:bg-green-100'
          : 'bg-red-100 text-red-800 hover:bg-red-100'
      }`}
    >
      {isOperational ? (
        <CheckCircle className="h-3 w-3 mr-1" />
      ) : (
        <AlertCircle className="h-3 w-3 mr-1" />
      )}
      {status}
    </Badge>
  );
}

export function SystemStatus({ services }: SystemStatusProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Activity className="h-5 w-5" />
          <span>System Status</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {services.map((item, index) => (
            <div key={index} className="flex items-center justify-between py-3 border-b last:border-0">
              <div className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full ${
                  item.status.toLowerCase() === 'operational' ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {item.service}
                </span>
              </div>
              <div className="text-right space-y-1">
                <StatusBadge status={item.status} />
                <p className="text-xs text-muted-foreground">{item.uptime} uptime</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Overall Status</span>
            <StatusBadge status="Operational" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Search,
  MessageSquare,
  FileText,
  Users,
  Terminal,
  FolderOpen,
  ArrowRight,
} from 'lucide-react';

const features = [
  {
    title: 'Semantic Search',
    description: 'Search across government documents with AI-powered semantic search',
    href: '/search',
    icon: Search,
    color: 'bg-blue-500',
  },
  {
    title: 'RAG Chat',
    description: 'Query government documents using AI-powered retrieval and generation',
    href: '/chat',
    icon: MessageSquare,
    color: 'bg-green-500',
  },
  {
    title: 'Document Library',
    description: 'Browse and analyze government documents with advanced capabilities',
    href: '/documents',
    icon: FileText,
    color: 'bg-purple-500',
  },
  {
    title: 'Entity Analysis',
    description: 'Explore entities and relationships in legislative documents',
    href: '/entities',
    icon: Users,
    color: 'bg-orange-500',
  },
  {
    title: 'API Console',
    description: 'Execute data processing and analysis scripts in a controlled environment',
    href: '/console',
    icon: Terminal,
    color: 'bg-red-500',
  },
  {
    title: 'Data Workspace',
    description: 'Collaborative environment for research and analysis projects',
    href: '/workspace',
    icon: FolderOpen,
    color: 'bg-indigo-500',
  },
];

export function FeatureGrid() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Platform Features
        </h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature, index) => {
          const IconComponent = feature.icon;
          return (
            <Card key={index} className="group hover:shadow-lg transition-all duration-200 cursor-pointer">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className={`p-3 rounded-lg ${feature.color} text-white`}>
                    <IconComponent className="h-6 w-6" />
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <CardTitle className="text-lg group-hover:text-primary transition-colors">
                  {feature.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  {feature.description}
                </p>
                <Button asChild variant="outline" size="sm" className="w-full">
                  <a href={feature.href}>
                    Launch Tool
                  </a>
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
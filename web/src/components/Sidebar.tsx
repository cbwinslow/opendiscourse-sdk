import React from 'react';
import { NavigationItem } from '@/types';
import { useAuth } from '@/contexts/AuthContext';

const navigationItems: NavigationItem[] = [
  {
    id: 'home',
    label: 'Home',
    href: '/',
    icon: 'home',
  },
  {
    id: 'rag',
    label: 'RAG Interface',
    href: '/rag_interface.html',
    icon: 'chat',
  },
  {
    id: 'documents',
    label: 'Document Viewer',
    href: '/data_viewer.html',
    icon: 'document',
  },
  {
    id: 'entities',
    label: 'Entity Viewer',
    href: '/entity_viewer.html',
    icon: 'tag',
  },
  {
    id: 'scripts',
    label: 'Script Runner',
    href: '/script_runner.html',
    icon: 'code',
  },
  {
    id: 'workspace',
    label: 'Workspace',
    href: '/workspace.html',
    icon: 'folder',
  },
];

const icons = {
  home: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  ),
  chat: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  ),
  document: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  tag: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
    </svg>
  ),
  code: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  ),
  folder: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  ),
};

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className = '' }: SidebarProps) {
  const { user, logout } = useAuth();
  const currentPath = window.location.pathname;

  return (
    <div className={`sidebar ${className}`}>
      <div className="p-6">
        <div className="flex items-center space-x-3 mb-8">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">OD</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-secondary-900">OpenDiscourse</h1>
            <p className="text-xs text-secondary-500">Enterprise Platform</p>
          </div>
        </div>

        <nav className="space-y-2">
          {navigationItems.map((item) => {
            const isActive = currentPath === item.href || 
                           (item.href === '/' && currentPath === '/web/index.html');
            
            return (
              <a
                key={item.id}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                    : 'text-secondary-600 hover:text-secondary-900 hover:bg-secondary-50'
                }`}
              >
                {item.icon && icons[item.icon as keyof typeof icons]}
                <span className="font-medium">{item.label}</span>
              </a>
            );
          })}
        </nav>
      </div>

      {user && (
        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-secondary-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-secondary-200 rounded-full flex items-center justify-center">
                <span className="text-secondary-600 font-medium text-sm">
                  {user.username.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <p className="text-sm font-medium text-secondary-900">{user.username}</p>
                <p className="text-xs text-secondary-500 capitalize">{user.role}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="text-secondary-400 hover:text-secondary-600 p-1"
              title="Logout"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
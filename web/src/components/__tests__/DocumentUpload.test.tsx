import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DocumentUpload from '../DocumentUpload';

// Mock fetch globally
global.fetch = jest.fn();

describe('DocumentUpload', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  test('renders upload zone with correct text', () => {
    render(<DocumentUpload />);
    
    expect(screen.getByText(/drag & drop documents here/i)).toBeInTheDocument();
    expect(screen.getByText(/click to select files/i)).toBeInTheDocument();
  });

  test('displays accepted file types', () => {
    const acceptedTypes = ['.pdf', '.docx', '.txt'];
    render(<DocumentUpload acceptedTypes={acceptedTypes} />);
    
    expect(screen.getByText(/supports: \.pdf, \.docx, \.txt/i)).toBeInTheDocument();
  });

  test('shows max files and size limits', () => {
    const maxFiles = 5;
    const maxSize = 1024 * 1024; // 1MB
    
    render(<DocumentUpload maxFiles={maxFiles} maxSize={maxSize} />);
    
    expect(screen.getByText(/max 5 files/i)).toBeInTheDocument();
    expect(screen.getByText(/1 mb per file/i)).toBeInTheDocument();
  });

  test('handles file selection', async () => {
    const mockOnUpload = jest.fn();
    render(<DocumentUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });
  });

  test('shows upload progress', async () => {
    const mockOnUpload = jest.fn();
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true })
    });
    
    render(<DocumentUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('Upload Progress (1 files)')).toBeInTheDocument();
    });
  });

  test('handles upload errors', async () => {
    const mockOnUpload = jest.fn();
    (fetch as jest.Mock).mockRejectedValue(new Error('Upload failed'));
    
    render(<DocumentUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeInTheDocument();
    });
  });

  test('allows file removal', async () => {
    render(<DocumentUpload />);
    
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });
    
    const removeButton = screen.getByRole('button', { name: /remove/i });
    fireEvent.click(removeButton);
    
    await waitFor(() => {
      expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
    });
  });

  test('formats file sizes correctly', () => {
    render(<DocumentUpload />);
    
    // This tests the internal formatFileSize function indirectly
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    const file = new File(['x'.repeat(1024)], 'test.txt', { type: 'text/plain' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // Should show "1 KB" for a 1024 byte file
    expect(screen.getByText(/1 kb/i)).toBeInTheDocument();
  });
});

"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, File, X } from "lucide-react";

interface FileUploaderProps {
  onUploadStart: () => void;
  onUploadSuccess: (sessionId: string, apiCount: number) => void;
  onUploadError: (message: string) => void;
  onUploadEnd: () => void;
}

export function FileUploader({
  onUploadStart,
  onUploadSuccess,
  onUploadError,
  onUploadEnd
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.har')) {
        setSelectedFile(file);
      } else {
        onUploadError("Please select a .har file");
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.name.endsWith('.har')) {
        setSelectedFile(file);
      } else {
        onUploadError("Please select a .har file");
      }
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onUploadError("No file selected");
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    onUploadStart();
    setUploadProgress(0);
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 300);
      
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload HAR file');
      }
      
      const data = await response.json();
      onUploadSuccess(data.session_id, data.api_count);
    } catch (error) {
      onUploadError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      onUploadEnd();
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload HAR File</CardTitle>
        <CardDescription>
          Select or drag & drop a .har file to upload
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div 
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            accept=".har"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileSelect}
          />
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            Drag and drop your .har file here, or click to browse
          </p>
        </div>
        
        {selectedFile && (
          <div className="mt-4">
            <div className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
              <div className="flex items-center space-x-2">
                <File className="h-5 w-5 text-blue-500" />
                <span className="font-medium text-sm truncate max-w-[200px]">
                  {selectedFile.name}
                </span>
                <span className="text-gray-500 text-xs">
                  ({Math.round(selectedFile.size / 1024)} KB)
                </span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClearFile}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            {uploadProgress > 0 && (
              <Progress value={uploadProgress} className="mt-2" />
            )}
            
            <Button 
              className="mt-4 w-full"
              onClick={handleUpload}
              disabled={uploadProgress > 0 && uploadProgress < 100}
            >
              {uploadProgress > 0 && uploadProgress < 100
                ? 'Uploading...'
                : 'Upload HAR File'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
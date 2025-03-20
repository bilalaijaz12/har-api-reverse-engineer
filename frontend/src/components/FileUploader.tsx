"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, File, X, AlertCircle } from "lucide-react";

interface FileUploaderProps {
  onUploadStart: () => void;
  onUploadSuccess: (sessionId: string, apiCount: number) => void;
  onUploadError: (message: string) => void;
  onFileRemoved: () => void;
  onUploadEnd: () => void;
}

export function FileUploader({
  onUploadStart,
  onUploadSuccess,
  onUploadError,
  onFileRemoved,
  onUploadEnd
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
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
    
    // Notify parent that file has been removed
    onFileRemoved();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    onUploadStart();
    setIsUploading(true);
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
      setIsUploading(false);
      onUploadEnd();
    }
  };

  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl">Upload HAR File</CardTitle>
        <CardDescription className="text-base">
          Select or drag & drop a .har file to upload
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div 
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
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
          <Upload className="mx-auto h-14 w-14 text-gray-400 mb-4" />
          <p className="text-lg text-gray-600 mb-2">
            Drag and drop your .har file here
          </p>
          <p className="text-sm text-gray-500">
            or click to browse
          </p>
        </div>
        
        {selectedFile && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between bg-gray-50 p-4 rounded-md">
              <div className="flex items-center space-x-3">
                <File className="h-6 w-6 text-blue-500" />
                <div>
                  <p className="font-medium text-base truncate max-w-[200px]">
                    {selectedFile.name}
                  </p>
                  <p className="text-gray-500 text-sm">
                    {Math.round(selectedFile.size / 1024)} KB
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClearFile}
                className="h-8 w-8"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            
            {uploadProgress > 0 && (
              <div className="space-y-1">
                <div className="flex justify-between text-sm text-gray-500">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="h-2" />
              </div>
            )}
            
            <Button 
              className="w-full h-12 text-base"
              onClick={handleUpload}
              disabled={isUploading}
            >
              {isUploading
                ? 'Uploading...'
                : 'Upload HAR File'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
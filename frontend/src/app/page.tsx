"use client";

import { useState } from "react";
import { FileUploader } from "@/components/FileUploader";
import { DescriptionInput } from "@/components/DescriptionInput";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import {ApiInfo} from "@/components/ApiInfo";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [apiCount, setApiCount] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [curlCommand, setCurlCommand] = useState<string | null>(null);
  const [apiDescription, setApiDescription] = useState<string>("");
  const [apiInfo, setApiInfo] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadSuccess = (sessionId: string, apiCount: number) => {
    setSessionId(sessionId);
    setApiCount(apiCount);
    setError(null);

    // Reset previous results when a new file is uploaded
    setCurlCommand(null);
    setApiDescription("");
    setApiInfo(null);
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
    setSessionId(null);
  };

  const handleAnalysisSuccess = (curl: string, description: string, info: any) => {
    setCurlCommand(curl);
    setApiDescription(description);
    setApiInfo(info);
    setError(null);
  };

  const handleAnalysisError = (errorMessage: string) => {
    setError(errorMessage);
    setCurlCommand(null);
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-6 md:p-24">
      <div className="w-full max-w-4xl space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">HAR API Reverse Engineer</h1>
          <p className="mt-2 text-gray-600">
            Upload a HAR file and describe the API you want to reverse-engineer.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-md">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-6">
            <FileUploader 
              onUploadStart={() => setIsUploading(true)}
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
              onUploadEnd={() => setIsUploading(false)}
            />

            {sessionId && (
              <DescriptionInput
                sessionId={sessionId}
                onProcessingStart={() => setIsProcessing(true)}
                onProcessingSuccess={handleAnalysisSuccess}
                onProcessingError={handleAnalysisError}
                onProcessingEnd={() => setIsProcessing(false)}
              />
            )}
          </div>

          <div>
            {curlCommand && (
              <div className="space-y-6">
                <ResultsDisplay 
                  curlCommand={curlCommand}
                  description={apiDescription}
                />
                
                {apiInfo && (
                  <ApiInfo 
                    parameters={apiInfo.parameters}
                    authentication={apiInfo.authentication}
                    description={apiInfo.description}
                    usage_notes={apiInfo.usage_notes}
                    response_format={apiInfo.response_format}
                  />
                )}
              </div>
            )}
            
            {!curlCommand && sessionId && (
              <div className="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-md">
                <h3 className="font-medium">HAR File Processed Successfully</h3>
                <p>Found {apiCount} potential API requests.</p>
                <p className="mt-2">Please enter a description of the API you're looking for.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
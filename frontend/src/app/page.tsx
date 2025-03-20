"use client";

import { useState } from "react";
import { FileUploader } from "@/components/FileUploader";
import { DescriptionInput } from "@/components/DescriptionInput";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { ApiInfo } from "@/components/ApiInfo";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [apiCount, setApiCount] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [curlCommand, setCurlCommand] = useState<string | null>(null);
  const [apiDescription, setApiDescription] = useState<string>("");
  const [apiInfo, setApiInfo] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Function to reset all result states
  const resetResults = () => {
    setCurlCommand(null);
    setApiDescription("");
    setApiInfo(null);
  };

  const handleUploadSuccess = (sessionId: string, apiCount: number) => {
    setSessionId(sessionId);
    setApiCount(apiCount);
    setError(null);
    resetResults();
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
    setSessionId(null);
    resetResults();
  };

  const handleFileRemoved = () => {
    setSessionId(null);
    setApiCount(0);
    setError(null);
    resetResults();
  };

  const handleAnalysisStart = () => {
    // Clear previous results when starting new analysis
    resetResults();
    setIsProcessing(true);
  };

  const handleAnalysisSuccess = (curl: string | null, description: string, info: any) => {
    setCurlCommand(curl);
    setApiDescription(description);
    setApiInfo(info);
    setError(null);
  };

  const handleAnalysisError = (errorMessage: string) => {
    setError(errorMessage);
    resetResults();
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8">
      <div className="w-full max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">HAR API Reverse Engineer</h1>
          <p className="mt-2 text-gray-600">
            Upload a HAR file and describe the API you want to reverse-engineer.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-md mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input section */}
          <div className="w-full">
            <FileUploader 
              onUploadStart={() => setIsUploading(true)}
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
              onFileRemoved={handleFileRemoved}
              onUploadEnd={() => setIsUploading(false)}
            />

            {sessionId && (
              <div className="mt-6">
                <DescriptionInput
                  sessionId={sessionId}
                  onProcessingStart={handleAnalysisStart}
                  onProcessingSuccess={handleAnalysisSuccess}
                  onProcessingError={handleAnalysisError}
                  onProcessingEnd={() => setIsProcessing(false)}
                />
              </div>
            )}
          </div>

          {/* Output section */}
          <div className="w-full">
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
                    confidence={apiInfo.confidence || 0}
                  />
                )}
              </div>
            )}
            
            {!curlCommand && apiInfo && apiInfo.confidence === 0 && (
              <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-md">
                <h3 className="font-medium">No Relevant API Found</h3>
                <p className="mt-2">{apiInfo.description}</p>
                <p className="mt-2">{apiInfo.usage_notes}</p>
              </div>
            )}

            {!curlCommand && apiInfo && apiInfo.confidence > 0 && apiInfo.confidence < 0.3 && (
              <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded-md">
                <h3 className="font-medium">Low Confidence Match</h3>
                <p className="mt-2">The API found has a very low confidence score and may not match your requirements.</p>
                <p className="mt-2">Try refining your description or upload a different HAR file.</p>
              </div>
            )}
            
            {!curlCommand && sessionId && !apiInfo && (
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
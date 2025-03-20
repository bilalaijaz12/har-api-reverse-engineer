"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Search, Loader2 } from "lucide-react";

interface DescriptionInputProps {
  sessionId: string;
  onProcessingStart: () => void;
  onProcessingSuccess: (curlCommand: string | null, description: string, apiInfo: any) => void;
  onProcessingError: (message: string) => void;
  onProcessingEnd: () => void;
}

export function DescriptionInput({
  sessionId,
  onProcessingStart,
  onProcessingSuccess,
  onProcessingError,
  onProcessingEnd
}: DescriptionInputProps) {
  const [description, setDescription] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  
  const handleSubmit = async () => {
    if (!description.trim()) {
      onProcessingError("Please enter a description of the API you're looking for");
      return;
    }
    
    // Clear previous results before starting new analysis
    onProcessingStart();
    setIsProcessing(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          description: description,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze API requests');
      }
      
      const data = await response.json();
      onProcessingSuccess(data.curl_command, description, data.api_info);
    } catch (error) {
      onProcessingError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setIsProcessing(false);
      onProcessingEnd();
    }
  };

  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl">Describe the API</CardTitle>
        <CardDescription className="text-base">
          Tell us what API you're looking for in the HAR file
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Textarea
          placeholder="For example: 'Return the API that fetches the weather of San Francisco' or 'Find the login API endpoint'"
          className="min-h-[120px] text-base p-4 resize-none"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <div className="flex justify-between items-center mt-2 mb-4">
          <div className="text-sm text-gray-500">
            Be specific about what data you're looking for
          </div>
          <div className="text-sm text-gray-500">
            {description.length} characters
          </div>
        </div>
        
        <Button 
          className="w-full h-12 text-base"
          onClick={handleSubmit}
          disabled={isProcessing || !description.trim()}
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Search className="mr-2 h-5 w-5" />
              Find API
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
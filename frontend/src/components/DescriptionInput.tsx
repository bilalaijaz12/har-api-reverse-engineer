"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Search, Loader2 } from "lucide-react";

interface DescriptionInputProps {
  sessionId: string;
  onProcessingStart: () => void;
  onProcessingSuccess: (curlCommand: string, description: string, apiInfo: any) => void;
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
    
    setIsProcessing(true);
    onProcessingStart();
    
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
    <Card>
      <CardHeader>
        <CardTitle>Describe the API</CardTitle>
        <CardDescription>
          Tell us what API you're looking for in the HAR file
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Textarea
          placeholder="For example: 'Return the API that fetches the weather of San Francisco' or 'Find the login API endpoint'"
          className="min-h-[100px]"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <div className="text-right text-xs text-gray-500 mt-1">
          {description.length} characters
        </div>
        
        <Button 
          className="mt-4 w-full"
          onClick={handleSubmit}
          disabled={isProcessing || !description.trim()}
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Search className="mr-2 h-4 w-4" />
              Find API
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
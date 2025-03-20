"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, PlayCircle, FileDown, Copy, Check, Zap } from "lucide-react";
import { ResponseInterpreter } from "@/components/ResponseInterpreter";

interface ApiTesterProps {
  curlCommand: string;
  description: string;
}

export function ApiTester({ curlCommand, description }: ApiTesterProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("raw");
  const [isInterpreting, setIsInterpreting] = useState(false);
  const [interpretation, setInterpretation] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  
  const handleTest = async () => {
    setIsLoading(true);
    setError(null);
    setResponse(null);
    setInterpretation(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          curl_command: curlCommand,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to execute API request');
      }
      
      const data = await response.json();
      setResponse(data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInterpret = async () => {
    if (!response) return;
    
    setIsInterpreting(true);
    
    try {
      const interpretResponse = await fetch('http://localhost:8000/api/interpret', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_response: typeof response.response === 'string' ? response.response : JSON.stringify(response.response),
          api_description: description,
        }),
      });
      
      if (!interpretResponse.ok) {
        const errorData = await interpretResponse.json();
        throw new Error(errorData.detail || 'Failed to interpret API response');
      }
      
      const data = await interpretResponse.json();
      setInterpretation(data.interpretation);
      setActiveTab("interpreted");
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setIsInterpreting(false);
    }
  };

  const handleCopy = async () => {
    if (!response) return;
    
    try {
      await navigator.clipboard.writeText(
        typeof response.response === 'string' ? response.response : JSON.stringify(response.response, null, 2)
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  const generatePdf = () => {
    if (!interpretation) return;
    
    // Create a hidden link element
    const element = document.createElement('a');
    
    // Create a Blob with the interpretation text
    const blob = new Blob([interpretation], { type: 'text/plain' });
    
    // Create a URL for the Blob
    element.href = URL.createObjectURL(blob);
    
    // Set the filename
    element.download = 'api-interpretation.md';
    
    // Simulate a click on the link
    document.body.appendChild(element);
    element.click();
    
    // Clean up
    document.body.removeChild(element);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <PlayCircle className="mr-2 h-5 w-5" />
          Test API Endpoint
        </CardTitle>
        <CardDescription>
          Execute the API request and see the response
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button 
          className="w-full mb-4"
          onClick={handleTest}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Executing Request...
            </>
          ) : (
            <>
              <Zap className="mr-2 h-4 w-4" />
              Execute Request
            </>
          )}
        </Button>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-md mb-4">
            {error}
          </div>
        )}
        
        {response && (
          <div className="space-y-4">
            <div className="bg-gray-100 p-2 rounded-md text-sm">
              <span className="font-medium">Status Code:</span> 
              <span className={`ml-2 ${
                response.status_code >= 200 && response.status_code < 300
                  ? 'text-green-600'
                  : response.status_code >= 400
                  ? 'text-red-600'
                  : 'text-yellow-600'
              }`}>
                {response.status_code}
              </span>
            </div>
            
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="text-xs"
                onClick={handleCopy}
              >
                {copied ? <Check className="h-3 w-3 mr-1" /> : <Copy className="h-3 w-3 mr-1" />}
                {copied ? 'Copied' : 'Copy Response'}
              </Button>
              
              {response && !interpretation && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-xs"
                  onClick={handleInterpret}
                  disabled={isInterpreting}
                >
                  {isInterpreting ? (
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  ) : (
                    <Zap className="h-3 w-3 mr-1" />
                  )}
                  {isInterpreting ? 'Interpreting...' : 'Interpret Response'}
                </Button>
              )}
              
              {interpretation && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-xs"
                  onClick={generatePdf}
                >
                  <FileDown className="h-3 w-3 mr-1" />
                  Download Interpretation
                </Button>
              )}
            </div>
            
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="raw">Raw Response</TabsTrigger>
                <TabsTrigger value="interpreted" disabled={!interpretation}>
                  Interpreted
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="raw" className="border rounded-md p-4 mt-2">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-sm max-h-96 overflow-y-auto">
                  <code>{typeof response.response === 'string'
                    ? response.response
                    : JSON.stringify(response.response, null, 2)}</code>
                </pre>
              </TabsContent>
              
              <TabsContent value="interpreted" className="border rounded-md p-4 mt-2">
                {interpretation && (
                  <ResponseInterpreter interpretation={interpretation} />
                )}
              </TabsContent>
            </Tabs>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
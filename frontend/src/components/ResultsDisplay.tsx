"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Copy, Check, Terminal, Code, PlayCircle } from "lucide-react";
import { ApiTester } from "@/components/ApiTester";

interface ResultsDisplayProps {
  curlCommand: string;
  description?: string;
}

export function ResultsDisplay({ curlCommand, description = "" }: ResultsDisplayProps) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState("curl");
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(curlCommand);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Terminal className="mr-2 h-5 w-5" />
            Generated Commands
          </CardTitle>
          <CardDescription>
            Use these commands to make the API request
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="curl">curl</TabsTrigger>
              <TabsTrigger value="python">Python</TabsTrigger>
              <TabsTrigger value="javascript">JavaScript</TabsTrigger>
            </TabsList>
            
            <TabsContent value="curl" className="mt-4">
              <div className="relative">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
                  <code>{curlCommand}</code>
                </pre>
                
                <Button
                  variant="outline" 
                  size="sm"
                  className="absolute top-2 right-2 h-8 bg-gray-800 hover:bg-gray-700 text-gray-100 border-gray-700"
                  onClick={handleCopy}
                >
                  {copied ? (
                    <>
                      <Check className="mr-1 h-4 w-4" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="mr-1 h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>
            
            <TabsContent value="python" className="mt-4">
              <div className="relative">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
                  <code>{generatePythonCode(curlCommand)}</code>
                </pre>
                
                <Button
                  variant="outline" 
                  size="sm"
                  className="absolute top-2 right-2 h-8 bg-gray-800 hover:bg-gray-700 text-gray-100 border-gray-700"
                  onClick={() => {
                    navigator.clipboard.writeText(generatePythonCode(curlCommand));
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                >
                  {copied ? (
                    <>
                      <Check className="mr-1 h-4 w-4" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="mr-1 h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>
            
            <TabsContent value="javascript" className="mt-4">
              <div className="relative">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
                  <code>{generateJavaScriptCode(curlCommand)}</code>
                </pre>
                
                <Button
                  variant="outline" 
                  size="sm"
                  className="absolute top-2 right-2 h-8 bg-gray-800 hover:bg-gray-700 text-gray-100 border-gray-700"
                  onClick={() => {
                    navigator.clipboard.writeText(generateJavaScriptCode(curlCommand));
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                >
                  {copied ? (
                    <>
                      <Check className="mr-1 h-4 w-4" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="mr-1 h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>
          </Tabs>
          
          <div className="mt-4 text-sm text-gray-600">
            <p>This command was generated based on the API request found in your HAR file.</p>
            <p className="mt-2">You can use it directly or modify it as needed.</p>
          </div>
        </CardContent>
      </Card>
      
      <ApiTester curlCommand={curlCommand} description={description} />
    </div>
  );
}

function generatePythonCode(curlCommand: string): string {
  // Simple conversion from curl to Python requests
  const parts = curlCommand.split(' ');
  let url = '';
  let method = 'GET';
  const headers: Record<string, string> = {};
  let data = '';
  
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i].trim();
    
    if (part === '-X' && i + 1 < parts.length) {
      method = parts[i + 1];
      i++;
    } else if (part === '-H' && i + 1 < parts.length) {
      const header = parts[i + 1].replace(/['"]/g, '');
      const [key, value] = header.split(': ');
      if (key && value) {
        headers[key] = value;
      }
      i++;
    } else if (part === '-d' && i + 1 < parts.length) {
      data = parts[i + 1].replace(/['"]/g, '');
      i++;
    } else if (i === parts.length - 1 && part.startsWith('"') && part.endsWith('"')) {
      url = part.replace(/['"]/g, '');
    } else if (i === parts.length - 1) {
      url = part;
    }
  }
  
  const pythonCode = `import requests

url = "${url}"
headers = ${JSON.stringify(headers, null, 4)}

response = requests.${method.toLowerCase()}(url, headers=headers${data ? ', data=\'' + data + '\'' : ''})

print(response.status_code)
print(response.json())
`;

  return pythonCode;
}

function generateJavaScriptCode(curlCommand: string): string {
  // Simple conversion from curl to JavaScript fetch
  const parts = curlCommand.split(' ');
  let url = '';
  let method = 'GET';
  const headers: Record<string, string> = {};
  let data = '';
  
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i].trim();
    
    if (part === '-X' && i + 1 < parts.length) {
      method = parts[i + 1];
      i++;
    } else if (part === '-H' && i + 1 < parts.length) {
      const header = parts[i + 1].replace(/['"]/g, '');
      const [key, value] = header.split(': ');
      if (key && value) {
        headers[key] = value;
      }
      i++;
    } else if (part === '-d' && i + 1 < parts.length) {
      data = parts[i + 1].replace(/['"]/g, '');
      i++;
    } else if (i === parts.length - 1 && part.startsWith('"') && part.endsWith('"')) {
      url = part.replace(/['"]/g, '');
    } else if (i === parts.length - 1) {
      url = part;
    }
  }
  
  const jsCode = `// Using fetch
const url = "${url}";
const options = {
    method: "${method}",
    headers: ${JSON.stringify(headers, null, 4)}${data ? ',\n    body: \'' + data + '\'' : ''}
};

fetch(url, options)
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));

// Using async/await
async function fetchData() {
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

fetchData();
`;

  return jsCode;
}
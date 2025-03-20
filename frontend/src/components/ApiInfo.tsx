"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { InfoIcon, Plus, Minus, Lock, Key, AlertCircle } from "lucide-react";

interface Parameter {
  name: string;
  description: string;
  required: boolean;
  type: string;
}

interface Authentication {
  type: string;
  location: string;
  key: string;
}

interface ApiInfoProps {
  parameters: Parameter[];
  authentication: Authentication;
  description: string;
  usage_notes: string;
  response_format: string;
  confidence?: number;
}

export function ApiInfo({ 
  parameters, 
  authentication, 
  description, 
  usage_notes, 
  response_format,
  confidence = 0 
}: ApiInfoProps) {
  // Normalize confidence to be between 0-100%
  const normalizedConfidence = Math.min(Math.max(0, confidence), 1);
  
  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl flex items-center">
          <InfoIcon className="mr-3 h-6 w-6" />
          API Documentation
        </CardTitle>
        <CardDescription className="text-base">
          Detailed information about this API endpoint
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-lg font-medium mb-3">Description</h3>
            <p className="text-base text-gray-600">{description}</p>
          </div>
          
          {/* Confidence Score */}
          {authentication.type !== "unknown" && (
            <div>
              <h3 className="text-lg font-medium mb-3 flex items-center">
                <AlertCircle className="mr-2 h-5 w-5" />
                Match Confidence
              </h3>
              <div className="flex items-center mb-2">
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      normalizedConfidence > 0.7 ? 'bg-green-500' :
                      normalizedConfidence > 0.4 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${normalizedConfidence * 100}%` }}
                  />
                </div>
                <span className="ml-3 text-base font-medium">
                  {Math.round(normalizedConfidence * 100)}%
                </span>
              </div>
              
              {normalizedConfidence < 0.5 && normalizedConfidence > 0 && (
                <div className="mt-3 p-4 bg-yellow-50 text-yellow-800 rounded-md text-sm">
                  <AlertCircle className="inline-block mr-2 h-5 w-5" />
                  <span className="font-medium">Warning:</span> Low confidence match. This API may not fully match your requirements.
                </div>
              )}
            </div>
          )}
          
          {/* Authentication */}
          <div>
            <h3 className="text-lg font-medium mb-3 flex items-center">
              <Lock className="mr-2 h-5 w-5" />
              Authentication
            </h3>
            <div className="bg-gray-50 p-4 rounded-md text-base">
              <div className="flex items-center mb-2">
                <span className="font-medium w-24">Type:</span>
                <Badge variant={authentication.type === "none" ? "secondary" : "default"} className="text-sm px-3 py-1">
                  {authentication.type}
                </Badge>
              </div>
              {authentication.type !== "none" && authentication.type !== "unknown" && (
                <>
                  <div className="flex items-center mb-2">
                    <span className="font-medium w-24">Location:</span>
                    <span>{authentication.location}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="font-medium w-24">Key:</span>
                    <span>{authentication.key}</span>
                  </div>
                </>
              )}
            </div>
          </div>
          
          {/* Parameters */}
          <div>
            <h3 className="text-lg font-medium mb-3 flex items-center">
              <Key className="mr-2 h-5 w-5" />
              Parameters
            </h3>
            {parameters && parameters.length > 0 ? (
              <div className="border rounded-md overflow-hidden">
                <table className="w-full text-base">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">Name</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">Type</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">Required</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {parameters.map((param, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-4 py-3 font-medium">{param.name}</td>
                        <td className="px-4 py-3">
                          <Badge variant="outline">{param.type}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          {param.required ? 
                            <Badge variant="destructive">Required</Badge> : 
                            <Badge variant="secondary">Optional</Badge>}
                        </td>
                        <td className="px-4 py-3 text-gray-600">{param.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-base text-gray-500">No parameters detected</p>
            )}
          </div>
          
          {/* Usage Notes & Response Format */}
          <Collapsible className="w-full">
            <CollapsibleTrigger className="flex items-center justify-between w-full p-4 bg-gray-50 rounded-md text-base">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 mr-2" />
                <span className="font-medium">Additional Information</span>
              </div>
              <div className="text-gray-500">
                <Plus className="h-5 w-5 plus-icon" />
                <Minus className="h-5 w-5 minus-icon hidden" />
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-4 px-4 text-base space-y-4">
              <div>
                <h4 className="font-medium mb-2">Usage Notes</h4>
                <p className="text-gray-600">{usage_notes}</p>
              </div>
              <div>
                <h4 className="font-medium mb-2">Response Format</h4>
                <p className="text-gray-600">{response_format}</p>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </CardContent>
    </Card>
  );
}
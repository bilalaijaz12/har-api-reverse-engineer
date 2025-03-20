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
}

export function ApiInfo({ 
  parameters, 
  authentication, 
  description, 
  usage_notes, 
  response_format 
}: ApiInfoProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <InfoIcon className="mr-2 h-5 w-5" />
          API Documentation
        </CardTitle>
        <CardDescription>
          Detailed information about this API endpoint
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-md font-medium mb-2">Description</h3>
            <p className="text-sm text-gray-600">{description}</p>
          </div>
          
          {/* Authentication */}
          <div>
            <h3 className="text-md font-medium mb-2 flex items-center">
              <Lock className="mr-2 h-4 w-4" />
              Authentication
            </h3>
            <div className="bg-gray-50 p-3 rounded-md text-sm">
              <div className="flex items-center mb-1">
                <span className="font-medium w-20">Type:</span>
                <Badge variant={authentication.type === "none" ? "secondary" : "default"}>
                  {authentication.type}
                </Badge>
              </div>
              {authentication.type !== "none" && (
                <>
                  <div className="flex items-center mb-1">
                    <span className="font-medium w-20">Location:</span>
                    <span>{authentication.location}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="font-medium w-20">Key:</span>
                    <span>{authentication.key}</span>
                  </div>
                </>
              )}
            </div>
          </div>
          
          {/* Parameters */}
          <div>
            <h3 className="text-md font-medium mb-2 flex items-center">
              <Key className="mr-2 h-4 w-4" />
              Parameters
            </h3>
            {parameters && parameters.length > 0 ? (
              <div className="border rounded-md overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium text-gray-500">Name</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-500">Type</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-500">Required</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-500">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {parameters.map((param, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-4 py-2 font-medium">{param.name}</td>
                        <td className="px-4 py-2">
                          <Badge variant="outline">{param.type}</Badge>
                        </td>
                        <td className="px-4 py-2">
                          {param.required ? 
                            <Badge variant="destructive">Required</Badge> : 
                            <Badge variant="secondary">Optional</Badge>}
                        </td>
                        <td className="px-4 py-2 text-gray-600">{param.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-500">No parameters detected</p>
            )}
          </div>
          
          {/* Usage Notes & Response Format */}
          <Collapsible className="w-full">
            <CollapsibleTrigger className="flex items-center justify-between w-full p-3 bg-gray-50 rounded-md text-sm">
              <div className="flex items-center">
                <AlertCircle className="h-4 w-4 mr-2" />
                <span className="font-medium">Additional Information</span>
              </div>
              <div className="text-gray-500">
                <Plus className="h-4 w-4 plus-icon" />
                <Minus className="h-4 w-4 minus-icon hidden" />
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-2 px-3 text-sm space-y-3">
              <div>
                <h4 className="font-medium mb-1">Usage Notes</h4>
                <p className="text-gray-600">{usage_notes}</p>
              </div>
              <div>
                <h4 className="font-medium mb-1">Response Format</h4>
                <p className="text-gray-600">{response_format}</p>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </CardContent>
    </Card>
  );
}
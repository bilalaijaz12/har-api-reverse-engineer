"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

interface ResponseInterpreterProps {
  interpretation: string;
}

export function ResponseInterpreter({ interpretation }: ResponseInterpreterProps) {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown>{interpretation}</ReactMarkdown>
    </div>
  );
}
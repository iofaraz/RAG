"use client";

import { useState } from "react";
import { askQuestion } from "@/services/api";
import { detectFocusNutrient } from "@/lib/utils";
import EmptyState from "./EmptyState";
import QuestionInput from "./QuestionInput";
import ExampleQuestions from "./ExampleQuestions";
import UserQuestion from "./UserQuestion";
import LoadingState from "./LoadingState";
import ErrorState from "./ErrorState";
import AIResponse from "./AIResponse";
import RetrievedSources from "@/components/results/RetrievedSources";

export default function ChatInterface() {
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [submitted, setSubmitted] = useState("");
  const [result, setResult] = useState(null);

  const isLoading = status === "loading";

  async function ask(text) {
    const question = text.trim();
    if (!question || isLoading) return;

    setSubmitted(question);
    setDraft("");
    setResult(null);
    setStatus("loading");

    try {
      setResult(await askQuestion(question));
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6 sm:py-12">
      {status === "idle" && <EmptyState />}

      <QuestionInput
        value={draft}
        onChange={setDraft}
        onSubmit={() => ask(draft)}
        disabled={isLoading}
      />

      {status === "idle" && <ExampleQuestions onSelect={ask} disabled={isLoading} />}

      {status !== "idle" && (
        <div className="mt-10 space-y-8">
          <UserQuestion question={submitted} />

          {isLoading && <LoadingState />}
          {status === "error" && <ErrorState onRetry={() => ask(submitted)} />}

          {status === "success" && result && (
            <>
              <p role="status" className="sr-only">
                Answer ready. {result.sources.length} sources retrieved.
              </p>
              <AIResponse answer={result.answer} sourceCount={result.sources.length} />
              <RetrievedSources
                sources={result.sources}
                focusNutrient={detectFocusNutrient(submitted)}
              />
              {/* Future: <KnowledgeConnections graph={result.graph_context} /> */}
            </>
          )}
        </div>
      )}
    </main>
  );
}

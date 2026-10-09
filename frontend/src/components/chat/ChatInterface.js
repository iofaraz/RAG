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
  const [conversation, setConversation] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  const isLoading = status === "loading";

  async function ask(text) {
    const question = text.trim();
    if (!question || isLoading) return;

    setSubmitted(question);
    setDraft("");
    setStatus("loading");
    setErrorMessage("");

    try {
      const result = await askQuestion(question);
      setConversation((prev) => [
        ...prev,
        {
          question,
          answer: result.answer,
          sources: result.sources,
          warnings: result.warnings,
        },
      ]);
      setStatus("success");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Please try again shortly.");
      setStatus("error");
    }
  }

  const showConversation = status !== "idle";

  return (
    <main id="main-content" className="mx-auto w-full max-w-5xl flex-1 px-4 pb-14 pt-8 sm:px-7 sm:pb-20 sm:pt-12 lg:px-10">
      {status === "idle" && <EmptyState />}
      {status !== "idle" && <h1 className="sr-only">Nutrix nutrition assistant</h1>}

      {showConversation && (
        <div className="space-y-8">
          {conversation.map((entry, index) => (
            <div key={`${entry.question}-${index}`} className="space-y-5 rounded-[1.75rem] border border-line/80 bg-white/55 p-4 sm:p-7">
              <UserQuestion question={entry.question} />
              <AIResponse answer={entry.answer} sourceCount={entry.sources.length} />
              {entry.warnings?.length > 0 && (
                <div role="status" className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950">
                  <p className="font-semibold">A note about this response</p>
                  <ul className="mt-1 list-inside list-disc">
                    {entry.warnings.map((warning, warningIndex) => (
                      <li key={`${warning}-${warningIndex}`}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
              <RetrievedSources
                sources={entry.sources}
                focusNutrient={detectFocusNutrient(entry.question)}
              />
            </div>
          ))}

          {isLoading && (
            <div className="space-y-4">
              <UserQuestion question={submitted} />
              <LoadingState />
            </div>
          )}

          {status === "error" && (
            <div className="space-y-4">
              <UserQuestion question={submitted} />
              <ErrorState message={errorMessage} onRetry={() => ask(submitted)} />
            </div>
          )}
        </div>
      )}

      <div className="mt-8">
        <QuestionInput
          value={draft}
          onChange={setDraft}
          onSubmit={() => ask(draft)}
          disabled={isLoading}
        />
      </div>

      {status === "idle" && <ExampleQuestions onSelect={ask} disabled={isLoading} />}
      <footer className="mt-12 border-t border-line/80 pt-5 text-center text-xs leading-5 text-muted">
        Nutrition information for general knowledge. Retrieved records may not support every part of an AI-generated explanation.
      </footer>
    </main>
  );
}

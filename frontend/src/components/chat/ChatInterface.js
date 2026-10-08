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
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6 sm:px-6 sm:py-10">
      {status === "idle" && <EmptyState />}

      {showConversation && (
        <div className="space-y-6">
          {conversation.map((entry, index) => (
            <div key={`${entry.question}-${index}`} className="space-y-5">
              <UserQuestion question={entry.question} />
              <AIResponse answer={entry.answer} sourceCount={entry.sources.length} />
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

      <div className={status === "idle" ? "mt-6" : "mt-8"}>
        <QuestionInput
          value={draft}
          onChange={setDraft}
          onSubmit={() => ask(draft)}
          disabled={isLoading}
        />
      </div>

      {status === "idle" && <ExampleQuestions onSelect={ask} disabled={isLoading} />}
    </main>
  );
}

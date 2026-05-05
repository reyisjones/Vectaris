import { useQuery } from "@tanstack/react-query";
import React from "react";
import { LLMRuntimeCard } from "../components/LLMRuntimeCard";
import { ErrorCard, LoadingCard } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { getLLMRuntime } from "../services/api";

export const LLMRuntimePage: React.FC = () => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["llm-runtime"],
    queryFn: getLLMRuntime,
    refetchInterval: 20_000,
  });

  return (
    <>
      <PageHeader
        title="LLM Runtime"
        subtitle="Local inference daemon (Ollama) — status and installed models"
      />
      {isError && <ErrorCard message="Failed to query LLM runtime." />}
      {isLoading || !data ? <LoadingCard rows={4} /> : <LLMRuntimeCard report={data} />}
    </>
  );
};

import { useQuery } from "@tanstack/react-query";
import React from "react";
import { AgentHealthTable } from "../components/AgentHealthTable";
import { ErrorCard, LoadingCard } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { getAgents } from "../services/api";

export const AgentsPage: React.FC = () => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["agents"],
    queryFn: getAgents,
    refetchInterval: 30_000,
  });

  return (
    <>
      <PageHeader
        title="Agents"
        subtitle="Health, throughput, and reliability across registered AI agents"
      />
      {isError && <ErrorCard message="Failed to fetch agent registry." />}
      {isLoading ? <LoadingCard rows={5} /> : <AgentHealthTable agents={data ?? []} />}
    </>
  );
};

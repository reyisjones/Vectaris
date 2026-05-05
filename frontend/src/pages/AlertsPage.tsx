import { useQuery } from "@tanstack/react-query";
import React from "react";
import { AlertsList } from "../components/AlertsList";
import { ErrorCard, LoadingCard } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { getAlerts } from "../services/api";

export const AlertsPage: React.FC = () => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    refetchInterval: 15_000,
  });

  return (
    <>
      <PageHeader title="Alerts" subtitle="Live alert evaluation across the platform" />
      {isError && <ErrorCard message="Failed to load alerts." />}
      {isLoading ? <LoadingCard rows={3} /> : <AlertsList alerts={data ?? []} />}
    </>
  );
};

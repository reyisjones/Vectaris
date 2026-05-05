import React from "react";

interface Props {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<Props> = ({ title, subtitle, actions }) => (
  <div className="page-header">
    <div>
      <h2>{title}</h2>
      {subtitle && <div className="subtitle">{subtitle}</div>}
    </div>
    {actions && <div>{actions}</div>}
  </div>
);

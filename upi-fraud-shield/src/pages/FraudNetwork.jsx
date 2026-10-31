import React, { useMemo, useState } from "react";
import { Network, RefreshCw, Search, Share2 } from "lucide-react";
import EmptyState from "../components/EmptyState";
import { DataLabel, DataNotice, ErrorPanel, MetricCard, PageHeading } from "../components/PagePrimitives";
import { apiService } from "../services/apiService";
import { formatCurrency, formatDateTime } from "../utils/formatters";
import { useApiMode } from "../hooks/useApiMode";

const riskStyles = {
  LOW: { fill: "#d9f3ef", stroke: "#00685f", text: "#0b514a" },
  MEDIUM: { fill: "#fff2cc", stroke: "#c27a00", text: "#754900" },
  HIGH: { fill: "#fee2e2", stroke: "#c53030", text: "#8c2020" }
};

function NetworkGraph({ network }) {
  const nodes = network.nodes || [];
  const edges = network.edges || [];
  if (!nodes.length) {
    return <EmptyState icon={Network} title="No network records" description="No account nodes were returned for this search." />;
  }

  const centerIndex = Math.max(0, nodes.findIndex((node) => node.id === network.center));
  const positions = new Map(
    nodes.map((node, index) => {
      if (index === centerIndex) return [node.id, { x: 400, y: 180 }];
      const peers = Math.max(nodes.length - 1, 1);
      const peerIndex = index < centerIndex ? index : index - 1;
      const angle = (2 * Math.PI * peerIndex) / peers - Math.PI / 2;
      return [node.id, { x: 400 + Math.cos(angle) * 260, y: 180 + Math.sin(angle) * 115 }];
    })
  );

  return (
    <div className="overflow-x-auto">
      <svg viewBox="0 0 800 360" role="img" aria-label={`Stored account network centered on ${network.center}`} className="mx-auto min-w-[640px]">
        <defs>
          <marker id="network-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 z" fill="#8091a6" />
          </marker>
        </defs>
        {edges.map((edge) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) return null;
          return (
            <line
              key={edge.id}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke="#9aabc0"
              strokeWidth="1.5"
              markerEnd="url(#network-arrow)"
            />
          );
        })}
        {nodes.map((node, index) => {
          const position = positions.get(node.id);
          const colors = riskStyles[node.risk_level] || riskStyles.LOW;
          const isCenter = index === centerIndex;
          return (
            <g key={node.id} transform={`translate(${position.x} ${position.y})`}>
              <circle r={isCenter ? 30 : 23} fill={colors.fill} stroke={colors.stroke} strokeWidth={isCenter ? 3 : 2} />
              <text y="4" textAnchor="middle" fill={colors.text} fontSize="10" fontWeight="700">
                {(node.id || "").slice(0, 9)}
              </text>
              <text y={isCenter ? 46 : 38} textAnchor="middle" fill="#526176" fontSize="9">
                {(node.label || node.id || "").slice(0, 22)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default function FraudNetwork() {
  const { mode } = useApiMode();
  const [accountId, setAccountId] = useState("");
  const [depth, setDepth] = useState("2");
  const [network, setNetwork] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const patterns = useMemo(() => network?.patterns || [], [network]);

  const loadNetwork = async (event) => {
    event?.preventDefault();
    if (!accountId.trim()) {
      setError("Enter an account ID to search stored graph relationships.");
      setNetwork(null);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await apiService.getAccountNetwork(accountId.trim(), Number(depth), mode);
      if (!Array.isArray(response.data?.nodes) || !Array.isArray(response.data?.edges)) {
        throw new Error("The backend returned an invalid network response.");
      }
      setNetwork(response.data);
      setLastUpdated(new Date());
    } catch (requestError) {
      setNetwork(null);
      setError(requestError.message || "Could not load stored network relationships.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeading
        eyebrow="Entity relationships"
        title="Fraud Network"
        description="Explore account relationships and graph patterns derived from local prototype records, which may include synthetic seed data. Connections are indicators, not proof of wrongdoing."
        actions={<DataLabel />}
      />

      <DataNotice>
        The graph is built from stored prototype records only. It is not a live UPI network and does not establish that any person or account committed fraud.
      </DataNotice>

      <section className="surface-card p-4 sm:p-5">
        <form onSubmit={loadNetwork} className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_180px_auto]">
          <label className="min-w-0">
            <span className="mb-1.5 block text-xs font-medium text-slate-600">Account ID</span>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                className="form-control pl-9"
                value={accountId}
                onChange={(event) => setAccountId(event.target.value)}
                placeholder="e.g. ACC_300"
                autoComplete="off"
              />
            </div>
          </label>
          <label>
            <span className="mb-1.5 block text-xs font-medium text-slate-600">Relationship depth</span>
            <select className="form-control" value={depth} onChange={(event) => setDepth(event.target.value)}>
              <option value="1">1 hop</option>
              <option value="2">2 hops</option>
              <option value="3">3 hops</option>
            </select>
          </label>
          <div className="flex items-end">
            <button type="submit" className="btn-primary w-full sm:w-auto" disabled={loading}>
              {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Network className="h-4 w-4" />}
              Analyze stored graph
            </button>
          </div>
        </form>
        {error && <p role="alert" className="mt-3 text-xs text-rose-700">{error}</p>}
      </section>

      {loading && <section className="surface-card p-6 text-center text-sm text-slate-500">Loading account relationships…</section>}
      {!loading && error && (
        <ErrorPanel title={mode === "MOCK" ? "Local API mode required" : "Network data unavailable"} error={error} onRetry={() => loadNetwork()} />
      )}
      {!loading && !error && network && (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <MetricCard label="Accounts in result" value={network.nodes.length.toLocaleString("en-IN")} icon={Network} />
            <MetricCard label="Stored relationships" value={network.edges.length.toLocaleString("en-IN")} icon={Share2} tone="slate" />
            <MetricCard label="Heuristic patterns" value={patterns.length.toLocaleString("en-IN")} icon={Search} tone={patterns.length ? "amber" : "green"} />
          </div>

          <section className="surface-card p-4 sm:p-6">
            <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-ink">Stored relationship map</h3>
                <p className="mt-1 text-xs text-slate-500">Center account: <span className="font-mono">{network.center}</span></p>
              </div>
              <p className="text-[10px] text-slate-500">Updated {lastUpdated?.toLocaleTimeString() || "not available"}</p>
            </div>
            <NetworkGraph network={network} />
          </section>

          <section className="surface-card p-4 sm:p-6">
            <h3 className="text-sm font-semibold text-ink">Detected graph patterns</h3>
            {patterns.length ? (
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {patterns.map((pattern, index) => (
                  <article key={`${pattern.pattern}-${index}`} className="rounded-md border border-outline-soft bg-canvas p-3">
                    <p className="text-xs font-semibold text-ink">{pattern.pattern.replaceAll("_", " ")}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-600">{pattern.explanation}</p>
                    {pattern.accounts?.length > 0 && <p className="mt-2 break-all font-mono text-[10px] text-slate-500">{pattern.accounts.join(" · ")}</p>}
                  </article>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-xs text-slate-500">No graph pattern was returned for this account and depth.</p>
            )}
          </section>

          <section className="surface-card overflow-hidden">
            <div className="border-b border-outline-soft px-4 py-3 sm:px-5">
              <h3 className="text-sm font-semibold text-ink">Stored relationship records</h3>
            </div>
            {network.edges.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[680px] text-left text-xs">
                  <thead className="bg-surface-container text-[10px] uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Flow</th>
                      <th className="px-4 py-3 font-semibold">Amount</th>
                      <th className="px-4 py-3 font-semibold">Transaction record</th>
                      <th className="px-4 py-3 font-semibold">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {network.edges.map((edge) => (
                      <tr key={edge.id} className="hover:bg-canvas">
                        <td className="px-4 py-3 font-mono">{edge.source} → {edge.target}</td>
                        <td className="px-4 py-3 font-medium">{formatCurrency(edge.amount)}</td>
                        <td className="px-4 py-3 font-mono text-slate-500">{edge.transaction_id || "Not recorded"}</td>
                        <td className="px-4 py-3 text-slate-600">{edge.timestamp ? formatDateTime(edge.timestamp) : "Not recorded"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-5 text-sm text-slate-500">No stored relationships were returned.</div>
            )}
          </section>
          {network.disclaimer && <p className="text-[11px] leading-5 text-slate-500">{network.disclaimer}</p>}
        </>
      )}
    </div>
  );
}

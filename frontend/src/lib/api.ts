const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface StatsResponse {
  total: number;
  by_analyzer: Record<string, number>;
  by_band: Record<string, number>;
  by_status: Record<string, number>;
}

export interface FindingResponse {
  id: string;
  analyzer: string;
  entity_type: string;
  entity_id: string;
  finding_type: string;
  score: number | null;
  band: string | null;
  status: string;
  summary: string;
  explanation: string | null;
  payload_json: Record<string, any> | null;
  created_at: string;
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/stats`, { next: { revalidate: 5 } });
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchTopFindings(limit = 10): Promise<FindingResponse[]> {
  const res = await fetch(`${API_BASE}/findings/top?limit=${limit}`, { next: { revalidate: 5 } });
  if (!res.ok) throw new Error('Failed to fetch top findings');
  return res.json();
}

export async function fetchFindings(limit = 50, offset = 0, analyzer?: string, band?: string, status?: string): Promise<FindingResponse[]> {
  const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
  if (analyzer) params.append('analyzer', analyzer);
  if (band) params.append('band', band);
  if (status) params.append('status', status);
  
  const res = await fetch(`${API_BASE}/findings?${params.toString()}`, { next: { revalidate: 5 } });
  if (!res.ok) throw new Error('Failed to fetch findings');
  return res.json();
}

export async function fetchFindingDetail(id: string): Promise<FindingResponse> {
  const res = await fetch(`${API_BASE}/findings/${id}`, { next: { revalidate: 5 } });
  if (!res.ok) throw new Error('Failed to fetch finding detail');
  return res.json();
}

export interface TopAccount {
  account_id: string;
  total_score: number;
  finding_count: number;
  critical_count: number;
}

export interface GraphNode {
  id: string;
  score: number;
  risk_band: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  amount: number;
  transaction_id: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function fetchTopAccounts(limit = 50): Promise<TopAccount[]> {
  const res = await fetch(`${API_BASE}/accounts/top?limit=${limit}`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error('Failed to fetch top accounts');
  const data = await res.json();
  return data.map((d: any) => ({
    account_id: d.account_id,
    total_score: d.total_score,
    finding_count: d.finding_count || d.critical_flags || 1, // Fallback if backend is old
    critical_count: d.critical_count || d.critical_flags || 0
  }));
}

export async function fetchGraphData(limit = 500): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/graph?limit=${limit}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Failed to fetch graph data');
  return res.json();
}

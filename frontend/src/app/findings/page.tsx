import { fetchFindings } from '@/lib/api';
import { FilterBar } from '@/components/FilterBar';
import { FindingsTable } from '@/components/FindingsTable';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { Search } from 'lucide-react';

export const revalidate = 10;
export const dynamic = 'force-dynamic';

export default async function FindingsPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  try {
    const params = await searchParams;
    const analyzer = typeof params.analyzer === 'string' ? params.analyzer : undefined;
    const band = typeof params.band === 'string' ? params.band : undefined;
    const status = typeof params.status === 'string' ? params.status : undefined;
    const offset = typeof params.offset === 'string' ? parseInt(params.offset, 10) : 0;
    
    // Convert 'all' to undefined for the API call
    const apiAnalyzer = analyzer === 'all' ? undefined : analyzer;

    const findings = await fetchFindings(50, offset, apiAnalyzer, band, status);

    return (
      <div className="flex flex-col max-w-7xl mx-auto h-full">
        <div className="flex flex-col gap-2 mb-6">
          <h1 className="text-xl font-semibold text-text">Review Findings</h1>
          <p className="text-sm text-text-muted">Prioritize, investigate, and resolve compliance flags.</p>
        </div>

        <FilterBar />

        {findings.length === 0 ? (
          <EmptyState 
            icon={Search}
            title="No findings match"
            hint="Try adjusting your filters or running the analyzers."
          />
        ) : (
          <>
            <FindingsTable findings={findings} />
            {findings.length >= 50 && (
              <div className="mt-6 flex justify-center">
                <a 
                  href={`/findings?offset=${offset + 50}${analyzer ? `&analyzer=${analyzer}` : ''}${band ? `&band=${band}` : ''}${status ? `&status=${status}` : ''}`}
                  className="px-4 py-2 bg-surface border border-border text-text font-medium text-sm rounded-[var(--r-control)] hover:bg-surface-sunken transition-colors"
                >
                  Load More
                </a>
              </div>
            )}
          </>
        )}
      </div>
    );
  } catch (error) {
    return (
      <div className="max-w-7xl mx-auto py-12">
        <ErrorState message="Failed to fetch findings. The backend may be offline." />
      </div>
    );
  }
}

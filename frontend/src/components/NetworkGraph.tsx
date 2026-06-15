'use client';
import { useEffect, useRef, useState, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { BAND, RiskBand } from '@/lib/severity';
import { GraphData, GraphNode, GraphEdge } from '@/lib/api';

// Dynamically import ForceGraph2D since it uses canvas/window
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex flex-col items-center justify-center text-text-muted bg-surface-sunken">
      <div className="animate-pulse flex items-center gap-2">
        <div className="w-2 h-2 bg-brand rounded-full"></div>
        <div className="w-2 h-2 bg-brand rounded-full animation-delay-200"></div>
        <div className="w-2 h-2 bg-brand rounded-full animation-delay-400"></div>
      </div>
      <p className="mt-4 text-sm font-medium">Initializing force layout...</p>
    </div>
  )
});

interface Props {
  data: GraphData;
}

export default function NetworkGraph({ data }: Props) {
  const fgRef = useRef<any>(null);
  const [containerDimensions, setContainerDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverNode, setHoverNode] = useState<string | null>(null);

  useEffect(() => {
    if (containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      setContainerDimensions({ width: clientWidth, height: clientHeight });
    }
    
    const handleResize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setContainerDimensions({ width: clientWidth, height: clientHeight });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Process data for graph
  const gData = useMemo(() => {
    return {
      nodes: data.nodes.map(n => {
        const bandKey = (n.risk_band?.toLowerCase() || 'medium') as RiskBand;
        const colorData = BAND[bandKey] || BAND.medium;
        return {
          ...n,
          id: n.id,
          val: Math.max(3, n.score / 15), // Node size
          color: colorData.solid,
          name: n.id
        };
      }),
      links: data.edges.map(e => ({
        ...e,
        source: e.source,
        target: e.target,
        value: Math.max(1, Math.log10(e.amount)) // Edge width
      }))
    };
  }, [data]);

  return (
    <div className="flex flex-col gap-4">
      <div ref={containerRef} className="w-full h-[600px] bg-canvas border border-border shadow-sm rounded-[var(--r-card)] overflow-hidden relative">
        {typeof window !== 'undefined' && (
          <ForceGraph2D
            ref={fgRef}
            width={containerDimensions.width}
            height={containerDimensions.height}
            graphData={gData}
            nodeLabel={(node: any) => `${node.id}\nScore: ${node.score?.toFixed(1)}\nBand: ${node.risk_band?.toUpperCase()}`}
            nodeColor={(node: any) => {
              if (hoverNode) {
                // If there's a hover node, only color it and its neighbors
                const isHovered = node.id === hoverNode;
                const isNeighbor = gData.links.some((l: any) => 
                  (l.source.id === hoverNode && l.target.id === node.id) || 
                  (l.target.id === hoverNode && l.source.id === node.id)
                );
                return isHovered || isNeighbor ? node.color : 'rgba(150, 160, 180, 0.2)'; // text-muted very dim
              }
              return node.color;
            }}
            nodeRelSize={5}
            linkColor={(link: any) => {
              if (hoverNode) {
                const isConnected = link.source.id === hoverNode || link.target.id === hoverNode;
                return isConnected ? 'rgba(39, 64, 107, 0.6)' : 'rgba(150, 160, 180, 0.1)'; // brand color vs dim
              }
              return 'var(--border)';
            }}
            linkWidth={(link: any) => (hoverNode && (link.source.id === hoverNode || link.target.id === hoverNode) ? link.value * 2 : link.value)}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            onNodeHover={(node: any) => setHoverNode(node ? node.id : null)}
            onNodeClick={(node: any) => {
              window.location.href = `/findings?analyzer=all&status=open`;
            }}
            backgroundColor="#F7F9FC" // explicitly hardcode canvas color for the canvas element
            d3AlphaDecay={0.05}
            d3VelocityDecay={0.1}
          />
        )}
      </div>
      
      <div className="flex items-center justify-center gap-6 px-4 py-3 bg-surface border border-border rounded-[var(--r-control)] text-sm">
        <span className="font-semibold text-text-muted mr-2">Risk Legend:</span>
        {(Object.keys(BAND) as RiskBand[]).map((key) => {
          const b = BAND[key];
          return (
            <div key={key} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: b.solid }}></span>
              <span className="capitalize text-text">{b.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

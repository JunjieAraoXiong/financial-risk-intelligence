# FE-EKG Component Library

React components for the FE-EKG visualization frontend.

---

## 1. GraphView Component (Cytoscape.js)

**File:** `src/components/GraphView/index.tsx`

```typescript
"use client";

import { useEffect, useRef } from "react";
import cytoscape, { Core, NodeSingular } from "cytoscape";
import { COLORS, LAYOUTS } from "@/lib/constants";
import { useGraphStore } from "@/stores/graphStore";

interface GraphViewProps {
  nodes: Array<{ id: string; label: string; type: string; group: string }>;
  edges: Array<{ source: string; target: string; type: string; strength: number }>;
  onNodeClick?: (nodeId: string) => void;
  onNodeHover?: (nodeId: string | null) => void;
}

export function GraphView({ nodes, edges, onNodeClick, onNodeHover }: GraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const { setSelectedNode, setZoom, setPan } = useGraphStore();

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    // Initialize Cytoscape
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: [
        // Nodes
        ...nodes.map((n) => ({
          data: { id: n.id, label: n.label, type: n.type, group: n.group },
        })),
        // Edges
        ...edges.map((e) => ({
          data: {
            id: `${e.source}-${e.target}`,
            source: e.source,
            target: e.target,
            type: e.type,
            strength: e.strength,
          },
        })),
      ],
      style: [
        {
          selector: "node",
          style: {
            "background-color": (ele) => {
              const group = ele.data("group");
              const type = ele.data("type");
              if (group === "entity") {
                return type === "bank" ? "#3b82f6" :
                       type === "regulator" ? "#8b5cf6" :
                       type === "investment_bank" ? "#ec4899" : "#64748b";
              }
              return "#f59e0b"; // events
            },
            label: (ele) => (ele.data("group") === "entity" ? ele.data("label") : ""),
            width: (ele) => (ele.data("group") === "entity" ? 30 : 12),
            height: (ele) => (ele.data("group") === "entity" ? 30 : 12),
            "font-size": 11,
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 5,
            color: "#fff",
            "text-outline-width": 2,
            "text-outline-color": "#1e293b",
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 3,
            "border-color": "#fbbf24",
          },
        },
        {
          selector: "edge",
          style: {
            width: (ele) => ele.data("strength") * 2,
            "line-color": (ele) => COLORS[ele.data("type") as keyof typeof COLORS] || "#64748b",
            "target-arrow-color": (ele) => COLORS[ele.data("type") as keyof typeof COLORS] || "#64748b",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            opacity: 0.6,
          },
        },
      ],
      layout: LAYOUTS.cose,
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.2,
    });

    const cy = cyRef.current;

    // Event handlers
    cy.on("tap", "node", (evt) => {
      const nodeId = evt.target.id();
      setSelectedNode(nodeId);
      onNodeClick?.(nodeId);
    });

    cy.on("mouseover", "node", (evt) => {
      const nodeId = evt.target.id();
      onNodeHover?.(nodeId);
    });

    cy.on("mouseout", "node", () => {
      onNodeHover?.(null);
    });

    cy.on("zoom", () => {
      setZoom(cy.zoom());
    });

    cy.on("pan", () => {
      const pan = cy.pan();
      setPan(pan);
    });

    return () => {
      cy?.destroy();
    };
  }, [nodes, edges]);

  return <div ref={containerRef} className="w-full h-full" />;
}
```

---

## 2. FilterPanel Component

**File:** `src/components/FilterPanel/index.tsx`

```typescript
"use client";

import { useState } from "react";
import { DateRangeFilter } from "./DateRangeFilter";
import { EventTypeFilter } from "./EventTypeFilter";
import { SearchFilter } from "./SearchFilter";

interface FilterPanelProps {
  onFilterChange: (filters: {
    startDate?: string;
    endDate?: string;
    types?: string[];
    search?: string;
  }) => void;
}

export function FilterPanel({ onFilterChange }: FilterPanelProps) {
  const [filters, setFilters] = useState({
    startDate: "2008-09-01",
    endDate: "2008-09-30",
    types: [] as string[],
    search: "",
  });

  const updateFilter = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Filters</h2>

      <SearchFilter
        value={filters.search}
        onChange={(search) => updateFilter("search", search)}
      />

      <DateRangeFilter
        startDate={filters.startDate}
        endDate={filters.endDate}
        onStartChange={(date) => updateFilter("startDate", date)}
        onEndChange={(date) => updateFilter("endDate", date)}
      />

      <EventTypeFilter
        selected={filters.types}
        onChange={(types) => updateFilter("types", types)}
      />
    </div>
  );
}
```

**File:** `src/components/FilterPanel/DateRangeFilter.tsx`

```typescript
interface DateRangeFilterProps {
  startDate: string;
  endDate: string;
  onStartChange: (date: string) => void;
  onEndChange: (date: string) => void;
}

export function DateRangeFilter({
  startDate,
  endDate,
  onStartChange,
  onEndChange,
}: DateRangeFilterProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Time Range
      </label>
      <div className="space-y-2">
        <input
          type="date"
          value={startDate}
          onChange={(e) => onStartChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        />
        <input
          type="date"
          value={endDate}
          onChange={(e) => onEndChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        />
      </div>
    </div>
  );
}
```

---

## 3. EventCard Component

**File:** `src/components/EventCard/index.tsx`

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchEventDetails } from "@/lib/api/events";
import { EventHeader } from "./EventHeader";
import { EventMeta } from "./EventMeta";
import { RelatedEvents } from "./RelatedEvents";

interface EventCardProps {
  eventId: string;
  onClose: () => void;
}

export function EventCard({ eventId, onClose }: EventCardProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["event", eventId],
    queryFn: () => fetchEventDetails(eventId),
  });

  if (isLoading) {
    return (
      <div className="fixed right-4 top-20 w-96 bg-white rounded-lg shadow-xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="fixed right-4 top-20 w-96 bg-white rounded-lg shadow-xl overflow-hidden">
      <EventHeader event={data} onClose={onClose} />
      <div className="p-6 space-y-4">
        <EventMeta event={data} />
        <RelatedEvents eventId={eventId} />
      </div>
    </div>
  );
}
```

---

## 4. Timeline Component

**File:** `src/components/Timeline/index.tsx`

```typescript
"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

interface TimelineProps {
  events: Array<{ date: string; label: string; type: string }>;
  onDateRangeChange: (start: string, end: string) => void;
}

export function Timeline({ events, onDateRangeChange }: TimelineProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || events.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 100;
    const margin = { top: 20, right: 20, bottom: 30, left: 20 };

    // Parse dates
    const dates = events.map((e) => new Date(e.date));
    const xScale = d3
      .scaleTime()
      .domain([d3.min(dates)!, d3.max(dates)!])
      .range([margin.left, width - margin.right]);

    // Draw axis
    const xAxis = d3.axisBottom(xScale).ticks(6);
    svg
      .append("g")
      .attr("transform", `translate(0, ${height - margin.bottom})`)
      .call(xAxis);

    // Draw event markers
    svg
      .selectAll("circle")
      .data(events)
      .join("circle")
      .attr("cx", (d) => xScale(new Date(d.date)))
      .attr("cy", height / 2)
      .attr("r", 4)
      .attr("fill", "#3b82f6")
      .attr("opacity", 0.6);

    // Brush for selection
    const brush = d3
      .brushX()
      .extent([
        [margin.left, 0],
        [width - margin.right, height - margin.bottom],
      ])
      .on("end", (event) => {
        if (event.selection) {
          const [x0, x1] = event.selection;
          const d0 = xScale.invert(x0);
          const d1 = xScale.invert(x1);
          onDateRangeChange(
            d0.toISOString().split("T")[0],
            d1.toISOString().split("T")[0]
          );
        }
      });

    svg.append("g").call(brush);
  }, [events]);

  return (
    <div className="w-full bg-white p-4 rounded-lg shadow">
      <svg ref={svgRef} className="w-full" height={100}></svg>
    </div>
  );
}
```

---

## 5. StatsPanel Component

**File:** `src/components/StatsPanel/index.tsx`

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchGraphStats } from "@/lib/api/graph";
import { StatCard } from "./StatCard";

export function StatsPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchGraphStats,
  });

  if (isLoading) return <div>Loading stats...</div>;
  if (!data) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Statistics</h2>

      <div className="grid grid-cols-2 gap-4">
        <StatCard label="Total Events" value={data.totalEvents} />
        <StatCard label="Entities" value={data.totalEntities} />
        <StatCard label="Relationships" value={data.totalRelationships} />
        <StatCard label="Evolution Links" value={data.evolutionLinks} />
      </div>

      <div className="pt-4 border-t">
        <h3 className="font-semibold mb-2">Top Entities</h3>
        <ul className="space-y-2">
          {data.topEntities?.slice(0, 5).map((entity: any) => (
            <li key={entity.label} className="flex justify-between text-sm">
              <span>{entity.label}</span>
              <span className="text-gray-500">{entity.degree} connections</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

---

## Component Usage Examples

### Main Graph Page

```typescript
// src/app/graph/page.tsx
"use client";

import { GraphView } from "@/components/GraphView";
import { FilterPanel } from "@/components/FilterPanel";
import { EventCard } from "@/components/EventCard";
import { Timeline } from "@/components/Timeline";
import { StatsPanel } from "@/components/StatsPanel";
import { useGraphData } from "@/hooks/useGraphData";
import { useGraphStore } from "@/stores/graphStore";

export default function GraphPage() {
  const { data, isLoading } = useGraphData();
  const { selectedNode, setSelectedNode } = useGraphStore();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <aside className="w-80 bg-gray-50 overflow-y-auto p-4 space-y-4">
        <FilterPanel onFilterChange={(filters) => console.log(filters)} />
        <StatsPanel />
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col">
        <div className="flex-1">
          <GraphView
            nodes={data?.nodes || []}
            edges={data?.edges || []}
            onNodeClick={setSelectedNode}
          />
        </div>
        <div className="h-32">
          <Timeline
            events={data?.events || []}
            onDateRangeChange={(start, end) => console.log(start, end)}
          />
        </div>
      </main>

      {/* Event detail card */}
      {selectedNode && (
        <EventCard eventId={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  );
}
```

---

**Status:** Component library documented ✅
**Next:** See UI_UX_DESIGN_SYSTEM.md for styling details

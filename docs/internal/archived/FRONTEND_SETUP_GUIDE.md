# FE-EKG Frontend Setup Guide

**Time to complete:** 30 minutes
**Prerequisites:** Node.js 18+, npm/yarn/pnpm

---

## Quick Start (5 Commands)

```bash
# 1. Create Next.js app
cd ~/Desktop/DDP
npx create-next-app@latest feekg-frontend --typescript --tailwind --app --src-dir --import-alias "@/*"

# 2. Install dependencies
cd feekg-frontend
npm install @tanstack/react-query@5 zustand cytoscape @types/cytoscape

# 3. Setup env vars
cp .env.example .env.local

# 4. Start Flask backend (separate terminal)
cd ../feekg && ./venv/bin/python api/app.py

# 5. Start frontend
cd ../feekg-frontend && npm run dev
```

Open `http://localhost:3000`

---

## Detailed Setup

### Step 1: Create Next.js Project (2 min)

```bash
cd ~/Desktop/DDP
npx create-next-app@latest feekg-frontend
```

**Prompts - Choose these:**
- ✅ TypeScript: Yes
- ✅ ESLint: Yes
- ✅ Tailwind CSS: Yes
- ✅ `src/` directory: Yes
- ✅ App Router: Yes
- ✅ Import alias: `@/*` (default)

---

### Step 2: Install Dependencies (3 min)

```bash
cd feekg-frontend

# Core dependencies
npm install @tanstack/react-query@5.17.0
npm install zustand@4.4.7
npm install cytoscape@3.28.1
npm install date-fns@3.0.0

# Dev dependencies
npm install -D @types/cytoscape
npm install -D @tanstack/react-query-devtools
```

**Package versions:**
- `@tanstack/react-query`: Server state management
- `zustand`: UI state management
- `cytoscape`: Graph visualization
- `date-fns`: Date formatting

---

### Step 3: Environment Variables (1 min)

Create `.env.local`:

```bash
# Flask API backend
NEXT_PUBLIC_API_URL=http://localhost:5000

# AllegroGraph (optional - for direct access)
NEXT_PUBLIC_AG_URL=https://qa-agraph.nelumbium.ai
NEXT_PUBLIC_AG_USER=sadmin
NEXT_PUBLIC_AG_PASS=279H-Dt<>,YU
NEXT_PUBLIC_AG_REPO=FEEKG

# Graph config
NEXT_PUBLIC_DEFAULT_PAGE_SIZE=100
NEXT_PUBLIC_MAX_NODES=1000
```

Create `.env.example` (for git):

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_DEFAULT_PAGE_SIZE=100
NEXT_PUBLIC_MAX_NODES=1000
```

**Add to `.gitignore`:**
```
.env.local
```

---

### Step 4: Update `tailwind.config.ts` (2 min)

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // FE-EKG color scheme
        emerald: {
          DEFAULT: '#10b981',
          50: '#ecfdf5',
          100: '#d1fae5',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
        },
        indigo: {
          DEFAULT: '#6366f1',
          50: '#eef2ff',
          100: '#e0e7ff',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
        },
        pink: {
          DEFAULT: '#ec4899',
          50: '#fdf2f8',
          100: '#fce7f3',
          500: '#ec4899',
          600: '#db2777',
          700: '#be185d',
        },
        purple: {
          DEFAULT: '#a855f7',
          50: '#faf5ff',
          100: '#f3e8ff',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
        },
      },
    },
  },
  plugins: [],
};
export default config;
```

---

### Step 5: Setup Root Layout (5 min)

**File:** `src/app/layout.tsx`

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FE-EKG - Financial Event Evolution Knowledge Graph",
  description: "Interactive visualization of financial event evolution networks",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

**File:** `src/app/providers.tsx`

```typescript
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

---

### Step 6: Create API Client (5 min)

**File:** `src/lib/api/client.ts`

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "APIError";
  }
}

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new APIError(response.status, `API Error: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new Error(`Network error: ${error}`);
  }
}
```

**File:** `src/lib/api/events.ts`

```typescript
import { apiClient } from "./client";

export interface Event {
  eventId: string;
  label: string;
  type: string;
  date: string;
  description?: string;
  csvRow?: string;
  confidence?: number;
}

export interface PaginatedResponse {
  events: Event[];
  offset: number;
  limit: number;
  total: number;
}

export async function fetchPaginatedEvents(
  offset = 0,
  limit = 100
): Promise<PaginatedResponse> {
  return apiClient<PaginatedResponse>(
    `/api/events/paginated?offset=${offset}&limit=${limit}`
  );
}

export async function fetchTimeWindow(
  start: string,
  end: string
): Promise<{ events: Event[] }> {
  return apiClient<{ events: Event[] }>(
    `/api/events/timewindow?start=${start}&end=${end}`
  );
}
```

---

### Step 7: Create Constants (2 min)

**File:** `src/lib/constants.ts`

```typescript
export const COLORS = {
  hasActor: "#10b981",
  hasTarget: "#ef4444",
  involves: "#3b82f6",
  relatedTo: "#a855f7",
  evolvesTo: "#f59e0b",
};

export const GRAPH_CONFIG = {
  DEFAULT_PAGE_SIZE: parseInt(
    process.env.NEXT_PUBLIC_DEFAULT_PAGE_SIZE || "100"
  ),
  MAX_NODES: parseInt(process.env.NEXT_PUBLIC_MAX_NODES || "1000"),
};
```

---

### Step 8: Test Setup (5 min)

**File:** `src/app/page.tsx`

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchPaginatedEvents } from "@/lib/api/events";

export default function Home() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["events", 0, 10],
    queryFn: () => fetchPaginatedEvents(0, 10),
  });

  if (isLoading) return <div className="p-8">Loading...</div>;
  if (error) return <div className="p-8 text-red-500">Error: {error.message}</div>;

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold mb-4">FE-EKG Setup Test</h1>
      <p className="mb-4">Found {data?.total} events</p>
      <ul className="space-y-2">
        {data?.events.map((event) => (
          <li key={event.eventId} className="p-3 bg-gray-100 rounded">
            <div className="font-semibold">{event.label}</div>
            <div className="text-sm text-gray-600">{event.date}</div>
          </li>
        ))}
      </ul>
    </main>
  );
}
```

---

### Step 9: Start Development Servers

**Terminal 1 - Backend:**
```bash
cd ~/Desktop/DDP/feekg
./venv/bin/python api/app.py
```

**Terminal 2 - Frontend:**
```bash
cd ~/Desktop/DDP/feekg-frontend
npm run dev
```

**Open:** `http://localhost:3000`

**Expected:** List of 10 events from API

---

## Troubleshooting

### Error: "Failed to fetch"

**Cause:** Backend not running

**Fix:**
```bash
cd feekg
./venv/bin/python api/app.py
```

### Error: "Module not found: Can't resolve '@/lib/api/client'"

**Cause:** Import alias not configured

**Fix:** Check `tsconfig.json` has:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Error: "CORS policy"

**Cause:** Flask CORS not configured

**Fix:** Backend should have CORS enabled (already done in `api/app.py`)

---

## Next Steps

1. ✅ Setup complete
2. Read `COMPONENT_LIBRARY.md` to build GraphView
3. Read `STATE_MANAGEMENT_GUIDE.md` for Zustand setup
4. Start Phase 1 MVP development

---

**Estimated Total Time:** 30 minutes
**Status:** Ready to build ✅

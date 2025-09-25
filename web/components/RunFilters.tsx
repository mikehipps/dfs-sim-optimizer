'use client';

import React, { useEffect, useMemo, useState } from 'react';

export type Filters = {
  minTop10Pct?: number;      // 0–100
  minProj?: number;          // projection floor
  salaryMin?: number;        // inclusive
  salaryMax?: number;        // inclusive
  includePlayers?: string[]; // match-any, case-insensitive
  excludePlayers?: string[]; // match-any, case-insensitive
};

type Props = {
  rows?: Array<Record<string, any>>;                  // optional: let the component do filtering
  onFiltered?: (rows: Array<Record<string, any>>) => void; // optional: notify parent after filtering
  csvName?: string;                                   // default 'filtered_runs.csv'
  className?: string;
  style?: React.CSSProperties;
  initial?: Partial<Filters>;
};

/* ----------------------------- helpers ------------------------------ */

const SEP = /[,\|\-\/\u00B7;:\s]+/g;

function getFirstNumber(row: Record<string, any>, keys: string[]): number | undefined {
  for (const k of keys) {
    if (k in row) {
      const v = (row as any)[k];
      if (typeof v === 'number' && Number.isFinite(v)) return v;
      if (typeof v === 'string' && v.trim() !== '' && !Number.isNaN(+v)) return +v;
    }
  }
  return undefined;
}

function normalizeName(s: string): string {
  return s.trim().toLowerCase();
}

function playerListFromRow(row: Record<string, any>): string[] {
  const candidates = ['players', 'roster', 'names', 'lineup'];
  for (const k of candidates) {
    if (k in row) {
      const v = (row as any)[k];
      if (Array.isArray(v)) return v.map((x) => normalizeName(String(x)));
      if (typeof v === 'string') return v.split(SEP).map(normalizeName).filter(Boolean);
    }
  }
  const textish = Object.values(row).filter((v) => typeof v === 'string').join(' ');
  return textish ? textish.split(SEP).map(normalizeName).filter(Boolean) : [];
}

/* ---------------------------- URL param helpers --------------------------- */
function getParam(u: URLSearchParams, k: string): string | undefined {
  const v = u.get(k);
  return v !== null && v !== '' ? v : undefined;
}
function setParam(u: URLSearchParams, k: string, v: string | number | undefined) {
  if (v === undefined || v === '' || (typeof v === 'number' && !Number.isFinite(v))) {
    u.delete(k);
  } else {
    u.set(k, String(v));
  }
}

/* ------------------------------ filter ------------------------------ */

export function applyFilters<T extends Record<string, any>>(rows: T[], f: Filters): T[] {
  if (!Array.isArray(rows) || !rows.length) return rows;

  const includes = (f.includePlayers ?? []).map(normalizeName).filter(Boolean);
  const excludes = (f.excludePlayers ?? []).map(normalizeName).filter(Boolean);

  return rows.filter((row) => {
    const top10 = getFirstNumber(row, [
      'top10', 'top10p', 'top10pct', 'top_ten_pct', 'top10_percent', 'p_top10', 'top10_prob',
    ]);
    const proj = getFirstNumber(row, ['proj', 'projection', 'fpts', 'points', 'fp', 'proj_pts']);
    const salary = getFirstNumber(row, ['salary', 'sal', 'cost', 'price']);

    if (typeof f.minTop10Pct === 'number' && Number.isFinite(f.minTop10Pct)) {
      if (typeof top10 !== 'number' || Number.isNaN(top10)) return false;
      const rowPct = top10 <= 1 ? top10 * 100 : top10;
      if (rowPct < f.minTop10Pct) return false;
    }

    if (typeof f.minProj === 'number' && Number.isFinite(f.minProj)) {
      if (typeof proj !== 'number' || Number.isNaN(proj)) return false;
      if (proj < f.minProj) return false;
    }

    if (typeof f.salaryMin === 'number' && Number.isFinite(f.salaryMin)) {
      if (typeof salary !== 'number' || Number.isNaN(salary)) return false;
      if (salary < f.salaryMin) return false;
    }
    if (typeof f.salaryMax === 'number' && Number.isFinite(f.salaryMax)) {
      if (typeof salary !== 'number' || Number.isNaN(salary)) return false;
      if (salary > f.salaryMax) return false;
    }

    const roster = playerListFromRow(row);
    if (includes.length) {
      const ok = includes.some((p) => roster.includes(p));
      if (!ok) return false;
    }
    if (excludes.length) {
      const bad = excludes.some((p) => roster.includes(p));
      if (bad) return false;
    }

    return true;
  });
}

/* ----------------------------- CSV export --------------------------- */

export function exportToCsv(rows: Array<Record<string, any>>, name = 'filtered_runs.csv') {
  if (!rows?.length) {
    alert('Nothing to export (no rows after filtering).');
    return;
  }
  const keys = Array.from(
    rows.reduce<Set<string>>((acc, r) => {
      Object.keys(r).forEach((k) => acc.add(k));
      return acc;
    }, new Set<string>())
  );

  const escape = (val: any) => {
    if (val === null || val === undefined) return '';
    let s = typeof val === 'string' ? val : JSON.stringify(val);
    s = s.replace(/"/g, '""');
    return /[",\n]/.test(s) ? `"${s}"` : s;
    };

  const header = keys.join(',');
  const body = rows.map((r) => keys.map((k) => escape((r as any)[k])).join(',')).join('\n');
  const csv = header + '\n' + body;

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(url);
  a.remove();
}

/* ------------------------------- UI --------------------------------- */


export default function RunFilters(props: Props) {
    const [minTop10Pct, setMinTop10Pct] = useState<number | ''>(props.initial?.minTop10Pct ?? '');
  const [minProj, setMinProj] = useState<number | ''>(props.initial?.minProj ?? '');
  const [salaryMin, setSalaryMin] = useState<number | ''>(props.initial?.salaryMin ?? '');
  const [salaryMax, setSalaryMax] = useState<number | ''>(props.initial?.salaryMax ?? '');
  const [includeRaw, setIncludeRaw] = useState<string>((props.initial?.includePlayers ?? []).join(', '));
  const [excludeRaw, setExcludeRaw] = useState<string>((props.initial?.excludePlayers ?? []).join(', '));

  // --- URL -> state (on mount) ---
  useEffect(() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      // only hydrate if the field is still blank (user hasn't typed)
      if (minTop10Pct === '') { const t = getParam(sp, 't'); if (t) setMinTop10Pct(Number(t)); }
      if (minProj     === '') { const p = getParam(sp, 'p'); if (p) setMinProj(Number(p)); }
      if (salaryMin   === '') { const sm = getParam(sp, 'smin'); if (sm) setSalaryMin(Number(sm)); }
      if (salaryMax   === '') { const sx = getParam(sp, 'smax'); if (sx) setSalaryMax(Number(sx)); }
      if (!includeRaw) { const inc = getParam(sp, 'inc'); if (inc) setIncludeRaw(inc); }
      if (!excludeRaw) { const exc = getParam(sp, 'exc'); if (exc) setExcludeRaw(exc); }
    } catch {}
  }, []);

  const filters: Filters = useMemo(() => ({
    minTop10Pct: minTop10Pct === '' ? undefined : Number(minTop10Pct),
    minProj:     minProj     === '' ? undefined : Number(minProj),
    salaryMin:   salaryMin   === '' ? undefined : Number(salaryMin),
    salaryMax:   salaryMax   === '' ? undefined : Number(salaryMax),
    includePlayers: includeRaw.split(SEP).map((s) => s.trim()).filter(Boolean),
    excludePlayers: excludeRaw.split(SEP).map((s) => s.trim()).filter(Boolean),
  }), [minTop10Pct, minProj, salaryMin, salaryMax, includeRaw, excludeRaw]);

  const filtered = useMemo(() => {
    if (!props.rows) return undefined;
    return applyFilters(props.rows, filters);
  }, [props.rows, filters]);

  // notify parent AFTER render to avoid setState-in-render
  useEffect(() => {
    if (props.onFiltered && Array.isArray(filtered)) {
      props.onFiltered(filtered);
    }
  }, [filtered, props.onFiltered]);


  /* sync filters -> URL */
  useEffect(() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      setParam(sp, 't', filters.minTop10Pct);
      setParam(sp, 'p', filters.minProj);
      setParam(sp, 'smin', filters.salaryMin);
      setParam(sp, 'smax', filters.salaryMax);
      setParam(sp, 'inc', (filters.includePlayers ?? []).join(','));
      setParam(sp, 'exc', (filters.excludePlayers ?? []).join(','));
      const url = window.location.pathname + '?' + sp.toString();
      window.history.replaceState(null, '', url);
    } catch {}
  }, [filters]);
  const onClear = () => {
    setMinTop10Pct('');
    setMinProj('');
    setSalaryMin('');
    setSalaryMax('');
    setIncludeRaw('');
    setExcludeRaw('');
  };

  return (
    <div className={`w-full rounded-xl border p-3 md:p-4 flex flex-col gap-3 bg-[var(--bg-panel,#0b0b0b08)] ${props.className ?? ''}`} style={props.style}>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        <label className="flex flex-col text-sm">
          <span className="opacity-70">Min Top10% *</span>
          <input
            inputMode="decimal"
            placeholder="e.g. 8"
            className="rounded-md border px-2 py-1"
            value={minTop10Pct}
            onChange={(e) => setMinTop10Pct(e.target.value === '' ? '' : Number(e.target.value))}
          />
        </label>
        <label className="flex flex-col text-sm">
          <span className="opacity-70">Min Proj</span>
          <input
            inputMode="decimal"
            placeholder="e.g. 100"
            className="rounded-md border px-2 py-1"
            value={minProj}
            onChange={(e) => setMinProj(e.target.value === '' ? '' : Number(e.target.value))}
          />
        </label>
        <label className="flex flex-col text-sm">
          <span className="opacity-70">Salary Min</span>
          <input
            inputMode="numeric"
            placeholder="e.g. 48000"
            className="rounded-md border px-2 py-1"
            value={salaryMin}
            onChange={(e) => setSalaryMin(e.target.value === '' ? '' : Number(e.target.value))}
          />
        </label>
        <label className="flex flex-col text-sm">
          <span className="opacity-70">Salary Max</span>
          <input
            inputMode="numeric"
            placeholder="e.g. 50000"
            className="rounded-md border px-2 py-1"
            value={salaryMax}
            onChange={(e) => setSalaryMax(e.target.value === '' ? '' : Number(e.target.value))}
          />
        </label>
        <label className="flex flex-col text-sm col-span-2 md:col-span-3">
          <span className="opacity-70">Include players (any)</span>
          <input
            placeholder="comma/space separated"
            className="rounded-md border px-2 py-1"
            value={includeRaw}
            onChange={(e) => setIncludeRaw(e.target.value)}
          />
        </label>
        <label className="flex flex-col text-sm col-span-2 md:col-span-3">
          <span className="opacity-70">Exclude players (any)</span>
          <input
            placeholder="comma/space separated"
            className="rounded-md border px-2 py-1"
            value={excludeRaw}
            onChange={(e) => setExcludeRaw(e.target.value)}
          />
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="rounded-md border px-3 py-1.5 font-medium hover:bg-black/5"
          onClick={() => {
            window.dispatchEvent(new CustomEvent('runs:filters:apply', { detail: filters }));
          }}
          title="Emits a runs:filters:apply event with the filter model"
        >
          Apply (emit)
        </button>

        <button
          type="button"
          className="rounded-md border px-3 py-1.5 font-medium hover:bg-black/5"
          onClick={() => {
            onClear();
            window.dispatchEvent(new CustomEvent('runs:filters:clear'));
          }}
        >
          Clear
        </button>

        <button
          type="button"
          className="rounded-md border px-3 py-1.5 font-medium hover:bg-black/5"
          onClick={() => {
            window.dispatchEvent(new CustomEvent('runs:export', { detail: filters }));
            if (Array.isArray(filtered)) exportToCsv(filtered, props.csvName ?? 'filtered_runs.csv');
          }}
        >
          Export filtered CSV
        </button>

        {'rows' in props && props.rows && (
          <span className="text-sm opacity-70 ml-2">
            {Array.isArray(filtered) ? `${filtered.length} / ${props.rows!.length} shown` : `${(props.rows as any[]).length} rows`}
          </span>
        )}
      </div>

      <p className="text-xs opacity-60">
        * Top10% accepts either 0–100 (percentage) or normalizes row values that are 0–1.
        Include/Exclude match ANY of the names found on a row.
      </p>
    </div>
  );
}

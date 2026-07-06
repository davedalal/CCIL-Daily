import React, { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const DATA = {"ccil": {}, "wss": {}, "sections_meta": {"as_of": "2026-07-06", "sections": {}, "scorecard": {"recommendation": "No recommendation can be made for this run: data/consolidated/history.json contains zero CCIL days and zero WSS weeks, so there is no underlying data for any of the seven signal sections (curve slope, 10Y trajectory, FCY hedging cost, supply premium, short-end funding, long-term funding, or FX position). This is the first run of the pipeline and inbox/ is empty aside from .gitkeep - no WSS/Arete files have been manually dropped yet, and the automated CCIL fetch (scripts/fetch_ccil.py) could not reach ccilindia.com from this environment due to a network/proxy restriction (ERR_TUNNEL_CONNECTION_FAILED), not bot detection or a report template change. Once a CCIL and/or WSS file is dropped into inbox/ and the pipeline re-run, sections will populate from real parsed numbers. No borrowing/hedging view is offered today given the total absence of data.", "tone": "neutral"}, "gaps": ["Section A (10Y-1Y G-Sec curve slope): no data - history.json has zero CCIL days.", "Section B (10Y benchmark trajectory): no data - history.json has zero CCIL days.", "Section C (MMIFOR vs OIS, FCY hedging cost): no data - history.json has zero CCIL days.", "Section D (G-Sec minus OIS, supply premium): no data - history.json has zero CCIL days.", "Section E (short-end funding - T-Bills, WACR vs repo, CD/CP): no data - history.json has zero WSS weeks.", "Section F (long-term funding, bond yield matrix): no data - history.json has zero WSS weeks.", "Section G (FX position - forward premia / USD data): no data - not present in history.json.", "Root cause: inbox/ contained only .gitkeep (no manually-dropped WSS/Arete files) and the automated CCIL fetch failed with a network/proxy error (ERR_TUNNEL_CONNECTION_FAILED) specific to this run environment, not a CCIL bot-detection block or template change - fetch_ccil.py's regex and page logic were not the failure point."]}};
// render_dashboard.py replaces the line above with:
//   const DATA = {...history.json + report_sections.json, merged...};
// This keeps the component itself static (reviewed once, in version control)
// while only the data changes day to day - port the fuller tab/chart layout
// from the manually-built dashboard (INR_Daily_Dashboard_03Jul2026.jsx) into
// this file as your permanent template once you're happy with it.

const COLORS = {
  bg: "#0a0e17", panel: "#0f1420", border: "#1e2940",
  amber: "#f0b429", green: "#3fb950", red: "#f85149", text: "#e6edf3", textDim: "#8b949e",
};

function toneColor(tone) {
  return tone === "hawkish" ? COLORS.red : tone === "dovish" ? COLORS.green : COLORS.amber;
}

function SectionCard({ id, section }) {
  if (!section) return null;
  return (
    <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 16, marginBottom: 16 }}>
      <div style={{ color: COLORS.amber, fontWeight: 700, marginBottom: 6 }}>{id}. {section.signal}</div>
      <p style={{ color: COLORS.text, fontSize: 13, lineHeight: 1.6 }}>{section.explanation}</p>
      <span style={{ color: toneColor(section.tone), fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>{section.tone}</span>
    </div>
  );
}

export default function Dashboard() {
  const dates = Object.keys(DATA.ccil || {}).sort();
  const gsecSeries = dates.map((d) => ({
    d,
    oneY: DATA.ccil[d]?.gsec?.["1Y"]?.current,
    tenY: DATA.ccil[d]?.gsec?.["10Y"]?.current,
  }));

  return (
    <div style={{ background: COLORS.bg, minHeight: "100vh", fontFamily: "monospace", color: COLORS.text, padding: 20 }}>
      <div style={{ fontSize: 20, fontWeight: 800, color: COLORS.amber }}>
        INR RATES &amp; FX DAILY — {DATA.sections_meta?.as_of || dates[dates.length - 1]}
      </div>

      <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 16, margin: "16px 0" }}>
        <div style={{ color: COLORS.amber, fontWeight: 700, marginBottom: 6 }}>Scorecard</div>
        <p style={{ fontSize: 13, lineHeight: 1.6 }}>{DATA.sections_meta?.scorecard?.recommendation}</p>
      </div>

      <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 16, marginBottom: 16 }}>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={gsecSeries}>
            <CartesianGrid stroke="#1c2333" strokeDasharray="3 3" />
            <XAxis dataKey="d" tick={{ fill: COLORS.textDim, fontSize: 10 }} />
            <YAxis tick={{ fill: COLORS.textDim, fontSize: 10 }} />
            <Tooltip contentStyle={{ background: "#131a2b", border: `1px solid ${COLORS.border}` }} />
            <Legend />
            <Line type="monotone" dataKey="oneY" name="1Y G-Sec" stroke={COLORS.green} strokeWidth={2} dot={{ r: 2 }} />
            <Line type="monotone" dataKey="tenY" name="10Y G-Sec" stroke={COLORS.amber} strokeWidth={2} dot={{ r: 2 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {["A", "B", "C", "D", "E", "F", "G"].map((id) => (
        <SectionCard key={id} id={id} section={DATA.sections_meta?.sections?.[id]} />
      ))}

      {DATA.sections_meta?.gaps?.length > 0 && (
        <div style={{ background: "#3a2a0022", border: "1px solid #8a6a1f", borderRadius: 6, padding: 12, fontSize: 11, color: COLORS.amber }}>
          {DATA.sections_meta.gaps.map((g, i) => <div key={i}>⚠ {g}</div>)}
        </div>
      )}
    </div>
  );
}

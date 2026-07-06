import React, { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const DATA = {"ccil": {"2026-07-06": {"gsec": {"10Y": {"1D": 0.0, "1M": -24.4, "1W": -2.5, "1Y": 35.0, "3M": -41.1, "current": 6.73}, "10Y_Bench": {"1D": 0.0, "1M": -27.2, "1W": -3.2, "1Y": 30.0, "3M": -39.4, "current": 6.69}, "15Y": {"1D": 0.0, "1M": -31.6, "1W": -4.7, "1Y": 31.0, "3M": -51.2, "current": 6.97}, "1Y": {"1D": 0.0, "1M": -21.0, "1W": 12.4, "1Y": 26.0, "3M": -15.0, "current": 5.77}, "20Y": {"1D": 0.0, "1M": -33.2, "1W": -4.4, "1Y": 31.0, "3M": -52.6, "current": 7.12}, "2Y": {"1D": 0.0, "1M": -24.8, "1W": 5.9, "1Y": 22.0, "3M": -39.7, "current": 6.0}, "30Y": {"1D": 0.0, "1M": -26.1, "1W": 1.0, "1Y": 32.0, "3M": -48.1, "current": 7.34}, "5Y": {"1D": 0.0, "1M": -28.3, "1W": -1.9, "1Y": 32.0, "3M": -46.0, "current": 6.45}}, "mmifor": {"1Y": null, "2Y": {"1D": 0.57, "1M": -1.26, "1W": 3.12, "1Y": 80.15, "3M": -31.8, "current": 6.81}, "3Y": {"1D": 0.5, "1M": 2.83, "1W": 8.25, "1Y": 74.32, "3M": -24.61, "current": 6.84}, "5Y": {"1D": 1.71, "1M": -13.09, "1W": 4.41, "1Y": 77.16, "3M": -16.03, "current": 7.04}}, "ois": {"1Y": {"1D": -2.89, "1M": -36.61, "1W": -2.54, "1Y": 26.23, "3M": -45.75, "current": 5.75}, "2Y": {"1D": -3.75, "1M": -46.47, "1W": -3.09, "1Y": 41.02, "3M": -53.44, "current": 5.89}, "3Y": {"1D": -2.66, "1M": -46.13, "1W": -2.19, "1Y": 45.01, "3M": -53.8, "current": 6.0}, "5Y": {"1D": -3.58, "1M": -48.5, "1W": -3.62, "1Y": 46.66, "3M": -59.07, "current": 6.16}}, "report_date": "2026-07-06", "source": "CCIL Daily Analytics", "source_dir": "data/raw_extract/ccil/CCIL_DAILY_ANALYSIS_06_07_26"}}, "wss": {}, "sections_meta": {"as_of": "2026-07-06", "sections": {"A": {"signal": "Curve slope ~96bps, mildly steeper y/y", "explanation": "10Y G-Sec (6.73%) minus 1Y G-Sec (5.77%) = 0.96pp (96bps) of positive slope. Using each tenor's own 1-year change-over column from CCIL (10Y +35bps y/y, 1Y +26bps y/y), the slope has widened by about 9bps versus a year ago (35bps - 26bps), i.e. from roughly 87bps to 96bps today. Both ends of the curve have risen over the past year, but the long end has risen slightly more.", "tone": "neutral"}, "B": {"signal": "10Y benchmark at 6.69%, rallying hard short-term but still up y/y", "explanation": "10Y Benchmark (6.94% GS 2036) is at 6.69% today, flat on the day (0bps) and down 3.2bps on the week. Over 1M and 3M it has rallied sharply: -27.2bps and -39.4bps respectively. Over 1Y it is still up 30.0bps, so today's level sits below the recent 1M/3M peak in yield but above where it was a year ago. Net read: a strong recent rally sitting on top of a higher year-ago base.", "tone": "dovish"}, "C": {"signal": "MMIFOR-OIS FCY hedging premium 84-92bps, widened 29-39bps y/y", "explanation": "Comparing CCIL's MMIFOR and MIBOR-OIS current levels for matching tenors: 2Y spread = 6.81% - 5.89% = 92bps; 3Y spread = 6.84% - 6.00% = 84bps; 5Y spread = 7.04% - 6.16% = 88bps. (1Y MMIFOR is discontinued since Jul-2023, so no 1Y spread.) Using each series' own 1-year change-over column, the spread itself has widened materially over the past year: 2Y by 80.15-41.02=39.1bps, 3Y by 74.32-45.01=29.3bps, 5Y by 77.16-46.66=30.5bps. FCY hedging via the MMIFOR route has gotten notably more expensive relative to onshore OIS over the past 12 months.", "tone": "hawkish"}, "D": {"signal": "G-Sec supply premium over OIS: 2-29bps, compressing y/y at 2Y/5Y", "explanation": "G-Sec minus OIS for matching tenors: 1Y = 5.77%-5.75% = 2bps; 2Y = 6.00%-5.89% = 11bps; 5Y = 6.45%-6.16% = 29bps. (No 3Y G-Sec tenor is published by CCIL, so the 3Y OIS point has no G-Sec match this run.) Using each series' 1-year change-over column, the premium has moved as follows over the past year: 1Y roughly flat (26.0-26.23=-0.2bps), 2Y narrowed by about 19bps (22.0-41.02=-19.0bps), 5Y narrowed by about 15bps (32.0-46.66=-14.7bps). The G-Sec supply premium over swaps has been compressing at the belly/long end even as absolute levels stay positive.", "tone": "dovish"}}, "scorecard": {"recommendation": "Short-end levels aren't available this run (no WSS data), so this reflects only the G-Sec/OIS/MMIFOR complex from today's CCIL report. The G-Sec curve is a normal, mildly steepening 96bps (10Y-1Y), with the long end (10Y benchmark) having rallied 27-39bps over the last one to three months even though it's still 30bps higher than a year ago - net neutral-to-dovish momentum on duration. FCY hedging via MMIFOR is expensive and getting more so (84-92bps over OIS, widened 29-39bps y/y), arguing against unhedged or MMIFOR-hedged foreign-currency borrowing right now. Meanwhile the G-Sec-over-OIS supply premium (2-29bps) has been compressing at 2Y/5Y, a mild positive for onshore government borrowing costs relative to swaps. On the numbers available today: favor onshore G-Sec/OIS-linked funding over MMIFOR-hedged FCY funding, and lean into the recent long-end rally cautiously given the higher year-ago base.", "tone": "neutral"}, "gaps": ["Section E (short-end funding: T-Bills, WACR vs repo, CD/CP) omitted - no RBI WSS file was present in inbox/ this run, so history.json has no wss data.", "Section F (long-term funding / bond yield matrix) omitted - no separate bond/Arete data source was present this run.", "Section G (FX position: forward premia / USD data) omitted - no WSS forward-premia data this run. Note: the CCIL PDF does contain an FX forwards/premia table (e.g. Tom, GBP rows) but parse_ccil.py does not currently extract it, so it is not in history.json either; flagging for a future script update rather than eyeballing numbers from the PDF.", "D: no 3Y G-Sec tenor exists in CCIL's published table, so the 3Y OIS point (6.00%) has no G-Sec-minus-OIS spread this run.", "Automated CCIL download (scripts/fetch_ccil.py) failed this run (Playwright browser channel mismatch in this environment) - pipeline ran against the manually-dropped inbox/CCIL_DAILY_ANALYSIS_06_07_26.pdf instead.", "history.json currently holds only a single day (2026-07-06) of CCIL data, so all changes described above are CCIL's own change-over columns (1D/1W/1M/3M/1Y), not a multi-day trend built from this dataset yet."]}};
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

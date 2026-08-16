import { useMemo, useRef, useState } from "react";
import { decryptJson, encryptJson, type EncryptedEnvelope } from "./crypto";
import { db } from "./db";
import { breakEven, recommendDecision } from "./decision";
import { extractEstimateText } from "./ocr";
import { parseDecisionPacket, type DecisionPacket } from "./packet";

const rules = [
  { code: "A", title: "Engine oil", summary: "Replace engine oil when displayed." },
  { code: "6", title: "Rear differential fluid", summary: "Replace rear differential fluid on applicable AWD vehicles." },
  { code: "7", title: "Brake fluid", summary: "Replace when displayed; Honda also gives a three-year fallback." },
];

const ruleSource = "https://techinfo.honda.com/rjanisis/pubs/om/ah/a3d42424iom/enu/details/131229047-12935.html";

function dollars(cents: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(cents / 100);
}

function cents(value: string) {
  const amount = Number(value);
  return Number.isFinite(amount) ? Math.max(0, Math.round(amount * 100)) : 0;
}

function downloadJson(filename: string, value: unknown) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [dealer, setDealer] = useState("328.01");
  const [alternative, setAlternative] = useState("160.00");
  const [tripHours, setTripHours] = useState("1.5");
  const [hourlyRate, setHourlyRate] = useState(100);
  const [missingScope, setMissingScope] = useState(false);
  const [safetyConcern, setSafetyConcern] = useState(false);
  const [dueNow, setDueNow] = useState(false);
  const [passphrase, setPassphrase] = useState("");
  const [packet, setPacket] = useState<DecisionPacket | null>(null);
  const [packetStatus, setPacketStatus] = useState("No encrypted plan imported on this device.");
  const [ocrText, setOcrText] = useState("");
  const [ocrStatus, setOcrStatus] = useState("Manual entry is always available.");
  const importRef = useRef<HTMLInputElement>(null);

  const calculation = useMemo(() => breakEven(cents(dealer), cents(alternative)), [dealer, alternative]);
  const breakEvenAtRate = calculation.breakEvenHours[`$${hourlyRate}/hour`] ?? 0;
  const decision = recommendDecision({
    safetyUncertainty: safetyConcern,
    missingScopeOrFees: missingScope,
    dueNow,
    alternativeSaves: calculation.savingsCents > 0,
    extraTripHours: Number(tripHours) || 0,
    breakEvenHours: breakEvenAtRate,
  });
  const quoteCount = packet?.quotes.length ?? 0;

  async function importPacket(file: File) {
    if (passphrase.length < 12) {
      setPacketStatus("Enter the packet passphrase (at least 12 characters) first.");
      return;
    }
    try {
      const envelope = JSON.parse(await file.text()) as EncryptedEnvelope;
      const parsed = parseDecisionPacket(await decryptJson(envelope, passphrase));
      await db.vault.put({ id: "active-plan", kind: "decision-packet", updatedAt: new Date().toISOString(), envelope });
      setPacket(parsed);
      setPacketStatus(`Imported ${parsed.plan.id}; encrypted copy saved on this device.`);
    } catch (error) {
      setPacketStatus(`Import failed: ${error instanceof Error ? error.message : "invalid packet"}`);
    }
  }

  async function unlockSavedPacket() {
    try {
      const record = await db.vault.get("active-plan");
      if (!record) throw new Error("no saved packet exists");
      const parsed = parseDecisionPacket(await decryptJson(record.envelope, passphrase));
      setPacket(parsed);
      setPacketStatus(`Unlocked ${parsed.plan.id} from encrypted local storage.`);
    } catch (error) {
      setPacketStatus(`Unlock failed: ${error instanceof Error ? error.message : "invalid passphrase"}`);
    }
  }

  async function exportDecision() {
    if (!packet || passphrase.length < 12) {
      setPacketStatus("Import a plan and enter its passphrase before exporting a decision.");
      return;
    }
    const updated: DecisionPacket = {
      ...packet,
      exported_at: new Date().toISOString(),
      on_site: {
        dealer_cents: cents(dealer),
        alternative_cents: cents(alternative),
        savings_cents: calculation.savingsCents,
        hourly_rate: hourlyRate,
        extra_trip_hours: Number(tripHours) || 0,
        break_even_hours: breakEvenAtRate,
        missing_scope_or_fees: missingScope,
        safety_uncertainty: safetyConcern,
        due_now: dueNow,
        support_state: decision,
        estimate_text: ocrText,
      },
    };
    const envelope = await encryptJson(updated, passphrase);
    await db.vault.put({ id: "on-site-decision", kind: "on-site-decision", updatedAt: new Date().toISOString(), envelope });
    downloadJson(`vehicle-maint-decision-${new Date().toISOString().slice(0, 10)}.encrypted.json`, envelope);
    setPacketStatus("Encrypted on-site decision exported. No provider was contacted.");
  }

  async function runOcr(file: File, input: HTMLInputElement) {
    try {
      setOcrStatus("Starting local OCR…");
      const text = await extractEstimateText(file, ({ status, progress }) => {
        setOcrStatus(`${status} ${Math.round(progress * 100)}%`);
      });
      setOcrText(text);
      setOcrStatus("Extraction complete. Review the text, then the photo selection is discarded.");
    } catch (error) {
      setOcrStatus(`OCR unavailable: ${error instanceof Error ? error.message : "use manual entry"}`);
    } finally {
      input.value = "";
    }
  }

  return (
    <main>
      <header className="masthead">
        <a className="brand" href="#top" aria-label="Vehicle Maintenance Planner home">
          <img src="/icon.svg" alt="" />
          <span>Vehicle Maintenance Planner</span>
        </a>
        <div className="privacy-badge"><span aria-hidden="true">●</span> Offline · encrypted · local</div>
      </header>

      <section className="hero" id="top">
        <div>
          <p className="eyebrow">At the counter, before the signature</p>
          <h1>Know what's due.<br />Know what your time is worth.</h1>
          <p className="hero-copy">A private decision screen for comparing written scope, real quotes, and the cost of another trip without sending your vehicle data anywhere.</p>
        </div>
        <aside className="vehicle-card">
          <p className="label">Initial catalog</p>
          <h2>2024 Honda CR-V</h2>
          <p>Sport-L Hybrid · AWD · U.S.</p>
          <div className="reading-row"><span>Displayed</span><strong>{packet?.plan.service_codes.join("") ?? "A67"}</strong></div>
          <div className="reading-row"><span>Odometer</span><strong>{(packet?.plan.odometer_miles ?? 8462).toLocaleString()} mi</strong></div>
        </aside>
      </section>

      <section className="section-grid">
        <article className="panel scope-panel">
          <div className="panel-heading">
            <div><p className="eyebrow">01 · Manufacturer scope</p><h2>What A67 means</h2></div>
            <a href={ruleSource} target="_blank" rel="noreferrer">Honda source ↗</a>
          </div>
          <div className="code-list">
            {rules.map((rule) => (
              <div className="code-row" key={rule.code}>
                <span className="code-chip">{rule.code}</span>
                <div><h3>{rule.title}</h3><p>{rule.summary}</p></div>
              </div>
            ))}
          </div>
          <p className="source-note">Scope is summarized, not copied. Dealer recommendations remain a separate origin.</p>
        </article>

        <article className="panel quote-panel">
          <p className="eyebrow">02 · Comparable quotes</p>
          <h2>{quoteCount} / 3 current written quotes</h2>
          <div className="progress"><span style={{ width: `${Math.min(quoteCount / 3, 1) * 100}%` }} /></div>
          <p>{quoteCount >= 3 ? "Enough quotes to calculate a best value." : "No best-value claim until three equivalent-scope quotes are imported."}</p>
          <div className="provider-mix"><span>Target mix</span><strong>2 dealers · 3 specialists · ≤30 mi</strong></div>
        </article>
      </section>

      <section className="decision-section">
        <div className="section-title"><p className="eyebrow">03 · Switching-cost check</p><h2>Is another trip actually worth it?</h2></div>
        <div className="calculator-grid">
          <div className="inputs panel">
            <label>Current estimate <span>$</span><input inputMode="decimal" value={dealer} onChange={(event) => setDealer(event.target.value)} /></label>
            <label>Best comparable alternative <span>$</span><input inputMode="decimal" value={alternative} onChange={(event) => setAlternative(event.target.value)} /></label>
            <label>Extra trip + appointment time <input inputMode="decimal" value={tripHours} onChange={(event) => setTripHours(event.target.value)} /><span>hours</span></label>
            <fieldset>
              <legend>Value of your time</legend>
              <div className="segmented">{[50, 100, 150].map((rate) => <button type="button" className={hourlyRate === rate ? "active" : ""} onClick={() => setHourlyRate(rate)} key={rate}>${rate}/hr</button>)}</div>
            </fieldset>
          </div>
          <div className="result panel">
            <p className="label">Likely price difference</p>
            <strong className="savings">{dollars(calculation.savingsCents)}</strong>
            <p>At ${hourlyRate}/hour, the alternative stops saving money after:</p>
            <div className="time-result"><strong>{breakEvenAtRate}</strong><span>extra hours</span></div>
            <div className="rate-table">{Object.entries(calculation.breakEvenHours).map(([rate, hours]) => <div key={rate}><span>{rate}</span><strong>{hours} h</strong></div>)}</div>
          </div>
          <div className={`decision-card ${decision}`}>
            <p className="label">Support state</p>
            <h3>{decision.replaceAll("_", " ")}</h3>
            <p>{decision === "defer_and_quote" ? "The estimated savings exceed the time cost of another trip. Confirm the service is safe to defer and use written scope." : decision === "clarify_before_authorizing" ? "Ask for the missing scope or fee details before signing." : decision === "seek_professional_safety_advice" ? "A safety concern should be assessed by a qualified professional." : "The entered facts do not show a better-value reason to make another trip."}</p>
            <label className="check"><input type="checkbox" checked={missingScope} onChange={(event) => setMissingScope(event.target.checked)} /> Scope or fees are missing</label>
            <label className="check"><input type="checkbox" checked={dueNow} onChange={(event) => setDueNow(event.target.checked)} /> Current facts establish due now</label>
            <label className="check"><input type="checkbox" checked={safetyConcern} onChange={(event) => setSafetyConcern(event.target.checked)} /> Safety condition is uncertain</label>
          </div>
        </div>
      </section>

      <section className="workflow-grid">
        <article className="panel estimate-panel">
          <p className="eyebrow">04 · Estimate capture</p><h2>Scan locally or enter manually</h2>
          <input className="sr-only" ref={importRef} type="file" accept="image/*" onChange={(event) => { const file = event.currentTarget.files?.[0]; if (file) void runOcr(file, event.currentTarget); }} />
          <button className="primary" type="button" onClick={() => importRef.current?.click()}>Choose estimate photo</button>
          <p className="status">{ocrStatus}</p>
          <textarea aria-label="Extracted estimate text" placeholder="Review OCR output or type estimate details here…" value={ocrText} onChange={(event) => setOcrText(event.target.value)} />
          <p className="source-note">The photo is never stored in IndexedDB and its selection is cleared after extraction.</p>
        </article>

        <article className="panel packet-panel">
          <p className="eyebrow">05 · Encrypted handoff</p><h2>Desktop ↔ phone packet</h2>
          <label>Packet passphrase<input type="password" autoComplete="current-password" value={passphrase} onChange={(event) => setPassphrase(event.target.value)} placeholder="12+ characters" /></label>
          <div className="button-row">
            <label className="secondary file-button">Import<input type="file" accept="application/json,.json" onChange={(event) => { const file = event.currentTarget.files?.[0]; if (file) void importPacket(file); event.currentTarget.value = ""; }} /></label>
            <button className="secondary" type="button" onClick={() => void unlockSavedPacket()}>Unlock saved</button>
            <button className="primary" type="button" onClick={() => void exportDecision()}>Export decision</button>
          </div>
          <p className="status">{packetStatus}</p>
        </article>
      </section>

      <section className="law-note">
        <div><p className="eyebrow">Washington check</p><h2>Written estimate + authorization threshold</h2></div>
        <p>For covered repairs over $100, Washington's Attorney General describes written-estimate requirements and additional authorization when the final price will exceed the estimate by more than 10%. <a href="https://www.atg.wa.gov/auto-repair" target="_blank" rel="noreferrer">Read the current state guidance ↗</a></p>
      </section>

      <footer><span>Private by design. No backend, telemetry, analytics, remote fonts, or runtime CDN.</span><span>Not mechanical, legal, or safety advice.</span></footer>
    </main>
  );
}

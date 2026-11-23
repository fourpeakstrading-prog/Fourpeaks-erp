import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError, type CompanySettings } from "../api";

export default function Settings() {
  const [s, setS] = useState<CompanySettings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.settings.get().then(setS).catch((err) => setError(err.message));
  }, []);

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!s) return;
    setError(null);
    setSaved(false);
    if (!s.company_name.trim()) {
      setError("Company name is required.");
      return;
    }
    try {
      setS(
        await api.settings.update({
          company_name: s.company_name.trim(),
          address: s.address,
          cr_number: s.cr_number,
          vat_number: s.vat_number,
          vat_enabled: s.vat_enabled,
          financial_year_start_month: s.financial_year_start_month,
        }),
      );
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save.");
    }
  }

  if (!s) return <p className="muted">Loading…</p>;

  return (
    <>
      <h1>Company settings</h1>
      <form className="card" onSubmit={onSave} noValidate>
        <div className="field">
          <label htmlFor="cn">Company name</label>
          <input id="cn" value={s.company_name} onChange={(e) => setS({ ...s, company_name: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="ad">Address</label>
          <input id="ad" value={s.address} onChange={(e) => setS({ ...s, address: e.target.value })} />
        </div>
        <div className="row">
          <div className="field">
            <label htmlFor="cr">Commercial registration number</label>
            <input id="cr" value={s.cr_number} onChange={(e) => setS({ ...s, cr_number: e.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="fy">Financial year starts in month</label>
            <input
              id="fy"
              type="number"
              min={1}
              max={12}
              value={s.financial_year_start_month}
              onChange={(e) => setS({ ...s, financial_year_start_month: Number(e.target.value) })}
            />
          </div>
        </div>
        <div className="row">
          <div className="field">
            <label htmlFor="vn">VAT number</label>
            <input id="vn" value={s.vat_number} onChange={(e) => setS({ ...s, vat_number: e.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="ve">VAT</label>
            <select id="ve" value={s.vat_enabled ? "on" : "off"} onChange={(e) => setS({ ...s, vat_enabled: e.target.value === "on" })}>
              <option value="off">Off (not registered)</option>
              <option value="on">On</option>
            </select>
          </div>
        </div>
        <p className="muted">
          Currency {s.currency}, {s.currency_decimals} decimal places. Fixed for this company.
        </p>
        {error && <div className="error">{error}</div>}
        {saved && <p className="muted">Saved.</p>}
        <button type="submit">Save</button>
      </form>
    </>
  );
}

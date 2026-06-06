import type { NontaxableForm } from "../forms/nontaxableForm";

interface Props {
  form: NontaxableForm;
  onChange: (form: NontaxableForm) => void;
}

export function NontaxableSourceForm({ form, onChange }: Props): JSX.Element {
  const setField = (field: keyof NontaxableForm, value: string): void => {
    onChange({ ...form, [field]: value });
  };
  const needsTaxable = ["total_adjusted", "current_monthly"].includes(
    form.incomeMethod,
  );
  const needsCurrent = form.incomeMethod === "current_monthly";

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="space-y-1 text-sm">
        <span className="font-medium">Source kind</span>
        <select
          aria-label="Source kind"
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) => setField("kind", event.target.value)}
          value={form.kind}
        >
          <option value="income">Non-taxable income</option>
          <option value="social_security">Social Security</option>
        </select>
      </label>
      {form.kind === "income" ? (
        <IncomeFields
          form={form}
          needsCurrent={needsCurrent}
          needsTaxable={needsTaxable}
          setField={setField}
        />
      ) : (
        <SocialSecurityFields form={form} setField={setField} />
      )}
    </div>
  );
}

interface FieldProps {
  form: NontaxableForm;
  setField: (field: keyof NontaxableForm, value: string) => void;
}

function IncomeFields({
  form,
  needsCurrent,
  needsTaxable,
  setField,
}: FieldProps & { needsCurrent: boolean; needsTaxable: boolean }): JSX.Element {
  return (
    <>
      <label className="space-y-1 text-sm">
        <span className="font-medium">Method</span>
        <select
          aria-label="Method"
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) => setField("incomeMethod", event.target.value)}
          value={form.incomeMethod}
        >
          <option value="gross_100">Gross amount</option>
          <option value="total_adjusted">Total adjusted</option>
          <option value="current_monthly">Current monthly</option>
        </select>
      </label>
      <MoneyInput label="Annual gross" onChange={setField} value={form.annualGross} />
      {needsTaxable ? (
        <MoneyInput label="Annual taxable" onChange={setField} value={form.annualTaxable} />
      ) : null}
      {needsCurrent ? (
        <MoneyInput label="Current monthly" onChange={setField} value={form.currentMonthly} />
      ) : null}
      <MoneyInput label="Gross-up rate" onChange={setField} value={form.grossUpRate} />
    </>
  );
}

function SocialSecurityFields({ form, setField }: FieldProps): JSX.Element {
  return (
    <>
      <label className="space-y-1 text-sm">
        <span className="font-medium">Method</span>
        <select
          aria-label="Method"
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) => setField("socialSecurityMethod", event.target.value)}
          value={form.socialSecurityMethod}
        >
          <option value="gross_100">Gross amount</option>
          <option value="adjusted">Adjusted</option>
        </select>
      </label>
      <MoneyInput label="Annual gross" onChange={setField} value={form.annualGross} />
    </>
  );
}

function MoneyInput({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (field: keyof NontaxableForm, value: string) => void;
  value: string;
}): JSX.Element {
  const field = labelToField(label);
  return (
    <label className="space-y-1 text-sm">
      <span className="font-medium">{label}</span>
      <input
        aria-label={label}
        className="w-full rounded-md border border-slate-300 px-3 py-2"
        inputMode="decimal"
        onChange={(event) => onChange(field, event.target.value)}
        value={value}
      />
    </label>
  );
}

function labelToField(label: string): keyof NontaxableForm {
  if (label === "Annual taxable") return "annualTaxable";
  if (label === "Current monthly") return "currentMonthly";
  if (label === "Gross-up rate") return "grossUpRate";
  return "annualGross";
}

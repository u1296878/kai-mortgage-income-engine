import type { SelfEmploymentKind } from "../types/selfEmployment";

export interface FieldConfig {
  name: string;
  label: string;
}

export interface ComponentConfig {
  key: string;
  label: string;
  fields: FieldConfig[];
}

export interface KindConfig {
  kind: SelfEmploymentKind;
  label: string;
  components: ComponentConfig[];
}

const w2 = { key: "w2_years", label: "W-2 wages", fields: f([["wages", "Wages"]]) };

export const SELF_EMPLOYMENT_KINDS: KindConfig[] = [
  personal("schedule_b", "Schedule B", [
    ["recurring_interest", "Recurring interest"],
    ["recurring_dividends", "Recurring dividends"],
  ]),
  personal("schedule_c", "Schedule C", [
    ["tax_year", "Tax year"],
    ["net_profit", "Net profit"],
    ["nonrecurring_income", "Nonrecurring income"],
    ["depletion", "Depletion"],
    ["depreciation", "Depreciation"],
    ["meals_entertainment_exclusion", "Meals exclusion"],
    ["business_use_of_home", "Business use of home"],
    ["business_miles", "Business miles"],
    ["amortization_casualty", "Amortization/casualty"],
    ["w2_self_employment_income", "Self-employment W-2 income"],
  ]),
  personal("schedule_d", "Schedule D", [
    ["recurring_capital_gains", "Recurring capital gains"],
  ]),
  personal("schedule_e_royalty", "Schedule E royalty", [
    ["royalty_income", "Royalty income"],
    ["total_expenses", "Total expenses"],
    ["depreciation_depletion", "Depreciation/depletion"],
  ]),
  personal("schedule_f", "Schedule F", [
    ["net_profit", "Net profit"],
    ["nontax_coop_ccc_payments", "Nontax coop/CCC payments"],
    ["nonrecurring_loss", "Nonrecurring loss"],
    ["nonrecurring_income", "Nonrecurring income"],
    ["depreciation", "Depreciation"],
    ["amortization_casualty_depletion", "Amortization/casualty/depletion"],
    ["business_use_of_home", "Business use of home"],
  ]),
  {
    kind: "partnership",
    label: "Partnership",
    components: [partnershipK1(), w2, form1065()],
  },
  {
    kind: "s_corporation",
    label: "S-Corporation",
    components: [sCorpK1(), w2, form1120s()],
  },
  {
    kind: "corporation",
    label: "Corporation",
    components: [w2, form1120()],
  },
];

export function configForKind(kind: SelfEmploymentKind): KindConfig {
  return SELF_EMPLOYMENT_KINDS.find((config) => config.kind === kind)!;
}

function partnershipK1(): ComponentConfig {
  return {
    key: "k1_years",
    label: "Partnership K-1",
    fields: f([
      ["ordinary_income", "Ordinary income"],
      ["net_rental_income", "Net rental income"],
      ["guaranteed_payments", "Guaranteed payments"],
    ]),
  };
}

function sCorpK1(): ComponentConfig {
  return {
    key: "k1_years",
    label: "S-Corp K-1",
    fields: f([
      ["ordinary_income", "Ordinary income"],
      ["net_rental_income", "Net rental income"],
    ]),
  };
}

function form1065(): ComponentConfig {
  return {
    key: "form_1065_years",
    label: "Form 1065",
    fields: f([
      ["passthrough_other_partnerships", "Passthrough partnerships"],
      ...businessReturnFields("L16 d", "L4b"),
    ]),
  };
}

function form1120s(): ComponentConfig {
  return {
    key: "form_1120s_years",
    label: "Form 1120S",
    fields: f(businessReturnFields("L17 d", "L3b")),
  };
}

function form1120(): ComponentConfig {
  return {
    key: "form_1120_years",
    label: "Form 1120",
    fields: f([
      ["taxable_income", "Taxable income"],
      ["total_tax", "Total tax"],
      ["nonrecurring_gains_losses", "Nonrecurring gains/losses"],
      ["nonrecurring_income", "Nonrecurring income"],
      ["depreciation", "Depreciation"],
      ["depletion", "Depletion"],
      ["amortization_casualty_nonrecurring_loss", "Amortization/casualty/loss"],
      ["nol_and_special_deductions", "NOL/special deductions"],
      ["mortgages_notes_payable_lt_1yr", "Mortgages/notes < 1yr"],
      ["travel_entertainment_exclusion", "T&E exclusion"],
      ["ownership_pct", "Ownership pct"],
      ["dividends_paid_to_borrower", "Dividends paid to borrower"],
    ]),
  };
}

function personal(
  kind: SelfEmploymentKind,
  label: string,
  fields: [string, string][],
): KindConfig {
  return { kind, label, components: [{ key: "years", label, fields: f(fields) }] };
}

function businessReturnFields(
  mortgageLine: string,
  travelLine: string,
): [string, string][] {
  return [
    ["nonrecurring_income", "Nonrecurring income"],
    ["depreciation", "Depreciation"],
    ["depreciation_8825", "Depreciation 8825"],
    ["depletion", "Depletion"],
    ["amortization_casualty_nonrecurring_loss", "Amortization/casualty/loss"],
    ["mortgages_notes_payable_lt_1yr", `Mortgages/notes < 1yr ${mortgageLine}`],
    ["travel_entertainment_exclusion", `T&E exclusion ${travelLine}`],
    ["ownership_pct", "Ownership pct"],
  ];
}

function f(fields: [string, string][]): FieldConfig[] {
  return fields.map(([name, label]) => ({ name, label }));
}

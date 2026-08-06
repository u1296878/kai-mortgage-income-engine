import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { NontaxableCalculationsPanel } from "./NontaxableCalculationsPanel";
import { RentalCalculationsPanel } from "./RentalCalculationsPanel";
import { SelfEmploymentCalculationsPanel } from "./SelfEmploymentCalculationsPanel";
import type { RentalCalculationResponse } from "../types/api";
import type { NonTaxableCalculationResponse } from "../types/nontaxable";
import type { SelfEmploymentCalculationResponse } from "../types/selfEmployment";


describe("calculation panels", () => {
  it("lets rental calculations be edited, excluded, and deleted", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    const onIncludedChange = vi.fn();
    render(
      <MemoryRouter>
        <RentalCalculationsPanel
          calculations={[rentalCalculation()]}
          caseId="case-1"
          deletingId={null}
          onDelete={onDelete}
          onIncludedChange={onIncludedChange}
          updatingId={null}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Edit" })).toHaveAttribute(
      "href",
      "/income/rental?caseId=case-1&calculationId=rental-1",
    );
    await user.click(screen.getByRole("checkbox", { name: "Included" }));
    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(onIncludedChange).toHaveBeenCalledWith("rental-1", false);
    expect(onDelete).toHaveBeenCalledWith("rental-1");
  });

  it("toggles and deletes self-employment calculations", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    const onIncludedChange = vi.fn();
    render(
      <SelfEmploymentCalculationsPanel
        calculations={[selfEmploymentCalculation()]}
        deletingId={null}
        onDelete={onDelete}
        onIncludedChange={onIncludedChange}
        updatingId={null}
      />,
    );

    expect(screen.getByText("Design LLC")).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: "Included" }));
    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(onIncludedChange).toHaveBeenCalledWith("self-1", false);
    expect(onDelete).toHaveBeenCalledWith("self-1");
  });

  it("renders and deletes non-taxable calculations", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(
      <NontaxableCalculationsPanel
        calculations={[nontaxableCalculation()]}
        deletingId={null}
        onDelete={onDelete}
      />,
    );

    const panel = screen.getByText("SSI Award").closest("div") as HTMLElement;
    expect(within(panel).getByText(/\$1,037\.50\/mo/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(onDelete).toHaveBeenCalledWith("nt-1");
  });
});


function rentalCalculation(): RentalCalculationResponse {
  return {
    id: "rental-1",
    case_id: "case-1",
    borrower_id: null,
    label: "123 Main St",
    inputs: {
      property_class: "primary_2_4_unit",
      method: "schedule_e",
      schedule_e_years: [],
      monthly_pitia: null,
      gross_monthly_rent: null,
      vacancy_factor: 0.25,
    },
    qualifying_monthly: 1125,
    annual_income: 13500,
    included: true,
    source_document_id: "doc-1",
    source_property_key: "a",
    breakdown: { qualifying_monthly: 1125, property_class: "primary_2_4_unit", method: "schedule_e", years: [] },
    created_at: "2026-05-31T00:00:00Z",
  };
}


function selfEmploymentCalculation(): SelfEmploymentCalculationResponse {
  return {
    id: "self-1",
    case_id: "case-1",
    borrower_id: null,
    label: "Design LLC",
    kind: "schedule_c",
    qualifying_monthly: 4166.67,
    annual_income: 50000.04,
    included: true,
    source_document_id: "doc-1",
    source_business_key: "business-1",
    breakdown: { kind: "schedule_c", qualifying_monthly: 4166.67, annual_income: 50000.04 },
    created_at: "2026-05-31T00:00:00Z",
  };
}


function nontaxableCalculation(): NonTaxableCalculationResponse {
  return {
    id: "nt-1",
    case_id: "case-1",
    borrower_id: null,
    label: "SSI Award",
    kind: "social_security",
    monthly: 1037.5,
    annual_income: 12450,
    breakdown: {
      monthly: 1037.5,
      method: "adjusted",
      taxable_monthly: 0,
      eligible_monthly: 1037.5,
    },
    created_at: "2026-05-31T00:00:00Z",
  };
}

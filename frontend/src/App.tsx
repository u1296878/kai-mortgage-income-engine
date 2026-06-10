import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layout/AppShell";
import { CaseDetailPage } from "./pages/CaseDetailPage";
import { CasesPage } from "./pages/CasesPage";
import { EmploymentIncomePage } from "./pages/EmploymentIncomePage";
import { RentalIncomePage } from "./pages/RentalIncomePage";
import { NontaxableIncomePage } from "./pages/NontaxableIncomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { SelfEmploymentIncomePage } from "./pages/SelfEmploymentIncomePage";

export function App(): JSX.Element {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/cases" replace />} />
      <Route element={<AppShell />}>
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/cases/:caseId" element={<CaseDetailPage />} />
        <Route path="/income/employment" element={<EmploymentIncomePage />} />
        <Route path="/income/rental" element={<RentalIncomePage />} />
        <Route path="/income/nontaxable" element={<NontaxableIncomePage />} />
        <Route path="/income/self-employment" element={<SelfEmploymentIncomePage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

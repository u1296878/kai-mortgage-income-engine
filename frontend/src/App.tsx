import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./auth/RequireAuth";
import { AppShell } from "./layout/AppShell";
import { AdminBrokersPage } from "./pages/AdminBrokersPage";
import { CaseDetailPage } from "./pages/CaseDetailPage";
import { CasesPage } from "./pages/CasesPage";
import { EmploymentIncomePage } from "./pages/EmploymentIncomePage";
import { RentalIncomePage } from "./pages/RentalIncomePage";
import { LoginPage } from "./pages/LoginPage";
import { NontaxableIncomePage } from "./pages/NontaxableIncomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RegisterPage } from "./pages/RegisterPage";

export function App(): JSX.Element {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/cases" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route path="/admin/brokers" element={<AdminBrokersPage />} />
          <Route path="/cases" element={<CasesPage />} />
          <Route path="/cases/:caseId" element={<CaseDetailPage />} />
          <Route path="/income/employment" element={<EmploymentIncomePage />} />
          <Route path="/income/rental" element={<RentalIncomePage />} />
          <Route path="/income/nontaxable" element={<NontaxableIncomePage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

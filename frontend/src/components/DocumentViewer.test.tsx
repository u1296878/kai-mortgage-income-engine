import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DocumentViewer } from "./DocumentViewer";

vi.mock("../auth/token", () => ({
  getStoredToken: () => "token-123",
}));

vi.mock("react-pdf", async () => {
  const React = await import("react");
  const Document = ({ children, onLoadSuccess }: { children: React.ReactNode; onLoadSuccess?: (args: { numPages: number }) => void }) => {
    React.useEffect(() => {
      onLoadSuccess?.({ numPages: 1 });
    }, [onLoadSuccess]);
    return <div>{children}</div>;
  };
  const Page = ({
    pageNumber,
    onLoadSuccess,
  }: {
    pageNumber: number;
    onLoadSuccess?: (page: { getViewport: (args: { scale: number }) => { width: number; height: number } }) => void;
  }) => {
    React.useEffect(() => {
      onLoadSuccess?.({
        getViewport: () => ({ width: 600, height: 792 }),
      });
    }, [onLoadSuccess]);
    return <div>Mock Page {pageNumber}</div>;
  };
  return { Document, Page, pdfjs: { GlobalWorkerOptions: { workerSrc: "" } } };
});

describe("DocumentViewer", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(new Blob([new Uint8Array([1, 2, 3])], { type: "application/pdf" }), { status: 200 }),
      ),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");
    URL.revokeObjectURL = vi.fn();
  });

  it("renders without crashing with a valid source reference", async () => {
    render(
      <DocumentViewer
        isOpen
        documentId="doc-1"
        onClose={() => undefined}
        source={{
          field: "w2_wages",
          value: 85000,
          document_id: "doc-1",
          page: 1,
          bounding_box: { x1: 100, y1: 200, x2: 250, y2: 220 },
        }}
      />,
    );

    expect(screen.getByText("Document Viewer")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Mock Page 1")).toBeInTheDocument());
  });

  it("places highlights using top-left PDF coordinates", async () => {
    render(
      <DocumentViewer
        isOpen
        documentId="doc-1"
        onClose={() => undefined}
        source={{
          field: "total_income",
          value: 94380,
          document_id: "doc-1",
          page: 1,
          bounding_box: { x1: 480, y1: 619, x2: 560, y2: 631 },
        }}
      />,
    );

    const highlight = await screen.findByTestId("source-highlight");
    const scale = 520 / 600;
    const oldFlippedTop = (792 - 631) * scale + 8;

    expect(parseFloat(highlight.style.top)).toBeCloseTo(619 * scale + 8, 2);
    expect(parseFloat(highlight.style.top)).not.toBeCloseTo(oldFlippedTop, 2);
  });
});

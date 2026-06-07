import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, Dispatch, SetStateAction } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import type { PDFPageProxy } from "pdfjs-dist";
import type { ExtractedField } from "../types/api";
import { getStoredToken } from "../auth/token";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();
const PAGE_WIDTH_PX = 520;

interface DocumentViewerProps {
  isOpen: boolean;
  documentId: string | null;
  source: ExtractedField | null;
  onClose: () => void;
}

interface PageMetrics {
  scale: number;
}
export function DocumentViewer({ isOpen, documentId, source, onClose }: DocumentViewerProps): JSX.Element {
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pageMetrics, setPageMetrics] = useState<Record<number, PageMetrics>>({});
  const pageRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
  useEffect(() => {
    if (!isOpen || !documentId) {
      return;
    }
    const token = getStoredToken();
    if (!token) {
      setError("Missing auth token for document viewer.");
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);
    setPageMetrics({});
    setNumPages(0);
    void fetch(`${apiBaseUrl}/documents/${documentId}/file`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Failed to load document (${response.status})`);
        }
        return response.blob();
      })
      .then((blob) => {
        if (!active) {
          return;
        }
        const objectUrl = URL.createObjectURL(blob);
        setFileUrl((previous) => {
          if (previous) {
            URL.revokeObjectURL(previous);
          }
          return objectUrl;
        });
      })
      .catch((caught) => {
        if (!active) {
          return;
        }
        const message = caught instanceof Error ? caught.message : "Failed to load document.";
        setError(message);
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [isOpen, documentId, apiBaseUrl]);

  useEffect(() => {
    if (!source || !isOpen) {
      return;
    }
    const pageElement = pageRefs.current[source.page];
    if (pageElement && typeof pageElement.scrollIntoView === "function") {
      pageElement.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [source, isOpen, numPages]);

  useEffect(() => {
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [fileUrl]);

  const pages = useMemo(() => Array.from({ length: numPages }, (_, index) => index + 1), [numPages]);

  const highlight = source ? buildHighlight(source, pageMetrics[source.page]) : null;
  if (!isOpen) {
    return <></>;
  }

  return (
    <aside className="fixed inset-y-0 right-0 z-50 w-full max-w-[620px] border-l border-slate-300 bg-white shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold">Document Viewer</h2>
        <button className="rounded border border-slate-300 px-3 py-1 text-sm" onClick={onClose} type="button">
          Close
        </button>
      </div>
      <div className="h-[calc(100vh-56px)] overflow-y-auto p-4">
        {loading ? <p className="text-sm text-slate-600">Loading document...</p> : null}
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {source ? <p className="mb-3 text-xs text-slate-600">Source page {source.page}</p> : null}
        {fileUrl ? (
          <Document file={fileUrl} onLoadSuccess={({ numPages: pageCount }) => setNumPages(pageCount)}>
            {pages.map((pageNumber) => (
              <div
                key={pageNumber}
                ref={(element) => {
                  pageRefs.current[pageNumber] = element;
                }}
                className="relative mb-4 w-[520px] max-w-full rounded border border-slate-200 bg-slate-50 p-2"
              >
                <Page
                  pageNumber={pageNumber}
                  width={PAGE_WIDTH_PX}
                  onLoadSuccess={(page) => setMetrics(page, pageNumber, setPageMetrics)}
                />
                {highlight && source?.page === pageNumber ? (
                  <div
                    data-testid="source-highlight"
                    className="pointer-events-none absolute border-2 border-yellow-500 bg-yellow-300/40"
                    style={highlight}
                  />
                ) : null}
              </div>
            ))}
          </Document>
        ) : null}
      </div>
    </aside>
  );
}

function setMetrics(
  page: PDFPageProxy,
  pageNumber: number,
  setPageMetrics: Dispatch<SetStateAction<Record<number, PageMetrics>>>,
): void {
  const viewport = page.getViewport({ scale: 1 });
  const scale = PAGE_WIDTH_PX / viewport.width;
  setPageMetrics((existing) => ({
    ...existing,
    [pageNumber]: { scale },
  }));
}

function buildHighlight(source: ExtractedField, metrics?: PageMetrics): CSSProperties | null {
  if (!metrics) {
    return null;
  }
  return {
    left: source.bounding_box.x1 * metrics.scale + 8,
    top: source.bounding_box.y1 * metrics.scale + 8,
    width: (source.bounding_box.x2 - source.bounding_box.x1) * metrics.scale,
    height: (source.bounding_box.y2 - source.bounding_box.y1) * metrics.scale,
  };
}

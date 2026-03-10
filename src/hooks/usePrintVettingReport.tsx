import { useCallback } from "react";
import { createRoot } from "react-dom/client";
import { PrintableVettingReport } from "@/components/PrintableVettingReport";
import type { VettingRequest } from "@/lib/types";

export function usePrintVettingReport() {
  const printReport = useCallback((vetting: VettingRequest) => {
    const printWindow = window.open("", "_blank", "width=1000,height=800");
    if (!printWindow) {
      alert("Please allow popups to print the report");
      return;
    }

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${vetting.subject_name} - Vetting Report</title>
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.5; color: #1a1a1a; background: white; }
            @media print {
              body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
              .no-print { display: none !important; }
              @page { size: letter; margin: 0.4in; }
            }
            .print-controls { position: fixed; top: 1rem; right: 1rem; z-index: 1000; display: flex; gap: 0.5rem; }
            .print-btn { padding: 0.5rem 1rem; background: #111827; color: white; border: none; border-radius: 0.375rem; cursor: pointer; font-weight: 500; font-size: 0.875rem; }
            .print-btn:hover { background: #374151; }
            .close-btn { padding: 0.5rem 1rem; background: #6b7280; color: white; border: none; border-radius: 0.375rem; cursor: pointer; font-weight: 500; font-size: 0.875rem; }
            .close-btn:hover { background: #4b5563; }
          </style>
        </head>
        <body>
          <div class="print-controls no-print">
            <button class="print-btn" onclick="window.print()">🖨️ Print / Save PDF</button>
            <button class="close-btn" onclick="window.close()">✕ Close</button>
          </div>
          <div id="report-root"></div>
        </body>
      </html>
    `);
    printWindow.document.close();

    setTimeout(() => {
      const container = printWindow.document.getElementById("report-root");
      if (container) {
        const root = createRoot(container);
        root.render(<PrintableVettingReport vetting={vetting} />);
      }
    }, 100);
  }, []);

  return { printReport };
}

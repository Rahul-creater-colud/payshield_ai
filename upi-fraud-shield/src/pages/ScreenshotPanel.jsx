import React, { useState } from "react";
import {
  UploadCloud,
  FileScan,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  RefreshCw,
  Eye,
  FileText,
  AlertOctagon,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  ShieldCheck,
  Check
} from "lucide-react";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";
import { useToast } from "../hooks/useToast";
import { isValidImageFile } from "../utils/validators";
import { mockScreenshotResults } from "../data/mockScreenshotResults";

export const ScreenshotPanel = () => {
  const { mode } = useApiMode();
  const toast = useToast();

  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [activeSampleKey, setActiveSampleKey] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);

  const sampleScenarios = mockScreenshotResults.sampleScams;

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validation = isValidImageFile(file);
    if (!validation.valid) {
      toast.error(validation.error, "Invalid File");
      return;
    }

    setSelectedFile(file);
    setActiveSampleKey(null);
    setScanResult(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      setImagePreview(event.target?.result);
    };
    reader.readAsDataURL(file);
    toast.info(`Loaded: ${file.name}`, "Image Ready");
  };

  const handleSelectSample = (sample) => {
    setActiveSampleKey(sample.id);
    setSelectedFile({ name: sample.filename });
    setScanResult(null);

    // Create an SVG data URL for realistic visual representation of the sample screenshot
    const isPhish = sample.riskCategory === "HIGH";
    const svgContent = `
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
        <rect width="600" height="400" fill="${isPhish ? "#450a0a" : "#022c22"}" rx="16"/>
        <rect x="20" y="20" width="560" height="360" fill="${isPhish ? "#1c1917" : "#064e3b"}" rx="12" stroke="${isPhish ? "#ef4444" : "#10b981"}" stroke-width="2"/>
        <text x="50" y="70" fill="#ffffff" font-family="sans-serif" font-size="20" font-weight="bold">${sample.name}</text>
        <text x="50" y="110" fill="${isPhish ? "#f87171" : "#6ee7b7"}" font-family="monospace" font-size="14">${sample.filename}</text>
        <line x1="50" y1="130" x2="550" y2="130" stroke="#475569" stroke-width="1"/>
        <text x="50" y="170" fill="#e2e8f0" font-family="sans-serif" font-size="14" width="500">
          ${isPhish ? "REVERSE-DEBIT PHISHING COLLECT / SCAM EVIDENCE" : "OFFICIAL BBPS VERIFIED RECEIPT"}
        </text>
        <rect x="50" y="200" width="500" height="120" fill="#0f172a" rx="8" stroke="#334155"/>
        <text x="70" y="240" fill="#38bdf8" font-family="monospace" font-size="13">OCR TEXT STREAM DETECTED:</text>
        <text x="70" y="270" fill="#cbd5e1" font-family="sans-serif" font-size="12">${sample.ocrExtractedText.slice(0, 55)}...</text>
        <text x="70" y="295" fill="#facc15" font-family="monospace" font-size="12">Risk Severity: ${sample.riskScore}/100 [${sample.riskCategory}]</text>
      </svg>
    `;
    const encoded = `data:image/svg+xml;utf8,${encodeURIComponent(svgContent)}`;
    setImagePreview(encoded);
    toast.info(`Selected demo receipt: "${sample.name}"`, "Demo Screenshot Loaded");
  };

  const handleStartScan = async () => {
    if (!imagePreview) {
      toast.warning("Please upload a screenshot or select a demo sample first", "No Image");
      return;
    }

    setScanning(true);
    setScanResult(null);

    try {
      const res = await apiService.scanScreenshot(selectedFile, activeSampleKey, mode);
      const data = res.data || res;
      setScanResult({
        ...data,
        data_label: data.data_label || (mode === "MOCK" ? "DEMO DATA" : "DEMO DATA — sample response")
      });

      if (data.riskCategory === "HIGH") {
        toast.error(`High Threat Identified: ${data.verdict}`, "Malicious Receipt");
      } else {
        toast.info("Synthetic demo result displayed; no uploaded image or payment was verified.", "Demo Sample");
      }
    } catch (err) {
      console.error("Scan error:", err);
      toast.error(err.message || "Failed to scan screenshot", "OCR Error");
    } finally {
      setScanning(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setImagePreview(null);
    setActiveSampleKey(null);
    setScanResult(null);
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
            Screenshot Demo & Evidence Scanner
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Sample results are synthetic. Uploaded-image OCR is not implemented in the local backend.
          </p>
          <p className="mt-1 text-[11px] font-semibold text-amber-700">
            DEMO samples only • uploaded images are not analyzed
          </p>
        </div>

        {/* Demo Preset Selectors */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-slate-400 mr-1 hidden lg:inline">Quick Demo Receipts:</span>
          {sampleScenarios.map((s) => (
            <button
              key={s.id}
              onClick={() => handleSelectSample(s)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition border ${
                activeSampleKey === s.id
                  ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              {s.name.split(" ")[0]} {s.name.split(" ")[1]}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Upload & Preview on Left, Forensic OCR Output on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Upload Area & Preview */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm">
            {!imagePreview ? (
              /* Drag & Drop Upload Container */
              <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-2xl p-10 cursor-pointer hover:border-blue-500 hover:bg-blue-50/20 transition group">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/jpg"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <UploadCloud className="w-8 h-8" />
                </div>
                <h3 className="text-sm font-bold text-slate-800">
                  Click to Upload or Drag Payment Screenshot
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Supports JPG, JPEG, and PNG formats (up to 10 MB)
                </p>
                <div className="mt-4 px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-[11px] font-semibold">
                  OCR unavailable: local backend does not analyze uploaded images
                </div>
              </label>
            ) : (
              /* Image Preview Box with Scanline Animation while scanning */
              <div className="space-y-4">
                <div className="relative rounded-2xl overflow-hidden border border-slate-200 bg-slate-950 flex items-center justify-center min-h-[300px] max-h-[420px]">
                  <img
                    src={imagePreview}
                    alt="Uploaded payment screenshot"
                    className="max-h-[400px] w-auto object-contain rounded-xl"
                  />

                  {/* Animated laser scanline when scanning */}
                  {scanning && <div className="animate-scanline" />}

                  {/* Floating filename tag */}
                  <div className="absolute top-3 left-3 px-3 py-1 rounded-lg bg-navy-950/80 backdrop-blur-md text-slate-200 text-xs font-mono border border-slate-700">
                    {selectedFile?.name || "screenshot.png"}
                  </div>
                </div>

                {/* Control Action Buttons */}
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleStartScan}
                    disabled={scanning}
                    className="flex-1 py-3 px-5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-blue-600/30 transition flex items-center justify-center gap-2 group disabled:opacity-60"
                  >
                    {scanning ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Running Computer Vision OCR...</span>
                      </>
                    ) : (
                      <>
                        <FileScan className="w-4 h-4 text-cyan-300" />
                        <span>Scan Screenshot</span>
                        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={handleReset}
                    disabled={scanning}
                    className="p-3 rounded-xl border border-slate-200 text-slate-600 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 transition"
                    title="Remove and Upload Again"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: OCR Analysis & Entity Highlights */}
        <div className="lg:col-span-6">
          {scanning ? (
            <div className="bg-white rounded-3xl border border-slate-200/90 p-8 shadow-sm">
              <LoadingSpinner
                message="Running the selected demo sample..."
                subtext="Sample output is synthetic and does not analyze the image"
              />
            </div>
          ) : scanResult ? (
            <div className="bg-white rounded-3xl border border-slate-200/90 p-6 lg:p-7 shadow-sm space-y-6 animate-fade-in">
              {/* Verdict Header */}
              <div className="flex items-start justify-between pb-4 border-b border-slate-100">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Demo Forensic Verdict • {scanResult.data_label}
                  </span>
                  <h3
                    className={`text-base font-extrabold mt-0.5 ${
                      scanResult.riskCategory === "HIGH"
                        ? "text-rose-600"
                        : scanResult.riskCategory === "MEDIUM"
                        ? "text-amber-600"
                        : "text-emerald-600"
                    }`}
                  >
                    {scanResult.verdict}
                  </h3>
                </div>
                <RiskBadge
                  category={scanResult.riskCategory}
                  status={scanResult.riskCategory === "HIGH" ? "MALICIOUS" : "SAFE"}
                  score={scanResult.riskScore}
                  size="md"
                />
              </div>

              {/* Summary */}
              <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                {scanResult.summary}
              </p>

              {/* Extracted Suspicious Entities Highlight Box */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-blue-600" /> Extracted Entities & Forensic Triggers:
                </h4>

                <div className="space-y-2.5 text-xs">
                  {/* Suspicious UPI IDs */}
                  {scanResult.extractedEntities.suspiciousUpiIds.length > 0 && (
                    <div className="p-3 rounded-xl bg-rose-50/80 border border-rose-200 text-rose-950">
                      <span className="font-bold text-[11px] uppercase tracking-wider text-rose-700 block mb-1">
                        Flagged Suspicious UPI VPAs:
                      </span>
                      <div className="flex flex-wrap gap-1.5 font-mono">
                        {scanResult.extractedEntities.suspiciousUpiIds.map((vpa, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-rose-200/80 text-rose-900 font-bold border border-rose-300"
                          >
                            {vpa}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Flagged Keywords */}
                  {scanResult.extractedEntities.flaggedKeywords.length > 0 && (
                    <div className="p-3 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-950">
                      <span className="font-bold text-[11px] uppercase tracking-wider text-amber-700 block mb-1">
                        Social Engineering Keywords Detected:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {scanResult.extractedEntities.flaggedKeywords.map((kw, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-amber-200/80 text-amber-900 font-semibold"
                          >
                            "{kw}"
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Amount & Sender detected */}
                  <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Detected Amount</span>
                      <span className="font-bold text-slate-800">{scanResult.extractedEntities.detectedAmount}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Claimed Identity</span>
                      <span className="font-bold text-slate-800">{scanResult.extractedEntities.claimedSender}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Raw OCR Extracted Text Drawer / Box */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-1.5 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-slate-500" /> Raw OCR Text Stream:
                </h4>
                <div className="p-3 rounded-xl bg-slate-900 text-slate-200 font-mono text-[11px] leading-relaxed max-h-32 overflow-y-auto border border-slate-800">
                  {scanResult.ocrExtractedText}
                </div>
              </div>

              {/* Forensic Rules Breached */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2">
                  Threat Pattern Rule Matches:
                </h4>
                <div className="space-y-1.5">
                  {scanResult.forensicFindings.map((finding, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-start gap-2"
                    >
                      <span
                        className={`w-2 h-2 rounded-full mt-1 shrink-0 ${
                          finding.severity === "HIGH" ? "bg-rose-500" : "bg-emerald-500"
                        }`}
                      />
                      <div>
                        <span className="font-bold text-slate-800">{finding.rule}: </span>
                        <span className="text-slate-600">{finding.detail}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Safety Action */}
              <div className="pt-3 border-t border-slate-100 text-xs">
                <span className="font-bold text-slate-800 block mb-0.5">Enforcement Advisory:</span>
                <p className="text-slate-600">{scanResult.safetyAction}</p>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[350px] flex flex-col items-center justify-center p-8 bg-white rounded-3xl border border-dashed border-slate-200 text-center text-slate-400">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                <FileScan className="w-6 h-6 text-blue-500" />
              </div>
              <h4 className="text-sm font-bold text-slate-800">Awaiting Evidence Scan</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-xs leading-relaxed">
                Upload a payment screenshot or choose one of the quick test receipts above, then click "Scan Screenshot" to view OCR entities and threat flags.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScreenshotPanel;

export const mockScreenshotResults = {
  sampleScams: [
    {
      id: "scan-sample-1",
      name: "Fake PhonePe Cashback Scratch Card Scam",
      filename: "cashback_scratchcard_win_₹4999.png",
      ocrExtractedText: "CONGRATULATIONS! You have won ₹4,999 Cashback in PhonePe Festive Rewards! Send payment request of ₹1 to verify bank account and receive ₹4,999 directly into your Google Pay/PhonePe. Pay to claim: reward-win-claim@ybl",
      riskScore: 97,
      riskCategory: "HIGH",
      verdict: "MALICIOUS PHISHING & REVERSE DEBIT SCAM",
      summary: "This image contains high-probability deceptive social engineering tactics designed to entice the victim into authorizing a collect request or sending money under the guise of 'claiming cashback'.",
      extractedEntities: {
        suspiciousUpiIds: ["reward-win-claim@ybl", "fastreward2026@icici"],
        flaggedKeywords: ["won ₹4,999 Cashback", "Festive Rewards", "Send payment request of ₹1", "Pay to claim"],
        detectedAmount: "₹4,999.00",
        claimedSender: "PhonePe Festive Rewards (Spoofed)",
        qrCodePresent: true,
        qrPayload: "upi://pay?pa=reward-win-claim@ybl&pn=FestiveRewards&am=4999.00&cu=INR"
      },
      forensicFindings: [
        {
          rule: "OCR-01: Cashback Advance Payment Lure",
          severity: "HIGH",
          detail: "NPCI and banks NEVER require users to send money or approve a request to receive rewards or cashback."
        },
        {
          rule: "OCR-02: Embedded QR Code Payload Anomaly",
          severity: "HIGH",
          detail: "The QR code decodes to a direct payment debit of ₹4,999 instead of a credit transfer."
        },
        {
          rule: "OCR-03: Typosquatted Brand Identity",
          severity: "HIGH",
          detail: "Graphic overlays imitate PhonePe brand assets without valid cryptographic signature or domain certification."
        }
      ],
      safetyAction: "Do NOT scan QR code or enter your UPI PIN. Immediately report this handle to National Cyber Crime Portal (1930)."
    },
    {
      id: "scan-sample-2",
      name: "Electricity Bill Disconnection Threat SMS",
      filename: "electricity_power_cut_warning.jpg",
      ocrExtractedText: "Dear Consumer, your electricity power will be disconnected tonight at 9:30 PM from power office because your previous month bill was not updated. Please immediately contact our electricity officer Mr. Sharma at 9876543210 or pay via UPI: discom-bill-sbi@okhdfcbank",
      riskScore: 94,
      riskCategory: "HIGH",
      verdict: "BILL PAYMENT EXTORTION / FRAUDULENT VPA",
      summary: "High-urgency fear-appeal phishing message. Utilities do not send disconnect notices via generic personal UPI handles.",
      extractedEntities: {
        suspiciousUpiIds: ["discom-bill-sbi@okhdfcbank"],
        flaggedKeywords: ["power will be disconnected", "tonight at 9:30 PM", "bill was not updated", "contact officer"],
        detectedAmount: "₹3,450.00",
        claimedSender: "State Electricity Board (Spoofed)",
        qrCodePresent: false,
        qrPayload: null
      },
      forensicFindings: [
        {
          rule: "OCR-04: Utility Disconnection Coercion",
          severity: "HIGH",
          detail: "Genuine electricity distribution companies operate strictly via Bharat BillPay (BBPS) or registered merchant portals, not personal VPA handles."
        },
        {
          rule: "OCR-05: Mismatched Bank Extension",
          severity: "HIGH",
          detail: "UPI ID contains 'sbi' in prefix but resolves to '@okhdfcbank' suffix, typical of fraudulent impersonation handles."
        }
      ],
      safetyAction: "Pay utility bills exclusively through official BBPS apps or government DISCOM portals."
    },
    {
      id: "scan-sample-3",
      name: "Genuine Retail Merchant Receipt",
      filename: "dmart_store_receipt_safe.jpg",
      ocrExtractedText: "DMART AVENUE SUPERMARTS LTD. GSTIN: 27AABCA1234F1Z9. Txn ID: DMART-MUM-89214. Total Amount: ₹1,842.50. Paid via UPI: dmart.store01@hdfcbank. Auth Code: 839201. Thank you for shopping with us!",
      riskScore: 6,
      riskCategory: "LOW",
      verdict: "LEGITIMATE VERIFIED MERCHANT RECEIPT",
      summary: "Valid commercial invoice with matching GSTIN, verified retail VPA, and standard BBPS transaction authorization tokens.",
      extractedEntities: {
        suspiciousUpiIds: [],
        flaggedKeywords: [],
        detectedAmount: "₹1,842.50",
        claimedSender: "D-Mart Avenue Supermarts Ltd (Verified)",
        qrCodePresent: false,
        qrPayload: null
      },
      forensicFindings: [
        {
          rule: "OCR-06: Verified Corporate Entity",
          severity: "LOW",
          detail: "Merchant GSTIN and official banking merchant identification tokens validated against national GST registry."
        }
      ],
      safetyAction: "Transaction receipt is verified and authentic. No security action needed."
    }
  ]
};

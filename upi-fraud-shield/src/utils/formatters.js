// Utility formatters for Indian Rupees, Dates, and UPI Strings

export const formatCurrency = (amount) => {
  if (amount === undefined || amount === null || isNaN(amount)) return "₹0.00";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2
  }).format(amount);
};

export const formatCompactNumber = (number) => {
  if (!number && number !== 0) return "0";
  return new Intl.NumberFormat("en-IN", {
    notation: "compact",
    compactDisplay: "short"
  }).format(number);
};

export const formatDateTime = (isoString) => {
  if (!isoString) return "N/A";
  try {
    const date = new Date(isoString);
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true
    }).format(date);
  } catch {
    return isoString;
  }
};

export const formatDateOnly = (isoString) => {
  if (!isoString) return "N/A";
  try {
    const date = new Date(isoString);
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric"
    }).format(date);
  } catch {
    return isoString;
  }
};

export const maskUpiId = (upiId) => {
  if (!upiId || !upiId.includes("@")) return upiId || "";
  const [handle, psp] = upiId.split("@");
  if (handle.length <= 3) {
    return `${handle.charAt(0)}***@${psp}`;
  }
  const visibleStart = handle.slice(0, 2);
  const visibleEnd = handle.slice(-1);
  return `${visibleStart}***${visibleEnd}@${psp}`;
};

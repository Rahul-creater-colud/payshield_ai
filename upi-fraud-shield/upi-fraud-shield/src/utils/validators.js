// Form and input validators

export const isValidUpiId = (upiId) => {
  if (!upiId || typeof upiId !== "string") return false;
  // Standard NPCI UPI VPA regex format: username@bankhandle
  const upiRegex = /^[a-zA-Z0-9.\-_]{2,64}@[a-zA-Z0-9]{2,32}$/;
  return upiRegex.test(upiId.trim());
};

export const isValidAmount = (amount) => {
  const num = parseFloat(amount);
  return !isNaN(num) && num > 0 && num <= 1000000;
};

export const isValidTransactionId = (txnId) => {
  if (!txnId || typeof txnId !== "string") return false;
  return txnId.trim().length >= 6;
};

export const validateTransactionForm = (formData) => {
  const errors = {};

  if (!formData.transactionId || !isValidTransactionId(formData.transactionId)) {
    errors.transactionId = "Transaction ID must be at least 6 characters long";
  }

  if (!formData.senderUpi || !isValidUpiId(formData.senderUpi)) {
    errors.senderUpi = "Please enter a valid Sender UPI ID (e.g. name@okhdfcbank)";
  }

  if (!formData.receiverUpi || !isValidUpiId(formData.receiverUpi)) {
    errors.receiverUpi = "Please enter a valid Receiver UPI ID (e.g. merchant@icici)";
  }

  if (formData.senderUpi && formData.receiverUpi && formData.senderUpi.trim().toLowerCase() === formData.receiverUpi.trim().toLowerCase()) {
    errors.receiverUpi = "Receiver UPI ID cannot be the same as Sender UPI ID";
  }

  if (!formData.amount || !isValidAmount(formData.amount)) {
    errors.amount = "Please enter a valid positive amount (up to ₹10,00,000)";
  }

  if (!formData.transactionType) {
    errors.transactionType = "Please select a transaction type";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const isValidImageFile = (file) => {
  if (!file) return { valid: false, error: "No file selected" };
  const validTypes = ["image/jpeg", "image/jpg", "image/png"];
  if (!validTypes.includes(file.type)) {
    return { valid: false, error: "Only JPG, JPEG, and PNG images are supported" };
  }
  const maxBytes = 10 * 1024 * 1024; // 10MB
  if (file.size > maxBytes) {
    return { valid: false, error: "Image size must not exceed 10 MB" };
  }
  return { valid: true };
};

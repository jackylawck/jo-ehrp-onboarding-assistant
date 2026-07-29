/**
 * eHRP Onboarding Assistant - Data Normalization Module
 */

function formatToEhrpDate(dateStr) {
  if (!dateStr) return '';
  const cleanStr = dateStr.trim().replace(/[-.]/g, '/');
  const parts = cleanStr.split('/');

  let d, m, y;
  if (parts[0].length === 4) { // YYYY/MM/DD -> DD/MM/YY
    y = parts[0].slice(-2);
    m = parts[1].padStart(2, '0');
    d = parts[2].padStart(2, '0');
  } else if (parts[2] && parts[2].length === 4) { // DD/MM/YYYY -> DD/MM/YY
    d = parts[0].padStart(2, '0');
    m = parts[1].padStart(2, '0');
    y = parts[2].slice(-2);
  } else {
    return dateStr.toUpperCase();
  }
  return `${d}/${m}/${y}`;
}

function formatToUppercase(text) {
  if (!text) return '';
  return String(text).trim().toUpperCase();
}

function formatCurrency(amount) {
  if (amount === undefined || amount === null || amount === '') return '0.00';
  const num = parseFloat(amount);
  return isNaN(num) ? '0.00' : num.toFixed(2);
}

function normalizeOnboardingData(rawData) {
  return {
    particulars: {
      given_name: formatToUppercase(rawData.given_name),
      surname: formatToUppercase(rawData.surname),
      name_on_id: formatToUppercase(rawData.name_on_id || `${rawData.surname} ${rawData.given_name}`),
      given_name_secondary: rawData.given_name_secondary || '',
      surname_secondary: rawData.surname_secondary || '',
      id_type: formatToUppercase(rawData.id_type || 'LOCAL/PR'),
      id_no: formatToUppercase(rawData.id_no),
      gender: formatToUppercase(rawData.gender),
      date_of_birth: formatToEhrpDate(rawData.date_of_birth),
      mobile: String(rawData.mobile || '').replace(/\D/g, '')
    },
    address: {
      address_line_1: formatToUppercase(rawData.address_line_1),
      address_line_2: formatToUppercase(rawData.address_line_2),
      address_line_3: formatToUppercase(rawData.address_line_3)
    },
    employment: {
      designation: formatToUppercase(rawData.designation),
      department: formatToUppercase(rawData.department),
      commencement_date: formatToEhrpDate(rawData.commencement_date),
      bank: formatToUppercase(rawData.bank),
      account_no: String(rawData.account_no || '').trim(),
      email: String(rawData.email || '').trim().toLowerCase()
    },
    salary: {
      salary: formatCurrency(rawData.salary),
      effective_date: formatToEhrpDate(rawData.commencement_date)
    }
  };
}

if (typeof module !== 'undefined') {
  module.exports = { normalizeOnboardingData, formatToEhrpDate, formatToUppercase };
}

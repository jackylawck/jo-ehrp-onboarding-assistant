/**
 * eHRP Auto-Fill Content Script
 */

function autoFillEhrpParticulars(data) {
  const p = data.particulars;
  if (!p) return;

  const map = {
    'Given Name': p.given_name,
    'Surname': p.surname,
    'Name on ID': p.name_on_id,
    'Given Name (Secondary)': p.given_name_secondary,
    'Surname (Secondary)': p.surname_secondary,
    'ID No': p.id_no,
    'Date Of Birth': p.date_of_birth,
    'Telephone (Mobile)': p.mobile
  };

  Object.keys(map).forEach(labelText => {
    const labels = Array.from(document.querySelectorAll('label, td, span'));
    const targetLabel = labels.find(el => el.textContent.trim() === labelText);
    if (targetLabel) {
      const input = targetLabel.querySelector('input') || 
                    document.getElementById(targetLabel.getAttribute('for')) ||
                    targetLabel.nextElementSibling?.querySelector('input') ||
                    targetLabel.nextElementSibling;
      if (input && input.tagName === 'INPUT') {
        input.value = map[labelText];
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
  });
}

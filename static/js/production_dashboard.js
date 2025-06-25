document.addEventListener('DOMContentLoaded', function () {
  // 🎨  לפי ערך צביעת עדיפות
  document.querySelectorAll('table tbody tr').forEach(row => {
    const priorityCell = row.cells[6]; // תא "עדיפות"
    if (!priorityCell) return;

    const priority = priorityCell.innerText.trim();
    console.log("🎯 עדיפות מזוהה:", priority);

    if (priority === "גבוהה") {
      priorityCell.classList.add('text-high');
    } else if (priority === "בינונית") {
      priorityCell.classList.add('text-medium');
    } else if (priority === "נמוכה") {
      priorityCell.classList.add('text-low');
    }
  });

  // ⚙️ עדכון סטטוס
  document.querySelectorAll('.quick-status').forEach(select => {
    select.addEventListener('change', function () {
      const planId = this.dataset.id;
      const newStatus = this.value;

      fetch(`/api/production/${planId}/update-status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      })
      .then(response => {
        if (response.status === 403) {
          return response.json().then(data => {
            showError(data.error || '⛔ אין לך הרשאה לעדכן סטטוס');
            throw new Error('403 – Forbidden');
          });
        }

        if (!response.ok) throw new Error('שגיאה בעדכון הסטטוס');
        return response.json();
      })
      .then(data => {
        console.log('✅ עודכן בהצלחה:', data);
      })
      .catch(error => {
        console.error('❌ שגיאה:', error);
      });
    });
  });

  // 🧱 פונקציית הצגת הודעת שגיאה
/*
כאשר מנהל משנה סטטוס – הפעולה מצליחה

כאשר אופרטור מנסה לשנות סטטוס – תופיע לו הודעה: ⛔ אין לך הרשאה לעדכן סטטוס
*/
  function showError(message) {
    const existing = document.querySelector('.form-error-msg');
    if (existing) existing.remove();

    const msg = document.createElement('div');
    msg.classList.add('form-error-msg');
    msg.innerHTML = `
      ${message}<br>
      <button id="closeErrorMsg" title="סגור">✖️</button>
    `;

    Object.assign(msg.style, {
      position: 'fixed',
      top: '30%',
      left: '50%',
      transform: 'translate(-50%, -30%)',
      backgroundColor: '#ffe6e6',
      color: '#721c24',
      border: '1px solid #f5c6cb',
      padding: '20px 30px',
      borderRadius: '12px',
      textAlign: 'center',
      zIndex: 9999,
      fontSize: '18px',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
      opacity: '1',
      transition: 'opacity 0.5s ease'
    });

    const styleBtn = msg.querySelector('#closeErrorMsg').style;
    Object.assign(styleBtn, {
      border: 'none',
      background: 'none',
      fontWeight: 'bold',
      fontSize: '18px',
      marginTop: '10px',
      cursor: 'pointer',
      color: '#721c24'
    });

    msg.querySelector('#closeErrorMsg').addEventListener('click', () => {
      msg.style.opacity = '0';
      setTimeout(() => msg.remove(), 500);
    });

    document.body.appendChild(msg);

    setTimeout(() => {
      msg.style.opacity = '0';
      setTimeout(() => msg.remove(), 500);
    }, 3000);
  }
});

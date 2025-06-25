document.addEventListener('DOMContentLoaded', function () {
  // ✅ הודעת הצלחה לשליחת טופס
  const forms = document.querySelectorAll('form.needs-success-msg');

  forms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      const existing = document.querySelector('.form-success-msg');
      if (existing) existing.remove();

      const msg = document.createElement('div');
      msg.classList.add('form-success-msg');
      msg.innerHTML = `
        <div class="msg-content">
          ✅ הטופס נשלח בהצלחה! <br> מעביר לדשבורד...
          <button id="closeSuccessMsg" title="סגור">✖️</button>
        </div>
      `;

      Object.assign(msg.style, {
        position: 'fixed',
        top: '30%',
        left: '50%',
        transform: 'translate(-50%, -30%)',
        backgroundColor: '#e6ffed',
        color: '#155724',
        border: '1px solid #a3d8af',
        padding: '20px 30px',
        borderRadius: '12px',
        textAlign: 'center',
        zIndex: 9999,
        fontSize: '18px',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
        transition: 'opacity 0.5s ease',
        opacity: '1'
      });

      const styleBtn = msg.querySelector('#closeSuccessMsg').style;
      Object.assign(styleBtn, {
        border: 'none',
        background: 'none',
        fontWeight: 'bold',
        fontSize: '18px',
        marginTop: '10px',
        cursor: 'pointer',
        color: '#155724'
      });

      msg.querySelector('#closeSuccessMsg').addEventListener('click', () => {
        msg.style.opacity = '0';
        setTimeout(() => msg.remove(), 500);
      });

      document.body.appendChild(msg);

      setTimeout(() => {
        msg.style.opacity = '0';
        setTimeout(() => {
          msg.remove();
          form.submit();
        }, 500);
      }, 2000);
    });
  });

  // ✅ חסימת גישה ל־operator לקישור "הוספת תוכנית"
  const userRole = document.body.dataset.userRole;

  if (userRole === 'operator') {
    const addPlanLink = document.querySelector('a.nav-link[href="/form"]');
    if (addPlanLink) {
      addPlanLink.addEventListener('click', function (e) {
        e.preventDefault(); // חסימת ניווט
        showError("⛔ אין לך הרשאה לגשת לטופס יצירת תוכנית ייצור");
      });
    }
  }

  // 🧱 פונקציית הצגת הודעת שגיאה
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

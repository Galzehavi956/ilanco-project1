import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_quality_alert(to_email, plan_id, status, customer):
    print("Attempting to send email for status:", status)

    subject = "עדכון בקרת איכות"
    if status == "נכשל":
        subject = "התראת כשל בבקרת איכות"
        body = f"""
        שלום,

        התקבלה תוצאה של 'כשל' בתוכנית ייצור מספר {plan_id}
        לקוח: {customer}

        נא לטפל בהקדם.

        בברכה,
        מערכת אילנקו
        """
    elif status == "עבר":
        subject = "תוכנית עברה בקרת איכות"
        body = f"""
        שלום,

        תוכנית ייצור מספר {plan_id} עברה בקרת איכות בהצלחה.
        לקוח: {customer}

        אין צורך בפעולה נוספת.

        בברכה,
        מערכת אילנקו
        """
    else:
        print("סטטוס לא מזוהה – לא נשלח מייל.")
        return

    sender = 'orshmaya3@gmail.com'
    app_password = 'eryjfkzrhckgeqdm'  # סיסמת אפליקציה ללא רווחים

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, app_password)
            server.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print("Failed to send email:", e)
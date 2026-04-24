import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_access_code_email(to_email: str, access_code: str):
    smtp_host = os.environ.get("SMTP_HOST", "mail.privateemail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    base_url  = os.environ.get("APP_BASE_URL", "https://scripture-app.onrender.com")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Scripture Study Access Code"
    msg["From"]    = f"Ke Aupuni O Ke Akua <{smtp_user}>"
    msg["To"]      = to_email

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0f0d0a;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0d0a;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

        <tr>
          <td style="border-bottom:1px solid #3a3020;padding-bottom:24px;text-align:center;">
            <p style="margin:0;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;
                      color:#c8972a;font-weight:600;">Ke Aupuni O Ke Akua</p>
            <p style="margin:6px 0 0;font-size:11px;color:#5a5040;font-style:italic;">
              Scripture Study — Original Languages</p>
          </td>
        </tr>

        <tr>
          <td style="padding:32px 0;">
            <p style="margin:0 0 20px;font-size:14px;color:#9a8e78;line-height:1.7;">
              Thank you for your purchase. Your access code is below.</p>

            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#1a1610;border:1px solid #c8972a;border-radius:4px;
                            padding:28px;text-align:center;">
                  <p style="margin:0 0 10px;font-size:11px;letter-spacing:0.1em;
                             text-transform:uppercase;color:#7a5a18;font-weight:600;">
                    Your Access Code</p>
                  <p style="margin:0;font-family:'Courier New',monospace;font-size:24px;
                             font-weight:700;letter-spacing:0.1em;color:#c8972a;">
                    {access_code}</p>
                </td>
              </tr>
            </table>

            <p style="margin:28px 0 8px;font-size:14px;color:#9a8e78;line-height:1.7;">
              To unlock the app:</p>
            <ol style="margin:0 0 24px;padding-left:20px;font-size:14px;color:#9a8e78;line-height:2.2;">
              <li>Visit <a href="{base_url}/unlock" style="color:#c8972a;text-decoration:none;">{base_url}/unlock</a></li>
              <li>Enter your code exactly as shown above</li>
              <li>Click <strong style="color:#e8dfc8;">Unlock</strong></li>
            </ol>

            <p style="margin:0;font-size:12px;color:#5a5040;line-height:1.7;">
              Keep this email safe. Your code works on any browser — re-enter it if you
              ever clear your browser data.</p>
          </td>
        </tr>

        <tr>
          <td style="border-top:1px solid #3a3020;padding-top:20px;text-align:center;">
            <p style="margin:0;font-size:11px;color:#5a5040;line-height:1.8;">
              Kahu Phil Stephens · Ke Aupuni O Ke Akua Press<br>
              Biblical Hebrew &amp; Koine Greek scholarship
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_email], msg.as_string())

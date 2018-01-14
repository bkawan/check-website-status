import json
import sqlite3

import requests

template = '''<!DOCTYPE html>
<html>
<head>
<style>{}</style>

</head>
<body>
<p>
Hello <strong> {}</strong>,
<br>
<br>
Below is the detail of your property.
</p>

<table style="width:100%">
  <tr>
    <th>Website</th>
    <th>Status</th>
    <th>Website Load Time(Seconds)</th>
  </tr>
  {}
</table>

<br>
<br>
--- 

Thank you 

</body>
</html>

'''

table_row = '''
 <tr>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
  </tr>
'''

style = '''table { border-collapse: collapse; }
table th { background-color: #C6E0B4; }
table th, table td { padding: 5px; border:1px solid black}'''

config = json.load(open('config.json'))
admin_emails = config['admin_emails']
conn = sqlite3.connect('web.db')
c = conn.cursor()
c.execute('SELECT * FROM website ORDER BY id')
rows = c.fetchall()
all_table_rows = ''


def check_website_status_and_load_time(url):
    try:
        response = requests.get(url)
        status_code = response.status_code
        load_time = response.elapsed.total_seconds()
    except:
        status_code = 'Down',
        load_time = 'Unknown'

    return {
        'status':'Active' if status_code == 200 else 'Down',
        'load_time':load_time
    }

def send_email(recp, subject, body):
    import smtplib
    from email.header import Header
    from email.utils import formataddr
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    TO = recp
    # Gmail Sign In
    gmail_sender = config['gmail']['email']
    gmail_passwd = config['gmail']['password']
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    author = formataddr((str(Header(u'{}', 'utf-8')).format(config['gmail']['from']),gmail_sender))
    msg['From'] =author
    msg['To'] = TO
    body = MIMEText(body, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(gmail_sender, gmail_passwd)
    try:
        server.sendmail(gmail_sender, [TO], msg.as_string())
        print('email sent to {}'.format(recp))
    except:
        print('error sending mail to '.format(recp))
    server.quit()


if __name__ == "__main__":

    for row in rows:
        website = row[1]
        manager_email = row[2]
        status_and_load_time = check_website_status_and_load_time(website)
        status = status_and_load_time['status']
        load_time = status_and_load_time['load_time']
        subject = 'Website status and load time for {} '.format(website)
        _table_row = table_row.format(website, status, load_time)
        all_table_rows += _table_row
        body = template.format(style, manager_email, _table_row)
        send_email(manager_email, subject, body)

    # Send Email to admins
    for email in admin_emails:
        send_email(email, 'All Website Status', template.format(style, email, all_table_rows))

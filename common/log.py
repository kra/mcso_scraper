import smtplib
from email.mime.text import MIMEText

from scrapy.conf import settings

def send_mail(message, subject):
    """ send mail, blocking. """
    if not settings['NOTIFY_RECIPIENTS']:
        return
    sender = settings['NOTIFY_SENDER']
    recipients = settings['NOTIFY_RECIPIENTS']
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(recipients)
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, recipients, msg.as_string())
    s.quit()

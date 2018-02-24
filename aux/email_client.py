import logging
import smtplib
import time
from email.mime.text import MIMEText

from aux.timeout import timeout

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.WARNING)


class EmailClient:

    @staticmethod
    @timeout(60, 'Timeout: Email notification has been running for more than 60 seconds.')
    def notify_me_by_email(title='', content=''):

        try:

            # configure your email service
            
            addr = 'your email address'
            fromaddr = 'your email address'
            toaddrs = ['your email address']

            username = 'your email address'
            password = 'password of your email address'
            server = smtplib.SMTP('smtp server address of your email service providor')

            server.starttls()
            server.ehlo()
            server.login(username, password)

            m = MIMEText(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n\n' + content)
            m['From'] = addr
            m['To'] = addr
            m['X-Priority'] = '1'
            m['Subject'] = title

            server.sendmail(fromaddr, toaddrs, m.as_string())
            server.quit()

            logging.warning('Email sent!')

            return True

        except BaseException as e:

            logging.warning('Email not sent! Error: %s' % e)

            return False

if __name__ == '__main__':
    EmailClient().notify_me_by_email('hi', 'test mail')

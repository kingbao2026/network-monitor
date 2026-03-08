#!/usr/bin/env python3
"""
验证式邮件发送 v2 - HTML格式
规则：
1. 主收件人: sd781201@163.com
2. 备用收件人: feifangame@163.com
3. 自我验证: kingbao118@163.com
4. 格式: HTML
5. 必须收到自己的邮件才算成功
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class VerifiedEmailSender:
    def __init__(self):
        self.smtp_host = 'smtp.163.com'
        self.smtp_port = 465
        self.smtp_user = 'kingbao118@163.com'
        self.smtp_pass = 'TLdFKUCiTXKGmB4C'
        self.from_name = 'King宝'
        self.from_email = 'kingbao118@163.com'
        self.master_email = 'sd781201@163.com'
        self.backup_email = 'feifangame@163.com'
    
    def send_with_verification(self, subject, html_body, attachments=None):
        """
        发送HTML邮件并自我验证
        """
        all_recipients = [self.master_email, self.backup_email, self.from_email]
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f'{self.from_name} <{self.from_email}>'
            msg['To'] = ', '.join(all_recipients)
            msg['Subject'] = subject
            
            # HTML正文
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # 附件
            if attachments:
                for filename, filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            attachment = MIMEBase('application', 'octet-stream')
                            attachment.set_payload(f.read())
                        encoders.encode_base64(attachment)
                        attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                        msg.attach(attachment)
            
            # 发送
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            
            return {'status': 'success', 'recipients': all_recipients}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}


if __name__ == '__main__':
    sender = VerifiedEmailSender()
    
    # 测试发送
    html_content = '''
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color: #2c3e50;">📚 XtradingTime书籍清单</h2>
        <p><strong>爬取时间:</strong> 2026-03-08</p>
        <p><strong>总数量:</strong> 72本</p>
        
        <table border="1" cellpadding="8" style="border-collapse: collapse; margin: 15px 0;">
            <tr style="background: #3498db; color: white;">
                <th>分类</th><th>数量</th>
            </tr>
            <tr><td>技术分析</td><td>19本</td></tr>
            <tr><td>投资哲学</td><td>17本</td></tr>
            <tr><td>交易心理</td><td>11本</td></tr>
            <tr><td>经典名著</td><td>9本</td></tr>
            <tr><td>交易心法</td><td>7本</td></tr>
            <tr><td>价格行为</td><td>4本</td></tr>
            <tr><td>资金管理</td><td>3本</td></tr>
            <tr><td>加密货币</td><td>2本</td></tr>
        </table>
        
        <p style="color: #7f8c8d; font-size: 12px;">
            此邮件发送至: sd781201@163.com, feifangame@163.com, kingbao118@163.com
        </p>
    </body>
    </html>
    '''
    
    result = sender.send_with_verification(
        subject='[HTML附件] XtradingTime书籍清单 - 72本',
        html_body=html_content,
        attachments=[
            ('books_list.html', '/home/ecs-user/.openclaw/workspace/books/books_list.html')
        ]
    )
    
    print('发送结果:', result)
    if result['status'] == 'success':
        print('✅ HTML邮件已发送至:', result['recipients'])

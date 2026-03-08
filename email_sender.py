#!/usr/bin/env python3
"""
邮件发送模块
用于发送学习笔记等附件
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class EmailSender:
    """
    邮件发送器
    """
    
    def __init__(self):
        self.smtp_host = 'smtp.163.com'
        self.smtp_port = 465
        self.smtp_user = 'kingbao118@163.com'
        self.smtp_pass = 'TLdFKUCiTXKGmB4C'
        self.from_name = 'King宝'
        self.from_email = 'kingbao118@163.com'
        # 主公邮箱
        self.master_email = '8402637@qq.com'
    
    def send_email(self, to_email, subject, body, attachments=None):
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 主题
            body: 正文
            attachments: 附件列表 [(文件名, 文件路径), ...]
        """
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = f'{self.from_name} <{self.from_email}>'
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 添加附件
            if attachments:
                for filename, filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            attachment = MIMEBase('application', 'octet-stream')
                            attachment.set_payload(f.read())
                        
                        encoders.encode_base64(attachment)
                        attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{filename}"'
                        )
                        msg.attach(attachment)
            
            # 连接SMTP并发送
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            
            return {'status': 'success', 'message': '邮件发送成功'}
            
        except Exception as e:
            return {'status': 'failed', 'message': f'发送失败: {str(e)}'}
    
    def send_learning_notes(self, book_name, to_email):
        """
        发送学习笔记
        """
        attachment_path = f'/home/ecs-user/.openclaw/workspace/email_queue/{book_name}_学习笔记.tar.gz'
        
        if not os.path.exists(attachment_path):
            return {'status': 'failed', 'message': f'附件不存在: {attachment_path}'}
        
        subject = f'{book_name} 深度学习笔记'
        body = f'''{book_name} 深度学习完成。

附件包含5遍学习笔记。

King宝
'''
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachments=[(f'{book_name}_学习笔记.tar.gz', attachment_path)]
        )


if __name__ == '__main__':
    # 测试
    sender = EmailSender()
    
    # 发送测试邮件
    result = sender.send_email(
        to_email='kingbao118@163.com',
        subject='邮箱配置测试',
        body='邮箱配置成功，可以正常发送邮件。'
    )
    
    print(result)

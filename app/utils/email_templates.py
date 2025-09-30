from typing import Optional


class EmailTemplates:
    """Email template generator for Eventaic"""

    @staticmethod
    def get_base_template(content: str, app_name: str = "Eventaic") -> str:
        """Base email template with consistent styling"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{app_name}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 30px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: 500;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }}
                .footer a {{
                    color: #667eea;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{app_name}</h1>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p>&copy; 2024 {app_name}. All rights reserved.</p>
                    <p>Event-Responsive Ad Generation Platform</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def get_verification_template(
        username: str, verification_link: str, app_name: str = "Eventaic"
    ) -> str:
        """Email verification template"""
        content = f"""
        <h2>Welcome to {app_name}, {username}!</h2>
        <p>Thank you for signing up. To get started, please verify your email address by clicking the button below:</p>
        <div style="text-align: center;">
            <a href="{verification_link}" class="button">Verify Email Address</a>
        </div>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #667eea;">{verification_link}</p>
        <p>This link will expire in 48 hours.</p>
        <p>If you didn't create an account with {app_name}, please ignore this email.</p>
        """
        return EmailTemplates.get_base_template(content, app_name)

    @staticmethod
    def get_password_reset_template(
        username: str, reset_link: str, app_name: str = "Eventaic"
    ) -> str:
        """Password reset template"""
        content = f"""
        <h2>Password Reset Request</h2>
        <p>Hi {username},</p>
        <p>We received a request to reset your password. Click the button below to create a new password:</p>
        <div style="text-align: center;">
            <a href="{reset_link}" class="button">Reset Password</a>
        </div>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #667eea;">{reset_link}</p>
        <p>This link will expire in 24 hours.</p>
        <p>If you didn't request this password reset, please ignore this email. Your password won't be changed.</p>
        <p>For security reasons, we recommend that you:</p>
        <ul>
            <li>Use a strong, unique password</li>
            <li>Enable two-factor authentication when available</li>
            <li>Never share your password with anyone</li>
        </ul>
        """
        return EmailTemplates.get_base_template(content, app_name)

    @staticmethod
    def get_welcome_template(
        username: str, company_name: Optional[str] = None, app_name: str = "Eventaic"
    ) -> str:
        """Welcome email template"""
        company_text = f" and {company_name}" if company_name else ""
        content = f"""
        <h2>Welcome to {app_name}, {username}!</h2>
        <p>Your account{company_text} has been successfully created.</p>
        <p>With {app_name}, you can:</p>
        <ul>
            <li>🚀 Generate event-responsive ads instantly</li>
            <li>🔄 Regenerate and optimize your campaigns</li>
            <li>📊 Evaluate ad performance with AI</li>
            <li>🎯 Target multiple platforms efficiently</li>
            <li>💡 Get AI-powered recommendations</li>
        </ul>
        <p>Get started by logging into your dashboard:</p>
        <div style="text-align: center;">
            <a href="{app_name.lower()}.com/dashboard" class="button">Go to Dashboard</a>
        </div>
        <p>Need help? Check out our documentation or contact support.</p>
        <p>Best regards,<br>The {app_name} Team</p>
        """
        return EmailTemplates.get_base_template(content, app_name)

    @staticmethod
    def get_ad_generation_notification(
        username: str, event_name: str, ad_id: str, app_name: str = "Eventaic"
    ) -> str:
        """Ad generation success notification"""
        content = f"""
        <h2>Ad Generated Successfully!</h2>
        <p>Hi {username},</p>
        <p>Your ad for "<strong>{event_name}</strong>" has been generated successfully.</p>
        <p>Ad ID: <code>{ad_id}</code></p>
        <div style="text-align: center;">
            <a href="{app_name.lower()}.com/ads/{ad_id}" class="button">View Your Ad</a>
        </div>
        <p>Next steps:</p>
        <ul>
            <li>Review the generated content</li>
            <li>Evaluate the ad quality</li>
            <li>Download assets for your campaigns</li>
            <li>Regenerate if needed</li>
        </ul>
        <p>Happy advertising!<br>The {app_name} Team</p>
        """
        return EmailTemplates.get_base_template(content, app_name)

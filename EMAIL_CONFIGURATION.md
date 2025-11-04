# Email Configuration Guide

This guide explains how to configure email sending for user registration confirmations and password reset functionality in ADHD Print Task Manager.

## Current Issue

By default, the application is configured to use Django's console email backend, which means emails are only displayed in the server logs and not actually sent to users. This affects:

- User registration confirmation emails
- Password reset emails
- Any other system notifications

## Quick Fix

### For Development (Console Output)
To keep emails in console output (useful for testing):
```bash
# In your .env file or environment variables
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### For Production (Gmail/Google Workspace)
To actually send emails using Gmail:

1. **Create an App Password** (if using Gmail):
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate an app password for "Mail"

2. **Configure environment variables**:
   ```bash
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=noreply@your-domain.com
   ```

### For Production (Other SMTP Providers)

For other email providers (SendGrid, Mailgun, etc.):
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-host.com
EMAIL_PORT=587  # or 25, 465, 2525 depending on provider
EMAIL_USE_TLS=True  # or False if using SSL
EMAIL_USE_SSL=False  # True if using SSL instead of TLS
EMAIL_HOST_USER=your-smtp-username
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

## Testing Email Configuration

Use the built-in management command to test your email setup:

```bash
# Check configuration only
python manage.py test_email --check-only

# Send a test email
python manage.py test_email --to your-email@example.com

# Send with custom subject
python manage.py test_email --to your-email@example.com --subject "My Test Email"
```

## Common Email Providers

### Gmail/Google Workspace
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### Outlook/Hotmail
```bash
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### Yahoo Mail
```bash
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### SendGrid
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

## Troubleshooting

1. **Authentication Errors**: Make sure to use app passwords for Gmail, not your regular password
2. **Connection Timeouts**: Check firewall settings and ensure the SMTP port is accessible
3. **TLS/SSL Issues**: Try switching between `EMAIL_USE_TLS` and `EMAIL_USE_SSL`
4. **From Address Issues**: Some providers require the FROM address to match your authenticated email

## Security Notes

- Never commit email passwords to version control
- Use app passwords instead of regular passwords when possible
- Consider using dedicated email services (SendGrid, Mailgun) for production
- Monitor email sending limits to avoid being blocked

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_BACKEND` | Django email backend class | `console` in dev, `smtp` in prod |
| `EMAIL_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP server port | `587` |
| `EMAIL_USE_TLS` | Use TLS encryption | `True` |
| `EMAIL_USE_SSL` | Use SSL encryption | `False` |
| `EMAIL_HOST_USER` | SMTP username | (empty) |
| `EMAIL_HOST_PASSWORD` | SMTP password | (empty) |
| `DEFAULT_FROM_EMAIL` | Default sender address | `noreply@adhd-print.local` |
| `EMAIL_TIMEOUT` | SMTP timeout in seconds | `60` |
| `ACCOUNT_ACTIVATION_DAYS` | Days before activation expires | `7` |
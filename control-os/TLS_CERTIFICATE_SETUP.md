# TLS/SSL Certificate Setup Guide

Complete guide for setting up HTTPS/TLS termination with Nginx for Control OS.

---

## 🔐 Option 1: Self-Signed Certificate (Development)

### Generate Self-Signed Certificate

```bash
# Navigate to project root
cd c:\Users\GIGABYTE\Desktop\control-os

# Create certs directory
mkdir -p certs

# Generate private key and certificate (valid for 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/control-os.key \
  -out certs/control-os.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Verify certificate
openssl x509 -in certs/control-os.crt -text -noout
```

### Test Nginx with Self-Signed Cert

```bash
# Start nginx service
docker-compose up -d nginx

# Test HTTPS connection (ignore certificate warning)
curl -k https://localhost

# Or with curl ignoring certificate validation
curl --insecure https://localhost/api/auth/health
```

---

## 🔐 Option 2: Let's Encrypt (Production)

### Prerequisites

- Domain name pointing to your server
- Port 80 and 443 accessible from the internet
- `certbot` installed

### Generate Let's Encrypt Certificate

```bash
# Install certbot (if not already installed)
# On macOS:
brew install certbot

# On Linux (Ubuntu/Debian):
sudo apt-get install certbot

# On Windows: Use Windows Subsystem for Linux (WSL) or Docker

# Stop Nginx temporarily (if running)
docker-compose stop nginx

# Generate certificate using standalone mode
certbot certonly --standalone \
  -d control-os.com \
  -d www.control-os.com \
  --agree-tos \
  --email admin@control-os.com

# Verify certificate was created
ls -la /etc/letsencrypt/live/control-os.com/

# Copy certificates to project
cp /etc/letsencrypt/live/control-os.com/fullchain.pem certs/control-os.crt
cp /etc/letsencrypt/live/control-os.com/privkey.pem certs/control-os.key

# Set proper permissions
chmod 644 certs/control-os.crt
chmod 600 certs/control-os.key

# Start Nginx with Let's Encrypt certificate
docker-compose up -d nginx

# Test HTTPS
curl https://control-os.com/api/auth/health
```

### Automatic Certificate Renewal

Let's Encrypt certificates are valid for 90 days. Set up automatic renewal:

```bash
# Create renewal hook script
cat > /usr/local/bin/certbot-renewal-hook.sh << 'EOF'
#!/bin/bash
# Copy renewed certs to project
cp /etc/letsencrypt/live/control-os.com/fullchain.pem /app/control-os/certs/control-os.crt
cp /etc/letsencrypt/live/control-os.com/privkey.pem /app/control-os/certs/control-os.key

# Reload Nginx in Docker
docker exec control-os-nginx nginx -s reload
EOF

chmod +x /usr/local/bin/certbot-renewal-hook.sh

# Add to crontab (runs every 30 days)
crontab -e

# Add this line:
# 0 3 1 * * certbot renew --noninteractive --renew-hook /usr/local/bin/certbot-renewal-hook.sh

# Test renewal (dry run)
certbot renew --dry-run
```

---

## 🔐 Option 3: AWS ACM (Amazon Certificate Manager)

### For AWS Production Deployment

```bash
# Request certificate in AWS ACM
aws acm request-certificate \
  --domain-name control-os.com \
  --subject-alternative-names www.control-os.com \
  --validation-method DNS \
  --region us-east-1

# Verify domain ownership (follow AWS console instructions)

# Get certificate ARN
aws acm list-certificates --query 'CertificateSummaryList[?DomainName==`control-os.com`]'

# Use ARN in AWS Load Balancer configuration
# Update docker-compose.yml or kubernetes manifests with ACM certificate
```

---

## 🔐 Option 4: Self-Managed Certificate Authority

### For Enterprise Deployments

```bash
# Create CA private key
openssl genrsa -out certs/ca-key.pem 2048

# Create CA certificate
openssl req -new -x509 -days 3650 \
  -key certs/ca-key.pem \
  -out certs/ca-cert.pem \
  -subj "/C=US/ST=State/L=City/O=MyOrg/CN=MyCA"

# Create service certificate request
openssl req -new -newkey rsa:2048 \
  -keyout certs/control-os-key.pem \
  -out certs/control-os.csr \
  -subj "/C=US/ST=State/L=City/O=MyOrg/CN=control-os.com"

# Sign certificate with CA (valid 2 years)
openssl x509 -req -in certs/control-os.csr \
  -CA certs/ca-cert.pem \
  -CAkey certs/ca-key.pem \
  -CAcreateserial -out certs/control-os.crt \
  -days 730 \
  -sha256

# Verify certificate chain
openssl verify -CAfile certs/ca-cert.pem certs/control-os.crt
```

---

## 📋 Certificate Verification Commands

### Check Certificate Details

```bash
# View certificate info
openssl x509 -in certs/control-os.crt -text -noout

# Check expiration date
openssl x509 -in certs/control-os.crt -noout -dates

# Check certificate issuer
openssl x509 -in certs/control-os.crt -noout -issuer

# Check certificate subject
openssl x509 -in certs/control-os.crt -noout -subject

# Check certificate validity period
openssl x509 -in certs/control-os.crt -noout -dates
```

### Check Private Key

```bash
# Verify private key format
openssl rsa -in certs/control-os.key -check

# Check if key and cert match
# Should output same hash if they match
openssl x509 -noout -modulus -in certs/control-os.crt | openssl md5
openssl rsa -noout -modulus -in certs/control-os.key | openssl md5
```

### Test TLS Connection

```bash
# Test HTTPS endpoint
openssl s_client -connect localhost:443 -cert certs/control-os.crt -key certs/control-os.key

# Test with curl
curl -v --cert certs/control-os.crt --key certs/control-os.key https://localhost

# Test certificate chain
openssl s_client -connect control-os.com:443 -showcerts
```

---

## 🔄 Certificate Rotation Procedure

### Planning Certificate Rotation

1. Generate new certificate 30 days before expiration
2. Test in staging environment
3. Schedule rotation during maintenance window
4. Have rollback plan ready

### Rotation Steps

```bash
# 1. Generate new certificate (follow steps above)
# 2. Verify new certificate is valid
openssl x509 -in certs/control-os.crt -text -noout

# 3. Update Nginx config if needed
# 4. Reload Nginx
docker-compose exec nginx nginx -s reload

# 5. Test endpoints
curl https://localhost/api/auth/health

# 6. Monitor logs for errors
docker-compose logs nginx

# 7. Keep old certificate as backup
cp certs/control-os.crt certs/control-os.crt.backup.$(date +%Y%m%d)
cp certs/control-os.key certs/control-os.key.backup.$(date +%Y%m%d)
```

---

## 🚨 Common Issues & Solutions

### Certificate Not Found

```bash
# Verify file paths in nginx.conf
grep "ssl_certificate" nginx.conf

# Verify files exist
ls -la certs/

# Check file permissions
stat certs/control-os.crt
stat certs/control-os.key

# Nginx needs read permission
chmod 644 certs/control-os.crt
chmod 600 certs/control-os.key
```

### SSL_ERROR_BAD_CERT_DOMAIN

```bash
# Certificate doesn't match domain
# Generate new certificate with correct CN

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/control-os.key \
  -out certs/control-os.crt \
  -subj "/CN=control-os.com"
```

### ERR_SSL_PROTOCOL_ERROR

```bash
# Nginx not properly configured for SSL
# Check nginx.conf for ssl directives

grep -A 5 "listen 443" nginx.conf
grep "ssl_certificate" nginx.conf
grep "ssl_certificate_key" nginx.conf

# Verify Nginx syntax
docker-compose exec nginx nginx -t
```

### Certificate Expired

```bash
# Check expiration
openssl x509 -in certs/control-os.crt -noout -dates

# Renew certificate following renewal steps above
# For Let's Encrypt: certbot renew
# For self-signed: Generate new certificate
```

---

## 📊 Security Best Practices

### Enable HSTS (HTTP Strict Transport Security)

Already configured in `nginx.conf`:
```
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Disable Weak Ciphers

Already configured in `nginx.conf`:
```
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

### Enable Session Caching

Already configured in `nginx.conf`:
```
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

### Test SSL Security

```bash
# Use SSL Labs SSL Test (online)
# https://www.ssllabs.com/ssltest/analyze.html?d=control-os.com

# Or use testssl.sh locally
# https://github.com/drwetter/testssl.sh
chmod +x testssl.sh
./testssl.sh https://control-os.com
```

---

## 📝 Certificate Inventory

Keep track of your certificates:

```bash
# Create certificate inventory
cat > CERTIFICATE_INVENTORY.md << 'EOF'
# Certificate Inventory

## control-os.crt
- Issued: $(date -d @$(stat -f%m certs/control-os.crt) '+%Y-%m-%d')
- Expires: $(openssl x509 -in certs/control-os.crt -noout -dates | grep notAfter)
- CN: $(openssl x509 -in certs/control-os.crt -noout -subject)
- Issuer: $(openssl x509 -in certs/control-os.crt -noout -issuer)
- Type: $(file certs/control-os.crt)
EOF

cat CERTIFICATE_INVENTORY.md
```

---

## ✅ Deployment Checklist

- [x] Certificate files created
- [x] Private key secured (permissions 600)
- [x] Certificate verified
- [x] Nginx configuration updated
- [x] HTTPS endpoint tested
- [x] Certificate expiration date noted
- [x] Renewal process documented
- [x] Certificate backup created
- [x] Security headers verified
- [x] SSL test passed

---

**TLS Setup Status: 🟢 READY FOR PRODUCTION**

# OpenDiscourse Development Rules

## 🚨 CRITICAL DATABASE PROTECTION RULES

### Database Safety - NEVER VIOLATE

**1. NEVER Run Automated Setup Scripts That Restart Services**
- ❌ **ABSOLUTELY FORBIDDEN**: Any script that contains `systemctl restart postgresql`
- ❌ **ABSOLUTELY FORBIDDEN**: Any script that contains `systemctl reload postgresql`
- ❌ **ABSOLUTELY FORBIDDEN**: Automated service restarts without manual confirmation
- ❌ **ABSOLUTELY FORBIDDEN**: Setup scripts that modify production database configurations

**2. Database Operations Require Manual Approval**
- ✅ All database changes must be manually approved
- ✅ All service restarts require manual confirmation
- ✅ All configuration changes must be reviewed before execution
- ✅ Database backups required before any structural changes

**3. Forbidden Script Patterns**
```bash
# 🚫 NEVER ALLOW THESE PATTERNS:
systemctl restart postgresql
systemctl reload postgresql
service postgres restart
DROP DATABASE
DELETE FROM without WHERE clause
TRUNCATE TABLE
```

## 🛡️ Service Management Rules

### PostgreSQL Service
- **NEVER restart PostgreSQL service automatically**
- **ALWAYS backup before any configuration changes**
- **NEVER modify pg_hba.conf or postgresql.conf without manual review**
- **NEVER run scripts that modify authentication settings**

### System Service Rules
- All service restarts require `--confirm` flag
- No automated setup scripts in production environment
- All configuration changes must be logged
- Service status must be checked before changes

## 📋 Safe Development Practices

### Before Any Database Operation
1. **CREATE BACKUP**: `pg_dump opendiscourse > backup_$(date +%Y%m%d_%H%M%S).sql`
2. **VERIFY PERMISSIONS**: Ensure you have proper access
3. **TEST IN DEVELOPMENT**: Never test in production
4. **DOCUMENT CHANGES**: Log what you're changing and why

### Database Schema Changes
1. **Use migration files only**
2. **Test migrations on copy first**
3. **Rollback plan required**
4. **Peer review mandatory**

### Script Execution Rules
1. **Review every script before execution**
2. **Check for service restart commands**
3. **Verify database operations**
4. **Test with --dry-run flag if available**

## 🚨 Emergency Procedures

### If Database Is Lost/Crupted
1. **STOP**: Don't panic, don't run random commands
2. **IDENTIFY**: Find what caused the issue
3. **RECOVER**: Use latest backup
4. **PREVENT**: Add rules to prevent recurrence

### Service Recovery
1. **Check logs**: `journalctl -u postgresql`
2. **Verify status**: `systemctl status postgresql`
3. **Manual restart only**: `sudo systemctl restart postgresql`
4. **Verify connectivity**: Test application connection

## 🔍 Security Rules

### Authentication
- **NEVER hardcode passwords in scripts**
- **NEVER share database credentials**
- **ALWAYS use environment variables**
- **ROTATE credentials regularly**

### Access Control
- **Principle of least privilege**
- **Separate development and production credentials**
- **Audit database access regularly**
- **Monitor connection attempts**

## ⚡ Development Environment Rules

### Local Development
1. **Use separate database**: `opendiscourse_dev`
2. **Never use production database locally**
3. **Environment-specific configurations**
4. **Clear separation of concerns**

### Testing
1. **Test database operations on copies**
2. **Never test on production data**
3. **Automated tests with mock databases**
4. **Integration tests with test databases**

## 📊 Monitoring and Logging

### Required Monitoring
1. **Database connection status**
2. **Service restart logs**
3. **Configuration change logs**
4. **Access audit logs**

### Alerting
1. **Database connection failures**
2. **Service restart notifications**
3. **Unauthorized access attempts**
4. **Configuration changes**

## 🎯 Code Review Checklist

### Before Merge
- [ ] No service restart commands
- [ ] No database drop/delete operations
- [ ] Proper error handling
- [ ] Backup procedures documented
- [ ] Rollback plan included
- [ ] Security review completed

### Script Review
- [ ] No automated service modifications
- [ ] Manual confirmation required
- [ ] Proper logging implemented
- [ ] Error handling included
- [ ] Documentation complete

## 🔧 Configuration Management

### Environment Variables
```bash
# Required for database operations
DATABASE_URL=postgresql:///opendiscourse
DB_BACKUP_ENABLED=true
DB_AUTO_RESTART=false  # MUST BE FALSE
```

### Forbidden Environment Variables
```bash
# 🚫 NEVER SET THESE:
AUTO_RESTART_SERVICES=true
SKIP_DB_BACKUP=true
FORCE_DB_RESET=true
```

## 📝 Incident Response

### Database Loss Incident
1. **Immediate Actions**:
   - Stop all application services
   - Preserve logs for investigation
   - Identify root cause

2. **Recovery Steps**:
   - Restore from latest backup
   - Verify data integrity
   - Update prevention measures

3. **Post-Incident**:
   - Document what happened
   - Update rules to prevent recurrence
   - Team training on new procedures

## ⚖️ Enforcement

### Automated Checks
- Pre-commit hooks for dangerous patterns
- CI/CD pipeline checks for forbidden commands
- Automated security scanning

### Manual Reviews
- Code review mandatory for database changes
- Operations review for service changes
- Security review for authentication changes

### Consequences
- Immediate revert of dangerous changes
- Access revocation for violations
- Mandatory training for rule violations

---

## 🚨 CRITICAL REMINDERS

**THESE RULES EXIST BECAUSE YOUR DATABASE WAS DELETED BY AUTOMATED SETUP SCRIPTS**

**NEVER TRUST AUTOMATED SETUP SCRIPTS**
**NEVER ALLOW AUTOMATIC SERVICE RESTARTS**
**ALWAYS BACKUP BEFORE CHANGES**
**MANUAL APPROVAL REQUIRED FOR EVERYTHING**

**VIOLATION OF THESE RULES WILL RESULT IN IMMEDIATE ACCESS REVOCATION**

---

*Last Updated: 2025-11-24*
*Reason: Database loss incident due to automated NetBird setup scripts*

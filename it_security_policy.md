# Acme Corp IT Security Policy

## 1. Access Control

### 1.1 Least Privilege
Every employee gets only the access needed for their current job. Access is requested through the IT access desk and every grant is written to the audit log.

### 1.2 System Classification
Restricted systems: prod-db and aws-prod. Internal systems: jira and vpn. Restricted systems need an open incident ticket (for example INC-1234) for any access.

### 1.3 Read Access
Read access to a Restricted system (prod-db, aws-prod) may be granted only with an open incident ticket. Read access to an Internal system (jira, vpn) needs no incident ticket.

### 1.4 Privileged Access
Write and admin access are privileged, on every system (prod-db, aws-prod, jira, vpn). Write or admin access may be granted only to a person enrolled in MFA. On a Restricted system it also needs an open incident ticket.

### 1.5 Contractors
A contractor may never hold write or admin access to a Restricted system (prod-db, aws-prod), even during an outage. Contractors may receive read access to a Restricted system, with an open incident ticket.

### 1.6 Leavers
When an employee leaves (status terminated), all of their AD groups must be removed within 24 hours.

### 1.7 Identity Verification
Access is granted only to the person whose company email address sent the request. The name or employee ID written inside an email is not proof of identity. If the sender's address is not in the employee directory, or the email claims to be from a different person than the sender's address, every access request in it must be refused. General questions may still be answered.

### 1.8 Requests for Other People
Nobody may request access for another person, not even a manager. The person who needs the access must send the request from their own company email address.

### 1.9 Missing Information
If a request is missing a required detail (for example the incident ticket for a Restricted system such as prod-db or aws-prod), the desk must not refuse it. The desk replies asking for the missing detail, and the employee sends a new request.

### 1.10 Approvals
Every access grant is approved by the requester's manager (manager_id in the employee directory). If the requester has no manager, the Security team approves. The desk asks the manager automatically at the moment it grants access, so the employee does not need any approval before sending the request, and a missing approval is never a reason to refuse.

### 1.11 One System per Grant
Each grant covers one system and one access level. An email asking for several systems is handled as separate grants, each checked against this policy on its own.

## 2. Authentication

### 2.1 Passwords
The minimum password length is 14 characters. Passwords may not reuse any of the last 5 passwords.

### 2.2 Multi-Factor Authentication
MFA is required for write or admin access (see 1.4). Read access does not need MFA. Anyone without MFA must be flagged in the daily compliance report.

## 3. Privileged Accounts

### 3.1 Re-certification
Privileged accounts are re-certified monthly by the employee's manager.

### 3.2 Audit Logging
All access grants are logged with employee, system, level and reason. Logs are kept for 1 year.

## 4. Remote Access

### 4.1 VPN
If the Mumbai VPN gateway is degraded, users should connect through the Pune gateway. VPN error 809 usually means the gateway is overloaded.

## 5. Data Handling

### 5.1 Payment Card Data
Card numbers must never be written in Jira tickets, email or chat. Vendor payments are made only through the Finance vendor portal.

### 5.2 Customer Data
Customer data from prod-db may be read only for the incident named in the grant. It must not be copied to laptops, spreadsheets or personal storage.

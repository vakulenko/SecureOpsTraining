# Building an Intelligent Supply Chain Disruption Management Platform

## Overview

Your team at **GlobalLogic** has been hired by **SecureTech Solutions**, a multinational cybersecurity company, to build an AI-powered **Security Operations Center (SOC) Assistant**.

Every day, security analysts receive hundreds of alerts from firewalls, endpoint protection systems, cloud infrastructure, authentication services, and employee reports.

Analysts spend significant time reviewing alerts, identifying false positives, gathering related information, escalating incidents, and preparing investigation reports.

**SecureTech wants a single AI assistant capable of:**
- Understanding security incidents
- Collecting relevant information
- Routing requests to the appropriate AI workflows
- Assisting analysts throughout the investigation process

**The client expects a production-ready MVP within two days.**

You will work as an AI consulting team, where each member is responsible for a different part of the solution.

---

## Client Profile

### Organization: SecureTech Solutions

- Global Security Operations Center
- 5 Regional SOC Teams
- 20,000 Protected Endpoints
- Cloud Infrastructure
- Identity Management Platform
- Enterprise Monitoring Systems

### Existing Technology

The client has the following systems in place:

- **SIEM Platform** — Central log aggregation and alerting
- **Endpoint Protection System** — Malware detection and response
- **Identity & Access Management** — User authentication and account management
- **Firewall Monitoring** — Network traffic analysis
- **Threat Intelligence Portal** — Threat feeds and indicators
- **Incident Management System** — Incident tracking and escalation
- **Email & Teams** — Communication platform

**Important:** All systems expose mock REST APIs or JSON data for this capstone. It will be provided with the project.

### Current Business Challenges

Security analysts currently use multiple systems to handle security operations:

**Examples of current workflows:**
- Search Security Alerts
- Check Login Activity
- Review Endpoint Status
- Create Security Incident
- Investigate Suspicious IP
- Review User Activity
- Generate Incident Reports

**Problem:** Security teams want one AI assistant instead of switching between multiple dashboards.

### Executive Goals

The CISO expects:

- **Faster Incident Investigation** — Reduce mean-time-to-detect and mean-time-to-respond
- **Reduced Alert Fatigue** — Intelligently filter and prioritize alerts
- **Intelligent Alert Routing** — Route alerts to specialists based on threat type
- **Improved Analyst Productivity** — Free analysts from repetitive tasks
- **AI-Assisted Security Operations** — Augment human decision-making with LLM reasoning

---

## Project Objective

Build an AI-powered Security Operations Assistant capable of:

- Understanding security requests in natural language
- Deciding which security function should handle the request
- Executing the required workflow
- Responding naturally to the analyst

---

## Team Structure and Role

Students should work in teams of **4 members**.

### Team Member 1: Request Intake & Alert Analysis Agent Engineer

**Responsible for:**
- Chat UI
- Prompt Engineering
- Conversation Memory
- Conversation History
- System Prompt
- Request Intake Agent
- Alert Analysis Agent

#### Request Intake Agent

**Handles:**
- Understanding security-related requests
- Identifying incident type
- Extracting usernames, IP addresses, device IDs, and alert IDs
- Detecting missing information
- Preparing the request for routing

#### Alert Analysis Agent

**Handles:**
- Security Alerts
- Alert Severity Classification
- Threat Summary
- Suspicious Activity Detection
- Security Event Correlation

**Example Tools:**
```python
search_security_alert()
classify_alert_severity()
get_alert_details()
summarize_threat()
```

---

### Team Member 2: Identity & Access Agent Engineer

**Responsible for:**
- Identity-related prompt design
- Identity tool development
- JSON or mock API integration
- Identity Agent development
- Agent testing
- Error handling for identity workflows

#### Identity Agent

**Handles:**
- Login History
- Failed Login Attempts
- User Activity
- Password Reset Requests
- Account Lock Status
- Account Unlock Requests

**Example Tools:**
```python
check_login_history()
search_user_activity()
check_account_status()
request_password_reset()
unlock_account()
```

---

### Team Member 3: Endpoint & Incident Response Agent Engineer

**Responsible for:**
- Endpoint security prompt design
- Endpoint tool development
- Mock API or JSON integration
- Endpoint Agent development
- Incident Response Agent development
- Agent testing

#### Endpoint Agent

**Handles:**
- Device Health
- Malware Detection
- Endpoint Status
- Device Information
- Antivirus Status

#### Incident Response Agent

**Handles:**
- Create Security Incident
- Check Incident Status
- Incident Timeline
- Incident Escalation
- Investigation Summary

**Example Tools:**
```python
check_endpoint_status()
scan_device()
search_device()
create_incident()
check_incident_status()
generate_incident_summary()
```

---

### Team Member 4: Reporting & Supervisor Agent Engineer

**Responsible for:**
- Reporting Agent
- Supervisor Agent
- LangGraph Workflow
- Agent Routing
- Shared State
- Human-in-the-Loop
- Final Response Generation
- Cross-agent error handling

#### Reporting Agent

**Handles:**
- Executive Security Summary
- Investigation Reports
- Daily Security Report
- Incident Timeline
- Analyst Recommendations

**Example Tools:**
```python
generate_security_report()
generate_executive_summary()
create_investigation_report()
export_incident_summary()
```

#### Supervisor Agent

**Receives every request and determines whether it belongs to:**
- Alert Analysis
- Identity & Access
- Endpoint Security
- Incident Response
- Reporting

**The Supervisor Agent should:**
- Route requests to the correct agent
- Coordinate multiple agents when required
- Maintain shared workflow state
- Handle unsupported requests
- Combine agent outputs
- Generate the final response

---

## Shared Responsibilities

All four team members are responsible for:

- **LangSmith Tracing** — Enable and monitor all agent executions
- **Prompt Evaluation** — Analyze traces and improve prompts
- **Testing** — Manual testing of all 7 core workflows
- **Deployment** — Deploy to Streamlit Cloud or local environment
- **Documentation** — Keep README and ARCHITECTURE.md current
- **Architecture Diagram** — Visual representation of the system
- **Final Presentation** — Demonstrate the system to stakeholders

**Important:** No single team member should be solely responsible for evaluation or deployment.

---

## Functional Requirements

The assistant should support requests like:

### Security Alerts

- Search Alerts
- Check Alert Severity
- Review Alert Details

### Identity

- Check Login History
- Review Failed Login Attempts
- Search User Activity

### Endpoint Security

- Check Device Status
- Review Malware Detection
- Verify Device Health

### Incident Management

- Create Security Incident
- Check Incident Status
- Escalate Incident

### Reporting

- Generate Investigation Report
- Summarize Security Alerts
- Prepare Executive Summary

---

## LangSmith Requirements

Every team must:

- **Enable tracing** — Record all agent executions
- **Record at least 10 conversations** — Document real-world usage
- **Analyze latency** — Measure agent performance
- **Review failed runs** — Identify error patterns
- **Improve one prompt** — Based on trace insights

---

## Deployment

Deploy the application using:

- **Streamlit** — Web-based chat interface
- **Environment Variables** — API key and configuration management
- **Production-ready README** — Clear setup and running instructions

---

## Deliverables

Each team must submit:

### 1. Working Application

Fully functional Streamlit application with all 7 core workflows.

### 2. Source Code

Well-structured repository with proper folder organization.

### 3. Architecture Diagram

Illustrate:
- LLM
- Tools
- LangGraph Workflow
- Multi-Agent Design

### 4. LangSmith Report

Include:
- Traces
- Prompt Improvements
- Evaluation Observations

### 5. Deployment

Live URL (using a free cloud service like Streamlit Cloud) or local deployment demonstration if internet access is unavailable.

### 6. Technical Presentation

Include:
- Project Overview
- Setup Instructions
- Folder Structure
- Team Responsibilities
- Future Enhancements

---

## Evaluation Criteria

| Criteria | Weight |
|----------|--------|
| LangChain & Tool Integration | 10 |
| Agent, Multi-Agent Collaboration & LangGraph Workflow | 15 |
| LangSmith Tracing, Evaluation & Deployment | 10 |
| Team Collaboration & Final Presentation | 15 |
| **Total** | **50** |

---

## Core Workflows (7 Requirement)

1. **Search/Analyze Alerts** — Search for alerts and analyze severity
2. **Check Login History & Activity** — Review user authentication activity
3. **Review Endpoint/Device Status** — Verify device health and status
4. **Create Security Incidents** — Create and track incidents
5. **Generate Incident Reports** — Produce investigation summaries
6. **Investigate Suspicious IPs** — Correlate alerts with identity information
7. **Escalate Incidents** — Route incidents to higher severity levels

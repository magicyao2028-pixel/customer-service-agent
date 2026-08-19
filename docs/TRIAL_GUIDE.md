# Reviewer Trial Guide

## Purpose

This 15–20 minute offline trial demonstrates governed customer-service triage, abstention, reviewer-feedback replay and a redaction-quality fixture. It sends no reply and writes to no ticketing platform.

## Clean start

```bash
python -m venv .venv
python -m pip install -e .
service-agent-trial
```

Expected result: `overall_passed` is `true`, 7/7 redaction cases pass, the existing 5/5 behavior fixture passes, and 2/2 accepted synthetic feedback records replay. The redaction report must not retain source messages or sensitive values.

## Failure and recovery

If a privacy case fails, inspect only its case ID and detection labels. Add a bounded synthetic regression before changing a pattern. Do not copy real customer text into a bug report or weaken abstention and human-handoff gates to obtain a green result.

## Real-pilot boundary

A real pilot still requires authenticated support users, approved retention and deletion, ticketing integration, privacy and jurisdiction review, monitored false-positive/false-negative handling, incident escalation and explicit human approval before any customer reply.

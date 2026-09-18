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

The v1.2 Trial also requires 4/4 conversation regressions. Safety on reply 1 or the final allowed reply and an explicit refund escalation must immediately produce `escalated` even without an order ID; ordinary missing evidence still stops as `clarification_exhausted` at two turns. The report rechecks every actual `conversation_guardrail_receipt` field with strict types, including evaluation counts, approval, no-send and privacy. Returned history/export/queue no-application, retention and zero-action values are also required by the Trial gate. Fourteen evidence claims link real files; `kind: trial` links target generated reports rather than implementation code.

The workflow prepares a handoff/draft only. Neither escalation nor Trial PASS means a human was notified, a customer reply was sent or the static browser sample was updated.

## Failure and recovery

If a privacy case fails, inspect only its case ID and detection labels. Add a bounded synthetic regression before changing a pattern. Do not copy real customer text into a bug report or weaken abstention and human-handoff gates to obtain a green result.

## Real-pilot boundary

A real pilot still requires authenticated support users, approved retention and deletion, ticketing integration, privacy and jurisdiction review, monitored false-positive/false-negative handling, incident escalation and explicit human approval before any customer reply.

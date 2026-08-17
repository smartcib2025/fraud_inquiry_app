# CPPD Investigation OS - Product Requirements Document

This document defines the requirements for the **CPPD Investigation OS — Google Antigravity Edition**, a secure investigation platform built around a hybrid Google Cloud + Supabase + Gemini architecture.

## 1. System Context & Goals
The CPPD Investigation OS serves law enforcement and compliance officers investigating complex fraud networks, transaction structuring, and financial crimes. The platform combines agentic automation with strict human-in-the-loop validation.

## 2. Core Architecture Roles
- **Google Antigravity**: Development environment, specialist developer agents orchestration, and secure managed runtime sandboxes for ad hoc analytical code execution.
- **Google Cloud Platform**: Production runtime hosts (Cloud Run), trigger backbone (Pub/Sub + Eventarc), secure storage, IAM role management, and Secrets.
- **Gemini**: Large language model layer for semantic extraction, summarization, timeline matching, and cross-case reasoning.
- **Supabase**: Relational case store, system of record, row-level access control (RLS), real-time updates, and pgvector embeddings.
- **Slack App**: System of notification, Command Line Interface (CLI) input, and workflow review/approval interfaces.
- **Model Context Protocol (MCP)**: Universal tool interfaces exposing investigation APIs.

## 3. High-Level Workflows (Phase 1)
1. **Victim Intake**: QR-based or online ingestion forms. Emits `VICTIM_REGISTERED` event. Extracts profile, statements, and contact details.
2. **Evidence Intake**: Intake processing. Performs SHA-256 integrity calculation, maps metadata, generates derived working copies, and schedules background OCR/extraction.
3. **Entity Resolution**: Identifies and links duplicate phone numbers, bank accounts, and people across cases.
4. **Evidence Gap Analysis**: Evaluates case state against an audit checklist to identify missing evidence.
5. **Cross-Case Matching**: Uses exact and fuzzy identifier matches to trigger alerts when accounts or contacts appear in separate investigations.

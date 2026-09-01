# Central Hybrid AI Gateway Specification (กก.1 บก.ปคบ.)

## 1. Unified Gateway Flow
$$\text{Agent Request} \longrightarrow \text{Auth \& Scope} \longrightarrow \text{Classification} \longrightarrow \text{DLP / Sanitizer} \longrightarrow \text{Routing Policy} \longrightarrow \text{Provider / Model} \longrightarrow \text{Audit}$$

## 2. Strict Boundary Rules
- All AI Agents MUST route through the central Gateway.
- Direct external LLM provider calls from client or backend agents are strictly prohibited.

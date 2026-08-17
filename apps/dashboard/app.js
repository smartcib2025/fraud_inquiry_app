// CPPD Investigation OS Controller (Phase 1)

document.addEventListener("DOMContentLoaded", () => {
    // Global fetch interceptor for Authorization Header
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        const token = localStorage.getItem("cppd_session_token") || "";
        if (token) {
            options.headers = options.headers || {};
            if (options.headers instanceof Headers) {
                options.headers.set("Authorization", `Bearer ${token}`);
            } else if (Array.isArray(options.headers)) {
                options.headers.push(["Authorization", `Bearer ${token}`]);
            } else {
                options.headers["Authorization"] = `Bearer ${token}`;
            }
        }
        return originalFetch(url, options);
    };

    // API endpoint config
    const API_BASE = "http://localhost:8000";
    
    // UI Local State fallback
    let state = {
        cases: [],
        findings: [],
        auditLogs: [],
        triggers: [
            { id: "trig-1", event_type: "VICTIM_REGISTERED", payload: { full_name: "Nattapong Sukprasert", case_id: "CASE-142" }, created_at: "Today, 18:45" },
            { id: "trig-2", event_type: "EVIDENCE_UPLOADED", payload: { title: "transfer_slip.png", case_id: "CASE-142" }, created_at: "Yesterday, 14:32" }
        ],
        alerts: [
            {
                id: "alert-1",
                type: "warning",
                title: "Cross-Case Target Match Detected",
                description: "Suspect account `401-229-3388` is shared between CASE-142 and CASE-087. Combined loss exceeds ฿2.1M.",
                time: "10 mins ago"
            }
        ]
    };

    // -------------------------------------------------------------
    // Single Page Router
    // -------------------------------------------------------------
    const navButtons = document.querySelectorAll(".nav-btn");
    const viewPanes = document.querySelectorAll(".view-pane");
    const viewTitle = document.getElementById("view-title");
    const viewSubtitle = document.getElementById("view-subtitle");

    const viewMeta = {
        "command-center": { title: "Command Center", subtitle: "Overview of division status and critical alerts." },
        "cases": { title: "Case Management", subtitle: "Relational investigation records and evidence registries." },
        "victim-intake": { title: "Victim Intake Portal", subtitle: "Simulated online witness and profile ingestion forms." },
        "entity-intelligence": { title: "Entity Intelligence Network", subtitle: "Resolved suspects and counterparties across cases." },
        "ai-findings": { title: "AI Findings & Supervisor Approvals", subtitle: "Investigator verification ledger for machine assertions." },
        "audit-logs": { title: "Compliance Audit Ledger", subtitle: "Immutable historical log of all database and system actions." },
        "trigger-center": { title: "Trigger Bus Center", subtitle: "Publish simulated Pub/Sub events directly into the CPPD OS API Gateway." },
        "settings": { title: "Security Settings", subtitle: "AI and local processing toggles." },
        "admin-console": { title: "Admin Console", subtitle: "User access approval and toggle controls." }
    };

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const view = btn.getAttribute("data-view");
            switchView(view);
        });
    });

    function switchView(viewName) {
        navButtons.forEach(b => b.classList.remove("active"));
        const activeBtn = document.querySelector(`.nav-btn[data-view="${viewName}"]`);
        if (activeBtn) activeBtn.classList.add("active");

        viewPanes.forEach(pane => pane.classList.remove("active"));
        const targetPane = document.getElementById(`view-${viewName}`);
        if (targetPane) targetPane.classList.add("active");

        // Update titles
        if (viewMeta[viewName]) {
            viewTitle.textContent = viewMeta[viewName].title;
            viewSubtitle.textContent = viewMeta[viewName].subtitle;
        }

        // Trigger fetches
        if (viewName === "cases") fetchCases();
        if (viewName === "ai-findings") fetchFindings();
        if (viewName === "audit-logs") fetchAuditLogs();
        if (viewName === "admin-console") fetchAdminUsers();
    }

    // -------------------------------------------------------------
    // Theme Management
    // -------------------------------------------------------------
    const themeToggle = document.getElementById("theme-toggle");
    const htmlElement = document.documentElement;

    themeToggle.addEventListener("click", () => {
        const currentTheme = htmlElement.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        htmlElement.setAttribute("data-theme", newTheme);
        themeToggle.innerHTML = newTheme === "dark" ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
        
        logAuditLocal("SWITCH_THEME", "profiles", "client", `User toggled client interface to ${newTheme} mode.`);
    });

    // -------------------------------------------------------------
    // Data Fetching Logic (FastAPI API with Local Fallbacks)
    // -------------------------------------------------------------
    async function fetchCases() {
        try {
            const res = await fetch(`${API_BASE}/api/cases`);
            if (!res.ok) throw new Error("API issue");
            state.cases = await res.json();
        } catch (e) {
            console.warn("Backend API offline, loading mock case index.", e);
            state.cases = [
                { id: "CASE-142", title: "Siam Network Ledger Structuring", description: "Investigation into structured cash transfers and suspected layering using fake online commerce entities.", status: "open", owning_unit: "Financial Crimes", sensitive: false },
                { id: "CASE-087", title: "Phuket Cyber Cash Layering", description: "Tracking illegal offshore gambling proceeds routed through local proxy banking accounts.", status: "open", owning_unit: "Financial Crimes", sensitive: false },
                { id: "CASE-112", title: "Bangkok Shell Company Network", description: "Network of interrelated shell companies sharing directors and bank accounts.", status: "under_review", owning_unit: "Cyber Division", sensitive: true }
            ];
        }
        renderCases();
        updateDashboardKPIs();
    }

    async function fetchFindings() {
        try {
            const res = await fetch(`${API_BASE}/api/ai-findings`);
            if (!res.ok) throw new Error("API issue");
            state.findings = await res.json();
        } catch (e) {
            if (state.findings.length === 0) {
                state.findings = [
                    { id: "ai-find-001", case_id: "CASE-142", entity_type: "BANK_ACCOUNT", entity_name: "401-229-3388", details: "Linked to Kittisak Wongsawat, active in Siam Network Ledger Structuring case", confidence: 0.95, status: "unverified" }
                ];
            }
        }
        renderFindings();
        updateDashboardKPIs();
    }

    async function fetchAuditLogs(emailFilter = "", actionFilter = "") {
        try {
            let url = `${API_BASE}/api/admin/audit-logs`;
            const params = [];
            if (emailFilter) params.push(`email=${encodeURIComponent(emailFilter)}`);
            if (actionFilter) params.push(`action=${encodeURIComponent(actionFilter)}`);
            if (params.length > 0) {
                url += "?" + params.join("&");
            }
            
            const res = await fetch(url);
            if (!res.ok) {
                const resNormal = await fetch(`${API_BASE}/api/audit-logs`);
                state.auditLogs = await resNormal.json();
            } else {
                state.auditLogs = await res.json();
            }
        } catch (e) {
            // Keep existing local list if API offline
        }
        renderAuditLogs();
    }

    async function fetchAdminUsers() {
        const tbody = document.querySelector("#admin-users-table tbody");
        if (!tbody) return;
        tbody.innerHTML = "<tr><td colspan='5' style='padding:1rem;'>Loading users...</td></tr>";
        
        try {
            const res = await fetch(`${API_BASE}/api/admin/users`);
            if (!res.ok) throw new Error("Unauthorized or server error");
            const users = await res.json();
            
            tbody.innerHTML = "";
            users.forEach(u => {
                const tr = document.createElement("tr");
                tr.style.borderBottom = "1px solid var(--border-color)";
                tr.innerHTML = `
                    <td style="padding: 0.75rem;"><strong>${u.full_name}</strong></td>
                    <td style="padding: 0.75rem;">${u.email}</td>
                    <td style="padding: 0.75rem;"><span class="badge" style="background: rgba(255,255,255,0.05); color: var(--text-primary); font-size: 0.8rem; border: 1px solid var(--border-color);">${u.role.toUpperCase()}</span></td>
                    <td style="padding: 0.75rem;">
                        <span class="badge" style="background: ${u.approved ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}; color: ${u.approved ? 'var(--success)' : 'var(--danger)'}">
                            ${u.approved ? 'Approved' : 'Pending'}
                        </span>
                    </td>
                    <td style="padding: 0.75rem; text-align: right;">
                        <button class="btn ${u.approved ? 'btn-danger' : 'btn-primary'} btn-sm btn-toggle-approve" data-userid="${u.id}" data-approved="${u.approved}" style="padding: 0.25rem 0.5rem; font-size: 0.8rem; border-radius: var(--border-radius);">
                            ${u.approved ? 'Revoke Access' : 'Approve Access'}
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            
            document.querySelectorAll(".btn-toggle-approve").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const userId = btn.getAttribute("data-userid");
                    const isApprovedNow = btn.getAttribute("data-approved") === "true";
                    
                    try {
                        const toggleRes = await fetch(`${API_BASE}/api/admin/users/${userId}/approve`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ approved: !isApprovedNow })
                        });
                        
                        if (toggleRes.ok) {
                            fetchAdminUsers();
                        } else {
                            alert("Failed to update approval status.");
                        }
                    } catch (e) {
                        alert("Error contacting API server.");
                    }
                });
            });
        } catch (e) {
            tbody.innerHTML = "<tr><td colspan='5' class='warn-color' style='padding:1rem;'>Failed to load user credentials. Admin privilege required.</td></tr>";
        }
    }

    // -------------------------------------------------------------
    // Render Functions
    // -------------------------------------------------------------
    function renderCases() {
        const tbody = document.querySelector("#cases-table tbody");
        tbody.innerHTML = "";
        
        state.cases.forEach(c => {
            const tr = document.createElement("tr");
            tr.style.cursor = "pointer";
            tr.innerHTML = `
                <td><strong>${c.id}</strong></td>
                <td>${c.title}</td>
                <td>${c.owning_unit}</td>
                <td><span class="badge" style="background-color: ${c.status === 'open' ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)'}; color: ${c.status === 'open' ? 'var(--success)' : 'var(--warning)'}">${c.status.toUpperCase()}</span></td>
                <td>${c.sensitive ? '<i class="fa-solid fa-lock warn-color"></i> Sensitive' : 'Public'}</td>
            `;
            tr.addEventListener("click", () => openCaseDetails(c.id));
            tbody.appendChild(tr);
        });
    }

    async function openCaseDetails(caseId) {
        const detailsPanel = document.getElementById("case-details-panel");
        const idHeader = document.getElementById("details-case-id");
        const titleHeader = document.getElementById("details-case-title");
        const descPara = document.getElementById("details-case-desc");
        
        const victimsList = document.getElementById("details-victims-list");
        const evidenceList = document.getElementById("details-evidence-list");
        const tasksList = document.getElementById("details-tasks-list");
        
        let caseData;
        try {
            const res = await fetch(`${API_BASE}/api/cases/${caseId}`);
            if (res.status === 403) {
                alert("Permission Denied: You do not have authorization to view this case.");
                detailsPanel.style.display = "none";
                return;
            }
            if (!res.ok) throw new Error("API issue");
            caseData = await res.json();
        } catch (e) {
            // Mock case details fallback
            caseData = {
                case: state.cases.find(c => c.id === caseId) || { id: caseId, title: "Siam Network Ledger Structuring", description: "Details of investigation", status: "open" },
                victims: [
                    { id: "v-1", full_name: "Nattapong Sukprasert", phone: "081-555-0192", loss_amount: 1250000.00 }
                ],
                evidence: [
                    { id: "ev-1", title: "Transfer slip receipt", type: "document", file_hash: "a3f82cb304b5...21415", status: "sealed" },
                    { id: "ev-2", title: "Line Chat Logs screenshot", type: "document", file_hash: "e7b92f7a63bc...1122a", status: "sealed" }
                ],
                tasks: [
                    { id: "t-1", title: "Verify Kittisak Wongsawat identity", description: "Cross-check details.", status: "pending", due_date: "2026-08-25" },
                    { id: "t-2", title: "Analyze bank transactions flow", description: "Evaluate layering flow.", status: "in_progress", due_date: "2026-08-28" }
                ]
            };
        }

        idHeader.textContent = caseData.case.id;
        titleHeader.textContent = caseData.case.title;
        descPara.textContent = caseData.case.description;

        // Render Victims
        victimsList.innerHTML = caseData.victims.map(v => `
            <div class="detail-item">
                <strong>${v.full_name}</strong><br>
                <span class="text-sm muted-text">Claimed Loss: ฿${v.loss_amount.toLocaleString()} | Phone: ${v.phone}</span>
            </div>
        `).join("") || '<p class="text-sm muted-text">No victims registered.</p>';

        // Render Evidence
        evidenceList.innerHTML = caseData.evidence.map(ev => `
            <div class="detail-item">
                <strong>${ev.title}</strong> (${ev.type})<br>
                <span class="text-sm muted-text" style="font-family: var(--font-mono)">SHA-256: ${ev.file_hash.substring(0, 16)}...</span><br>
                <span class="badge" style="background-color: rgba(255,255,255,0.05); color: var(--text-primary); font-size: 0.65rem; padding: 0.1rem 0.3rem; display: inline-block; margin-top: 0.25rem">${ev.status.toUpperCase()}</span>
            </div>
        `).join("") || '<p class="text-sm muted-text">No evidence logs registered.</p>';

        // Render Tasks
        tasksList.innerHTML = caseData.tasks.map(t => `
            <div class="detail-item">
                <div class="justify-between" style="display: flex; align-items: center">
                    <strong>${t.title}</strong>
                    <span class="badge" style="background-color: ${t.status === 'completed' ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)'}; color: ${t.status === 'completed' ? 'var(--success)' : 'var(--warning)'}">${t.status.toUpperCase()}</span>
                </div>
                <p class="text-xs muted-text margin-top-md">${t.description || ''}</p>
                <span class="text-xs muted-text">Deadline: ${t.due_date.split("T")[0]}</span>
            </div>
        `).join("") || '<p class="text-sm muted-text">No active tasks.</p>';

        // Fetch readiness
        let readinessPercent = 40;
        try {
            const res = await fetch(`${API_BASE}/api/cases/${caseId}/readiness`);
            const readiness = await res.json();
            readinessPercent = readiness.readiness_percentage;
        } catch (e) {
            readinessPercent = caseId === "CASE-142" ? 75 : 40;
        }
        document.getElementById("details-readiness-percent").textContent = readinessPercent + "%";
        document.getElementById("details-readiness-bar").style.width = readinessPercent + "%";

        // Fetch timeline contradictions
        let timelineEvents = [];
        try {
            const res = await fetch(`${API_BASE}/api/cases/${caseId}/timeline`);
            const timeline = await res.json();
            timelineEvents = timeline.events;
        } catch (e) {
            timelineEvents = [
                { date: "2026-08-09 14:32:00", event: "Victim Nattapong transfers 1.25M THB to SCB account 401-229-3388", source: "Victim Statement", status: "consistent" },
                { date: "2026-08-09 15:00:00", event: "Suspect Kittisak claims he was out of town in Chiang Mai and card was lost", source: "Suspect Statement", status: "contradictory", conflict_notes: "SCB login registers IP location in Bangkok at 14:32, contradicting Chiang Mai alibi." }
            ];
        }
        
        const contradictionsList = document.getElementById("details-contradictions-list");
        contradictionsList.innerHTML = timelineEvents.map(e => `
            <div class="detail-item" style="border-left: 3px solid ${e.status === 'contradictory' ? 'var(--danger)' : 'var(--border-color)'}">
                <div class="justify-between" style="display: flex; align-items: center">
                    <strong>${e.event}</strong>
                    <span class="badge" style="background-color: ${e.status === 'contradictory' ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.05)'}; color: ${e.status === 'contradictory' ? 'var(--danger)' : 'var(--text-muted)'}; font-size: 0.65rem; padding: 0.1rem 0.3rem">${e.status.toUpperCase()}</span>
                </div>
                <span class="text-xs muted-text">Date: ${e.date} | Source: ${e.source}</span>
                ${e.conflict_notes ? `<p class="text-xs text-danger" style="margin-top: 0.25rem"><i class="fa-solid fa-triangle-exclamation"></i> ${e.conflict_notes}</p>` : ''}
            </div>
        `).join("") || '<p class="text-sm muted-text">No statements audited yet.</p>';

        // Render Transactions list
        const txList = document.getElementById("details-transactions-list");
        const caseTxs = caseData.transactions || [
            { reference_number: "TXN-99882211", amount: 1250000.0, transaction_date: "2026-08-09T14:32:00Z" }
        ];
        txList.innerHTML = caseTxs.map(t => `
            <div class="detail-item">
                <div class="justify-between" style="display: flex">
                    <span class="font-mono text-sm">${t.reference_number}</span>
                    <strong class="warn-color">฿${parseFloat(t.amount).toLocaleString()}</strong>
                </div>
                <span class="text-xs muted-text">Date: ${t.transaction_date.split("T")[0]}</span>
            </div>
        `).join("") || '<p class="text-sm muted-text">No transaction logs registered.</p>';

        detailsPanel.style.display = "block";
        logAuditLocal("VIEW_CASE_DETAILS", "cases", caseId, `User viewed complete detail profile for case ${caseId}`);
    }

    document.getElementById("btn-close-details").addEventListener("click", () => {
        document.getElementById("case-details-panel").style.display = "none";
    });

    function renderFindings() {
        const tbody = document.querySelector("#findings-table tbody");
        tbody.innerHTML = "";
        
        state.findings.forEach(f => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${f.id}</strong></td>
                <td>${f.case_id}</td>
                <td><span class="badge">${f.entity_type}</span></td>
                <td>${f.details}</td>
                <td><span class="font-mono">${(f.confidence * 100).toFixed(0)}%</span></td>
                <td>
                    <span class="badge" style="background-color: ${f.status === 'verified' ? 'rgba(16,185,129,0.15)' : f.status === 'rejected' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)'}; color: ${f.status === 'verified' ? 'var(--success)' : f.status === 'rejected' ? 'var(--danger)' : 'var(--warning)'}">
                        ${f.status.toUpperCase()}
                    </span>
                </td>
                <td>
                    ${f.status === 'unverified' ? `
                        <button class="btn btn-primary btn-sm btn-verify" data-id="${f.id}"><i class="fa-solid fa-check"></i> Verify</button>
                        <button class="btn btn-danger btn-sm btn-reject" data-id="${f.id}"><i class="fa-solid fa-xmark"></i> Reject</button>
                    ` : '<span class="muted-text text-xs">Closed</span>'}
                </td>
            `;
            
            // Add click events to verify buttons
            const vBtn = tr.querySelector(".btn-verify");
            if (vBtn) {
                vBtn.addEventListener("click", () => processVerifyFinding(f.id, "verified"));
            }
            const rBtn = tr.querySelector(".btn-reject");
            if (rBtn) {
                rBtn.addEventListener("click", () => processVerifyFinding(f.id, "rejected"));
            }
            
            tbody.appendChild(tr);
        });

        const activeFindings = state.findings.filter(f => f.status === "unverified").length;
        document.getElementById("findings-count").textContent = activeFindings;
        if (activeFindings === 0) {
            document.getElementById("findings-count").style.display = "none";
        } else {
            document.getElementById("findings-count").style.display = "inline-block";
        }
    }

    async function processVerifyFinding(findingId, status) {
        try {
            const res = await fetch(`${API_BASE}/api/ai-findings/${findingId}/verify?status=${status}`, { method: "POST" });
            const updated = await res.json();
            const idx = state.findings.findIndex(f => f.id === findingId);
            if (idx !== -1) state.findings[idx] = updated.finding;
        } catch (e) {
            // Local fallback mock update
            const item = state.findings.find(f => f.id === findingId);
            if (item) item.status = status;
            logAuditLocal("VERIFY_AI_FINDING", "ai_findings", findingId, `Investigator review: assertion marked as ${status.toUpperCase()}`);
        }
        renderFindings();
        updateDashboardKPIs();
    }

    function renderAuditLogs() {
        const tbody = document.querySelector("#audit-table tbody");
        tbody.innerHTML = "";
        
        state.auditLogs.slice().reverse().forEach(log => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="font-mono text-xs">${log.logged_at}</span></td>
                <td><span class="badge" style="background-color: rgba(255,255,255,0.05); color: var(--text-primary)">${log.action}</span></td>
                <td><span class="font-mono text-xs">${log.table_name || '-'}</span></td>
                <td><span class="font-mono text-xs">${log.record_id || '-'}</span></td>
                <td class="muted-text text-sm">${log.query_details}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // -------------------------------------------------------------
    // Core Workflow Simulation / Forms
    // -------------------------------------------------------------
    const intakeForm = document.getElementById("victim-intake-form");
    intakeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const caseId = document.getElementById("intake-case-id").value;
        const text = document.getElementById("intake-raw-statement").value;
        
        const btn = document.getElementById("btn-submit-intake");
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Extracting...';
        
        try {
            // Check if backend is available
            const res = await fetch(`${API_BASE}/api/pubsub/publish`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    event_type: "VICTIM_REGISTERED",
                    payload: {
                        case_id: caseId,
                        full_name: "Nattapong Sukprasert",
                        phone: "081-555-0192",
                        loss_amount: 1250000.00,
                        raw_statement: text
                    }
                })
            });
            if (res.ok) {
                logAuditLocal("VICTIM_INTAKE", "victims", "new", "Extracted statement entities successfully.");
                alert("Victim statement processed successfully by Gemini and registered.");
                switchView("command-center");
                loadAllInitialData();
            } else {
                throw new Error("API rejection");
            }
        } catch (err) {
            // Local Simulation fallback if backend offline
            setTimeout(() => {
                logAuditLocal("VICTIM_INTAKE_MOCK", "victims", "new", "Gemini extraction simulator processed statement. Entities resolved.");
                
                // Add target match trigger alert
                state.alerts.unshift({
                    id: "alert-" + Date.now(),
                    type: "warning",
                    title: "Entity Match Warning",
                    description: "Phone `081-555-0192` extracted. Registered to case CASE-142.",
                    time: "Just now"
                });
                
                state.triggers.unshift({
                    id: "trig-" + Date.now(),
                    event_type: "VICTIM_REGISTERED",
                    payload: { full_name: "Nattapong Sukprasert", case_id: caseId },
                    created_at: "Just now"
                });
                
                // Reset form button
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-microchip"></i> Run AI Extraction (Gemini Flash)';
                
                alert("Simulator: Statement extracted successfully. Cross-case matches analyzed.");
                switchView("command-center");
                renderAlertsFeed();
                renderTimelineTriggers();
            }, 1000);
        }
    });

    // -------------------------------------------------------------
    // Pub/Sub Trigger Panel Actions
    // -------------------------------------------------------------
    const triggerButtons = document.querySelectorAll(".btn-trigger");
    triggerButtons.forEach(btn => {
        btn.addEventListener("click", async () => {
            const triggerType = btn.getAttribute("data-trigger");
            let eventType = "VICTIM_REGISTERED";
            let payload = { case_id: "CASE-142" };
            
            if (triggerType === "EVIDENCE_UPLOADED_MOCK") {
                eventType = "EVIDENCE_UPLOADED";
                payload = { case_id: "CASE-142", title: "SCB Statement Ledger CSV", filename: "scb_statement.csv" };
            } else if (triggerType === "ENTITY_CREATED_MOCK") {
                eventType = "ENTITY_CREATED";
                payload = { case_id: "CASE-142", name: "089-111-2345", type: "PHONE" };
            } else if (triggerType === "EVIDENCE_GAP_MOCK") {
                eventType = "EVIDENCE_GAP_FOUND";
                payload = { case_id: "CASE-142", gaps: ["Missing verified bank account transaction statement ledger"] };
            }
            
            try {
                const res = await fetch(`${API_BASE}/api/pubsub/publish`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ event_type: eventType, payload: payload })
                });
                if (res.ok) {
                    alert(`Event ${eventType} published to bus.`);
                    loadAllInitialData();
                }
            } catch (e) {
                // Mock local trigger update
                state.triggers.unshift({
                    id: "trig-" + Date.now(),
                    event_type: eventType,
                    payload: payload,
                    created_at: "Just now"
                });
                
                if (eventType === "ENTITY_CREATED") {
                    state.alerts.unshift({
                        id: "alert-" + Date.now(),
                        type: "danger",
                        title: "🚨 Cross-Case Account Match",
                        description: `Identifier ${payload.name} found in CASE-087 and CASE-142. Priority high.`,
                        time: "Just now"
                    });
                    // Add AI finding
                    state.findings.unshift({
                        id: "ai-find-" + Date.now(),
                        case_id: "CASE-142",
                        entity_type: "PHONE",
                        entity_name: payload.name,
                        details: `Cross-case link detected with CASE-087. Phone active in structuring.`,
                        confidence: 0.93,
                        status: "unverified"
                    });
                } else if (eventType === "EVIDENCE_GAP_FOUND") {
                    state.alerts.unshift({
                        id: "alert-" + Date.now(),
                        type: "warning",
                        title: "⚠️ Evidence Gap Detected",
                        description: "Audit check: Case missing verified bank transaction ledger.",
                        time: "Just now"
                    });
                }
                
                logAuditLocal("PUBLISH_EVENT_MOCK", "trigger_events", eventType, `Local simulator fired event: ${eventType}`);
                alert(`Simulator: Published event ${eventType} to local queue.`);
                renderTimelineTriggers();
                renderAlertsFeed();
                renderFindings();
            }
        });
    });

    // Helper to write audit trail to client log state
    function logAuditLocal(action, table, recordId, details) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        state.auditLogs.push({
            logged_at: timestamp,
            action: action,
            table_name: table,
            record_id: recordId,
            query_details: details
        });
    }

    function renderAlertsFeed() {
        const feed = document.getElementById("critical-alerts-feed");
        feed.innerHTML = state.alerts.map(a => `
            <div class="alert-item ${a.type}">
                <div class="alert-icon"><i class="fa-solid fa-${a.type === 'danger' ? 'triangle-exclamation' : 'circle-exclamation'}"></i></div>
                <div class="alert-details">
                    <h4>${a.title}</h4>
                    <p>${a.description}</p>
                    <span class="timestamp">${a.time}</span>
                </div>
            </div>
        `).join("") || '<p class="muted-text text-sm">No critical alerts pending.</p>';
    }

    function renderTimelineTriggers() {
        const timeline = document.getElementById("recent-triggers-timeline");
        timeline.innerHTML = state.triggers.map(t => `
            <div class="timeline-step">
                <div class="step-point"></div>
                <div class="step-content">
                    <p class="step-title">${t.event_type}</p>
                    <p class="step-desc">${JSON.stringify(t.payload)}</p>
                    <span class="step-time">${t.created_at}</span>
                </div>
            </div>
        `).join("");
    }

    function updateDashboardKPIs() {
        document.getElementById("stat-cases").textContent = state.cases.length || 3;
        document.getElementById("stat-victims").textContent = 2 + (state.triggers.filter(t => t.event_type === "VICTIM_REGISTERED").length - 1);
        document.getElementById("stat-evidence").textContent = 2 + state.triggers.filter(t => t.event_type === "EVIDENCE_UPLOADED").length;
        document.getElementById("stat-alerts").textContent = state.findings.filter(f => f.status === 'unverified').length;
    }

    // -------------------------------------------------------------
    // Initialization
    // -------------------------------------------------------------
    function loadAllInitialData() {
        fetchCases();
        fetchFindings();
        fetchAuditLogs();
        renderAlertsFeed();
        renderTimelineTriggers();
        fetchAISettings();
    }
    
    async function fetchAISettings() {
        try {
            const res = await fetch(`${API_BASE}/api/settings/ai`);
            if (res.ok) {
                const settings = await res.json();
                document.getElementById("ai-mode").value = settings.mode;
                document.getElementById("ai-endpoint").value = settings.local_endpoint;
                document.getElementById("ai-model").value = settings.local_model;
            }
        } catch (e) {
            console.error("Failed to load AI settings:", e);
        }
    }

    // AI Settings listeners
    const aiForm = document.getElementById("form-ai-settings");
    if (aiForm) {
        aiForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const mode = document.getElementById("ai-mode").value;
            const local_endpoint = document.getElementById("ai-endpoint").value;
            const local_model = document.getElementById("ai-model").value;
            
            try {
                const res = await fetch(`${API_BASE}/api/settings/ai`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mode, local_endpoint, local_model })
                });
                const data = await res.json();
                if (data.status === "success") {
                    alert("AI Settings successfully saved.");
                    logAuditLocal("UPDATE_AI_SETTINGS", "profiles", "ai_settings", `Saved AI processing mode: ${mode}`);
                } else {
                    alert("Failed to save AI settings.");
                }
            } catch (err) {
                alert("Settings saved locally (API offline fallback).");
                logAuditLocal("UPDATE_AI_SETTINGS", "profiles", "ai_settings", `Saved AI mode locally: ${mode}`);
            }
        });
    }

    const presetOllamaBtn = document.getElementById("btn-preset-ollama");
    if (presetOllamaBtn) {
        presetOllamaBtn.addEventListener("click", () => {
            document.getElementById("ai-mode").value = "local_pc";
            document.getElementById("ai-endpoint").value = "http://localhost:11434/v1";
            document.getElementById("ai-model").value = "llama3";
        });
    }

    const presetCibBtn = document.getElementById("btn-preset-cib");
    if (presetCibBtn) {
        presetCibBtn.addEventListener("click", () => {
            document.getElementById("ai-mode").value = "local_agency";
            document.getElementById("ai-endpoint").value = "https://api.cib.go.th/gpt/v1";
            document.getElementById("ai-model").value = "cib-gpt-v1";
        });
    }
    
    // Case Briefing Agent Trigger Listeners
    const briefingBtn = document.getElementById("btn-generate-briefing");
    const briefingModal = document.getElementById("briefing-modal");
    const briefingContent = document.getElementById("briefing-content");
    const closeBriefingBtn = document.getElementById("btn-close-briefing");
    const doneBriefingBtn = document.getElementById("btn-done-briefing");
    const copyBriefingBtn = document.getElementById("btn-copy-briefing");
    
    let currentBriefingRaw = "";

    if (briefingBtn) {
        briefingBtn.addEventListener("click", async () => {
            const caseId = document.getElementById("details-case-id").textContent;
            briefingContent.textContent = "Spawning Antigravity Agent workflow...\nRunning secure sandbox briefing checks...\nAggregating timeline analysis logs...";
            briefingModal.style.display = "flex";
            
            try {
                const res = await fetch(`${API_BASE}/api/agents/run?case_id=${caseId}&goal=briefing`, {
                    method: "POST"
                });
                const data = await res.json();
                if (data.status === "success") {
                    currentBriefingRaw = data.result.briefing_markdown;
                    briefingContent.textContent = currentBriefingRaw;
                    logAuditLocal("GENERATE_CASE_BRIEFING", "cases", caseId, `Antigravity Agent generated briefing package for case ${caseId}`);
                } else {
                    briefingContent.textContent = "Error compiling briefing: " + (data.message || "Unknown error");
                }
            } catch (e) {
                currentBriefingRaw = `# CPPD COMMAND BRIEFING PACKAGE: ${caseId}\n\n**Case Reference**: Siam Network Ledger Structuring\n**Current Status**: OPEN\n**Case Readiness Index**: 85%\n**Compiled By**: Antigravity Agent\n\n## 1. Executive Summary\nInvestigation into structured cash transfers and suspected layering using fake online commerce entities.\n\n## 2. Inhabitants & Participants\n- **Victims**: Nattapong Sukprasert, Somsak Test\n\n## 3. Timeline Audits & Contradictions\n- ⚠️ **Date**: 2026-08-09 15:00:00 | **Event**: Suspect Kittisak claims he was out of town in Chiang Mai and card was lost | **Status**: CONTRADICTORY\n  - *Conflict Notes*: SCB login registers IP location in Bangkok at 14:32, contradicting Chiang Mai alibi.\n- ✅ **Date**: 2026-08-09 14:32:00 | **Event**: Victim Nattapong transfers 1.25M THB to SCB account 401-229-3388 | **Status**: CONSISTENT\n\n## 4. Evidence Vault & Integrity\n- **Transfer slip receipt** | Type: document | Hash: e14724de31d79860...\n- **Line Chat Logs screenshot** | Type: document | Hash: c4f23b7a5a8f4c1d...\n\n## 5. Outstanding Tasks\n- [PENDING] Verify Kittisak Wongsawat identity\n- [IN_PROGRESS] Analyze bank transactions flow\n- [COMPLETED] Review intake statement for Somsak Test\n- [COMPLETED] Verify cross-case association on identifier 089-111-2345`;
                briefingContent.textContent = currentBriefingRaw;
            }
        });
    }

    if (closeBriefingBtn) {
        closeBriefingBtn.addEventListener("click", () => {
            briefingModal.style.display = "none";
        });
    }

    if (doneBriefingBtn) {
        doneBriefingBtn.addEventListener("click", () => {
            briefingModal.style.display = "none";
        });
    }

    if (copyBriefingBtn) {
        copyBriefingBtn.addEventListener("click", () => {
            navigator.clipboard.writeText(currentBriefingRaw);
            alert("Briefing copied to clipboard.");
        });
    }

    // Google Sign-in flow
    const loginOverlay = document.getElementById("login-overlay");
    const googleLoginBtn = document.getElementById("btn-google-login");
    const logoutBtn = document.getElementById("btn-logout");
    
    function checkSession() {
        const token = localStorage.getItem("cppd_session_token");
        const email = localStorage.getItem("cppd_session_email");
        const name = localStorage.getItem("cppd_session_name");
        const role = localStorage.getItem("cppd_session_role");
        
        if (token && email) {
            if (loginOverlay) loginOverlay.style.display = "none";
            document.getElementById("profile-name").textContent = name || "Somchai Dev";
            document.getElementById("profile-role").textContent = role ? role.toUpperCase() : "Commander";
            
            const navAdmin = document.getElementById("nav-admin-console");
            if (navAdmin) {
                navAdmin.style.display = role === "admin" ? "block" : "none";
            }
            
            loadAllInitialData();
        } else {
            if (loginOverlay) loginOverlay.style.display = "flex";
        }
    }

    if (googleLoginBtn) {
        googleLoginBtn.addEventListener("click", async () => {
            const email = document.getElementById("login-email").value;
            
            try {
                const res = await fetch(`${API_BASE}/api/auth/google/callback`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ code: "mock-google-code", email: email })
                });
                const data = await res.json();
                
                if (res.status === 403) {
                    alert(data.detail || "Access Denied: Your account is pending administrator approval.");
                    return;
                }
                
                if (data.status === "success") {
                    localStorage.setItem("cppd_session_token", data.token);
                    localStorage.setItem("cppd_session_email", data.email);
                    localStorage.setItem("cppd_session_name", data.name);
                    localStorage.setItem("cppd_session_role", data.role);
                    
                    checkSession();
                    alert("Gmail Authentication successful.");
                } else {
                    alert("Login failed.");
                }
            } catch (err) {
                localStorage.setItem("cppd_session_token", "mock-sess-tok-999");
                localStorage.setItem("cppd_session_email", email);
                localStorage.setItem("cppd_session_name", email.split(".")[0]);
                localStorage.setItem("cppd_session_role", "investigator");
                checkSession();
                alert("Offline mock login successful.");
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            try {
                await fetch(`${API_BASE}/api/auth/logout`, { method: "POST" });
            } catch(e) {}
            localStorage.clear();
            checkSession();
        });
    }

    // Filter button for audit logs
    const filterAuditBtn = document.getElementById("btn-filter-audit");
    if (filterAuditBtn) {
        filterAuditBtn.addEventListener("click", () => {
            const emailFilter = document.getElementById("filter-audit-email").value.trim();
            const actionFilter = document.getElementById("filter-audit-action").value;
            fetchAuditLogs(emailFilter, actionFilter);
        });
    }

    // Write baseline system audit logs
    logAuditLocal("INITIALIZE_SYSTEM", "profiles", "sys", "CPPD Investigation OS Client shell initialized.");
    checkSession();
});

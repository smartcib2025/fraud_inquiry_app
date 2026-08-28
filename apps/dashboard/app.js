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

    // 3-Language Translation Mappings
    const translations = {
        th: {
            "nav-dashboard": "แผงควบคุม",
            "nav-new-intake": "รับเรื่องร้องเรียนใหม่",
            "nav-cases": "จัดการคดี",
            "nav-ai-intelligence": "ศูนย์สืบสวน AI",
            "nav-reports": "ระบบสร้างรายงาน",
            "nav-admin-audit": "ผู้ดูแลระบบ & ตรวจสอบ",
            "btn-signout": "ออกจากระบบ",
            "api-online": "ระบบเชื่อมต่ออยู่",
            
            "view-title-command-center": "ศูนย์ปฏิบัติการ กก.1 บก.ปคบ.",
            "view-sub-command-center": "ภาพรวมสถานะหน่วยงานและข้อความแจ้งเตือนที่สำคัญ",
            "view-title-new-intake": "ระบบรับเรื่องข้อมูลผู้เสียหาย กก.1",
            "view-sub-new-intake": "แบบฟอร์มรับเรื่องร้องเรียนและประมวลผล OCR สลิป/บัญชีผู้ต้องสงสัย",
            "view-title-cases": "พื้นที่จัดการคดี (Case Workspace)",
            "view-sub-cases": "ข้อมูลสรุปผู้เสียหาย พยานหลักฐาน เส้นทางการเงิน แผนการสืบสวน และประเด็นข้อกฎหมาย",
            "view-title-ai-intelligence": "ศูนย์วิเคราะห์ข้อมูลสืบสวนสอบสวนอัจฉริยะ (AI Copilot)",
            "view-sub-ai-intelligence": "แผนภูมิเครือข่ายเชื่อมโยงคดี การตรวจสอบจุดบกพร่องพยานหลักฐาน และการวิเคราะห์ข้อพิรุธ alibi",
            "view-title-reports": "ระบบร่างเอกสาร & AI Document Generator",
            "view-sub-reports": "เขียนร่างรายงานสรุปเสนอผู้บังคับบัญชา แผนประทุษกรรม และรายงานบัญชีม้าธุรกรรมต้องสงสัย",
            "view-title-admin-audit": "ศูนย์ควบคุมสิทธิและตรวจสอบการปฏิบัติตามกฎหมาย (Compliance Audit)",
            "view-sub-admin-audit": "การอนุมัติสิทธิพนักงานสอบสวน และประวัติการสืบค้นข้อมูลสำนวนคดีอย่างละเอียดที่บิดเบือนไม่ได้",
            "ocr-header": "ระบบสแกนหลักฐาน & OCR Simulator",
            "ocr-label-case": "เชื่อมโยงกับคดี",
            "ocr-label-title": "ชื่อของเอกสาร",
            "ocr-label-file": "เลือกไฟล์สลิป (PNG/JPG) หรือไฟล์บัญชี (TXT)",
            "ocr-btn-run": "อัปโหลดและประมวลผล OCR",
            "ocr-result-title": "⚡ ผลการดึงข้อมูล OCR"
        },
        en: {
            "nav-dashboard": "Dashboard",
            "nav-new-intake": "New Intake",
            "nav-cases": "Case Workspace",
            "nav-ai-intelligence": "AI Investigation Center",
            "nav-reports": "Report Generator",
            "nav-admin-audit": "Admin/Audit",
            "btn-signout": "Sign Out",
            "api-online": "API Online",
            
            "view-title-command-center": "CCPD AI Copilot — Division 1 Dashboard",
            "view-sub-command-center": "Overview of division status and critical alerts.",
            "view-title-new-intake": "New Intake Ingestion Portal",
            "view-sub-new-intake": "Register complaints and simulate OCR transaction extractions.",
            "view-title-cases": "Case Workspace",
            "view-sub-cases": "Evidence-first case details, victims ledger, money flow, and timeline tools.",
            "view-title-ai-intelligence": "AI Investigation Center",
            "view-sub-ai-intelligence": "Suspect connection networks, gaps auditor, and alibi checks.",
            "view-title-reports": "Report Generator",
            "view-sub-reports": "Draft executive summaries, action plans, and transaction reports.",
            "view-title-admin-audit": "Admin & Compliance Audit Center",
            "view-sub-admin-audit": "Staff credentials permissions list and immutable compliance audit logs.",
            "ocr-header": "Evidence & OCR Simulator",
            "ocr-label-case": "Link to Case",
            "ocr-label-title": "Document Title",
            "ocr-label-file": "Select Slip (PNG/JPG) or Ledger (TXT)",
            "ocr-btn-run": "Upload & Process OCR",
            "ocr-result-title": "⚡ OCR Extracted Data"
        },
        zh: {
            "nav-dashboard": "仪表盘",
            "nav-new-intake": "新案录入",
            "nav-cases": "案件工作区",
            "nav-ai-intelligence": "AI调查中心",
            "nav-reports": "报告生成器",
            "nav-admin-audit": "管理与审计",
            "btn-signout": "登出",
            "api-online": "接口已联机",
            
            "view-title-command-center": "CCPD AI 协理 — 经侦一队指挥中心",
            "view-sub-command-center": "部门状态和关键警报概述。",
            "view-title-new-intake": "新案录入登记大厅",
            "view-sub-new-intake": "注册受害者投诉并模拟 OCR 资金流水识别提取。",
            "view-title-cases": "案件工作区",
            "view-sub-cases": "提供受害者名单、证据链、资金流向、时间轴和法理要素等核心功能。",
            "view-title-ai-intelligence": "AI 智能综合分析中心",
            "view-sub-ai-intelligence": "嫌疑人关联图谱、起诉证据缺陷审查、和供词疑点审计。",
            "view-title-reports": "智能报告与文书自动生成器",
            "view-sub-reports": "自动起草结案呈批表、侦查计划书和洗钱资金链分析报告。",
            "view-title-admin-audit": "合规审计与系统管理中心",
            "view-sub-admin-audit": "警员访问批准控制台与不可篡改的履职合规审计日志。",
            "ocr-header": "证据与 OCR 模拟器",
            "ocr-label-case": "链接到案件",
            "ocr-label-title": "文件标题",
            "ocr-label-file": "选择转账单 (PNG/JPG) 或账簿 (TXT)",
            "ocr-btn-run": "上传并进行 OCR 处理",
            "ocr-result-title": "⚡ OCR 提取数据"
        }
    };

    function applyTranslations(lang) {
        localStorage.setItem("cppd_lang", lang);
        const bundle = translations[lang] || translations["th"];
        document.querySelectorAll("[data-i18n]").forEach(el => {
            const key = el.getAttribute("data-i18n");
            if (bundle[key]) {
                el.textContent = bundle[key];
            }
        });
        
        // Update current active view title and description
        const activeBtn = document.querySelector(".nav-btn.active");
        if (activeBtn) {
            const viewName = activeBtn.getAttribute("data-view");
            if (viewName && bundle[`view-title-${viewName}`]) {
                viewTitle.textContent = bundle[`view-title-${viewName}`];
                viewSubtitle.textContent = bundle[`view-sub-${viewName}`];
            }
        }
    }

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
        "command-center": { title: "Dashboard", subtitle: "Overview of division status and critical alerts." },
        "new-intake": { title: "New Intake Ingestion Portal", subtitle: "Register complaints and simulate OCR transactions." },
        "cases": { title: "Case Workspace", subtitle: "Evidence-first case details, victims ledger, and timeline tools." },
        "ai-intelligence": { title: "AI Investigation Center", subtitle: "Suspect connection networks, gaps auditor, and alibi checks." },
        "reports": { title: "Report Generator", subtitle: "Draft executive summaries and investigation blueprints." },
        "admin-audit": { title: "Admin & Compliance Audit Center", subtitle: "Staff credentials permissions list and immutable compliance audit logs." }
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

        const currentLang = localStorage.getItem("cppd_lang") || "th";
        const bundle = translations[currentLang] || translations["th"];
        if (bundle[`view-title-${viewName}`]) {
            viewTitle.textContent = bundle[`view-title-${viewName}`];
            viewSubtitle.textContent = bundle[`view-sub-${viewName}`];
        } else if (viewMeta[viewName]) {
            viewTitle.textContent = viewMeta[viewName].title;
            viewSubtitle.textContent = viewMeta[viewName].subtitle;
        }

        if (viewName === "cases") fetchCases();
        if (viewName === "new-intake") fetchIntakes();
        if (viewName === "admin-audit") {
            fetchAdminUsers();
            fetchAuditLogs();
        }
    }

    // -------------------------------------------------------------
    // Theme Management
    // -------------------------------------------------------------
    const themeToggle = document.getElementById("theme-toggle");
    const htmlElement = document.documentElement;

    // Load saved theme preference on initialization
    const savedTheme = localStorage.getItem("cppd_theme") || "dark";
    htmlElement.setAttribute("data-theme", savedTheme);
    if (themeToggle) {
        themeToggle.innerHTML = savedTheme === "dark" ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    }

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const currentTheme = htmlElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            htmlElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("cppd_theme", newTheme);
            themeToggle.innerHTML = newTheme === "dark" ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
            
            logAuditLocal("SWITCH_THEME", "profiles", "client", `User toggled client interface to ${newTheme} mode.`);
        });
    }

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
    // -------------------------------------------------------------
    // Core Workflow Simulation / Forms & Intake Promotion
    // -------------------------------------------------------------
    async function fetchIntakes() {
        try {
            const res = await fetch(`${API_BASE}/api/intakes`);
            if (!res.ok) throw new Error("API issue");
            state.intakes = await res.json();
        } catch (e) {
            console.warn("Backend API offline, using local mock intakes.", e);
            if (!state.intakes || state.intakes.length === 0) {
                state.intakes = [
                    {
                        id: "INTAKE-001",
                        title: "Cosmetics Scam Complaint",
                        reporter_name: "Sunisa Saelim",
                        reporter_phone: "082-111-9988",
                        triage_urgency: "high",
                        triage_reason: "Multiple similar complaints logged against this seller within 24 hours.",
                        status: "pending",
                        created_at: "2026-08-16T09:00:00Z"
                    }
                ];
            }
        }
        renderIntakes();
    }

    function renderIntakes() {
        const tbody = document.querySelector("#intakes-table tbody");
        if (!tbody) return;
        tbody.innerHTML = "";
        
        state.intakes.forEach(i => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${i.id}</strong></td>
                <td>${i.title}</td>
                <td>${i.reporter_name}</td>
                <td>${i.reporter_phone}</td>
                <td>
                    <span class="badge" style="background-color: ${i.triage_urgency === 'high' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)'}; color: ${i.triage_urgency === 'high' ? 'var(--danger)' : 'var(--warning)'}">
                        ${i.triage_urgency.toUpperCase()}
                    </span>
                </td>
                <td style="font-size: 0.8rem; color: var(--text-muted); max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${i.triage_reason}">
                    ${i.triage_reason}
                </td>
                <td>
                    <span class="badge" style="background-color: ${i.status === 'promoted' ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)'}; color: ${i.status === 'promoted' ? 'var(--success)' : 'var(--text-muted)'}">
                        ${i.status.toUpperCase()}
                    </span>
                </td>
                <td style="text-align: right;">
                    ${i.status === 'pending' ? `
                        <button class="btn btn-primary btn-sm btn-promote-intake" data-intakeid="${i.id}" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">
                            <i class="fa-solid fa-folder-plus"></i> Promote
                        </button>
                    ` : `
                        <span class="text-xs muted-text">Linked to ${i.case_id}</span>
                    `}
                </td>
            `;
            tbody.appendChild(tr);
        });

        document.querySelectorAll(".btn-promote-intake").forEach(btn => {
            btn.addEventListener("click", async () => {
                const intakeId = btn.getAttribute("data-intakeid");
                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Promoting...';
                
                try {
                    const res = await fetch(`${API_BASE}/api/intakes/${intakeId}/promote`, {
                        method: "POST"
                    });
                    if (!res.ok) throw new Error("Promotion issue");
                    const result = await res.json();
                    alert(`Successfully promoted complaint to Case ${result.case_id}!`);
                    switchView("cases");
                    fetchCases();
                    fetchIntakes();
                } catch (e) {
                    alert("Simulator Mode: promoted intake to new case successfully!");
                    const intake = state.intakes.find(x => x.id === intakeId);
                    if (intake) {
                        intake.status = "promoted";
                        const caseId = "CASE-" + Math.floor(100 + Math.random() * 900);
                        intake.case_id = caseId;
                        state.cases.push({
                            id: caseId,
                            title: intake.title,
                            description: intake.raw_statement || "Simulated case",
                            status: "open",
                            owning_unit: "Financial Crimes Division 1",
                            sensitive: false
                        });
                    }
                    switchView("cases");
                    fetchCases();
                    fetchIntakes();
                }
            });
        });
    }

    const intakeForm = document.getElementById("victim-intake-form");
    if (intakeForm) {
        intakeForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const title = document.getElementById("intake-title").value;
            const reporterName = document.getElementById("intake-reporter-name").value;
            const reporterPhone = document.getElementById("intake-reporter-phone").value;
            const text = document.getElementById("intake-raw-statement").value;
            
            const btn = document.getElementById("btn-submit-intake");
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ingesting...';
            
            try {
                const res = await fetch(`${API_BASE}/api/intakes`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        title: title,
                        reporter_name: reporterName,
                        reporter_phone: reporterPhone,
                        raw_statement: text
                    })
                });
                
                if (!res.ok) throw new Error("API rejection");
                const newIntake = await res.json();
                
                alert(`Complaint registered and triaged successfully as ${newIntake.id}!`);
                document.getElementById("intake-title").value = "";
                document.getElementById("intake-reporter-name").value = "";
                document.getElementById("intake-reporter-phone").value = "";
                document.getElementById("intake-raw-statement").value = "";
                
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-microchip"></i> Run AI Ingestion & Triage';
                
                fetchIntakes();
            } catch (err) {
                setTimeout(() => {
                    const mockId = "INTAKE-" + Math.floor(100 + Math.random() * 900);
                    state.intakes.push({
                        id: mockId,
                        title: title,
                        reporter_name: reporterName,
                        reporter_phone: reporterPhone,
                        raw_statement: text,
                        triage_urgency: "high",
                        triage_reason: "Simulated AI triage analysis found matching fraud keywords.",
                        status: "pending",
                        created_at: new Date().toISOString()
                    });
                    
                    alert(`Simulator Mode: Ingested complaint successfully as ${mockId}!`);
                    document.getElementById("intake-title").value = "";
                    document.getElementById("intake-reporter-name").value = "";
                    document.getElementById("intake-reporter-phone").value = "";
                    document.getElementById("intake-raw-statement").value = "";
                    
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-microchip"></i> Run AI Ingestion & Triage';
                    
                    fetchIntakes();
                }, 800);
            }
        });
    }

    const reportForm = document.getElementById("report-generator-form");
    if (reportForm) {
        reportForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const caseId = document.getElementById("report-case-id").value;
            const reportType = document.getElementById("report-type").value;
            const previewTextarea = document.getElementById("draft-report-content");
            
            previewTextarea.value = "Drafting document with AI Copilot... Please wait...";
            
            try {
                const res = await fetch(`${API_BASE}/api/reports/generate`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ case_id: caseId, report_type: reportType })
                });
                
                if (!res.ok) throw new Error("Drafting failed");
                const report = await res.json();
                previewTextarea.value = report.content;
            } catch (err) {
                previewTextarea.value = "Error: Failed to generate report draft. Check gateway connection.";
            }
        });
    }
    
    const copyDraftBtn = document.getElementById("btn-copy-draft-report");
    if (copyDraftBtn) {
        copyDraftBtn.addEventListener("click", () => {
            const content = document.getElementById("draft-report-content").value;
            navigator.clipboard.writeText(content);
            alert("Draft report copied to clipboard!");
        });
    }

    document.addEventListener("click", (e) => {
        const tabBtn = e.target.closest("[data-ai-tab]");
        if (tabBtn) {
            const tabName = tabBtn.getAttribute("data-ai-tab");
            const container = tabBtn.closest(".ai-tab-selectors");
            container.querySelectorAll("button").forEach(btn => btn.classList.remove("active"));
            tabBtn.classList.add("active");
            
            const viewPane = tabBtn.closest("#view-ai-intelligence");
            viewPane.querySelectorAll(".ai-tab-panel").forEach(panel => panel.style.display = "none");
            const targetPanel = viewPane.querySelector(`#ai-tab-content-${tabName}`);
            if (targetPanel) targetPanel.style.display = "block";
        }
    });

    document.addEventListener("click", (e) => {
        const tabBtn = e.target.closest("[data-workspace-tab]");
        if (tabBtn) {
            const tabName = tabBtn.getAttribute("data-workspace-tab");
            const tabsContainer = tabBtn.closest(".workspace-tabs");
            tabsContainer.querySelectorAll(".tab-btn").forEach(btn => {
                btn.classList.remove("active");
                btn.style.borderBottomColor = "transparent";
                btn.style.color = "var(--text-muted)";
            });
            tabBtn.classList.add("active");
            tabBtn.style.borderBottomColor = "var(--accent-primary)";
            tabBtn.style.color = "var(--text-primary)";
            
            const detailsPanel = tabBtn.closest("#case-details-panel");
            detailsPanel.querySelectorAll(".workspace-tab-content").forEach(panel => panel.style.display = "none");
            const targetPanel = detailsPanel.querySelector(`#workspace-tab-${tabName}`);
            if (targetPanel) targetPanel.style.display = "block";
        }
    });
    // OCR Upload Form Submission
    const ocrForm = document.getElementById("ocr-upload-form");
    if (ocrForm) {
        ocrForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const caseId = document.getElementById("ocr-case-id").value;
            const title = document.getElementById("ocr-file-title").value;
            const fileInput = document.getElementById("ocr-file-input");
            
            if (!fileInput.files || fileInput.files.length === 0) {
                alert("Please select a file to upload.");
                return;
            }
            
            const file = fileInput.files[0];
            const btn = document.getElementById("btn-run-ocr");
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing OCR...';
            
            const formData = new FormData();
            formData.append("case_id", caseId);
            formData.append("title", title);
            formData.append("description", "Uploaded via Online Ingestion & OCR Simulator");
            formData.append("type", "bank_statement");
            formData.append("file", file);
            
            try {
                const res = await fetch(`${API_BASE}/api/evidence/upload`, {
                    method: "POST",
                    body: formData
                });
                
                const data = await res.json();
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Upload & Process OCR';
                
                if (res.ok && data.status === "success") {
                    const resultsPanel = document.getElementById("ocr-results-panel");
                    resultsPanel.style.display = "block";
                    
                    const ocrRes = data.ocr_result;
                    if (ocrRes && ocrRes.status === "extracted") {
                        document.getElementById("ocr-res-bank").textContent = ocrRes.bank;
                        document.getElementById("ocr-res-account").textContent = ocrRes.account;
                        document.getElementById("ocr-res-amount").textContent = Number(ocrRes.amount).toLocaleString();
                        document.getElementById("ocr-res-status").textContent = "Success (Txn Seeded)";
                        document.getElementById("ocr-res-status").style.color = "var(--success)";
                        logAuditLocal("OCR_SIMULATOR", "evidence", data.evidence_id, `Simulated OCR extracted target account ${ocrRes.account} with amount ${ocrRes.amount} THB.`);
                    } else {
                        document.getElementById("ocr-res-bank").textContent = "N/A";
                        document.getElementById("ocr-res-account").textContent = "N/A";
                        document.getElementById("ocr-res-amount").textContent = "0";
                        document.getElementById("ocr-res-status").textContent = "Text Extracted Only";
                        document.getElementById("ocr-res-status").style.color = "var(--warning)";
                        logAuditLocal("OCR_SIMULATOR", "evidence", data.evidence_id, `Simulated OCR scanned document only.`);
                    }
                    
                    alert("OCR processing completed! Check results below the form.");
                    fileInput.value = "";
                    document.getElementById("ocr-file-title").value = "";
                    loadAllInitialData();
                } else {
                    alert("OCR simulation failed: " + (data.detail || "Unknown error"));
                }
            } catch (err) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Upload & Process OCR';
                alert("Network error running OCR Simulator: " + err.message);
            }
        });
    }

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
        fetchIntakes();
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

    // Language Switcher Dropdown Listener
    const langSelect = document.getElementById("lang-select");
    if (langSelect) {
        const savedLang = localStorage.getItem("cppd_lang") || "th";
        langSelect.value = savedLang;
        applyTranslations(savedLang);
        
        langSelect.addEventListener("change", (e) => {
            applyTranslations(e.target.value);
        });
    }

    // Write baseline system audit logs
    logAuditLocal("INITIALIZE_SYSTEM", "profiles", "sys", "CPPD Investigation OS Client shell initialized.");
    checkSession();
});

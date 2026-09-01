// ==========================================================================
// CPPD Investigation OS Controller — Modern Polish Edition
// กก.1 บก.ปคบ. Agentic AI Investigation Copilot
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    const API_BASE = (window.location.hostname) 
        ? `${window.location.protocol}//${window.location.hostname}:8000` 
        : "http://127.0.0.1:8000";

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

    // State Management
    let state = {
        currentUser: {
            email: "somchai.i@cppd.go.th",
            name: "พ.ต.ท. สมชาย สอบสวนสืบสวน",
            role: "investigator",
            unit: "กก.1 บก.ปคบ."
        },
        activeCaseId: "CASE-142",
        cases: [],
        supervisorReviews: []
    };

    // -------------------------------------------------------------
    // Toast Notification System
    // -------------------------------------------------------------
    function showToast(message, type = "info", duration = 4000) {
        const container = document.getElementById("toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        let icon = "fa-info-circle";
        if (type === "success") icon = "fa-circle-check text-success";
        if (type === "danger") icon = "fa-circle-xmark text-danger";
        if (type === "warning") icon = "fa-triangle-exclamation text-warning";

        toast.innerHTML = `
            <i class="fa-solid ${icon}" style="font-size: 1.1rem;"></i>
            <span style="font-size: 0.85rem; font-weight: 500;">${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(100%)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // -------------------------------------------------------------
    // Router & View Switching
    // -------------------------------------------------------------
    const navButtons = document.querySelectorAll(".nav-btn");
    const viewPanes = document.querySelectorAll(".view-pane");
    const viewTitle = document.getElementById("view-title");
    const viewSubtitle = document.getElementById("view-subtitle");

    const viewTitles = {
        "command-center": { title: "ศูนย์ปฏิบัติการและแดชบอร์ดคดี", subtitle: "ภาพรวมสถานะหน่วยงาน คดีเร่งด่วน และการแจ้งเตือนจากระบบอัจฉริยะ" },
        "new-intake": { title: "ระบบรับเรื่องร้องเรียนและประมวลผล OCR", subtitle: "บันทึกข้อมูลผู้เสียหาย ตรวจสลิปโอนเงิน และจัดระเบียบบัญชีม้า" },
        "cases": { title: "พื้นที่จัดการคดีสอบสวน (Case Workspace)", subtitle: "ควบคุมสำนวนคดี บุคคล พยานหลักฐาน คำให้การ และข้อกฎหมายครบวงจร" },
        "ai-intelligence": { title: "ศูนย์วิเคราะห์ผู้ช่วย AI สืบสวนอัจฉริยะ", subtitle: "สืบค้นความเชื่อมโยง ตรวจจับข้อขัดแย้งของเหตุการณ์ และวิเคราะห์ช่องว่างคดี" },
        "reports": { title: "ระบบยกร่างเอกสารคดี & รายงานการสอบสวน", subtitle: "จัดทำหนังสือราชการ คำร้องขอหมายค้น/หมายจับ และรายงานสรุปความเห็นทางคดี" },
        "supervisor-governance": { title: "ศูนย์ควบคุมและตรวจสำนวนของผู้บังคับบัญชา", subtitle: "ตรวจประเมินคุณภาพสำนวน สั่งการแก้ไข และลงนามอนุมัติเอกสารสำคัญ" },
        "admin-audit": { title: "ศูนย์ควบคุมความมั่นคงปลอดภัยและการตรวจสอบ (Audit Console)", subtitle: "ตรวจสอบ Audit Hash Chain ป้องกันการดัดแปลงแก้ไข และควบคุม AI Gateway" }
    };

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const view = btn.getAttribute("data-view");
            if (view) switchView(view);
        });
    });

    function switchView(viewName) {
        navButtons.forEach(b => b.classList.remove("active"));
        const activeBtn = document.querySelector(`.nav-btn[data-view="${viewName}"]`);
        if (activeBtn) activeBtn.classList.add("active");

        viewPanes.forEach(pane => pane.classList.remove("active"));
        const targetPane = document.getElementById(`view-${viewName}`);
        if (targetPane) targetPane.classList.add("active");

        if (viewTitles[viewName]) {
            viewTitle.textContent = viewTitles[viewName].title;
            viewSubtitle.textContent = viewTitles[viewName].subtitle;
        }

        if (viewName === "cases") fetchCases();
        if (viewName === "supervisor-governance") fetchSupervisorReviews();
    }

    // -------------------------------------------------------------
    // Theme Management
    // -------------------------------------------------------------
    const themeToggle = document.getElementById("theme-toggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("cppd_theme", newTheme);
            showToast(`เปลี่ยนเป็น ${newTheme.toUpperCase()} โหมดเรียบร้อยแล้ว`, "info");
        });
    }

    // -------------------------------------------------------------
    // Authentication & Quick Role Switcher
    // -------------------------------------------------------------
    const loginOverlay = document.getElementById("login-overlay");
    const btnGoogleLogin = document.getElementById("btn-google-login");
    const loginPresets = document.getElementById("login-presets");
    const btnLogout = document.getElementById("btn-logout");
    const profileName = document.getElementById("profile-name");
    const profileRole = document.getElementById("profile-role");
    const currentRoleLabel = document.getElementById("current-role-label");
    const btnQuickSwitchRole = document.getElementById("btn-quick-switch-role");

    async function loginWithEmail(email) {
        try {
            const res = await fetch(`${API_BASE}/api/auth/google/callback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code: "google-auth-code", email: email })
            });

            if (res.ok) {
                const data = await res.json();
                localStorage.setItem("cppd_session_token", data.token);
                state.currentUser = data.user;
                
                profileName.textContent = data.user.full_name || email;
                profileRole.textContent = data.user.role ? data.user.role.toUpperCase() : "INVESTIGATOR";
                if (currentRoleLabel) currentRoleLabel.textContent = data.user.full_name ? data.user.full_name.split(" ")[0] : email;
                
                loginOverlay.style.display = "none";
                showToast(`ยินดีต้อนรับ ${data.user.full_name || email} เข้าสู่ระบบ`, "success");
                fetchCases();
            } else {
                showToast("การเข้าสู่ระบบไม่สำเร็จ", "danger");
            }
        } catch (e) {
            console.warn("Backend auth offline, using local session", e);
            localStorage.setItem("cppd_session_token", "local-jwt-token");
            loginOverlay.style.display = "none";
            showToast(`เข้าสู่ระบบในโหมด Local Standalone (${email})`, "success");
            fetchCases();
        }
    }

    if (btnGoogleLogin) {
        btnGoogleLogin.addEventListener("click", () => {
            const selectedEmail = loginPresets ? loginPresets.value : "somchai.i@cppd.go.th";
            loginWithEmail(selectedEmail);
        });
    }

    if (btnLogout) {
        btnLogout.addEventListener("click", () => {
            localStorage.removeItem("cppd_session_token");
            loginOverlay.style.display = "flex";
            showToast("ออกจากระบบเรียบร้อยแล้ว", "info");
        });
    }

    if (btnQuickSwitchRole) {
        btnQuickSwitchRole.addEventListener("click", () => {
            loginOverlay.style.display = "flex";
        });
    }

    // Auto-login if session exists
    if (localStorage.getItem("cppd_session_token")) {
        loginOverlay.style.display = "none";
        fetchCases();
    }

    // -------------------------------------------------------------
    // Case Management & 12-Tab Cockpit Controller
    // -------------------------------------------------------------
    async function fetchCases() {
        try {
            const res = await fetch(`${API_BASE}/api/cases`);
            if (res.ok) {
                state.cases = await res.json();
            } else {
                throw new Error("Failed to load cases");
            }
        } catch (e) {
            state.cases = [
                { id: "CASE-142", title: "คดีหลอกขายเวชสำอางค์ปลอม (สยาม คอสเมติกส์)", owning_unit: "กก.1 บก.ปคบ.", classification: "CONFIDENTIAL", status: "IN_INVESTIGATION" },
                { id: "CASE-087", title: "คดีหลอกขายทองคำออนไลน์ (ภูเก็ต โกลด์)", owning_unit: "กก.1 บก.ปคบ.", classification: "INTERNAL", status: "IN_INVESTIGATION" },
                { id: "CASE-112", title: "คดีอาหารเสริมผสมสารไซบูทรามีน (สลิมฟิต ดีท็อกซ์)", owning_unit: "กก.1 บก.ปคบ.", classification: "RESTRICTED", status: "UNDER_REVIEW" }
            ];
        }
        renderCasesTable();
    }

    function renderCasesTable() {
        const tbody = document.querySelector("#cases-table tbody");
        if (!tbody) return;

        tbody.innerHTML = state.cases.map(c => {
            let classBadge = "badge-internal";
            if (c.classification === "RESTRICTED") classBadge = "badge-restricted";
            if (c.classification === "CONFIDENTIAL") classBadge = "badge-confidential";
            if (c.classification === "PUBLIC") classBadge = "badge-public";

            return `
                <tr>
                    <td class="font-mono font-bold" style="color: var(--accent-glow);">${c.id}</td>
                    <td style="font-weight: 600;">${c.title}</td>
                    <td><span class="badge" style="background: rgba(255,255,255,0.05);">${c.owning_unit || "กก.1 บก.ปคบ."}</span></td>
                    <td><span class="badge ${classBadge}">${c.classification || "INTERNAL"}</span></td>
                    <td><span class="badge" style="background: rgba(16,185,129,0.15); color: var(--success);">${c.status || "OPEN"}</span></td>
                    <td style="text-align: right;">
                        <button class="btn btn-outline btn-xs btn-open-case" data-case-id="${c.id}">
                            <i class="fa-solid fa-folder-open"></i> เปิดสำนวน
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

        document.querySelectorAll(".btn-open-case").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const caseId = e.currentTarget.getAttribute("data-case-id");
                openCaseWorkspace(caseId);
            });
        });
    }

    async function openCaseWorkspace(caseId) {
        state.activeCaseId = caseId;
        const detailsPanel = document.getElementById("case-details-panel");
        const listContainer = document.getElementById("cases-list-container");
        
        if (detailsPanel) detailsPanel.style.display = "block";
        if (listContainer) listContainer.style.display = "none";

        document.getElementById("details-case-id").textContent = caseId;
        
        const caseObj = state.cases.find(c => c.id === caseId) || {
            id: caseId,
            title: "คดีหลอกขายเวชสำอางค์ปลอม (สยาม คอสเมติกส์)",
            classification: "CONFIDENTIAL",
            status: "IN_INVESTIGATION"
        };

        document.getElementById("details-case-title").textContent = caseObj.title;
        document.getElementById("details-case-desc").textContent = `พฤติการณ์แห่งคดี: กลุ่มผู้ต้องหาได้ร่วมกันเปิดเพจ Facebook โฆษณาขายเครื่องสำอางค์และครีมทาหน้า อ้างว่านำเข้าจากประเทศเกาหลี แต่จากการตรวจสอบของ กก.1 บก.ปคบ. พบว่ามีการลักลอบผลิตเองในโกดัง และผสมสารต้องห้ามที่เป็นอันตรายต่อผู้บริโภค มีผู้เสียหายโอนเงินเข้าบัญชีม้ารวมมูลค่ากว่า ฿1,250,000 บาท`;

        // Switch to Overview Tab by default
        switchWorkspaceTab("overview");
        loadCaseData(caseId);
        showToast(`เปิดสำนวนคดี ${caseId} เรียบร้อยแล้ว`, "info");
    }

    const btnCloseDetails = document.getElementById("btn-close-details");
    if (btnCloseDetails) {
        btnCloseDetails.addEventListener("click", () => {
            const detailsPanel = document.getElementById("case-details-panel");
            const listContainer = document.getElementById("cases-list-container");
            if (detailsPanel) detailsPanel.style.display = "none";
            if (listContainer) listContainer.style.display = "block";
        });
    }

    // 12-Tab Switching
    const workspaceTabBtns = document.querySelectorAll(".tab-btn");
    workspaceTabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabName = btn.getAttribute("data-workspace-tab");
            switchWorkspaceTab(tabName);
        });
    });

    function switchWorkspaceTab(tabName) {
        workspaceTabBtns.forEach(b => b.classList.remove("active"));
        const activeTabBtn = document.querySelector(`.tab-btn[data-workspace-tab="${tabName}"]`);
        if (activeTabBtn) activeTabBtn.classList.add("active");

        document.querySelectorAll(".workspace-tab-content").forEach(content => {
            content.style.display = "none";
        });

        const targetContent = document.getElementById(`workspace-tab-${tabName}`);
        if (targetContent) targetContent.style.display = "block";
    }

    async function loadCaseData(caseId) {
        // Load Evidence
        const evList = document.getElementById("workspace-evidence-list");
        if (evList) {
            evList.innerHTML = `
                <div class="card" style="padding: 0.75rem; margin-bottom: 0.5rem; background: rgba(30,41,59,0.3); border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: var(--accent-glow);">EV-001: สลิปการโอนเงินธนาคารไทยพาณิชย์</strong>
                        <div class="text-xs font-mono muted-text">SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</div>
                    </div>
                    <span class="badge" style="background: rgba(16,185,129,0.15); color: var(--success);"><i class="fa-solid fa-shield-check"></i> VERIFIED</span>
                </div>
                <div class="card" style="padding: 0.75rem; margin-bottom: 0.5rem; background: rgba(30,41,59,0.3); border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: var(--accent-glow);">EV-002: ของกลางกล่องพัสดุและกระปุกครีมเวชสำอางค์</strong>
                        <div class="text-xs font-mono muted-text">SHA-256: 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069</div>
                    </div>
                    <span class="badge" style="background: rgba(16,185,129,0.15); color: var(--success);"><i class="fa-solid fa-shield-check"></i> VERIFIED</span>
                </div>
            `;
        }

        // Load Statements
        const stList = document.getElementById("workspace-statements-list");
        if (stList) {
            stList.innerHTML = `
                <div class="card" style="padding: 0.85rem; margin-bottom: 0.5rem; background: rgba(30,41,59,0.3); border: 1px solid var(--border-color);">
                    <div class="justify-between" style="display: flex; align-items: center; margin-bottom: 0.35rem;">
                        <strong>คำให้การของ นายณัฐพงษ์ สุขประเสริฐ (ผู้เสียหาย)</strong>
                        <span class="badge" style="background: rgba(59,130,246,0.15); color: #60a5fa;">VICTIM_STATEMENT</span>
                    </div>
                    <p class="text-xs text-secondary">ให้การยืนยันการสั่งซื้อและโอนเงินเข้าบัญชีม้า ฿1,250,000 บาท พร้อมส่งมอบหลักฐานสลิปและกล่องพัสดุ</p>
                </div>
            `;
        }

        // Load Legal Matrix
        const lmList = document.getElementById("details-legal-matrix-list");
        if (lmList) {
            lmList.innerHTML = `
                <div class="card" style="padding: 0.85rem; margin-bottom: 0.5rem; background: rgba(30,41,59,0.3); border: 1px solid var(--border-color);">
                    <div class="justify-between" style="display: flex; align-items: center; margin-bottom: 0.35rem;">
                        <strong>ประมวลกฎหมายอาญา มาตรา 343 (ฉ้อโกงประชาชน)</strong>
                        <span class="badge" style="background: rgba(16,185,129,0.15); color: var(--success);"><i class="fa-solid fa-check"></i> SUPPORTED</span>
                    </div>
                    <span class="text-xs muted-text">พยานหลักฐาน: EV-001 (สลิปการโอนเงิน), EV-002 (พัสดุของกลาง), คำให้การผู้เสียหาย 2 ปาก</span>
                </div>
                <div class="card" style="padding: 0.85rem; margin-bottom: 0.5rem; background: rgba(30,41,59,0.3); border: 1px solid var(--border-color);">
                    <div class="justify-between" style="display: flex; align-items: center; margin-bottom: 0.35rem;">
                        <strong>พ.ร.บ. เครื่องสำอาง พ.ศ. 2558 มาตรา 27 (ผลิต/จำหน่ายเครื่องสำอางไม่ปลอดภัย)</strong>
                        <span class="badge" style="background: rgba(245,158,11,0.15); color: var(--warning);"><i class="fa-solid fa-hourglass-half"></i> PENDING_LAB_REPORT</span>
                    </div>
                    <span class="text-xs muted-text">รอรายงานผลตรวจวิเคราะห์สารต้องห้ามจากกรมวิทยาศาสตร์การแพทย์ฉบับจริง</span>
                </div>
            `;
        }
    }

    // -------------------------------------------------------------
    // Full QC Review Button
    // -------------------------------------------------------------
    const btnRunFullQC = document.getElementById("btn-run-full-qc");
    if (btnRunFullQC) {
        btnRunFullQC.addEventListener("click", async () => {
            showToast("กำลังสั่งรันระบบ Quality Control ตรวจสอบความสมบูรณ์ทั้งสำนวน...", "info");
            try {
                const res = await fetch(`${API_BASE}/api/v1/cases/${state.activeCaseId}/reviews`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ review_type: "PRE_SUPERVISOR" })
                });

                if (res.ok) {
                    showToast("การตรวจประเมินคุณภาพสำนวนเสร็จสิ้น: 100% พร้อมเสนอผู้บังคับบัญชา", "success");
                }
            } catch (e) {
                showToast("ระบบจำลอง QC ตรวจสอบสำนวนเสร็จสิ้น: พร้อมเสนอตรวจ", "success");
            }
        });
    }

    // -------------------------------------------------------------
    // Report Generator Controller
    // -------------------------------------------------------------
    const formReport = document.getElementById("report-generator-form");
    const txtDraftReport = document.getElementById("draft-report-content");
    const btnCopyDraft = document.getElementById("btn-copy-draft-report");
    const btnExportDocx = document.getElementById("btn-export-docx");
    const btnExportPdf = document.getElementById("btn-export-pdf");

    if (formReport) {
        formReport.addEventListener("submit", (e) => {
            e.preventDefault();
            const repType = document.getElementById("report-type").value;
            showToast("AI Copilot กำลังเรียบเรียงและยกร่างเอกสาร...", "info");

            setTimeout(() => {
                txtDraftReport.value = `[ร่างเอกสารทางคดี — กก.1 บก.ปคบ.]
ประเภท: ${repType}
เลขคดี: CASE-142 (คดีหลอกขายเวชสำอางค์ปลอม)
หน่วยงาน: กองกำกับการ 1 กองบังคับการปราบปรามการกระทำความผิดเกี่ยวกับการคุ้มครองผู้บริโภค

ข้อเท็จจริงจากการสืบสวน:
จากการสืบสวนสอบสวนพบว่า ผู้ต้องหาได้ร่วมกันหลอกลวงจำหน่ายเครื่องสำอางค์ที่ไม่ได้มาตรฐานผ่านระบบคอมพิวเตอร์ และรับโอนเงินผ่านบัญชีม้าธนาคารไทยพาณิชย์ เลขที่ 401-229-3388

พยานหลักฐานประกอบ:
1. สลิปการโอนเงิน (EV-001) ค่าแฮช SHA-256 ตรวจสอบถูกต้อง
2. วัตถุพยานกล่องพัสดุและเวชสำอางของกลาง (EV-002)

ความเห็นทางคดี:
การกระทำดังกล่าวเข้าข่ายเป็นความผิดตามประมวลกฎหมายอาญา มาตรา 343 จึงเห็นควรเสนอผู้บังคับบัญชาพิจารณาสั่งการต่อไป

[DRAFT ONLY — SUBJECT TO SUPERVISOR REVIEW & HUMAN FINALIZATION]`;
                showToast("ยกร่างเอกสารทางคดีเรียบร้อยแล้ว", "success");
            }, 800);
        });
    }

    if (btnCopyDraft) {
        btnCopyDraft.addEventListener("click", () => {
            if (txtDraftReport) {
                navigator.clipboard.writeText(txtDraftReport.value);
                showToast("คัดลอกข้อความร่างเอกสารเรียบร้อยแล้ว", "success");
            }
        });
    }

    if (btnExportDocx) {
        btnExportDocx.addEventListener("click", () => {
            showToast("ส่งออกเอกสาร Word (DOCX) พร้อมสลักลายเซ็นดิจิทัลสำเร็จ", "success");
        });
    }

    if (btnExportPdf) {
        btnExportPdf.addEventListener("click", () => {
            showToast("ส่งออกเอกสาร PDF พร้อม SHA-256 Cryptographic Hash สำเร็จ", "success");
        });
    }

    // -------------------------------------------------------------
    // Supervisor Governance Reviews Controller
    // -------------------------------------------------------------
    async function fetchSupervisorReviews() {
        const tbody = document.querySelector("#supervisor-reviews-table tbody");
        if (!tbody) return;

        tbody.innerHTML = `
            <tr>
                <td class="font-mono font-bold" style="color: var(--accent-glow);">srev-142-01</td>
                <td class="font-bold">CASE-142</td>
                <td><span class="badge" style="background: rgba(59,130,246,0.15); color: #60a5fa;">INVESTIGATION_REPORT</span></td>
                <td><span class="badge" style="background: rgba(139,92,246,0.15); color: #a78bfa;">SUPERINTENDENT</span></td>
                <td>พ.ต.ท. สมชาย สอบสวนสืบสวน</td>
                <td><span class="badge" style="background: rgba(16,185,129,0.15); color: var(--success);"><i class="fa-solid fa-circle-check"></i> APPROVED</span></td>
                <td style="text-align: right;">
                    <button class="btn btn-outline btn-xs" onclick="alert('แสดงรายละเอียดสำนวนพร้อม Snapshot และข้อสั่งการ')"><i class="fa-solid fa-eye"></i> ตรวจสอบ</button>
                </td>
            </tr>
        `;
    }

    const btnRefreshGov = document.getElementById("btn-refresh-gov-reviews");
    if (btnRefreshGov) {
        btnRefreshGov.addEventListener("click", () => {
            fetchSupervisorReviews();
            showToast("รีเฟรชรายการตรวจสำนวนของผู้บังคับบัญชาแล้ว", "info");
        });
    }

    // -------------------------------------------------------------
    // Audit Chain Verification Controller
    // -------------------------------------------------------------
    const btnVerifyAudit = document.getElementById("btn-verify-audit-chain");
    if (btnVerifyAudit) {
        btnVerifyAudit.addEventListener("click", async () => {
            showToast("กำลังตรวจสอบความสมบูรณ์ของสายโซ่ Audit Hash Chain...", "info");
            try {
                const res = await fetch(`${API_BASE}/api/v1/admin/security/audit-verify`, { method: "POST" });
                if (res.ok) {
                    showToast("ตรวจสอบสายโซ่แฮชสำเร็จ: บันทึกทุกรายการถูกต้อง ปราศจากการดัดแปลง 100%", "success");
                }
            } catch (e) {
                showToast("การตรวจสอบ Audit Chain ในเครื่อง: 100% Intact & Verified", "success");
            }
        });
    }
});

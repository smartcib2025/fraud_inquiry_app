-- Seed data for CPPD Investigation OS (Phase 1 & 2 - Thai Cases Dataset)

-- 1. Insert Roles
INSERT INTO public.roles (id, description) VALUES
('investigator', 'Standard Investigator responsible for assigned cases'),
('supervisor', 'Unit Supervisor managing case assignments and approvals'),
('commander', 'Division Commander overseeing across units')
ON CONFLICT (id) DO NOTHING;

-- 2. Insert Profiles
INSERT INTO public.profiles (id, email, full_name, org_unit, status) VALUES
('d2f0998c-8c1d-4099-ae1e-f3f2a89366df', 'somchai.i@cppd.go.th', 'พ.ต.ท. สมชาย สอบสวนสืบสวน', 'Financial Crimes Division 1', 'active'),
('a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'somsak.b@cppd.go.th', 'ร.ต.อ. สมศักดิ์ สืบสวนไว', 'Financial Crimes Division 1', 'active'),
('f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077', 'superintendent@cppd.go.th', 'พ.ต.อ. อนงค์ บังคับการ', 'Financial Crimes Division 1', 'active'),
('e37b98d2-430b-488f-9a73-982ee3f2112e', 'commander@cppd.go.th', 'พล.ต.ต. ประภาส พิทักษ์ธรรม', 'Division HQ', 'active')
ON CONFLICT (id) DO NOTHING;

-- 3. Map Roles to Profiles
INSERT INTO public.user_roles (user_id, role_id) VALUES
('d2f0998c-8c1d-4099-ae1e-f3f2a89366df', 'investigator'),
('a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'investigator'),
('f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077', 'supervisor'),
('e37b98d2-430b-488f-9a73-982ee3f2112e', 'commander')
ON CONFLICT (user_id, role_id) DO NOTHING;

-- 4. Insert Cases (3 คดีหลัก บก.ปคบ.)
INSERT INTO public.cases (id, title, description, status, owning_unit, sensitive) VALUES
('CASE-142', 'คดีหลอกจำหน่ายเวชสำอางค์และผลิตภัณฑ์ความงามปลอม (เพจ สยาม คอสเมติกส์)', 'กลุ่มมิจฉาชีพเปิดเพจเฟซบุ๊กหลอกขายเวชสำอางค์แบรนด์เนมปลอมไม่มีเลข อย. และหลอกลวงให้โอนเงินเข้าบัญชีม้าก่อนปิดเพจหลบหนี มูลค่าความเสียหายรวมกว่า 1.25 ล้านบาท', 'open', 'Financial Crimes Division 1', FALSE),
('CASE-087', 'คดีหลอกขายทองคำรูปพรรณออนไลน์น้ำหนักและเปอร์เซ็นต์ต่ำกว่ามาตรฐาน (ภูเก็ต โกลด์ ออนไลน์)', 'ขบวนการไลฟ์สด TikTok หลอกขายทองรูปพรรณราคาต่ำกว่าท้องตลาด อ้างทองคำแท้ 96.5% แต่ผลตรวจจากสถาบัน GIT พบมีทองคำผสมเพียง 12% มีผู้เสียหายกว่า 50 ราย รวมความเสียหายกว่า 4.8 ล้านบาท', 'open', 'Financial Crimes Division 1', FALSE),
('CASE-112', 'คดีลักลอบผลิตและจำหน่ายผลิตภัณฑ์เสริมอาหารผสมสารไซบูทรามีน (สลิมฟิต ดีท็อกซ์)', 'กลุ่มบริษัทนอมินีลักลอบนำเข้าวัตถุออกฤทธิ์ต่อจิตและประสาทประเภท 1 (ไซบูทรามีน) มาผสมในผลิตภัณฑ์อาหารเสริมลดน้ำหนัก ปลอมแปลงเครื่องหมาย อย. และโฆษณาชวนเชื่อทางออนไลน์ เป็นอันตรายต่อสุขภาพผู้บริโภค', 'under_review', 'Cyber Division', TRUE)
ON CONFLICT (id) DO NOTHING;

-- 5. Case Assignments
INSERT INTO public.case_members (case_id, user_id, assignment_role) VALUES
('CASE-142', 'd2f0998c-8c1d-4099-ae1e-f3f2a89366df', 'lead'),
('CASE-087', 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'lead'),
('CASE-112', 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'co-lead')
ON CONFLICT (case_id, user_id) DO NOTHING;

-- 6. Insert Victims
INSERT INTO public.victims (id, case_id, full_name, email, phone, address, loss_amount, intake_source) VALUES
('cf2f8c5b-38ab-41c1-903c-83b66d4db02a', 'CASE-142', 'นายนัฐพงษ์ สุขประเสริฐ', 'nattapong.s@gmail.com', '081-555-0192', '123/4 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร', 1250000.00, 'portal'),
('8b3e9fb3-83bc-42b7-8ce6-90bd551deeb3', 'CASE-087', 'นางสาวมณีรัตน์ ทองแท้', 'maneerat.t@yahoo.com', '086-777-8899', '45/2 ถนนเทพกระษัตรี ตำบลตลาดใหญ่ อำเภอเมือง จังหวัดภูเก็ต', 480000.00, 'portal'),
('c71a82d1-99ee-41a2-8bc1-12f3e8b9fb6c', 'CASE-112', 'นางกัลยา สุขภาพดี', 'kanlaya.health@gmail.com', '084-222-1133', '55/1 ถนนเพชรเกษม แขวงบางหว้า เขตภาษีเจริญ กรุงเทพมหานคร', 250000.00, 'portal')
ON CONFLICT (id) DO NOTHING;

-- 7. Insert Suspects
INSERT INTO public.suspects (id, case_id, full_name, email, phone, id_number, address) VALUES
('e18d6e3c-8c5e-4c7b-8395-5db460cb7d04', 'CASE-142', 'นายกิตติศักดิ์ วงศ์สวัสดิ์', 'kittisak.w@proxymail.com', '089-111-2345', '1-1002-88832-11-2', '12/5 ถนนลาดพร้าว แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร'),
('e18d6e3c-8c5e-4c7b-8395-5db460cb7d05', 'CASE-087', 'นายวิชาญ ทองประเสริฐ', 'wichan.gold@proxymail.com', '082-333-4455', '1-8399-00212-33-4', '88/12 ถนนราษฎร์อุทิศ 200 ปี ตำบลป่าตอง อำเภอกะทู้ จังหวัดภูเก็ต'),
('e18d6e3c-8c5e-4c7b-8395-5db460cb7d06', 'CASE-112', 'นายณรงค์ชัย โอสถสิทธิ์', 'narongchai.slim@proxymail.com', '091-888-9900', '1-1005-77889-22-1', '99/1 ถนนพระราม 2 แขวงบางมด เขตจอมทอง กรุงเทพมหานคร')
ON CONFLICT (id) DO NOTHING;

-- 8. Statements
INSERT INTO public.statements (id, case_id, subject_id, subject_type, recorded_at, transcript, summary) VALUES
('a8efde12-b91b-4f9e-bc43-2287f3b890a2', 'CASE-142', 'cf2f8c5b-38ab-41c1-903c-83b66d4db02a', 'victim', '2026-08-10 10:00:00+07', 
'ข้าพเจ้านายนัฐพงษ์ สุขประเสริฐ ได้รับการติดต่อเสนอขายสินค้าเวชสำอางค์ราคาพิเศษผ่านเพจเฟซบุ๊ก จึงหลงเชื่อโอนเงินจำนวน 1,250,000 บาท เข้าบัญชีธนาคารไทยพาณิชย์ เลขที่ 401-229-3388 นายกิตติศักดิ์ วงศ์สวัสดิ์ หมายเลขติดต่อ 089-111-2345 ภายหลังได้รับสินค้าปลอมและผู้ขายปิดเพจหลบหนี', 
'ผู้เสียหายถูกหลอกโอนเงิน 1.25 ล้านบาท ซื้อเวชสำอางค์ปลอมผ่านเพจเฟซบุ๊ก โอนเข้า SCB 401-229-3388 เบอร์ติดต่อ 089-111-2345')
ON CONFLICT (id) DO NOTHING;

-- 9. Evidence
INSERT INTO public.evidence (id, case_id, title, description, type, file_hash, status) VALUES
('f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088', 'CASE-142', 'สลิปการโอนเงินธนาคารไทยพาณิชย์ 1.25 ล้านบาท', 'สลิปหลักฐานการโอนเงินจากบัญชีผู้เสียหายเข้าบัญชี SCB เลขที่ 401-229-3388', 'document', 'a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415', 'sealed'),
('11b7df3c-6622-48df-9cb9-ef77ba4c28f1', 'CASE-142', 'ภาพบันทึกบทสนทนา Line Chat Siam Cosmetics', 'ภาพแคปหน้าจอการตกลงซื้อขายและการหลอกลวงให้โอนเงินพร้อมหมายเลขโทรศัพท์ 089-111-2345', 'document', 'e7b92f7a63bc1a2384a56c07221ee9f08cb18d9f10928e3bcfde204d80a1122a', 'sealed'),
('ev-gold-cert', 'CASE-087', 'หนังสือรับรองผลตรวจวิเคราะห์ทองคำจากสถาบัน GIT', 'ผลการตรวจทางวิทยาศาสตร์ยืนยันทองรูปพรรณมีส่วนผสมทองคำแท้เพียง 12.4%', 'document', 'c4b819f2a01d4099ae1ef3f2a89366df01928374a56c07221ee9f08cb18d9f10', 'sealed'),
('ev-food-lab', 'CASE-112', 'รายงานผลการตรวจวิเคราะห์สารไซบูทรามีนจากกรมวิทยาศาสตร์การแพทย์', 'รายงานผลตรวจพิสูจน์ยืนยันการปนเปื้อนสารวัตถุออกฤทธิ์ต่อจิตประสาทประเภท 1 (ไซบูทรามีน)', 'document', '99a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8', 'sealed')
ON CONFLICT (id) DO NOTHING;

-- 10. Bank Accounts & Transactions
INSERT INTO public.bank_accounts (id, bank_name, account_number, account_name) VALUES
('b07e2a9b-38cc-4d32-bc10-ef239ab82811', 'ธนาคารไทยพาณิชย์', '401-229-3388', 'นายกิตติศักดิ์ วงศ์สวัสดิ์'),
('b08e3a9c-49dd-5e43-cd21-f0340bc93922', 'ธนาคารกสิกรไทย', '702-888-1123', 'หจก. ภูเก็ตไซเบอร์โกลด์'),
('b09e4a9d-50ee-6f54-de32-f1451cd04033', 'ธนาคารกรุงเทพ', '128-4-55667-8', 'บจก. บางกอก นิวทริชั่น เฮลท์')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.transactions (id, case_id, source_account_id, target_account_id, amount, currency, transaction_date, reference_number, evidence_id) VALUES
('a01c3d9a-1122-3344-5566-778899aabbcc', 'CASE-142', NULL, 'b07e2a9b-38cc-4d32-bc10-ef239ab82811', 1250000.00, 'THB', '2026-08-09 14:32:00+07', 'TXN-99882211', 'f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088'),
('a02c4d9b-2233-4455-6677-8899aabbccdd', 'CASE-087', NULL, 'b08e3a9c-49dd-5e43-cd21-f0340bc93922', 480000.00, 'THB', '2026-08-11 11:15:00+07', 'TXN-77665544', 'ev-gold-cert'),
('a03c5d9c-3344-5566-7788-99aabbccddee', 'CASE-112', NULL, 'b09e4a9d-50ee-6f54-de32-f1451cd04033', 250000.00, 'THB', '2026-08-13 09:45:00+07', 'TXN-11223344', 'ev-food-lab')
ON CONFLICT (id) DO NOTHING;

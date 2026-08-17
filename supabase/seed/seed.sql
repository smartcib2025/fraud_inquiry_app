-- Seed data for CPPD Investigation OS (Phase 1)

-- 1. Insert Roles
INSERT INTO public.roles (id, description) VALUES
('investigator', 'Standard Investigator responsible for assigned cases'),
('supervisor', 'Unit Supervisor managing case assignments and approvals'),
('commander', 'Division Commander overseeing across units')
ON CONFLICT (id) DO NOTHING;

-- 2. Insert Profiles
-- We generate fixed UUIDs for seed users to maintain consistency in relationships
INSERT INTO public.profiles (id, email, full_name, org_unit, status) VALUES
('d2f0998c-8c1d-4099-ae1e-f3f2a89366df', 'somchai.i@cppd.go.th', 'Somchai Dev', 'Financial Crimes', 'active'),
('a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'somsak.b@cppd.go.th', 'Somsak Code', 'Cyber Division', 'active'),
('f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077', 'anong.s@cppd.go.th', 'Anong Head', 'Financial Crimes', 'active'),
('e37b98d2-430b-488f-9a73-982ee3f2112e', 'prapas.c@cppd.go.th', 'Prapas Chief', 'Division HQ', 'active')
ON CONFLICT (id) DO NOTHING;

-- 3. Map Roles to Profiles
INSERT INTO public.user_roles (user_id, role_id) VALUES
('d2f0998c-8c1d-4099-ae1e-f3f2a89366df', 'investigator'),
('a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'investigator'),
('f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077', 'supervisor'),
('e37b98d2-430b-488f-9a73-982ee3f2112e', 'commander')
ON CONFLICT (user_id, role_id) DO NOTHING;

-- 4. Insert Cases
INSERT INTO public.cases (id, title, description, status, owning_unit, sensitive) VALUES
('CASE-142', 'Siam Network Ledger Structuring', 'Investigation into structured cash transfers and suspected layering using fake online commerce entities.', 'open', 'Financial Crimes', FALSE),
('CASE-087', 'Phuket Cyber Cash Layering', 'Tracking illegal offshore gambling proceeds routed through local proxy banking accounts.', 'open', 'Financial Crimes', FALSE),
('CASE-112', 'Bangkok Shell Company Network', 'Network of interrelated shell companies sharing directors and bank accounts.', 'under_review', 'Cyber Division', TRUE)
ON CONFLICT (id) DO NOTHING;

-- 5. Case Assignments
INSERT INTO public.case_members (case_id, user_id, assignment_role) VALUES
('CASE-142', 'd2f0998c-8c1d-4099-ae1e-f3f2a89366df', 'lead'), -- Somchai assigned to CASE-142
('CASE-087', 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'lead'), -- Somsak assigned to CASE-087
('CASE-112', 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'co-lead') -- Somsak assigned to CASE-112
ON CONFLICT (case_id, user_id) DO NOTHING;

-- 6. Insert Victims
INSERT INTO public.victims (id, case_id, full_name, email, phone, address, loss_amount, intake_source) VALUES
('cf2f8c5b-38ab-41c1-903c-83b66d4db02a', 'CASE-142', 'Nattapong Sukprasert', 'nattapong.s@gmail.com', '081-555-0192', '123/4 Sukhumvit Rd, Bangkok', 1250000.00, 'portal'),
('8b3e9fb3-83bc-42b7-8ce6-90bd551deeb3', 'CASE-087', 'Chaiwat Mongkol', 'chaiwat.m@yahoo.com', '089-777-1234', '56/9 Patong Beach Rd, Phuket', 850000.00, 'portal')
ON CONFLICT (id) DO NOTHING;

-- 7. Insert Witnesses
INSERT INTO public.witnesses (id, case_id, full_name, email, phone, relationship_to_victim) VALUES
('06b9b3cc-660c-4ec8-b648-2d8fb617bfd2', 'CASE-142', 'Sunisa Jaiyen', 'sunisa.j@outlook.com', '084-222-9988', 'Accountant at target merchant')
ON CONFLICT (id) DO NOTHING;

-- 8. Insert Suspects
INSERT INTO public.suspects (id, case_id, full_name, email, phone, id_number, address) VALUES
('e18d6e3c-8c5e-4c7b-8395-5db460cb7d04', 'CASE-142', 'Kittisak Wongsawat', 'kittisak.w@proxymail.com', '089-111-2345', '1-1002-88832-11-2', '77/1 Rama IX Rd, Bangkok')
ON CONFLICT (id) DO NOTHING;

-- 9. Statements
INSERT INTO public.statements (id, case_id, subject_id, subject_type, recorded_at, transcript, summary) VALUES
('a8efde12-b91b-4f9e-bc43-2287f3b890a2', 'CASE-142', 'cf2f8c5b-38ab-41c1-903c-83b66d4db02a', 'victim', '2026-08-10 10:00:00+07', 
'I was contacted by a seller on Facebook offering bulk electronics at discount. I transferred 1.25M Baht to Siam Commerce Bank account number 401-229-3388. After payment, the seller deleted the Facebook page. The phone number they contacted me with was 089-111-2345.', 
'Victim defrauded of 1.25M THB by fake Facebook seller. Funds transferred to SCB 401-229-3388. Contact phone: 089-111-2345.')
ON CONFLICT (id) DO NOTHING;

-- 10. Evidence
INSERT INTO public.evidence (id, case_id, title, description, type, file_hash, status) VALUES
('f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088', 'CASE-142', 'Transfer slip receipt', 'Bank receipt slip showing 1.25M THB transfer to SCB account.', 'document', 'a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415', 'sealed'),
('11b7df3c-6622-48df-9cb9-ef77ba4c28f1', 'CASE-142', 'Line Chat Logs screenshot', 'Screenshots showing contact between suspect and victim.', 'document', 'e7b92f7a63bc1a2384a56c07221ee9f08cb18d9f10928e3bcfde204d80a1122a', 'sealed')
ON CONFLICT (id) DO NOTHING;

-- 11. Bank Accounts & Transactions
-- Account SCB 401-229-3388 is linked to suspect
INSERT INTO public.bank_accounts (id, bank_name, account_number, account_name) VALUES
('b07e2a9b-38cc-4d32-bc10-ef239ab82811', 'Siam Commerce Bank', '401-229-3388', 'Kittisak Wongsawat'),
('b08e3a9c-49dd-5e43-cd21-f0340bc93922', 'Kasikorn Bank', '702-888-1123', 'Siam Electronics Co. Ltd')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.transactions (id, case_id, source_account_id, target_account_id, amount, currency, transaction_date, reference_number, evidence_id) VALUES
('a01c3d9a-1122-3344-5566-778899aabbcc', 'CASE-142', NULL, 'b07e2a9b-38cc-4d32-bc10-ef239ab82811', 1250000.00, 'THB', '2026-08-09 14:32:00+07', 'TXN-99882211', 'f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088')
ON CONFLICT (id) DO NOTHING;

-- 12. Knowledge Graph Entities
INSERT INTO public.entities (id, type, name) VALUES
('c01f8c5b-38ab-41c1-903c-83b66d4db03a', 'PERSON', 'Kittisak Wongsawat'),
('c02f8c5b-38ab-41c1-903c-83b66d4db03b', 'PHONE', '089-111-2345'),
('c03f8c5b-38ab-41c1-903c-83b66d4db03c', 'BANK_ACCOUNT', '401-229-3388')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.entity_identifiers (id, entity_id, identifier_type, value) VALUES
('d01f8c5b-38ab-41c1-903c-83b66d4db04a', 'c01f8c5b-38ab-41c1-903c-83b66d4db03a', 'national_id', '1-1002-88832-11-2'),
('d02f8c5b-38ab-41c1-903c-83b66d4db04b', 'c02f8c5b-38ab-41c1-903c-83b66d4db03b', 'phone_number', '089-111-2345'),
('d03f8c5b-38ab-41c1-903c-83b66d4db04c', 'c03f8c5b-38ab-41c1-903c-83b66d4db03c', 'bank_account_number', '401-229-3388')
ON CONFLICT (id) DO NOTHING;

-- Link entities to CASE-142
INSERT INTO public.case_entities (case_id, entity_id) VALUES
('CASE-142', 'c01f8c5b-38ab-41c1-903c-83b66d4db03a'),
('CASE-142', 'c02f8c5b-38ab-41c1-903c-83b66d4db03b'),
('CASE-142', 'c03f8c5b-38ab-41c1-903c-83b66d4db03c')
ON CONFLICT (case_id, entity_id) DO NOTHING;

-- Entity relationships
INSERT INTO public.entity_relationships (source_entity_id, target_entity_id, relationship_type, confidence, source_evidence_id) VALUES
('c01f8c5b-38ab-41c1-903c-83b66d4db03a', 'c03f8c5b-38ab-41c1-903c-83b66d4db03c', 'OWNS', 1.00, 'f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088')
ON CONFLICT (id) DO NOTHING;

-- 13. Investigation Tasks
INSERT INTO public.investigation_tasks (id, case_id, title, description, assigned_to, status, due_date) VALUES
('918d6e3c-8c5e-4c7b-8395-5db460cb7d10', 'CASE-142', 'Verify Kittisak Wongsawat identity', 'Cross-check suspect ID with Department of Provincial Administration registry.', 'd2f0998c-8c1d-4099-ae1e-f3f2a89366df', 'pending', '2026-08-25 17:00:00+07'),
('918d6e3c-8c5e-4c7b-8395-5db460cb7d11', 'CASE-142', 'Analyze bank transactions flow', 'Review layering indicators from transaction reports on SCB 401-229-3388.', 'd2f0998c-8c1d-4099-ae1e-f3f2a89366df', 'in_progress', '2026-08-28 17:00:00+07')
ON CONFLICT (id) DO NOTHING;

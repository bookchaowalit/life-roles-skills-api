---
title: solo-roles-skills — Product Card
doc_id: CARD-solo-roles-skills
doc_type: product-card
verdict: showcase
version: 0.1
date: 2026-10-11
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
---

# solo-roles-skills — Product Card

## 1. สรุปคุณค่าในหนึ่งประโยค

ช่วยเจ้าของ Solo Empire ติดตามบทบาท ทักษะ เส้นทางเรียนรู้ของแต่ละบทบาท การจัดสรรเวลาต่อโปรเจกต์ และบันทึกความก้าวหน้า

## 2. ปัญหาและผู้ใช้เป้าหมาย

- ปัญหา: ข้อมูลบทบาทและทักษะเดิมอยู่ใน SQLite ส่วนกลาง
- ผู้ใช้: เจ้าของคนเดียว (internal)

## 3. สิ่งที่ทำได้จริงตอนนี้

- API 12 resource เช่น `/v1/personal-roles`, `/v1/skills`, `/v1/skill-categories`, `/v1/role-path-steps`, `/v1/role-project-allocations`, `/v1/progress-log` พร้อมตารางลิงก์ไป goal/project/task/context
- `role_id` เป็น text id จาก `docs/registries` (ROLE-CATALOG) ตาม `cell.yaml`
- Publisher `roles-skills-publisher` (cron `5 * * * *`)

## 4. หลักฐานสถานะ

| รายการ | ค่า (ตรวจจาก repository) |
|---|---|
| Stack | FastAPI, Python |
| Commits | 5 (แรก 2026-10-10 → ล่าสุด 2026-10-11) |
| Source | ประมาณ 2,213 บรรทัดใน 15 ไฟล์ (ไม่รวมเทสต์) — ส่วนใหญ่มาจาก template cellkit ร่วมกัน |
| Tests | 2 ไฟล์ |
| CI | ไม่มี |
| Deploy config | Dockerfile + Railway (ตาม README); ไม่ได้ตรวจ deploy จริงในรอบนี้ |
| Live URL | ไม่มี (ไม่ได้ตรวจ) |
| README | 45 บรรทัด |

## 5. คุณค่าและจุดต่าง

- แยกเป็น 1 cell = 1 repo / 1 backend / 1 Neon database ตามแนว decentralize ของ Solo Empire; ใช้ identity, authorization, executions และ audit ของ `empire-platform` ผ่าน HTTP ด้วย token ของผู้เรียก ไม่เก็บ provider token เอง
- มุมรายได้: ไม่มี — เป็นโครงสร้างภายในของเจ้าของ แต่ pattern สร้าง cell จาก `cell.yaml` ด้วย `solo-cell-kit` ใช้ซ้ำได้ **[สมมติฐาน]**

## 6. ช่องว่างสำคัญ

- ไม่มี CI
- เป็น instance ของ template `cellkit` (โครงเดียวกับอีก 10 repo)
- มีข้อมูลจริงใน Neon หรือไม่ **[ต้องยืนยัน]**

## 7. คำตัดสิน

**`showcase`** — ระบบภายในที่ทำงานตามสัญญา ไม่ใช่ผลิตภัณฑ์ จะเปลี่ยนเมื่อมีผู้ใช้อื่นนอกจากเจ้าของ

## 8. ขั้นต่อไป

1. ยืนยันว่า API ออนไลน์และมีข้อมูลจริง
2. เพิ่ม CI รัน `pytest`

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `cell.yaml`
- `tests/test_contract.py`, `migrations/`, `Dockerfile`

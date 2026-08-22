# Scholarship Discovery Module — Scope & Sources (Phase 1)

## Overview & Metadata

* **Source**: [National Scholarship Portal (NSP)](https://scholarships.gov.in)
* **Academic Year**: `2026-27`
* **Target Audience**: School Students (**Class 9 and Class 10** / Secondary School / Pre-Matric)
* **Domain / Subject Alignment**: Secondary School Academic Assistant (Science / General)
* **Module Purpose**: **Scholarship discovery only** (information retrieval, eligibility guidance, and scheme matching)

---

## 1. Objectives & Scope Definition

### Why Scope to Class 9 & 10?
The National Scholarship Portal (NSP) catalogues hundreds of Central, State, and UGC/AICTE schemes. Most of these target post-matriculation, undergraduate, postgraduate, technical, or doctoral research candidates.

Our educational assistant currently focuses on **Class 9 and 10 students**. Attempting to index or scrape the entire portal introduces noise, irrelevant search results, and complex eligibility criteria (such as entrance exams, degree accreditation, and thesis criteria) that do not apply to school-age learners.

By scoping specifically to **Pre-Matric** and **Secondary School** schemes for Academic Year **2026-27**, we ensure:
1. **High Retrieval Precision**: Contextual recommendations match the exact age, class level, and school types of our target users.
2. **Simplified Filtering**: Criteria focus on core variables (academic percentage, annual family income, category/caste, disability status, school type).
3. **Actionable Recommendations**: Students and parents receive clear, verifiable criteria without navigating irrelevant higher-education schemes.

---

## 2. Included vs. Excluded Schemes

| Category | Status | Rationale |
| :--- | :---: | :--- |
| **National Means-cum-Merit Scheme (NMMSS)** | **INCLUDED** | Primary merit-cum-means scheme for Class 9 students from Govt/aided schools. |
| **PM-YASASVI (Pre-Matric & Top Class Schools)** | **INCLUDED** | Premier national scheme for OBC/EBC/DNT students in Classes 9–10. |
| **Pre-Matric SC & ST Schemes** | **INCLUDED** | Core affirmative action schemes supporting retention in Classes 9–10. |
| **Pre-Matric Scheme for Students with Disabilities** | **INCLUDED** | High-support scheme covering assistive allowances for Class 9–10 PwD students. |
| **Pre-Matric Minorities Scheme** | **INCLUDED** | Targeted financial aid for minority students in Classes 9–10. |
| **Pre-Matric Wards of Beedi/Cine/Mine Workers** | **INCLUDED** | Specialized welfare scheme for children of unorganized labor workers. |
| **Post-Matric Schemes (Class 11, 12, UG, PG)** | **EXCLUDED** | Outside current user persona (school students below matriculation). |
| **UGC / AICTE Schemes (Pragati, Saksham, Swanath)** | **EXCLUDED** | Strictly for degree/diploma technical and university students. |
| **Fellowships & Ph.D. Research Grants** | **EXCLUDED** | Higher education only. |
| **Overseas / Study Abroad Scholarships** | **EXCLUDED** | Post-secondary international education only. |

---

## 3. Targeted Schemes Catalogue

The current scoped schemes catalogued in [`sources.json`](file:///c:/Users/Arnav/Desktop/academic-rag-assistant/scholarships/sources.json) are:

### 1. National Means-cum-Merit Scholarship Scheme (NMMSS)
* **Ministry**: Ministry of Education (*Department of School Education & Literacy*)
* **Eligible Classes**: Class 9 to Class 12 (Selection test taken in Class 8 / entry at Class 9)
* **Income Limit**: $\le$ ₹3,50,000 / year
* **Key Criteria**: $\ge$ 55% in Class 7; selection via State-level MAT/SAT exam; studying in Government/Aided/Local Body schools.
* **Benefit**: ₹12,000 / year (₹1,000 / month via DBT).

### 2. PM-YASASVI Pre-Matric Scholarship
* **Ministry**: Ministry of Social Justice & Empowerment (MoSJE)
* **Eligible Classes**: Class 9 and Class 10
* **Target Beneficiaries**: OBC, EBC, and DNT students studying in Government schools.
* **Income Limit**: $\le$ ₹2,50,000 / year
* **Benefit**: ₹4,000 / year consolidated academic allowance.

### 3. PM-YASASVI Top Class Education in Schools
* **Ministry**: Ministry of Social Justice & Empowerment (MoSJE)
* **Eligible Classes**: Class 9 to Class 12
* **Target Beneficiaries**: Meritorious OBC, EBC, DNT students enrolled in designated "Top Class Schools".
* **Income Limit**: $\le$ ₹2,50,000 / year
* **Benefit**: Up to ₹75,000 / year (Classes 9–10) covering tuition, boarding, and non-refundable fees.

### 4. Pre-Matric Scholarship for Students with Disabilities
* **Ministry**: MoSJE (*Department of Empowerment of Persons with Disabilities*)
* **Eligible Classes**: Class 9 and Class 10
* **Target Beneficiaries**: Students with $\ge 40\%$ certified disability (UDID card).
* **Income Limit**: $\le$ ₹2,50,000 / year
* **Benefit**: Maintenance allowance + ₹1,000 book grant + specialized disability/reader allowances.

### 5. Pre-Matric Scholarship Scheme for SC Students (Component 1)
* **Ministry**: Ministry of Social Justice & Empowerment (MoSJE)
* **Eligible Classes**: Class 9 and Class 10
* **Target Beneficiaries**: Scheduled Caste (SC) students in recognized schools.
* **Income Limit**: $\le$ ₹2,50,000 / year
* **Benefit**: ₹3,500 – ₹7,000 / year academic allowance.

### 6. Pre-Matric Scholarship Scheme for ST Students
* **Ministry**: Ministry of Tribal Affairs (MoTA)
* **Eligible Classes**: Class 9 and Class 10
* **Target Beneficiaries**: Scheduled Tribe (ST) students.
* **Income Limit**: $\le$ ₹2,50,000 / year
* **Benefit**: Academic allowance and maintenance grant (₹3,000 – ₹6,250 / year).

### 7. Financial Assistance for Wards of Beedi / Cine / IOMC / LSDM Workers
* **Ministry**: Ministry of Labour and Employment (MoL&E)
* **Eligible Classes**: Class 1 to Class 10 (Scoped for Class 9–10)
* **Target Beneficiaries**: Children of active Beedi, Cine, Iron Ore, Manganese, Chrome Ore, or Limestone/Dolomite mine workers.
* **Income Limit**: Monthly family income $\le$ ₹10,000 (Approx. ₹1,20,000 / year).
* **Benefit**: ₹2,000 / year for Class 9–10 students.

### 8. Pre-Matric Scholarship Scheme for Minorities
* **Ministry**: Ministry of Minority Affairs (MoMA)
* **Eligible Classes**: Class 9 and Class 10
* **Target Beneficiaries**: Muslim, Christian, Sikh, Buddhist, Jain, and Parsi students.
* **Income Limit**: $\le$ ₹1,00,000 / year
* **Key Criteria**: $\ge 50\%$ marks in previous annual examination.
* **Benefit**: Tuition fee assistance up to ₹4,000 / year + monthly maintenance allowance.

### 9. Pre-Matric Scholarship for Children of Parents in Hazardous/Unclean Occupations
* **Ministry**: Ministry of Social Justice & Empowerment (MoSJE)
* **Eligible Classes**: Class 1 to Class 10 (Scoped for Class 9–10)
* **Target Beneficiaries**: Children of manual scavengers, tanners, flayers, and waste pickers.
* **Income Limit**: No income limit.
* **Benefit**: Monthly stipend (₹700–₹1,100) + ₹1,000 annual ad-hoc grant.

---

## 4. Key Discovery & Policy Guidelines for AY 2026-27

1. **One Time Registration (OTR)**:
   * All students applying on NSP for AY 2026-27 require a 14-digit unique OTR generated via Aadhaar or Aadhaar Enrolment ID (EID) linked to a mobile number.
   * Our discovery assistant should inform students about this prerequisite before they begin external applications.

2. **Direct Benefit Transfer (DBT)**:
   * Scholarships are disbursed directly into Aadhaar-seeded bank accounts through PFMS (Public Financial Management System).

3. **Discovery vs. Application**:
   * **In-App Scope**: Provide schema-driven query matching, eligibility calculation (income, caste, marks, class), and timeline alerts.
   * **Out-of-Scope**: Application submission, credential storage, and document uploads (which must occur directly on [scholarships.gov.in](https://scholarships.gov.in)).

---

## 5. File Structure

```text
scholarships/
├── README.md       # Scope, policy definitions, scheme catalogue, and target rules (this file)
└── sources.json    # Machine-readable schema defining target Class 9/10 NSP schemes
```

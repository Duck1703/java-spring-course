# Build While You Learn — Java Spring Boot + Spendwise

## 1. Mục đích của tài liệu

Tài liệu này là MASTER PLAN cho việc chuyển khóa học Java 17 + Spring Boot 3.x hiện tại từ một Course Reader/LMS thông thường thành một trải nghiệm:

# Build While You Learn

Người học không chỉ học Java và Spring Boot theo từng Day.

Người học đồng thời xây dựng một project thật xuyên suốt toàn bộ khóa học:

# Spendwise — Personal Expense & Budget Tracker

Khóa học phải tạo ra hai luồng song song:

Learning Track
→ học kiến thức Java/Spring

Project Track
→ áp dụng kiến thức đó để Spendwise phát triển dần từ V0.1 đến V1.0

Mục tiêu cuối cùng:

Học Java/Spring
→ hiểu bản chất
→ biết kiến thức giải quyết vấn đề gì
→ áp dụng vào Spendwise
→ project tiến hóa qua từng giai đoạn
→ cuối khóa có một backend application hoàn chỉnh đủ tốt để sử dụng, demo portfolio và trình bày trong phỏng vấn.

Tài liệu này là source of truth cho việc thiết kế lại website và tích hợp Spendwise vào khóa học.

Không được thay đổi các quyết định lớn trong tài liệu này chỉ để làm UI dễ hơn.

---

# 2. Nguyên tắc cốt lõi

Khóa học phải tuân theo triết lý:

Concept
→ Problem
→ Solution
→ Project Application

Không học technology chỉ vì syllabus có technology đó.

Mỗi technology nên xuất hiện khi Spendwise có một vấn đề thực tế cần nó giải quyết.

Ví dụ:

Transaction
→ chuyển tiền giữa hai Account cần atomicity

File I/O
→ import sao kê CSV

Async
→ import dữ liệu lớn không nên block request

Scheduler
→ recurring transaction

Redis
→ dashboard aggregation cần cache

External API
→ exchange rate

Security
→ mỗi user chỉ được truy cập dữ liệu của chính mình

Testing
→ business rules tài chính phải deterministic và chính xác

Monitoring
→ background jobs và API cần quan sát trong production

Nếu một concept không có Project Application tự nhiên:

KHÔNG ép nó vào Spendwise.

Lesson vẫn có thể là pure theory.

---

# 3. Không thay syllabus hiện tại

`course-data` hiện tại vẫn là syllabus chính thức.

Giữ cấu trúc:

Unit
→ Day
→ Section

Không tự:

- xóa Day;
- đổi thứ tự Day;
- thay curriculum bằng roadmap khác;
- tạo thêm hàng loạt Day mới;
- phá nội dung theory hiện tại.

Spendwise phải được tích hợp VÀO curriculum hiện tại.

Curriculum không được thiết kế lại chỉ để phục vụ project.

---

# 4. Hai track của khóa học

Website phải thể hiện rõ hai track độc lập nhưng liên kết với nhau.

## Learning Track

Theo dõi:

- Unit hiện tại;
- Day hiện tại;
- lesson đã hoàn thành;
- Java progress;
- Spring progress;
- overall course progress.

Learning Progress được quyết định bởi việc người học hoàn thành lesson.

## Project Track

Theo dõi:

- Spendwise release hiện tại;
- milestone hiện tại;
- feature đã hoàn thành;
- build task;
- project progress;
- architecture hiện tại.

Project Progress KHÔNG được đồng nhất với Learning Progress.

Ví dụ:

Day 20 — Transaction: COMPLETED

nhưng:

Spendwise — Atomic Transfer: NOT IMPLEMENTED

là trạng thái hoàn toàn hợp lệ.

Học xong kiến thức không đồng nghĩa project task đã hoàn thành.

---

# 5. Product: Spendwise

## Product Name

Spendwise

## Product Type

Personal Expense & Budget Tracker

## Product Vision

Một backend application giúp cá nhân:

- quản lý Account;
- ghi lại Transaction;
- phân loại chi tiêu;
- quản lý Budget;
- xử lý Transfer;
- quản lý recurring transaction;
- import transaction từ CSV;
- tự động áp dụng categorization rule;
- xem dashboard và report;
- theo dõi dữ liệu tài chính cá nhân.

Về cuối khóa có thể bổ sung AI để:

- đề xuất category;
- tạo monthly spending insight;
- giải thích các thay đổi đáng chú ý trong chi tiêu.

AI chỉ đóng vai trò hỗ trợ.

AI không được thay thế business rules cốt lõi.

---

# 6. Target User

Target user chính:

một cá nhân muốn quản lý thu chi cá nhân.

Trong giai đoạn khóa học:

người học chính là user đầu tiên của Spendwise.

Ứng dụng trước tiên phục vụ single-user behavior về mặt trải nghiệm.

Tuy nhiên backend vẫn phải có User + ownership để học authentication và authorization đúng cách.

---

# 7. Core Domain

Core domain dự kiến bao gồm:

User

Account

Transaction

Category

Budget

RecurringTransaction

Rule

ImportBatch

Report

Không bắt buộc tất cả entity xuất hiện ngay từ V0.1.

Domain phải phát triển incremental.

---

# 8. Business logic quan trọng

Spendwise không được trở thành CRUD application.

Các business rules sau là lý do chính project tồn tại.

## Account Balance

Account có balance được tính từ transaction hoặc được quản lý theo design phù hợp.

Không để dữ liệu balance thay đổi tùy tiện bên ngoài domain/service phù hợp.

## Transaction

Transaction phải có:

- amount hợp lệ;
- type hợp lệ;
- Account hợp lệ;
- ownership hợp lệ.

Sử dụng BigDecimal cho tiền.

Không sử dụng double/float cho business amount.

## Transfer

Transfer giữa hai Account phải đảm bảo:

Account A
→ money out

Account B
→ money in

Hai thay đổi phải thành công cùng nhau.

Nếu một phần thất bại:

toàn bộ operation phải rollback.

Đây là project use case chính cho database transaction.

## Category

Transaction có thể được phân loại theo category.

Ví dụ:

Food

Transport

Housing

Entertainment

Salary

Category có thể phát triển thêm hierarchy sau nếu thực sự cần, nhưng không bắt buộc trong MVP.

## Budget

User có thể đặt budget theo category và period.

Ví dụ:

Food
→ 3.000.000 VND / month

Hệ thống tính:

budget limit

spent

remaining

percentage

status

Budget không được xóa hoặc chỉnh transaction thực tế chỉ vì user vượt ngân sách.

## Recurring Transaction

Ví dụ:

Rent
→ monthly

Internet
→ monthly

Salary
→ monthly

Recurring transaction phải có:

next due date

frequency

active status

logic tránh tạo duplicate.

## Rule Engine

Ví dụ:

description contains "GRAB"

→ category = Transport

Hoặc:

description contains "NETFLIX"

→ category = Entertainment

Rule cần có:

conditions

actions

priority/order

audit hoặc rule hit nếu phù hợp.

Không xây một DSL phức tạp trong khóa học.

## CSV Import

User import statement:

CSV
→ parse
→ normalize
→ validate
→ deduplicate
→ categorize
→ save

Import phải có kết quả:

successful rows

duplicate rows

failed rows

Import cùng một file hoặc transaction giống nhau không được tạo duplicate một cách vô kiểm soát.

## Dashboard

Dashboard tổng hợp:

current balance

income this month

expense this month

spending by category

budget status

recent transactions

monthly trend

Dashboard là use case chính cho:

Stream

aggregation

database query

projection

cache

Redis

## Report

Có thể tạo:

monthly report

CSV export

Optional:

PDF report nếu thời gian cho phép.

Report generation có thể trở thành background task khi học Async.

---

# 9. Scope Control

Spendwise phải được giữ ở mức Finance Lite.

Mục tiêu là học backend engineering.

Mục tiêu KHÔNG phải xây phần mềm kế toán hoàn chỉnh.

## Không làm trong V1.0

Không implement:

- full double-entry accounting;
- general ledger;
- tax;
- stock trading;
- investment portfolio;
- cryptocurrency;
- bank synchronization;
- Open Banking;
- OCR receipt;
- family/shared finance;
- financial advisor;
- loan system;
- payment gateway;
- microservices;
- Kafka;
- Kubernetes;
- mobile app;
- blockchain;
- complex accounting reconciliation;
- support mọi file format ngân hàng;
- full multi-currency accounting engine.

CSV là format import chính của khóa học.

OFX/QIF/CAMT và các format khác để post-course.

---

# 10. AI Scope

AI là advanced feature.

Không được đưa AI vào sớm.

Core backend phải hoạt động đúng trước.

AI có thể hỗ trợ:

## AI Category Suggestion

Input:

transaction description

historical categories

user categorization behavior

Output:

suggested category

AI chỉ suggest.

User confirm trước khi thay đổi dữ liệu.

## AI Monthly Insight

Backend tự aggregate dữ liệu trước.

Ví dụ backend tạo:

food spending = +23%

transport = -10%

total spending = +8%

Sau đó AI chỉ chuyển dữ liệu có cấu trúc thành insight tự nhiên.

Không để LLM tự query database hoặc tự tính business numbers.

## AI Guardrails

AI không:

- tự transfer tiền;
- tự chỉnh transaction;
- tự sửa budget;
- tự xóa dữ liệu;
- đưa ra quyết định tài chính nghiêm trọng.

AI là recommendation layer.

---

# 11. Spendwise Evolution Roadmap

Project phát triển theo version.

Mỗi version phải giải quyết một vấn đề rõ ràng.

---

# V0.1 — Java Domain

## Goal

Xây domain cơ bản của Spendwise bằng Java thuần.

## Features

Money

Account

Transaction

Category

basic domain validation

## Learning focus

Class

Object

Constructor

Encapsulation

Enum

Inheritance/Polymorphism nếu có use case phù hợp

Exception

## Architecture

CLI/Test
↓
Domain Objects

## Expected result

Có thể tạo Account.

Có thể tạo Transaction.

Business invariants cơ bản được bảo vệ.

Không cần Spring.

Không database.

Không REST.

---

# V0.2 — Java Application

## Goal

Biến domain thành một application Java nhỏ hoạt động được.

## Features

In-memory repository

Transaction service

basic statistics

CSV read/write cơ bản

## Learning focus

Interface

Generics

Collections

Lambda

Stream

Exception Handling

File I/O

## Architecture

CLI
↓
Service
↓
Repository
↓
Memory / File

## Expected result

Có thể:

- quản lý transactions trong memory;
- tìm kiếm;
- nhóm theo category;
- tính tổng thu/chi;
- lưu/load dữ liệu đơn giản.

Concurrency chỉ áp dụng nếu có use case tự nhiên.

Không ép concurrency vào project.

---

# V0.3 — Spring Boot Core

## Goal

Migration application sang Spring Boot.

## Features

Spring Boot bootstrap

Service beans

Repository abstraction

Configuration

Profiles nếu cần

## Learning focus

Spring Boot

IoC

Dependency Injection

Bean lifecycle

Configuration

## Architecture

Spring Boot
↓
Service
↓
Repository
↓
Memory

## Expected result

Domain Java hiện tại tiếp tục được reuse.

Business logic không được viết lại chỉ vì chuyển sang Spring.

---

# V0.4 — REST API

## Goal

Expose Spendwise qua HTTP API.

## Features

Account API

Transaction API

Category API

DTO

Validation

Exception response

## Learning focus

Spring MVC

REST API

@RequestMapping

@GetMapping

@PostMapping

@PathVariable

@RequestParam

DTO

Bean Validation

@RestControllerAdvice

ProblemDetail

## Architecture

HTTP
↓
Controller
↓
Service
↓
Repository

## Expected result

Có thể sử dụng Swagger/Postman để:

create account

create transaction

list transactions

filter transactions

manage categories

Frontend chưa bắt buộc.

---

# V0.5 — Persistence

## Goal

Dữ liệu tồn tại sau khi restart application.

## Features

PostgreSQL

JPA entities

relationships

repositories

atomic transfer

transactions

## Learning focus

Spring Data JPA

Entity

Relationships

Persistence Context

Transaction

@Transactional

Query

Performance fundamentals

## Architecture

REST
↓
Controller
↓
Service
↓
Repository
↓
JPA
↓
PostgreSQL

## Important project problem

Transfer:

Account A
→ -500000

Account B
→ +500000

Phải atomic.

## Expected result

Restart application không làm mất dữ liệu.

Transfer phải rollback nếu operation không hoàn tất.

---

# V0.6 — Security & Ownership

## Goal

Biến Spendwise thành multi-user backend đúng nghĩa.

## Features

Register

Login

JWT

Authorization

Ownership

## Learning focus

Spring Security

Authentication

Authorization

JWT

SecurityContext

role

resource ownership

## Important rule

User A không được đọc/sửa/xóa:

Account

Transaction

Budget

của User B.

## Expected result

API được bảo vệ.

Ownership phải được kiểm tra ở backend.

Không dựa vào frontend để bảo vệ dữ liệu.

---

# V0.7 — Business Engine

## Goal

Đưa business logic của Spendwise vượt khỏi CRUD.

## Features

Budget

Recurring Transaction

Rule Engine

advanced statistics

## Learning focus

Domain Service

Business Rules

Transaction

Scheduling preparation

JPA query

aggregation

testing

## Expected result

Spendwise bắt đầu hoạt động giống một sản phẩm thực.

---

# V0.8 — Data Processing

## Goal

Xử lý dữ liệu transaction thực tế.

## Features

CSV Import

ImportBatch

validation

deduplication

import result

background import nếu dataset lớn

CSV Export

## Learning focus

File Handling

Parsing

Exception Handling

Batch Processing

Idempotency

Async

## Architecture

Upload CSV
↓
Import API
↓
ImportBatch
↓
Parser
↓
Validation
↓
Deduplication
↓
Persistence

Optional:

HTTP Request
↓
202 Accepted
↓
Async Job
↓
ImportBatch status

## Expected result

Import cùng transaction nhiều lần không tạo duplicate không kiểm soát.

Import failure không làm hệ thống mất trạng thái không rõ ràng.

---

# V0.9 — Production Engineering

## Goal

Đưa Spendwise gần với production backend.

## Features

Redis

Dashboard cache

Recurring scheduler

External Exchange Rate API

Testing

OpenAPI

Logging

Monitoring

Docker

## Learning focus

Cache

Redis

Cache invalidation

Async

Scheduler

External API

RestClient/WebClient

Retry

Circuit Breaker nếu syllabus hỗ trợ

Unit Testing

Integration Testing

Testcontainers

Actuator

Micrometer

Docker

## Architecture

Client
↓
Spring Boot
├── PostgreSQL
├── Redis
└── External FX API

## Expected result

Application có:

persistent database

cache

background/scheduled jobs

external integration

tests

health check

metrics

Dockerized environment

---

# V1.0 — Smart Finance

## Goal

Hoàn thiện project và bổ sung intelligent feature có giá trị.

## Core

Tất cả chức năng chính ổn định.

## Optional AI

AI Category Suggestion

AI Monthly Insight

## Final Engineering Focus

refactoring

architecture review

test coverage

production readiness

documentation

portfolio README

final demo

---

# 12. Course ↔ Project Mapping

Website phải hỗ trợ mapping từ curriculum sang Spendwise.

Mapping phải dựa trên lesson thực tế trong `course-data`.

Không hard-code giả chỉ để render UI.

Ví dụ mapping định hướng:

Java Platform
→ foundation

Classes / Objects / Encapsulation
→ Money / Account / Transaction domain

Inheritance / Polymorphism
→ strategy/rule abstraction nếu phù hợp

Interface
→ repository/parser abstraction

Generics
→ Repository<T, ID>

Collections
→ in-memory storage / transaction grouping

Exception
→ domain/import exceptions

Stream
→ financial aggregation

Concurrency
→ chỉ sử dụng khi có use case thực

File I/O
→ CSV storage/import

Spring Boot
→ application migration

IoC / DI
→ service/repository dependencies

Spring MVC
→ REST API

Validation
→ transaction/account input validation

Exception Handling
→ consistent API error

JPA
→ persistent financial data

Relationships
→ Account/Transaction/Category/Budget

Transaction
→ atomic account transfer

Security
→ authentication + ownership

JPA Performance
→ dashboard/query optimization

Cache / Redis
→ dashboard cache

Async
→ import/report jobs

Scheduling
→ recurring transaction

File Handling
→ CSV import/export

External API
→ exchange rate

Testing
→ domain/business correctness

OpenAPI
→ API documentation

Logging
→ request/job tracing

Monitoring
→ health/metrics

Docker
→ application environment

System Design
→ architecture review

Final Project
→ stabilization / integration / release

AI phải đọc lesson thật trước khi tạo mapping chính thức.

Nếu lesson nào không có Spendwise use case tự nhiên:

project mapping có thể để trống hoặc ghi:

"Không áp dụng trực tiếp vào project."

---

# 13. Lesson Experience

Lesson page hiện tại vẫn phải ưu tiên THEORY.

Project không được chiếm mất nội dung học.

Cấu trúc lesson mong muốn:

Lesson Title

Summary

Prerequisites

Outcomes

Project Context

Theory Sections

Common Mistakes

Project Application

References

Project task chỉ xuất hiện như optional action.

Không tự ép người học code.

---

# 14. Project Context trong Lesson

Nếu lesson có liên quan Spendwise, đầu lesson nên có:

## Why this matters in Spendwise

Trả lời:

Spendwise hiện đang gặp vấn đề gì?

Concept hôm nay giải quyết vấn đề gì?

Feature nào sẽ được unlock?

Ví dụ Transaction:

Spendwise cần transfer giữa hai Account.

Hai cập nhật database phải thành công cùng nhau.

Nếu chỉ một cập nhật thành công:

financial data bị inconsistent.

Concept hôm nay:

Database Transaction

@Transactional

Rollback

Project Feature:

Atomic Account Transfer

---

# 15. Project Application cuối Lesson

Cuối lesson có thể hiển thị:

## Used in Spendwise

Release:

V0.5 — Persistence

Feature:

Atomic Transfer

Relevant components:

TransferService

AccountRepository

TransactionRepository

Không cần bắt user implement ngay.

Có thể cung cấp:

Open Build Task

nhưng đây là optional action.

---

# 16. Before / After Architecture

Một lesson quan trọng có thể mô tả project trước và sau khi học.

Ví dụ Redis.

Before:

Dashboard Request
↓
Spring Boot
↓
PostgreSQL
↓
Aggregation every request

After:

Dashboard Request
↓
Redis
├── HIT → Response
└── MISS
    ↓
PostgreSQL
    ↓
Cache result

Feature này là P1/P2.

Không bắt buộc cho mọi lesson.

---

# 17. Website Information Architecture

Top-level navigation định hướng:

Learn

Project

Architecture

Resources

Không cần tạo hàng loạt page nếu renderer hiện tại hỗ trợ route view tốt hơn.

Reuse architecture hiện tại tối đa.

---

# 18. Learn Area

Learn giữ các chức năng hiện tại:

Dashboard

Curriculum

Lesson

Search

Progress

References

Theme

Lesson navigation

Không phá các chức năng đang hoạt động.

---

# 19. Dashboard mới

Dashboard phải trả lời 4 câu ngay lập tức:

1. Tôi đang học đến đâu?

2. Spendwise đang ở version nào?

3. Lesson hiện tại đóng góp gì cho project?

4. Tôi nên làm gì tiếp theo?

Dashboard có hai progress riêng.

## Learning Progress

Java

Spring

Overall

## Project Progress

Current Release

Release Progress

Completed Features

Current Milestone

Ví dụ:

CURRENT LEARNING

Day 20 — Transactions

CURRENT BUILD

Spendwise V0.5 — Persistence

TODAY'S PROJECT IMPACT

Unlock:
Atomic Account Transfer

NEXT

Learn:
JPA Query

Build:
TransferService

---

# 20. Project Workspace

Project là first-class area.

## Spendwise Overview

Hiển thị:

Product name

Product purpose

Current release

Overall project progress

Current milestone

Core capabilities

## Roadmap

Hiển thị:

V0.1 Java Domain

V0.2 Java Application

V0.3 Spring Boot Core

V0.4 REST API

V0.5 Persistence

V0.6 Security

V0.7 Business Engine

V0.8 Data Processing

V0.9 Production

V1.0 Smart Finance

Status:

RELEASED

BUILDING

PLANNED

Không dùng status giả nếu state chưa tồn tại.

---

# 21. Release Detail

Mỗi release có thể hiển thị:

Release Name

Problem

Goal

Features

Learning Dependencies

Architecture

Acceptance Criteria

Project Tasks

Example:

V0.5 — Persistence

Problem:

Application restart làm mất dữ liệu.

Goal:

Persist financial data.

Features:

Account persistence

Transaction persistence

Category persistence

Atomic transfer

Learning Dependencies:

JPA

Relationships

Transaction

Acceptance Criteria:

Data survives restart.

Transfer atomic.

Invalid transfer rollback.

---

# 22. Architecture Area

Architecture không phải tài liệu tĩnh.

Nó phải cho thấy project trưởng thành theo khóa học.

## V0.2

CLI
↓
Service
↓
Repository
↓
Memory

## V0.4

HTTP
↓
Controller
↓
Service
↓
Repository

## V0.5

REST
↓
Controller
↓
Service
↓
Repository
↓
PostgreSQL

## V0.9

Client
↓
Spring Boot
├── PostgreSQL
├── Redis
└── External API

Architecture phải lấy từ project data nếu khả thi.

Không hard-code một sơ đồ duy nhất không liên quan release.

---

# 23. Course ↔ Project Map

Tạo view cho phép người học nhìn:

Course Day

Concept

Project Problem

Spendwise Feature

Release

Ví dụ:

Day 4
→ Encapsulation
→ protect financial invariants
→ Money / Account
→ V0.1

Day 10
→ Stream
→ aggregate spending
→ Statistics
→ V0.2

Day 20
→ Transaction
→ account transfer consistency
→ Atomic Transfer
→ V0.5

Day 25
→ Cache
→ expensive dashboard aggregation
→ Dashboard Cache
→ V0.9

Đây là một trong những view quan trọng nhất của Build While You Learn.

---

# 24. Project Progress Model

Course progress và project progress phải được lưu riêng.

Course progress:

lesson completed

Project progress:

feature/task/release completed

Project release có thể được tính:

completed required project tasks
/
total required project tasks

Không tự đánh dấu project task completed chỉ vì lesson completed.

---

# 25. Data Architecture Requirements

Không bắt buộc sử dụng một JSON shape cụ thể ngay từ đầu.

Coding agent phải inspect schema hiện tại trước.

Data architecture mới cần hỗ trợ tối thiểu:

Project metadata

Project releases

Project milestones/features

Lesson → Release mapping

Lesson → Project Feature mapping

Project Context

Project Application

Project progress state

Architecture evolution metadata nếu cần

Acceptance criteria

Không hard-code các dữ liệu này trực tiếp trong rendering function nếu có thể biểu diễn thành data.

Data first.

UI second.

---

# 26. Existing Features Must Be Preserved

Không làm mất:

Curriculum sidebar

Lesson rendering

Course progress

Search

Dark/light/system theme

References

Previous/next navigation

Responsive layout

Local persistence nếu đang dùng

Import/export progress nếu đang dùng

Existing lesson content

Accessibility cơ bản

Nếu phải thay schema:

cần migration/compatibility strategy phù hợp.

---

# 27. Visual Direction

Không thiết kế giống:

Udemy

Coursera

generic LMS

marketing landing page

Visual direction:

Developer Learning Workspace

Tham khảo tinh thần:

GitHub

Linear

developer documentation

build/release dashboard

IDE/project workspace

Không copy UI cụ thể của sản phẩm khác.

UI nên:

clean

dense vừa phải

developer-oriented

information-first

ít decoration không cần thiết

responsive

readable

---

# 28. Design Language

Java:

orange accent

Spring:

green accent

Project/Spendwise:

có accent riêng nhưng không áp đảo Java/Spring

Code:

dark code surface có thể tiếp tục giữ

Typography:

developer-friendly

Project status có thể sử dụng:

RELEASED

BUILDING

PLANNED

Course status:

COMPLETED

CURRENT

UPCOMING

Không dùng quá nhiều badge.

---

# 29. Non-Goals của Website

Website KHÔNG phải:

IDE

code editor

terminal

Git client

CI/CD dashboard

cloud deployment platform

AI coding environment

Người học vẫn code Spendwise trong IDE như IntelliJ IDEA.

Website chỉ phải trả lời:

What am I learning?

Why am I learning it?

Where is it used?

What am I building?

Where is the project now?

What comes next?

---

# 30. Implementation Priority

## P0 — Core Build While You Learn

Bắt buộc hoàn thành trước.

Project data model

Spendwise releases

Lesson → Project mapping

Separate Project Progress

Dashboard Learning + Project

Lesson Project Context

Lesson Project Application

Basic Project Overview

Basic Roadmap

Navigation integration

Không làm visual polish lớn trước khi P0 data hoàn chỉnh.

---

# 31. P1 — Project Workspace

Sau khi P0 ổn định.

Release detail pages

Course ↔ Project Map

Architecture evolution

Domain overview

Better Project Roadmap

Build task view

Before/After architecture cho lesson quan trọng

---

# 32. P2 — UX Polish

Chỉ sau P0/P1.

Micro-interaction

small animation

better mobile navigation

project status refinement

visual polish

filtering

better progress visualization

Không thêm gamification không cần thiết.

---

# 33. Implementation Workflow bắt buộc

Coding agent phải làm theo thứ tự:

READ MASTER PLAN

↓

AUDIT CURRENT APP

↓

UNDERSTAND CURRENT DATA

↓

DESIGN DATA ARCHITECTURE

↓

CREATE COURSE ↔ PROJECT MAPPING

↓

IMPLEMENT DATA

↓

VALIDATE DATA

↓

IMPLEMENT P0 UI

↓

VALIDATE CURRENT FEATURES

↓

IMPLEMENT P1

↓

FINAL REVIEW

Không bắt đầu bằng:

CSS redesign

hero section

card layout

animation

hard-coded Spendwise demo.

---

# 34. Research Rules

Nếu cần bổ sung technical information cho lesson/project mapping:

ưu tiên:

Java:

Oracle Documentation

Java Language Specification

JVM Specification

OpenJDK

Spring:

Official Spring Framework Documentation

Official Spring Boot Documentation

Official Spring Security Documentation

Official Spring Data Documentation

Hibernate Documentation khi liên quan

Không dùng blog làm source chính nếu official docs có nội dung tương ứng.

Project design không được thay đổi tùy tiện dựa trên một tutorial.

---

# 35. Version Compatibility

Khóa học hiện tại target:

Java 17

Spring Boot 3.x

Spring Framework 6.x

Jakarta APIs

Không đưa code hoặc architecture phụ thuộc vào:

javax API cũ

deprecated Spring APIs

version không phù hợp với syllabus

Nếu project config thực tế pin một version cụ thể:

giữ nhất quán với project.

---

# 36. Build Task Philosophy

Build task phải giống task của project thật.

Không viết:

"Exercise: practice @Transactional."

Viết:

"Implement atomic account transfer."

Sau đó liên kết:

Knowledge:

@Transactional

Rollback

Persistence Context

Build task nên có:

Problem

Goal

Constraints

Acceptance Criteria

Relevant lessons

Không tự cung cấp toàn bộ implementation solution trừ khi người dùng yêu cầu.

---

# 37. Acceptance Criteria — Overall

Build While You Learn được coi là thành công khi:

Người học mở Dashboard và hiểu ngay:

- đang học Day nào;
- Spendwise ở version nào;
- lesson hôm nay giúp feature nào;
- bước tiếp theo là gì.

Lesson có thể trả lời:

"Tại sao tôi cần học concept này?"

Project page cho thấy:

Spendwise V0.1 → V1.0.

Release page cho thấy:

problem → goal → feature → learning dependency.

Architecture cho thấy project tiến hóa theo thời gian.

Course ↔ Project Map cho thấy:

knowledge → project problem → feature.

Course Progress và Project Progress hoạt động độc lập.

Existing curriculum không bị phá.

Existing lesson content không bị mất.

UI không chứa Spendwise hard-code chỉ để trang trí.

Project không trở thành Finance enterprise application.

Spendwise vẫn nằm trong Finance Lite scope.

---

# 38. Acceptance Criteria — Data

Project data phải có khả năng đại diện:

Spendwise

releases

features

project mapping

project context

progress

acceptance criteria

Lesson mapping không được phụ thuộc vào title text matching nếu có thể dùng ID ổn định.

Không duplicate cùng một nội dung project ở nhiều nơi nếu có thể reference bằng ID.

Data phải validate được.

Renderer phải xử lý gracefully nếu lesson không có project mapping.

---

# 39. Acceptance Criteria — UI

Desktop hoạt động.

Mobile hoạt động.

Không horizontal overflow không cần thiết.

Navigation hoạt động.

Search hoạt động.

Theme hoạt động.

Course progress hoạt động.

Project progress hoạt động.

Lesson previous/next hoạt động.

Không có major console error.

Không có route dead-end.

Project UI phải lấy data thật.

---

# 40. Acceptance Criteria — Learning

Project không được làm theory bị rút ngắn.

Theory vẫn là nội dung chính của lesson.

Project Context chỉ tạo motivation/context.

Project Application chỉ cho thấy kiến thức được dùng ở đâu.

Build Task là optional.

Người học có thể:

chỉ học theory

hoặc

học + build project.

Cả hai workflow đều phải hợp lệ.

---

# 41. Acceptance Criteria — Spendwise

Không được biến thành CRUD-only app.

Ít nhất project roadmap phải tạo đường tới:

domain invariants

financial aggregation

atomic transfer

ownership

budget

recurring transaction

rule-based categorization

CSV import

deduplication/idempotency

background processing

scheduler

cache

external API

testing

monitoring

Docker

AI optional

Nhưng các feature chỉ xuất hiện đúng release của chúng.

---

# 42. Important Product Principle

Không được chọn technology trước rồi bịa feature.

Luôn hỏi:

Spendwise hiện gặp problem gì?

Sau đó mới hỏi:

Java/Spring feature nào giải quyết được problem đó?

Mental model:

PROJECT PROBLEM

↓

ENGINEERING NEED

↓

COURSE CONCEPT

↓

IMPLEMENTATION

Ví dụ:

dashboard query bắt đầu đắt

↓

need caching

↓

Spring Cache / Redis

↓

Dashboard Cache

Không phải:

khóa học có Redis

↓

phải tìm chỗ để nhét Redis.

---

# 43. Important Learning Principle

Không phải mọi lesson đều phải làm project tiến thêm một feature.

Có ba loại mapping hợp lệ.

## Direct Application

Concept được dùng ngay trong Spendwise.

## Future Application

Concept cần cho release tương lai.

## Theory Only

Concept quan trọng để hiểu Java/Spring nhưng project hiện tại không có use case tự nhiên.

Cả ba đều hợp lệ.

Không ép Direct Application cho mọi Day.

---

# 44. Final Product State

Cuối khóa, Spendwise nên có kiến trúc gần:

Client / Swagger
↓
Spring Boot REST API
↓
Application / Domain Services
↓
Spring Data JPA
↓
PostgreSQL

và khi phù hợp:

Redis

Scheduler

Async background jobs

External FX API

Logging

Actuator/Metrics

Docker

AI suggestion layer

Không cần microservices.

Modular monolith là đủ.

---

# 45. Portfolio Outcome

Cuối khóa người học phải có thể giải thích:

Tại sao dùng BigDecimal cho money?

Tại sao domain cần invariant?

Tại sao Transfer cần @Transactional?

Nếu hai transfer concurrent thì chuyện gì xảy ra?

Tại sao import cần deduplication/idempotency?

Async import được track thế nào?

Scheduler làm sao tránh duplicate recurring transaction?

Cache dashboard invalidation khi nào?

User ownership được enforce ở đâu?

External API failure được xử lý thế nào?

Business rules được test ra sao?

Application được monitor thế nào?

Spendwise được Dockerize ra sao?

Nếu project cho phép trả lời những câu này bằng implementation thật:

mục tiêu Build While You Learn đã đạt.

---

# 46. Final Design Principle

Website không chỉ nói:

"Day 20 — học Transaction."

Website phải tạo được mental model:

Spendwise hiện cần chuyển tiền giữa hai Account.

↓

Nếu update chỉ thành công một nửa:

financial data bị sai.

↓

Để giải quyết:

hôm nay học Transaction.

↓

Sau bài này:

bạn có kiến thức để build Atomic Transfer.

Đây là trải nghiệm cốt lõi của toàn bộ hệ thống.

---

# 47. Instructions cho Coding Agent

Khi coding agent đọc tài liệu này:

1. Inspect codebase hiện tại trước.

2. Không giả định schema mới trước khi hiểu schema cũ.

3. Reuse hệ thống hiện tại tối đa.

4. Data architecture trước UI.

5. Không hard-code Spendwise vào presentation layer nếu có thể biểu diễn bằng data.

6. Không phá curriculum.

7. Không xóa nội dung lesson.

8. Không redesign toàn bộ visual system nếu không cần.

9. Không thêm feature ngoài scope để làm demo đẹp hơn.

10. Không dừng giữa task chỉ để hỏi xác nhận nếu implementation plan đã rõ và không có blocker thực sự.

11. Validate mỗi phase trước khi tiếp tục.

12. Hoàn thành P0 trước P1.

13. Hoàn thành P1 trước P2 polish.

14. Nếu plan và code hiện tại xung đột:

ưu tiên giữ functionality hiện tại và tìm migration strategy.

15. Nếu một quyết định thực sự không thể suy ra:

ghi rõ blocker thay vì tự thay đổi product scope.

---

# 48. Definition of Done

Project redesign chỉ được coi là DONE khi:

Build While You Learn không còn là khẩu hiệu.

Spendwise thực sự tồn tại trong data model.

Lesson thực sự map sang Spendwise.

Project progress thực sự độc lập với course progress.

Dashboard thực sự kết nối learning và building.

Project Roadmap thực sự dựa trên V0.1 → V1.0.

Architecture thực sự thể hiện evolution.

Course ↔ Project Map thực sự tồn tại.

Theory vẫn giữ nguyên vai trò chính.

Existing app functionality vẫn hoạt động.

Spendwise scope vẫn nằm trong Finance Lite.

Người học có thể nhìn cả khóa học và hiểu:

"Tôi không làm hàng chục bài tập Java/Spring rời rạc.

Tôi đang học từng công nghệ để từng bước xây một backend application thật."

---

# END OF MASTER PLAN

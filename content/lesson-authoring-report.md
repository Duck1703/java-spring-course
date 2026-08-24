# Lesson Authoring Report

## day-01 - JVM, JRE, JDK & Data Types

Source resources used:
- res-1cec64c5e683 (Interning thủ công; String Pool; Vị trí lưu trữ Pool qua các phiên bản Java; new String() vs literal)
- res-99801d0b7043 (JDK gồm những gì; JRE gồm những gì; JVM là gì; Vùng dữ liệu runtime của JVM (tutorial))
- res-9d76570d9362 (Autoboxing là gì; Bảng ánh xạ kiểu nguyên thủy - lớp bọc; Unboxing là gì)
- res-acff7fd27edc (Frame, local variable, operand stack; Kiểu boolean trong JVM; Vùng dữ liệu runtime của JVM (JVMS))
- res-f7cc3f86702d (String là đối tượng bất biến)

Inaccessible supplied links:
- res-62d9985bbc6f

Practice inventory (4 total):
- day01-prac-1: type=concept, interaction=multiple-choice
- day01-prac-2: type=predict-output, interaction=multiple-choice
- day01-prac-3: type=concept, interaction=self-check
- day01-prac-4: type=coding, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=4: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-02 - Operators & Control Flow

Source resources used:
- res-284db3d782e6 (Cấu trúc switch block (rule vs labeled); Fall-through trong switch nhãn kiểu cũ; Kiểu dữ liệu hợp lệ cho switch; Pattern matching cơ bản (type pattern))
- res-28fe8d3fda30 (Vai trò của break trong switch; switch hoạt động trên kiểu nào; switch trên String)
- res-740a979a150e (Cú pháp for cơ bản; Enhanced for (for-each))
- res-82c961b7a92a (Ba nhóm câu lệnh điều khiển luồng)
- res-df903793f0b9 (Bảng độ ưu tiên toán tử; Thứ tự đánh giá toán tử)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day02-prac-1: type=concept, interaction=multiple-choice
- day02-prac-2: type=predict-output, interaction=multiple-choice
- day02-prac-3: type=concept, interaction=self-check
- day02-prac-4: type=coding, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-03 - - Lab 1: Implement `StringCalculator` applying String immutability and primitive optimization

Source resources used:
- res-1cec64c5e683 (String Pool; new String() vs literal)
- res-82c961b7a92a (Ba nhóm câu lệnh điều khiển luồng)
- res-df903793f0b9 (Bảng độ ưu tiên toán tử; Thứ tự đánh giá toán tử (trái sang phải))

Inaccessible supplied links:
- res-62d9985bbc6f

Practice inventory (3 total):
- day03-prac-1: type=applied, interaction=self-check
- day03-prac-2: type=coding, interaction=self-check
- day03-prac-3: type=concept, interaction=multiple-choice

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=7: - Lab 1: Implement `StringCalculator` applying String immutability and primitive optimization
  - Input: a string containing a simple arithmetic expression (addition/subtraction)
  - Output: integer result

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-04 - Classes, Objects, Encapsulation

Source resources used:
- res-4f42c781654a (Constructor có tham số; Constructor mặc định; Gọi constructor khác bằng this())
- res-563d80135c91 (Bốn mức truy cập; Lớp top-level chỉ dùng public/default; Thứ tự chính tắc của modifier)
- res-ae202f300a2b (Nội dung bài học Classes and Objects)

Inaccessible supplied links:
- res-9458879c2540
- res-f31ffcf74f40

Practice inventory (3 total):
- day04-prac-1: type=concept, interaction=multiple-choice
- day04-prac-2: type=concept, interaction=multiple-choice
- day04-prac-3: type=coding, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=9: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-05 - Inheritance, Polymorphism & Abstract

Source resources used:
- res-36a8d5deef22 (Method overriding qua ví dụ GenericFile/ImageFile; Polymorphism tĩnh và động; Upcast/downcast và ClassCastException)
- res-aad15fef0599 (Kế thừa lớp bằng extends; Thành viên nào được kế thừa; this và super khi trùng tên thành viên; Đa kế thừa qua interface)
- res-b5dd43254a15 (Khi nào nên dùng abstract class; Ràng buộc với abstract method; Định nghĩa abstract class)

Inaccessible supplied links:
- res-10672cc3a9fa

Practice inventory (4 total):
- day05-prac-1: type=concept, interaction=multiple-choice
- day05-prac-2: type=predict-output, interaction=multiple-choice
- day05-prac-3: type=concept, interaction=self-check
- day05-prac-4: type=coding, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-06 - - Assignment 2: Employee Management System

Source resources used:
- res-36a8d5deef22 (Method overriding qua ví dụ GenericFile/ImageFile; Polymorphism tĩnh và động)
- res-aad15fef0599 (Kế thừa lớp bằng extends; Thành viên nào được kế thừa; this và super khi trùng tên thành viên)
- res-ae202f300a2b (Nội dung bài học Classes and Objects)
- res-b5dd43254a15 (Khi nào nên dùng abstract class; Ràng buộc với abstract method; Định nghĩa abstract class)

Inaccessible supplied links: none.

Practice inventory (3 total):
- day06-prac-1: type=applied, interaction=self-check
- day06-prac-2: type=concept, interaction=multiple-choice
- day06-prac-3: type=coding, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=12: - Assignment 2: Employee Management System
  - Base `Employee` abstract (id, name, baseSalary) + method `calculateSalary()` abstract
  - Subclass: `Developer` (overtimeHours, bonusRate), `Manager` (teamSize, kpiMultiplier)
  - `PayrollService` calculates total salary using polymorphism
  - Uses a Record for `EmployeeDTO`
  - Unit tests verify the correctness of each salary type

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-07 - Interface, Inner Classes & Enums

Source resources used:
- res-0196dd00302a (Nội dung bài học Interfaces and Inheritance)

Inaccessible supplied links:
- res-ec467b92f9e7
- res-4bc225ad1d9e
- res-062b84a9042d
- res-c246ae22f99a

Practice inventory (4 total):
- day07-prac-1: type=concept, interaction=multiple-choice
- day07-prac-2: type=concept, interaction=self-check
- day07-prac-3: type=coding, interaction=self-check
- day07-prac-4: type=coding, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=14: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-08 - Generics, Collections & Exception Handling

Source resources used:
- res-12fa3a9d4910 (Cấu trúc trang tổng hợp Collections Series)
- res-30d834f8fef0 (Anti-pattern: nuốt exception và return/throw trong finally; Checked vs unchecked; Phân cấp Exception)
- res-74dcb3852a23 (Nội dung bài học Exceptions)
- res-899383bc8d09 (Nội dung Trail Collections của Oracle)
- res-8abee0bfd5a7 (Generic method và bounded type; Lý do có generics; Type erasure; Wildcard (dấu hỏi ?) trong generics)
- res-9762250d04d9 (Cú pháp try-with-resources cơ bản; Nhiều resource trong một try; Thứ tự đóng resource; Tự tạo resource với AutoCloseable)
- res-e3b2dcb60e96 (Mục đích bài học Generics)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day08-prac-1: type=concept, interaction=multiple-choice
- day08-prac-2: type=predict-output, interaction=multiple-choice
- day08-prac-3: type=coding, interaction=self-check
- day08-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-09 - - Lab 3: Custom Collection & Exception Framework

Source resources used:
- res-12fa3a9d4910 (Cấu trúc trang tổng hợp Collections Series)
- res-30d834f8fef0 (Checked vs unchecked; Phân cấp Exception)
- res-899383bc8d09 (Nội dung Trail Collections của Oracle)
- res-9762250d04d9 (Tự tạo resource với AutoCloseable)
- res-e3b2dcb60e96 (Mục đích bài học Generics)

Inaccessible supplied links: none.

Practice inventory (3 total):
- day09-prac-1: type=applied, interaction=self-check
- day09-prac-2: type=concept, interaction=multiple-choice
- day09-prac-3: type=coding, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=17: - Lab 3: Custom Collection & Exception Framework
  - Implement `SimpleArrayList<E>` with dynamic array (add, get, remove, size, iterator)
  - Implement `SimpleHashMap<K,V>` with separate chaining
  - Custom exception hierarchy: `DataAccessException` → `DuplicatedKeyException`, `KeyNotFoundException`
  - Test coverage ≥ 80%

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-10 - Lambda & Stream API Chuyên Sâu

Source resources used:
- res-55e66ec50cc0 (Cấu trúc trang tổng hợp Streams Series)
- res-713a3e371ba0 (Lọc theo nhiều điều kiện; Stream.filter() nhận Predicate; Xử lý checked exception trong Predicate)

Inaccessible supplied links:
- res-0851edc9dd41
- res-9b1feb8ea22f
- res-b73632f693f7

Practice inventory (4 total):
- day10-prac-1: type=concept, interaction=multiple-choice
- day10-prac-2: type=predict-output, interaction=multiple-choice
- day10-prac-3: type=coding, interaction=self-check
- day10-prac-4: type=concept, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=19: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-11 - Concurrency & File I/O

Source resources used:
- res-0c7109cb4fa8 (Custom serialization và transient; Ràng buộc kế thừa/composition khi serialize; Serialization/deserialization là gì; serialVersionUID)
- res-3393c8cbdaaf (6 trạng thái vòng đời Thread; Cách vào trạng thái BLOCKED; WAITING vs TIMED_WAITING)
- res-543deb939f9e (Cấu trúc bài học File I/O featuring NIO.2)
- res-88adadc6f2f4 (Cấu trúc trang tổng hợp IO Series)
- res-9a6cde117315 (Quy tắc happens-before; Vấn đề memory visibility và reordering; volatile giải quyết vấn đề gì)
- res-a553d0d4478d (Race condition là gì; Reentrancy của khóa synchronized; synchronized instance vs static method)
- res-d6607fed4419 (Copy và move file; Path và lớp Files là entry point của NIO.2; Tạo và xóa file/thư mục)
- res-fc9869512a5f (Nội dung các mục con; Vì sao cần synchronization)
- res-fe3cc9768091 (Ba nhóm nội dung con; Executor là gì và vì sao cần)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day11-prac-1: type=concept, interaction=multiple-choice
- day11-prac-2: type=predict-output, interaction=multiple-choice
- day11-prac-3: type=coding, interaction=self-check
- day11-prac-4: type=coding, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-12 - - Assignment 4: Data Processing Pipeline

Source resources used:
- res-543deb939f9e (Cấu trúc bài học File I/O featuring NIO.2)
- res-88adadc6f2f4 (Cấu trúc trang tổng hợp IO Series)
- res-d6607fed4419 (Copy và move file; Path và lớp Files là entry point của NIO.2; Tạo và xóa file/thư mục)

Inaccessible supplied links:
- res-9b1feb8ea22f
- res-b73632f693f7

Practice inventory (4 total):
- day12-prac-1: type=concept, interaction=multiple-choice
- day12-prac-2: type=coding, interaction=self-check
- day12-prac-3: type=concept, interaction=self-check
- day12-prac-4: type=coding, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=22: - Assignment 4: Data Processing Pipeline
  - Read file CSV 500K rows (simulated sales data)
  - Stream transform: filter invalid → group by category → aggregate revenue → sort top 10
  - Parallel vs sequential benchmark (JMH)
  - Thread-safe result accumulator
  - Export report ra JSON

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-13 - Spring Boot Fundamentals & Bean Lifecycle

Source resources used:
- res-56487c83dc65 (Cấu trúc trang tổng hợp Learn Spring Boot Series)
- res-bb04db80cab2 (Bean là gì; BeanFactory và ApplicationContext; Dependency Injection theo định nghĩa của Spring Framework)
- res-bf1095022eae (Các annotation dành cho scope web-aware (request/session/application); Prototype scope và trách nhiệm dọn dẹp; Scoped proxy để tiêm bean ngắn hạn vào bean singleton; Singleton scope khác singleton pattern GoF; Sáu scope Spring hỗ trợ)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day13-prac-1: type=concept, interaction=multiple-choice
- day13-prac-2: type=coding, interaction=self-check
- day13-prac-3: type=concept, interaction=self-check
- day13-prac-4: type=concept, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=24: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-14 - Dependency Injection & Configuration

Source resources used:
- res-02399daadb94 (Constructor-based DI; Field-based DI và nhược điểm; IoC là gì; Setter-based DI)
- res-b6fc716e051f (Auto-configuration hoạt động theo classpath; Auto-configuration không xâm lấn (non-invasive); Tắt một auto-configuration class cụ thể; Xem báo cáo auto-configuration đang áp dụng)
- res-bf1095022eae (Scoped proxy để tiêm bean ngắn hạn vào bean singleton)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day14-prac-1: type=concept, interaction=multiple-choice
- day14-prac-2: type=coding, interaction=self-check
- day14-prac-3: type=concept, interaction=self-check
- day14-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-15 - - Assignment 5: Multi-module Notification Service

Source resources used:
- res-7bf1b25b2e6b (@ConfigurationProperties với prefix chung; Constructor binding và Java record bất biến; Nested properties: List, Map, Class; Validate property bằng JSR-380)
- res-aee8bfb64b8c (Constructor binding và record cho property bất biến; Kích hoạt tài liệu YAML theo profile; Quy tắc relaxed binding)
- res-bb04db80cab2 (Dependency Injection theo định nghĩa của Spring Framework)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day15-prac-1: type=concept, interaction=multiple-choice
- day15-prac-2: type=coding, interaction=self-check
- day15-prac-3: type=concept, interaction=self-check
- day15-prac-4: type=concept, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=27: - Assignment 5: Multi-module Notification Service
  - Interface `NotificationService` → EmailSender, SmsSender, PushSender
  - @Qualifier or @Profile select implementation 
  - @ConfigurationProperties for each config (SMTP, Twilio, Firebase)
  - Retry logic when send fail
  - The Factory pattern creates the correct sender based on the notification type.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-16 - Controller & Request/Response

Source resources used:
- res-06dd51e41e25 (Builder tĩnh của ResponseEntity; Khi nào không cần ResponseEntity; ResponseEntity là gì)
- res-2aefb097db80 (@PathVariable và kiểu {*path}; Cú pháp URI pattern; RequestMapping và các shortcut theo HTTP method; Thu hẹp mapping theo consumes/produces)
- res-d8a874d76b06 (@PathVariable đơn, nhiều biến và ràng buộc regex; @RequestParam và params attribute; Lỗi Ambiguous Mapping)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day16-prac-1: type=concept, interaction=multiple-choice
- day16-prac-2: type=coding, interaction=self-check
- day16-prac-3: type=concept, interaction=self-check
- day16-prac-4: type=concept, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=29: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-17 - Validation & Exception Handling

Source resources used:
- res-1f904f56cc5a (Dependency cần thiết từ Boot 2.3; Dùng @Valid trong REST controller; Ràng buộc trên entity bằng Bean Validation; Xử lý lỗi validate bằng @ExceptionHandler)
- res-7f4116f00d7f (Cài đặt logic validate bằng ConstraintValidator; Validate ở cấp class cho nhiều field; Định nghĩa annotation validate tùy chỉnh)
- res-8a73cd80ad49 (Bật ProblemDetail qua property; So với cách xử lý lỗi truyền thống; Trả ProblemDetail trong exception handler toàn cục; Đặc tả ProblemDetail)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day17-prac-1: type=concept, interaction=multiple-choice
- day17-prac-2: type=coding, interaction=self-check
- day17-prac-3: type=concept, interaction=self-check
- day17-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-18 - - Lab 6: User & Task Management API

Source resources used:
- res-2aefb097db80 (@PathVariable và kiểu {*path}; RequestMapping và các shortcut theo HTTP method)
- res-7f4116f00d7f (Cài đặt logic validate bằng ConstraintValidator; Định nghĩa annotation validate tùy chỉnh)
- res-8a73cd80ad49 (Trả ProblemDetail trong exception handler toàn cục; Đặc tả ProblemDetail)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day18-prac-1: type=concept, interaction=multiple-choice
- day18-prac-2: type=coding, interaction=self-check
- day18-prac-3: type=concept, interaction=self-check
- day18-prac-4: type=concept, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=32: - Lab 6: User & Task Management API
  - CRUD Task: title, description, status (TODO/IN_PROGRESS/DONE), priority, dueDate
  - Validation: title notBlank, dueDate in future, valid status transition
  - Custom validator: @ValidStatusTransition
  - Global exception handler ProblemDetail
  - Postman collection export

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-19 - Entity Design & Relationships

Source resources used:
- res-01d4c9bc1c9c (@Entity annotation; @Table và @Column; @Transient, @Temporal, @Enumerated; Chiến lược sinh khóa chính)
- res-749fa81acd48 (Cơ chế proxy của lazy loading; FetchType mặc định theo Jakarta Persistence; Khái niệm eager và lazy loading)
- res-cf695e39df80 (CascadeType chuẩn JPA; CascadeType.PERSIST và CascadeType.REMOVE)
- res-d20f2a5470d7 (Many-to-many hai chiều; Quan hệ hai chiều dùng mappedBy; Quan hệ một chiều; Đánh đổi giữa hai kiểu quan hệ)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day19-prac-1: type=concept, interaction=multiple-choice
- day19-prac-2: type=coding, interaction=self-check
- day19-prac-3: type=concept, interaction=self-check
- day19-prac-4: type=concept, interaction=multiple-choice

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=34: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-20 - Query, Transaction & Patterns

Source resources used:
- res-2e4a3dd62ec7 (Kết hợp Sort vào PageRequest; Page<T> so với Slice<T>; PageRequest.of và Pageable; PagingAndSortingRepository)
- res-749fa81acd48 (Cân nhắc fetch khi thiết kế projection/query)
- res-82b36b19c96f (Auditing thuần JPA bằng callback; Hibernate Envers cho audit log chi tiết; Spring Data JPA auditing)
- res-cf695e39df80 (CascadeType.LOCK (mở rộng riêng của Hibernate))

Inaccessible supplied links: none.

Practice inventory (4 total):
- day20-prac-1: type=concept, interaction=multiple-choice
- day20-prac-2: type=coding, interaction=self-check
- day20-prac-3: type=concept, interaction=self-check
- day20-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-21 - - Assignment 7: E-Commerce Data Layer

Source resources used:
- res-2e4a3dd62ec7 (PageRequest.of cho truy vấn top-selling/orders theo khoảng ngày; PagingAndSortingRepository cho các truy vấn danh sách)
- res-82b36b19c96f (Spring Data JPA auditing cho created_at/updated_at của Order)

Inaccessible supplied links:
- res-553bbd92e5d0

Practice inventory (4 total):
- day21-prac-1: type=concept, interaction=multiple-choice
- day21-prac-2: type=coding, interaction=self-check
- day21-prac-3: type=concept, interaction=self-check
- day21-prac-4: type=concept, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=37: - Assignment 7: E-Commerce Data Layer
  - Entities: User, Product, Category, Order, OrderItem
  - Full relationships + cascade correct
  - Repository query: top-selling products, orders by date range, user history
  - Flyway migration (V1__init.sql → V2__seed_data.sql)
  - @DataJpaTest integration test

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-22 - Authentication with Spring Security + JWT

Source resources used:
- res-65703b737426 (Cấu hình OAuth2 Resource Server qua issuer-uri; JwtAuthenticationProvider và luồng xác thực JWT; Quy trình discovery lúc khởi động (JWK Set); Xử lý mỗi request có Bearer token)
- res-d5aebfb9d1ed (DelegatingPasswordEncoder là PasswordEncoder mặc định; Lịch sử tiến hoá cách lưu mật khẩu; User.withDefaultPasswordEncoder() chỉ dùng cho demo, không production; Định dạng lưu trữ {id}encodedPassword)
- res-f301a3d0645a (Bảo vệ tấn công session fixation; SessionCreationPolicy.STATELESS; requireExplicitSave trong Spring Security 6)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day22-prac-1: type=concept, interaction=multiple-choice
- day22-prac-2: type=coding, interaction=self-check
- day22-prac-3: type=concept, interaction=self-check
- day22-prac-4: type=concept, interaction=multiple-choice

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=39: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-23 - Authorization & JPA Performance

Source resources used:
- res-1559f0cd62e7 (Bảo vệ BREACH bằng XorCsrfTokenRequestAttributeHandler; CsrfFilter và CsrfTokenRequestHandler; CsrfTokenRepository)
- res-ce09de5e928a (FetchType.EAGER vẫn có thể gây N+1; FetchType.LAZY không tự động tránh N+1; Định nghĩa N+1)
- res-d1d09e3813e4 (CSRF bật mặc định từ Spring Security 4.x; Hai kiểu tấn công CSRF cơ bản; Khi nào cần/không cần CSRF cho API stateless)
- res-fa00cc21947b (@PreAuthorize và @PostAuthorize; @PreFilter và @PostFilter; Bật Method Security bằng @EnableMethodSecurity; Hạn chế do AOP proxy (self-invocation không được chặn); Test bằng @WithMockUser)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day23-prac-1: type=concept, interaction=multiple-choice
- day23-prac-2: type=coding, interaction=self-check
- day23-prac-3: type=concept, interaction=self-check
- day23-prac-4: type=concept, interaction=multiple-choice

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-24 - - Lab 8: Auth Service + Performance Optimization

Source resources used:
- res-28c8c8bc71df (Cấu hình hibernate.jdbc.batch_size; Hiệu năng đo được qua benchmark; Mặc định Hibernate không tự động batch; hibernate.order_inserts / order_updates)
- res-65703b737426 (JwtAuthenticationProvider xác thực Bearer token mỗi request; Xử lý request có Bearer token lúc runtime)
- res-8437fa16cd25 (@SoftDelete là cơ chế native của Hibernate 6.4; Cần @NotFound cho @ManyToOne LAZY khi entity liên kết có thể bị soft-delete)
- res-ce09de5e928a (N+1 với second-level cache; Định nghĩa N+1 áp dụng cho Product list API)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day24-prac-1: type=concept, interaction=multiple-choice
- day24-prac-2: type=coding, interaction=self-check
- day24-prac-3: type=concept, interaction=self-check
- day24-prac-4: type=concept, interaction=multiple-choice

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=42: - Lab 8: Auth Service + Performance Optimization
  - Register + Login + Refresh + Logout (Redis blacklist)
  - @PreAuthorize role-based: CUSTOMER vs ADMIN
  - Product list API: fix N+1 when load category
  - Benchmark before/after optimize
  - Security integration test with @WithMockUser

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-25 - Caching & Async Processing

Source resources used:
- res-1c6109c5ec54 (Chi can starter-data-redis + starter-cache + @EnableCaching)
- res-347895e9400e (@EnableCaching tren class @SpringBootApplication; Gan @Cacheable len method truy van cham)
- res-710573bd4385 (RedisCacheConfiguration.entryTtl/disableCachingNullValues; RedisCacheManager.builder tuy chinh cacheDefaults; TTL reset khi ghi, TTI can GETEX tu Redis 6.2.0)
- res-e95ba2d69401 (@CacheEvict(allEntries=true) xoa toan bo entry; @EnableCaching bat ConcurrentMapCacheManager mac dinh; Phan biet @Cacheable (bo qua khi co cache) va @CachePut (luon goi method); condition/unless SpEL cho cache co dieu kien)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day25-prac-1: type=concept, interaction=multiple-choice
- day25-prac-2: type=coding, interaction=self-check
- day25-prac-3: type=concept, interaction=multiple-choice
- day25-prac-4: type=concept, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=44: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-26 - File Upload/Download & External API

Source resources used:
- res-6543ba492a80 (Chuan hoa duong dan va kiem tra nam trong rootLocation de chong path traversal; Controller GET / (danh sach), GET /files/{filename} (tai xuong), POST / (tai len); Gioi han dung luong upload qua spring.servlet.multipart.*; Test upload bang MockMvc + MockMultipartFile)
- res-74d398e3d23c (Cau hinh multipart trong Spring Boot (max-file-size/max-request-size); Nhan mot file qua @RequestParam MultipartFile; Upload nhieu file cung ten input)
- res-b8b29a249f37 (Chuoi goi method/uri/body/header/retrieve(); Tao instance qua create()/create(baseUrl)/builder(), timeout mac dinh; WebClient la reactive HTTP client thay the RestTemplate; WebTestClient de test WebClient call)
- res-ea68bcb99823 (Cac lua chon thu vien CSV: Apache Commons CSV, OpenCSV, Jackson dataformat CSV; Escape dau phay/dau nhay kep/xuong dong trong truong CSV; Ghi CSV bang PrintWriter thuan Java + Collectors.joining)
- res-f6c8ab355f09 (3 trang thai Closed/Open/Half-Open; Retry khong trang thai (stateless) vs Circuit Breaker co trang thai)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day26-prac-1: type=concept, interaction=multiple-choice
- day26-prac-2: type=coding, interaction=self-check
- day26-prac-3: type=concept, interaction=multiple-choice
- day26-prac-4: type=coding, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-27 - - Assignment 9: Product & Order Features

Source resources used:
- res-033c4bfa05f5 (@Async cho gui email xac nhan don hang; Method @Async tra ve CompletableFuture cho cap nhat ton kho)
- res-1c6109c5ec54 (Cache backend Redis cho danh sach san pham/cay danh muc)
- res-4b45b7c76586 (@CircuitBreaker fallbackMethod cho payment gateway call)
- res-74d398e3d23c (Upload anh san pham qua MultipartFile)
- res-97fce5fda99a (@EnableScheduling bat scheduled job; fixedDelay cho job huy don hang cho qua 30 phut)
- res-b8b29a249f37 (WebClient goi payment gateway mock)
- res-e95ba2d69401 (@CacheEvict(allEntries=true) khi tao/sua/xoa san pham hoac danh muc; Ap dung @Cacheable cho truy van danh sach san pham)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day27-prac-1: type=concept, interaction=multiple-choice
- day27-prac-2: type=coding, interaction=self-check
- day27-prac-3: type=concept, interaction=self-check
- day27-prac-4: type=concept, interaction=multiple-choice

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=47: - Assignment 9: Product & Order Features
  - Cache product list, category tree. Evict on create/update/delete.
  - @Async: order confirmation email, inventory update
  - @Scheduled: cancel pending orders > 30 min
  - Product image upload + thumbnail
  - WebClient call payment gateway (mock) with circuit breaker
  - Export orders CSV (admin)

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-28 - Testing Spring Boot

Source resources used:
- res-31a2e0685799 (4 gia tri webEnvironment: MOCK/RANDOM_PORT/DEFINED_PORT/NONE; @JsonTest chi khoi tao JacksonTester/GsonTester/JsonbTester; @MockitoBean/@MockitoSpyBean thay the @MockBean tu Spring Boot 3.4; @WebMvcTest va @DataJpaTest chi khoi tao slice can thiet)
- res-3807593857d1 (MockMvc khong mo ket noi mang that; RestAssured voi webEnvironment RANDOM_PORT; SpringExtension + @WebAppConfiguration + MockMvcBuilders; perform(get()).andExpect(jsonPath...))
- res-ae66be8c9f5f (@DataJpaTest voi H2 in-memory + TestEntityManager; @MockBean thay the bean phu thuoc that; @SpringBootTest voi webEnvironment.MOCK; @WebMvcTest(Controller.class) chi khoi tao mot controller; Bang cac annotation slice test khac)
- res-bccebfeaf062 (3 module chinh: JUnit Platform/Jupiter/Vintage; @BeforeAll/@AfterAll/@BeforeEach/@AfterEach/@DisplayName/@Disabled; assertAll gom nhieu assertion, assumeTrue bo qua test; assertThrows va @TestFactory DynamicTest)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day28-prac-1: type=concept, interaction=multiple-choice
- day28-prac-2: type=coding, interaction=self-check
- day28-prac-3: type=concept, interaction=multiple-choice
- day28-prac-4: type=coding, interaction=self-check

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=49: Assignment

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-29 - Documentation, Logging, Monitoring & Docker

Source resources used:
- res-79cbefdda273 (/v3/api-docs va /swagger-ui.html mac dinh; Tat/loc endpoint qua packagesToScan/pathsToMatch; Tich hop OpenAPI info vao endpoint Actuator; springdoc-openapi-starter-webmvc-ui dependency)
- res-84fc38d27c0a (PostgreSQLContainer static field cho test tich hop; RestAssured goi API qua RANDOM_PORT trong test tich hop)
- res-93813d9b62f4 (3 dinh dang JSON dung san: ecs/gelf/logstash; MDC.put them truong tuy chinh vao log; logging.structured.format.console tu Spring Boot 3.4.0)
- res-be79b4f73d01 (@DynamicPropertySource dang ky property tu container; @ServiceConnection tu dong tao ConnectionDetails; @Testcontainers + @Container quan ly vong doi container)
- res-fa57300ac53c (Actuator cung cap health/metrics qua HTTP/JMX; Cac endpoint pho bien: /beans, /env, /metrics, /loggers; HealthIndicator tuy chinh va health group; Mac dinh chi expose /health va /info)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day29-prac-1: type=concept, interaction=multiple-choice
- day29-prac-2: type=coding, interaction=self-check
- day29-prac-3: type=concept, interaction=multiple-choice
- day29-prac-4: type=coding, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-30 - - Lab 10: Production Readiness

Source resources used:
- res-79cbefdda273 (/v3/api-docs va /swagger-ui.html cho toan bo endpoint; springdoc-openapi-starter-webmvc-ui cho tai lieu OpenAPI)
- res-84fc38d27c0a (@DynamicPropertySource tro Spring context vao container; PostgreSQLContainer static field cho test tich hop that; RestAssured + RANDOM_PORT kiem tra endpoint that)
- res-8d5e61cc0a53 (Nhan org.springframework.boot.service-connection cho anh tuy chinh; Tu dong tao ConnectionDetails cho service pho bien trong compose; spring-boot-docker-compose tu dong chay docker compose up/down)
- res-ae66be8c9f5f (@SpringBootTest(MOCK) cho test tich hop tang service; @WebMvcTest cho unit test tang controller)
- res-e3236d24d45f (4 layer mac dinh: dependencies/snapshot-dependencies/resources/application; Han che cua fat jar mot layer duy nhat; java -Djarmode=layertools -jar app.jar extract trong Dockerfile multi-stage)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day30-prac-1: type=concept, interaction=multiple-choice
- day30-prac-2: type=coding, interaction=self-check
- day30-prac-3: type=concept, interaction=self-check
- day30-prac-4: type=concept, interaction=multiple-choice

Assignment preservation: 1 syllabus assignment(s) carried over.
- row=52: - Lab 10: Production Readiness
  - Unit test + Integration test (Testcontainers) for all service
  - JaCoCo coverage report ≥ 75%
  - OpenAPI doc for all endpoint
  - JSON structured logging + traceId propagation
  - Actuator + Prometheus metrics + custom HealthIndicator
  - Dockerfile + docker-compose.yml (app + DB + Redis)
  - GitHub Actions CI: build → test → docker build

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-31 - System Design & Project Kickoff

Source resources used:
- res-06398bb0cc69 (Không dùng default package; Vị trí Main Application Class)
- res-348a6a4cb0b8 (Annotated Controllers; DispatcherServlet là front controller; Error Responses & ControllerAdvice)
- res-f023c0083770 (3 mục tiêu chính của Spring Boot)

Inaccessible supplied links:
- res-39bc1924ee00

Practice inventory (4 total):
- day31-prac-1: type=concept, interaction=multiple-choice
- day31-prac-2: type=coding, interaction=self-check
- day31-prac-3: type=concept, interaction=multiple-choice
- day31-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-32 - System Design & Project Kickoff

Source resources used:
- res-afbebe6cf212 (Implement Persistable để tùy chỉnh; save() behavior (persist vs merge))
- res-b307e54a2685 (@ExceptionHandler cơ bản trả về ProblemDetail; Global handling với @RestControllerAdvice; Spring Boot ErrorController & properties)

Inaccessible supplied links:
- res-553bbd92e5d0
- res-af7171222f9a

Practice inventory (4 total):
- day32-prac-1: type=concept, interaction=multiple-choice
- day32-prac-2: type=coding, interaction=self-check
- day32-prac-3: type=concept, interaction=multiple-choice
- day32-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-33 - Development Sprint 1

Source resources used:
- res-65703b737426 (Cấu hình JWT tối thiểu qua issuer-uri; JwtAuthenticationProvider; Quy trình discovery lúc khởi động; Xử lý mỗi request có Bearer token)
- res-afbebe6cf212 (Persistable cho BaseEntity của dự án; save() behavior áp dụng cho Category/User)
- res-cf695e39df80 (CascadeType chuẩn JPA; CascadeType riêng của Hibernate; CascadeType.LOCK; CascadeType.PERSIST và REMOVE)

Inaccessible supplied links:
- res-553bbd92e5d0
- res-aa4cbb2b9a5c

Practice inventory (4 total):
- day33-prac-1: type=concept, interaction=multiple-choice
- day33-prac-2: type=concept, interaction=multiple-choice
- day33-prac-3: type=concept, interaction=multiple-choice
- day33-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-34 - Development Sprint 2

Source resources used:
- res-74d398e3d23c (Cấu hình multipart Servlet 3.0; Cấu hình multipart trong Spring Boot; Upload một file; Upload nhiều file)
- res-e95ba2d69401 (@CacheEvict; @Cacheable vs @CachePut; Bật cache và CacheManager mặc định; Cache có điều kiện)

Inaccessible supplied links:
- res-553bbd92e5d0
- res-aa4cbb2b9a5c

Practice inventory (4 total):
- day34-prac-1: type=concept, interaction=multiple-choice
- day34-prac-2: type=concept, interaction=multiple-choice
- day34-prac-3: type=coding, interaction=self-check
- day34-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-35 - Development Sprint 3

Source resources used:
- res-033c4bfa05f5 (Ghi đè Executor mặc định; Kiểu trả về bất đồng bộ; Kích hoạt @Async; Xử lý exception cho method void)
- res-2c011d89d6e0 (5 mức isolation; 7 loại propagation transaction; Thứ tự ưu tiên @Transactional)
- res-8d5e61cc0a53 (Chờ container sẵn sàng và profile; Quản lý vòng đời container tự động; Service Connections; Ảnh Docker tùy chỉnh)
- res-e3236d24d45f (Buildpacks; Dùng layertools trong Dockerfile; Hạn chế của fat jar truyền thống; Layered jar - 4 layer mặc định)
- res-ea68bcb99823 (Ghi CSV bằng PrintWriter thuần Java; Thư viện CSV bên thứ ba; Xử lý ký tự đặc biệt)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day35-prac-1: type=concept, interaction=multiple-choice
- day35-prac-2: type=concept, interaction=multiple-choice
- day35-prac-3: type=concept, interaction=multiple-choice
- day35-prac-4: type=coding, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-36 - Final Defense

Source resources used:
- res-79cbefdda273 (Dependency springdoc-openapi cơ bản; Tích hợp Actuator; Tắt/lọc endpoint; Đường dẫn mặc định /swagger-ui.html)
- res-ae66be8c9f5f (@DataJpaTest; @SpringBootTest voi webEnvironment.MOCK; @WebMvcTest; Bảng các annotation auto-configured khác; Mock dependency voi @MockBean)
- res-be79b4f73d01 (@DynamicPropertySource; Các loại ConnectionDetails hỗ trợ sẵn; Quản lý container bằng JUnit Extension; Quản lý container bằng Spring Bean; Service Connection tự động)
- res-e3236d24d45f (Buildpacks; Hạn chế của fat jar truyền thống; Layered jar - 4 layer mặc định)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day36-prac-1: type=concept, interaction=multiple-choice
- day36-prac-2: type=concept, interaction=multiple-choice
- day36-prac-3: type=coding, interaction=self-check
- day36-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-37 - Final theory

Source resources used:
- res-004dba8a7332 (Cấu trúc chuẩn JLS 17 (19 chương); Phạm vi JLS 17)
- res-56b8234cf832 (Cấu trúc Spring Framework Reference (7 phần))
- res-8fc303d6f753 (Java Back to Basics series landing page)
- res-d5dfac91a451 (Java Tutorial series landing page)
- res-f023c0083770 (3 mục tiêu chính của Spring Boot)

Inaccessible supplied links: none.

Practice inventory (4 total):
- day37-prac-1: type=concept, interaction=multiple-choice
- day37-prac-2: type=concept, interaction=multiple-choice
- day37-prac-3: type=concept, interaction=self-check
- day37-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-38 - Final practice

Source resources used: none (internal curriculum content, no external resourceIds assigned for this lesson).

Inaccessible supplied links: none.

Practice inventory (4 total):
- day38-prac-1: type=concept, interaction=multiple-choice
- day38-prac-2: type=concept, interaction=self-check
- day38-prac-3: type=concept, interaction=multiple-choice
- day38-prac-4: type=concept, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-39-64 - Learners work with project tasks in FSU Project

Source resources used: none (internal curriculum content, no external resourceIds assigned for this lesson).

Inaccessible supplied links: none.

Practice inventory (4 total):
- day3964-prac-1: type=applied, interaction=self-check
- day3964-prac-2: type=applied, interaction=self-check
- day3964-prac-3: type=concept, interaction=self-check
- day3964-prac-4: type=concept, interaction=multiple-choice

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

## day-65-66 - Evaluate learners after training and OJT phase

Source resources used: none (internal curriculum content, no external resourceIds assigned for this lesson).

Inaccessible supplied links: none.

Practice inventory (4 total):
- day6566-prac-1: type=applied, interaction=self-check
- day6566-prac-2: type=concept, interaction=self-check
- day6566-prac-3: type=concept, interaction=self-check
- day6566-prac-4: type=applied, interaction=self-check

Assignment preservation: 0 syllabus assignment(s) carried over.

Baseline lint: PASS (no post-17 Java syntax or legacy javax/Spring APIs detected).

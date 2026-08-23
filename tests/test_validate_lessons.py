from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.validate_lessons import (
    build_source_index,
    main,
    validate_corpus,
    validate_lesson,
)


def _catalog_lesson(**overrides):
    lesson = {
        "id": "day-01",
        "unitId": "unit-01",
        "group": "java",
        "title": "JVM, JRE, JDK & Data Types",
        "objectives": ["LO1"],
        "durationMinutes": 150.0,
        "sourceRows": [3, 4],
        "syllabusAssignments": [{"row": 4, "text": "Assignment"}],
        "resourceIds": ["res-acff7fd27edc", "res-99801d0b7043"],
    }
    lesson.update(overrides)
    return lesson


def _catalog(lessons=None):
    lessons = lessons if lessons is not None else [_catalog_lesson()]
    return {"lessons": lessons}


def _source_note(resource_id="res-acff7fd27edc", lesson_ids=("day-01",),
                  status="read", locator="§2.5 Run-Time Data Areas",
                  heading="2.5. Run-Time Data Areas", cache_text=None):
    if status == "read":
        read = {
            "status": "read",
            "pageTitle": "Chapter 2. The Structure of the JVM",
            "relevantHeadings": [heading],
            "topics": ["run-time data areas"],
            "facts": [
                {
                    "topic": "run-time data areas",
                    "summary": "Tóm tắt ngắn gọn về vùng dữ liệu runtime.",
                    "locator": locator,
                }
            ],
            "limitation": None,
        }
    else:
        read = {
            "status": "unavailable",
            "pageTitle": None,
            "relevantHeadings": [],
            "topics": [],
            "facts": [],
            "limitation": "HTTP 404: not found",
        }
    return {
        "resourceId": resource_id,
        "batch": "java-foundations",
        "requestedUrl": "https://example.test/a",
        "lessonIds": list(lesson_ids),
        "access": {
            "status": "ok" if status == "read" else "not_found",
            "httpStatus": 200 if status == "read" else 404,
            "finalUrl": "https://example.test/a",
            "contentSha256": "a" * 64 if status == "read" else None,
        },
        "read": read,
        "fallbackEvidence": None,
    }


def _source_index(notes=None):
    notes = notes if notes is not None else [_source_note()]
    return build_source_index(notes)


def _choice(choice_id, text="An option"):
    return {"id": choice_id, "text": text}


def _sourceusage_entry(entry_id="cite-01", resource_id="res-acff7fd27edc",
                        locator="§2.5 Run-Time Data Areas", topic="run-time data areas"):
    return {"id": entry_id, "resourceId": resource_id, "locator": locator, "topic": topic}


def _code_block(block_id="block-code-01", citations=("cite-01",), compile_=True,
                 code="class Snippet { static int add(int a, int b) { return a + b; } }",
                 language="java", partial_reason=None):
    block = {
        "id": block_id,
        "type": "code",
        "citations": list(citations),
        "language": language,
        "code": code,
        "compile": compile_,
    }
    if not compile_:
        block["partialReason"] = partial_reason or "Illustrative fragment, not a full program"
    return block


def _paragraph_block(block_id="block-para-01", text="Đoạn văn giới thiệu.", citations=()):
    return {"id": block_id, "type": "paragraph", "citations": list(citations), "text": text}


def _section(section_id="sec-01", blocks=None):
    blocks = blocks if blocks is not None else [_paragraph_block(), _code_block()]
    return {"id": section_id, "title": "JVM Architecture", "blocks": blocks}


def _multiple_choice_practice(practice_id="practice-01", choices=None, correct=("choice-a",),
                               source_usage=("cite-01",)):
    choices = choices if choices is not None else [_choice("choice-a"), _choice("choice-b")]
    return {
        "id": practice_id,
        "type": "concept",
        "interaction": "multiple-choice",
        "prompt": "JVM stack lưu gì?",
        "choices": choices,
        "correctChoiceIds": list(correct),
        "hint": "Xem lại vùng dữ liệu runtime.",
        "solution": "JVM stack lưu các frame theo lời gọi phương thức.",
        "explanation": "Mỗi lần gọi phương thức tạo một frame mới.",
        "rubric": "Đúng nếu nêu được frame/local variable/operand stack.",
        "sourceUsage": list(source_usage),
    }


def _self_check_practice(practice_id="practice-02"):
    return {
        "id": practice_id,
        "type": "predict-output",
        "interaction": "self-check",
        "prompt": "Dự đoán kết quả của đoạn code trên.",
        "choices": [],
        "correctChoiceIds": [],
        "hint": "Theo dõi từng bước thực thi.",
        "solution": "Kết quả in ra tổng hai số.",
        "explanation": "Chương trình cộng hai số nguyên.",
        "rubric": "Đúng nếu nêu đúng kết quả.",
        "sourceUsage": [],
    }


def _lesson(**overrides):
    lesson = {
        "schemaVersion": 1,
        "id": "day-01",
        "catalogRef": _catalog_lesson(),
        "unitId": "unit-01",
        "group": "java",
        "kind": "theory",
        "title": "JVM, JRE, JDK & Data Types",
        "summary": "Giới thiệu JVM, JRE, JDK và các kiểu dữ liệu trong Java.",
        "durationMinutes": 150.0,
        "objectives": ["LO1"],
        "prerequisites": [],
        "outcomes": ["Giải thích được vai trò của JVM."],
        "sections": [_section()],
        "commonMistakes": ["Nhầm lẫn JRE và JDK."],
        "practices": [_multiple_choice_practice(), _self_check_practice()],
        "syllabusAssignments": [{"row": 4, "text": "Assignment"}],
        "enhancedExercises": [],
        "references": [
            {
                "id": "ref-01",
                "type": "external",
                "resourceId": "res-acff7fd27edc",
                "citationId": "cite-01",
            }
        ],
        "sourceUsage": [_sourceusage_entry()],
        "authoring": {
            "baseline": "Java 17 / Spring Boot 3.x / Spring Framework 6 / Jakarta",
            "reviewStatus": "reviewed",
            "limitations": [],
        },
    }
    lesson.update(overrides)
    return lesson


class ValidateLessonAcceptsValidFixtureTests(unittest.TestCase):
    def test_accepts_a_complete_valid_lesson(self):
        lesson = _lesson()
        catalog_lesson = _catalog_lesson()
        source_index = _source_index()

        errors = validate_lesson(lesson, catalog_lesson, source_index)

        self.assertEqual(errors, [])


class ValidateLessonRejectionTests(unittest.TestCase):
    def setUp(self):
        self.source_index = _source_index()

    def test_rejects_lesson_id_not_in_catalog(self):
        errors = validate_lesson(_lesson(), None, self.source_index)
        self.assertTrue(any("day-01" in error and "catalog" in error for error in errors))

    def test_rejects_unit_mismatch_with_catalog(self):
        lesson = _lesson(unitId="unit-02")
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("unitId" in error for error in errors))

    def test_rejects_group_mismatch_with_catalog(self):
        lesson = _lesson(group="spring")
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("group" in error for error in errors))

    def test_rejects_title_mismatch_with_catalog(self):
        lesson = _lesson(title="Different Title")
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("title" in error for error in errors))

    def test_rejects_objectives_mismatch_with_catalog(self):
        lesson = _lesson(objectives=["LO1", "LO2"])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("objectives" in error for error in errors))

    def test_rejects_technical_section_with_empty_source_usage(self):
        lesson = _lesson(sections=[_section(blocks=[
            _paragraph_block(),
            _code_block(citations=()),
        ])])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("citations" in error for error in errors))

    def test_rejects_citation_to_blocked_or_unread_source(self):
        unread_index = _source_index([_source_note(status="unavailable")])
        errors = validate_lesson(_lesson(), _catalog_lesson(), unread_index)
        self.assertTrue(any("read" in error for error in errors))

    def test_rejects_citation_to_resource_not_linked_to_lesson(self):
        catalog_lesson = _catalog_lesson(resourceIds=["res-99801d0b7043"])
        errors = validate_lesson(_lesson(), catalog_lesson, self.source_index)
        self.assertTrue(any("res-acff7fd27edc" in error and "linked" in error for error in errors))

    def test_rejects_citation_locator_absent_from_source_note(self):
        lesson = _lesson(sourceUsage=[_sourceusage_entry(locator="§9.9 Nonexistent")])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("locator" in error for error in errors))

    def test_rejects_practice_count_below_minimum(self):
        lesson = _lesson(practices=[_multiple_choice_practice()])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("practices" in error for error in errors))

    def test_rejects_practice_count_above_maximum(self):
        practices = [
            _multiple_choice_practice(f"practice-{i}") for i in range(5)
        ]
        lesson = _lesson(practices=practices)
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("practices" in error for error in errors))

    def test_rejects_practice_missing_hint(self):
        practice = _multiple_choice_practice()
        del practice["hint"]
        lesson = _lesson(practices=[practice, _self_check_practice()])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("hint" in error for error in errors))

    def test_rejects_practice_missing_solution(self):
        practice = _multiple_choice_practice()
        practice["solution"] = ""
        lesson = _lesson(practices=[practice, _self_check_practice()])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("solution" in error for error in errors))

    def test_rejects_practice_missing_explanation(self):
        practice = _multiple_choice_practice()
        practice["explanation"] = ""
        lesson = _lesson(practices=[practice, _self_check_practice()])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("explanation" in error for error in errors))

    def test_rejects_multiple_choice_with_fewer_than_two_choices(self):
        practice = _multiple_choice_practice(choices=[_choice("choice-a")], correct=("choice-a",))
        lesson = _lesson(practices=[practice, _self_check_practice()])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("choices" in error for error in errors))

    def test_rejects_multiple_choice_with_unknown_correct_choice_id(self):
        practice = _multiple_choice_practice(correct=("choice-unknown",))
        lesson = _lesson(practices=[practice, _self_check_practice()])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("correctChoiceIds" in error for error in errors))

    def test_rejects_multiple_choice_with_no_correct_answer(self):
        practice = _multiple_choice_practice(correct=())
        lesson = _lesson(practices=[practice, _self_check_practice()])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("correctChoiceIds" in error for error in errors))

    def test_rejects_self_check_practice_with_nonempty_choices(self):
        practice = _self_check_practice()
        practice["choices"] = [_choice("choice-a")]
        lesson = _lesson(practices=[_multiple_choice_practice(), practice])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("self-check" in error for error in errors))

    def test_rejects_self_check_practice_with_nonempty_correct_choice_ids(self):
        practice = _self_check_practice()
        practice["correctChoiceIds"] = ["choice-a"]
        lesson = _lesson(practices=[_multiple_choice_practice(), practice])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("self-check" in error for error in errors))

    def test_rejects_technical_lesson_without_code_or_config_block(self):
        lesson = _lesson(sections=[_section(blocks=[_paragraph_block()])])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("code" in error for error in errors))

    def test_rejects_copied_301_character_source_run(self):
        cached_sentence = "Đây là một đoạn văn bản mẫu rất dài được sao chép nguyên văn. " * 6
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "res-acff7fd27edc.txt"
            cache_path.write_text(cached_sentence, encoding="utf-8")
            note = _source_note(cache_text=str(cache_path))
            note["access"]["cacheText"] = str(cache_path)
            source_index = _source_index([note])
            source_index["res-acff7fd27edc"]["cacheText"] = str(cache_path)

            lesson = _lesson(sections=[_section(blocks=[
                _paragraph_block(text=cached_sentence[:400], citations=["cite-01"]),
                _code_block(),
            ])])
            errors = validate_lesson(lesson, _catalog_lesson(), source_index)

        self.assertTrue(any("300" in error for error in errors))

    def test_accepts_concise_paraphrase_even_with_matching_cache(self):
        cached_sentence = "Đây là một đoạn văn bản mẫu rất dài được sao chép nguyên văn. " * 6
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "res-acff7fd27edc.txt"
            cache_path.write_text(cached_sentence, encoding="utf-8")
            note = _source_note()
            source_index = _source_index([note])
            source_index["res-acff7fd27edc"]["cacheText"] = str(cache_path)

            lesson = _lesson(sections=[_section(blocks=[
                _paragraph_block(text="Tóm tắt ngắn gọn, diễn giải lại.", citations=["cite-01"]),
                _code_block(),
            ])])
            errors = validate_lesson(lesson, _catalog_lesson(), source_index)

        self.assertEqual(errors, [])

    def test_rejects_lost_syllabus_assignment(self):
        lesson = _lesson(syllabusAssignments=[])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("syllabusAssignments" in error for error in errors))

    def test_rejects_changed_syllabus_assignment_text(self):
        lesson = _lesson(syllabusAssignments=[{"row": 4, "text": "Different text"}])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("syllabusAssignments" in error for error in errors))

    def test_rejects_duplicate_section_ids(self):
        lesson = _lesson(sections=[_section(section_id="sec-01"), _section(section_id="sec-01", blocks=[_code_block(block_id="block-code-02")])])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("duplicate" in error and "sec-01" in error for error in errors))

    def test_rejects_duplicate_practice_ids(self):
        lesson = _lesson(practices=[_multiple_choice_practice("practice-01"), _self_check_practice("practice-01")])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("duplicate" in error and "practice-01" in error for error in errors))

    def test_rejects_duplicate_citation_ids(self):
        lesson = _lesson(sourceUsage=[_sourceusage_entry("cite-01"), _sourceusage_entry("cite-01")])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("duplicate" in error and "cite-01" in error for error in errors))

    def test_rejects_java_post_17_string_template_syntax(self):
        code = 'class Snippet { String s = STR."value"; }'
        lesson = _lesson(sections=[_section(blocks=[
            _paragraph_block(),
            _code_block(code=code, compile_=False, partial_reason="Illustrative fragment"),
        ])])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("post-17" in error or "STR." in error for error in errors))

    def test_rejects_java_post_17_record_pattern_switch(self):
        code = "class Snippet { void m(Object o) { switch (o) { case Point(int x, int y) when x > 0 -> System.out.println(x); default -> {} } } }"
        lesson = _lesson(sections=[_section(blocks=[
            _paragraph_block(),
            _code_block(code=code, compile_=False, partial_reason="Illustrative fragment"),
        ])])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertTrue(any("post-17" in error for error in errors))

    def test_rejects_spring_legacy_javax_persistence(self):
        code = "import javax.persistence.Entity;\n@Entity\nclass User {}"
        lesson = _lesson(
            group="spring",
            sections=[_section(blocks=[
                _paragraph_block(),
                _code_block(code=code, compile_=False, partial_reason="Illustrative fragment", language="java"),
            ])],
        )
        catalog_lesson = _catalog_lesson(group="spring")
        errors = validate_lesson(lesson, catalog_lesson, self.source_index)
        self.assertTrue(any("javax.persistence" in error for error in errors))

    def test_rejects_spring_legacy_javax_validation(self):
        code = "import javax.validation.constraints.NotNull;"
        lesson = _lesson(
            group="spring",
            sections=[_section(blocks=[
                _paragraph_block(),
                _code_block(code=code, compile_=False, partial_reason="Illustrative fragment", language="java"),
            ])],
        )
        catalog_lesson = _catalog_lesson(group="spring")
        errors = validate_lesson(lesson, catalog_lesson, self.source_index)
        self.assertTrue(any("javax.validation" in error for error in errors))

    def test_allows_legacy_pattern_mentioned_in_text_language_migration_prose(self):
        code = "javax.persistence.Entity was replaced by jakarta.persistence.Entity in Spring Boot 3."
        lesson = _lesson(sections=[_section(blocks=[
            _paragraph_block(),
            _code_block(
                block_id="block-migration-note",
                code=code,
                language="text",
                compile_=False,
                partial_reason="Prose migration note, not executable code",
                citations=["cite-01"],
            ),
        ])])
        errors = validate_lesson(lesson, _catalog_lesson(), self.source_index)
        self.assertEqual(errors, [])


class ValidateCorpusTests(unittest.TestCase):
    def test_reports_missing_catalog_lessons(self):
        catalog = _catalog([_catalog_lesson(id="day-01"), _catalog_lesson(id="day-02")])
        lessons = [_lesson()]

        errors = validate_corpus(catalog, lessons, _source_index())

        self.assertTrue(any("day-02" in error and "missing" in error for error in errors))

    def test_accepts_full_coverage(self):
        catalog = _catalog([_catalog_lesson(id="day-01")])
        lessons = [_lesson()]

        errors = validate_corpus(catalog, lessons, _source_index())

        self.assertEqual(errors, [])

    def test_only_scope_ignores_unauthored_catalog_lessons(self):
        catalog = _catalog([_catalog_lesson(id="day-01"), _catalog_lesson(id="day-02")])
        lessons = [_lesson()]

        errors = validate_corpus(catalog, lessons, _source_index(), required_ids={"day-01"})

        self.assertEqual(errors, [])

    def test_rejects_cross_lesson_duplicate_ids(self):
        catalog = _catalog([_catalog_lesson(id="day-01"), _catalog_lesson(id="day-02")])
        lesson_two = _lesson(id="day-02", catalogRef=_catalog_lesson(id="day-02"))
        errors = validate_corpus(catalog, [_lesson(), lesson_two], _source_index(), required_ids={"day-01", "day-02"})
        self.assertTrue(any("duplicate" in error and "sec-01" in error for error in errors))


class CliTests(unittest.TestCase):
    def _write_fixture_project(self, root: Path):
        catalog = _catalog([_catalog_lesson(id="day-01")])
        (root / "course-catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
        manifest = {"resources": [
            {"resourceId": "res-acff7fd27edc", "requestedUrl": "https://example.test/a"},
            {"resourceId": "res-99801d0b7043", "requestedUrl": "https://example.test/b"},
        ]}
        (root / "content").mkdir(parents=True, exist_ok=True)
        (root / "content" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        notes_dir = root / "content" / "source-notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        (notes_dir / "java-foundations.json").write_text(
            json.dumps([_source_note()]), encoding="utf-8"
        )
        lessons_dir = root / "content" / "lessons"
        lessons_dir.mkdir(parents=True, exist_ok=True)
        (lessons_dir / "day-01.json").write_text(json.dumps(_lesson()), encoding="utf-8")
        return catalog, lessons_dir

    def test_valid_single_lesson_corpus_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_fixture_project(root)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--catalog", str(root / "course-catalog.json"),
                    "--manifest", str(root / "content" / "source-manifest.json"),
                    "--source-notes-dir", str(root / "content" / "source-notes"),
                    "--lessons-dir", str(root / "content" / "lessons"),
                ])

        self.assertEqual(exit_code, 0)
        self.assertIn("PASS lessons=1", output.getvalue())

    def test_invalid_lesson_exits_nonzero_with_error_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, lessons_dir = self._write_fixture_project(root)
            broken = _lesson()
            broken["title"] = "Wrong title"
            (lessons_dir / "day-01.json").write_text(json.dumps(broken), encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--catalog", str(root / "course-catalog.json"),
                    "--manifest", str(root / "content" / "source-manifest.json"),
                    "--source-notes-dir", str(root / "content" / "source-notes"),
                    "--lessons-dir", str(lessons_dir),
                ])

        self.assertEqual(exit_code, 1)
        lines = [line for line in output.getvalue().splitlines() if line]
        self.assertTrue(all(line.startswith("ERROR ") for line in lines))

    def test_list_requirements_works_without_lesson_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = _catalog([_catalog_lesson(id="day-01")])
            (root / "course-catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
            manifest = {"resources": [
                {"resourceId": "res-acff7fd27edc", "requestedUrl": "https://example.test/a"},
            ]}
            (root / "content").mkdir(parents=True, exist_ok=True)
            (root / "content" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "content" / "source-notes"
            notes_dir.mkdir(parents=True, exist_ok=True)
            (notes_dir / "java-foundations.json").write_text(
                json.dumps([_source_note()]), encoding="utf-8"
            )
            lessons_dir = root / "content" / "lessons"

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--catalog", str(root / "course-catalog.json"),
                    "--manifest", str(root / "content" / "source-manifest.json"),
                    "--source-notes-dir", str(notes_dir),
                    "--lessons-dir", str(lessons_dir),
                    "--list-requirements", "day-01",
                ])

        self.assertEqual(exit_code, 0)
        self.assertFalse(lessons_dir.exists())
        report = output.getvalue()
        self.assertIn("day-01", report)
        self.assertIn("res-acff7fd27edc", report)
        self.assertIn("§2.5 Run-Time Data Areas", report)

    def test_only_flag_validates_subset_without_requiring_others(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = _catalog([_catalog_lesson(id="day-01"), _catalog_lesson(id="day-02")])
            (root / "course-catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
            manifest = {"resources": [
                {"resourceId": "res-acff7fd27edc", "requestedUrl": "https://example.test/a"},
                {"resourceId": "res-99801d0b7043", "requestedUrl": "https://example.test/b"},
            ]}
            (root / "content").mkdir(parents=True, exist_ok=True)
            (root / "content" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "content" / "source-notes"
            notes_dir.mkdir(parents=True, exist_ok=True)
            (notes_dir / "java-foundations.json").write_text(
                json.dumps([_source_note()]), encoding="utf-8"
            )
            lessons_dir = root / "content" / "lessons"
            lessons_dir.mkdir(parents=True, exist_ok=True)
            (lessons_dir / "day-01.json").write_text(json.dumps(_lesson()), encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--catalog", str(root / "course-catalog.json"),
                    "--manifest", str(root / "content" / "source-manifest.json"),
                    "--source-notes-dir", str(notes_dir),
                    "--lessons-dir", str(lessons_dir),
                    "--only", "day-01",
                ])

        self.assertEqual(exit_code, 0)
        self.assertIn("PASS lessons=1", output.getvalue())

    def test_compile_java_compiles_valid_snippet_and_reports_errors_for_invalid_one(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, lessons_dir = self._write_fixture_project(root)
            cache_root = root / ".course-cache"

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--catalog", str(root / "course-catalog.json"),
                    "--manifest", str(root / "content" / "source-manifest.json"),
                    "--source-notes-dir", str(root / "content" / "source-notes"),
                    "--lessons-dir", str(lessons_dir),
                    "--compile-java",
                    "--course-cache-dir", str(cache_root),
                ])
            self.assertEqual(exit_code, 0)

            broken = _lesson(sections=[_section(blocks=[
                _paragraph_block(),
                _code_block(code="class Snippet { void broken( { } }"),
            ])])
            (lessons_dir / "day-01.json").write_text(json.dumps(broken), encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--catalog", str(root / "course-catalog.json"),
                    "--manifest", str(root / "content" / "source-manifest.json"),
                    "--source-notes-dir", str(root / "content" / "source-notes"),
                    "--lessons-dir", str(lessons_dir),
                    "--compile-java",
                    "--course-cache-dir", str(cache_root),
                ])
            self.assertEqual(exit_code, 1)
            self.assertIn("day-01", output.getvalue())
            self.assertIn("block-code-01", output.getvalue())


if __name__ == "__main__":
    unittest.main()

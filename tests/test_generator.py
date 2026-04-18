import tempfile
import unittest
from pathlib import Path

from testmaxxing.config import GenerationConfig
from testmaxxing.generator import (
    build_test_file,
    build_go_test_file,
    build_java_test_file,
    build_javascript_test_file,
    default_output_path,
    split_go_function_path,
    split_java_function_path,
    split_javascript_function_path,
    split_function_path,
    write_test_file,
)


class GeneratorTests(unittest.TestCase):
    def test_split_function_path_supports_dot_and_colon(self) -> None:
        self.assertEqual(split_function_path("math.sqrt"), ("math", "sqrt"))
        self.assertEqual(split_function_path("math:sqrt"), ("math", "sqrt"))

    def test_split_go_function_path_supports_dot_and_colon(self) -> None:
        self.assertEqual(
            split_go_function_path("github.com/acme/pkg.Transform"),
            ("github.com/acme/pkg", "Transform"),
        )
        self.assertEqual(
            split_go_function_path("github.com/acme/pkg:Transform"),
            ("github.com/acme/pkg", "Transform"),
        )

    def test_split_java_function_path_supports_dot_and_colon(self) -> None:
        self.assertEqual(
            split_java_function_path("com.acme.tools.Strings.normalize"),
            ("com.acme.tools", "Strings", "normalize"),
        )
        self.assertEqual(
            split_java_function_path("com.acme.tools.Strings:normalize"),
            ("com.acme.tools", "Strings", "normalize"),
        )

    def test_split_javascript_function_path_supports_dot_and_colon(self) -> None:
        self.assertEqual(
            split_javascript_function_path("lib/strings.normalize"),
            ("lib/strings", "normalize"),
        )
        self.assertEqual(
            split_javascript_function_path("lib/strings:normalize"),
            ("lib/strings", "normalize"),
        )

    def test_generated_file_has_expected_number_of_tests(self) -> None:
        config = GenerationConfig(function_path="math.sqrt", tests=4, seed=123)
        content = build_test_file(config)
        self.assertEqual(content.count("\ndef test_"), 4)
        self.assertIn("assert True", content)
        compile(content, "<generated>", "exec")

    def test_generated_go_file_has_expected_number_of_tests(self) -> None:
        config = GenerationConfig(
            function_path="github.com/acme/pkg.Transform",
            lang="go",
            tests=3,
            seed=123,
        )
        content = build_go_test_file(config)
        self.assertEqual(content.count("\nfunc Test"), 3)
        self.assertIn("package pkg", content)
        self.assertIn("import \"testing\"", content)
        self.assertIn("t.Log(\"Target function:\", targetPath)", content)

    def test_generated_java_file_has_expected_number_of_tests(self) -> None:
        config = GenerationConfig(
            function_path="com.acme.tools.Strings.normalize",
            lang="java",
            tests=3,
            seed=123,
        )
        content = build_java_test_file(config)
        self.assertEqual(content.count("\n    @Test"), 3)
        self.assertIn("package com.acme.tools;", content)
        self.assertIn("public class StringsGibberishTest", content)
        self.assertIn("assertTrue(true);", content)

    def test_generated_javascript_file_has_expected_number_of_tests(self) -> None:
        config = GenerationConfig(
            function_path="lib/strings.normalize",
            lang="javascript",
            tests=3,
            seed=123,
        )
        content = build_javascript_test_file(config)
        self.assertEqual(content.count("\ntest("), 3)
        self.assertIn("const test = require(\"node:test\");", content)
        self.assertIn("assert.equal(true, true);", content)

    def test_write_test_file_uses_default_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = GenerationConfig(
                function_path="math.sqrt",
                tests=2,
                output=str(Path(tmp) / default_output_path("math.sqrt")),
            )
            out = Path(write_test_file(config))
            self.assertTrue(out.exists())
            self.assertIn("test_math_sqrt_gibberish.py", out.name)

    def test_default_output_path_for_go_uses_go_suffix(self) -> None:
        out = default_output_path("github.com/acme/pkg.Transform", "go")
        self.assertTrue(out.endswith("_gibberish_test.go"))

    def test_default_output_path_for_java_uses_java_suffix(self) -> None:
        out = default_output_path("com.acme.tools.Strings.normalize", "java")
        self.assertTrue(out.endswith("_GibberishTest.java"))

    def test_default_output_path_for_javascript_uses_js_suffix(self) -> None:
        out = default_output_path("lib/strings.normalize", "javascript")
        self.assertTrue(out.endswith("_gibberish.test.js"))


if __name__ == "__main__":
    unittest.main()

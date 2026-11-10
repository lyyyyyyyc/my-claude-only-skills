"""验收器正反测试；所有数据为临时夹具，不是实际项目运行证据。"""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
from audit_package import check_package, file_in, inventory, sha256


class PackageChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        self.package = self.project / "支撑材料"
        self.package.mkdir()
        self.private = self.project / "private-audit"
        self.private.mkdir()
        for name in ("Code", "Figures", "User_data"):
            (self.package / name).mkdir()
        self.put(
            "Readme.txt",
            "测试夹具\n\n1. 材料说明\n仅供自动测试\n\n2. 代码运行说明\n测试命令\n",
        )
        for name in ("run_all.py", "01_model.py", "02_plot.py"):
            self.put(f"Code/{name}", "print('fixture')\n")
        self.put("Code/requirements.txt", "# 仅用标准库\n")
        self.put(
            "code_sources.csv",
            "源文件,交付脚本\nsource.ipynb,Code/01_model.py\n",
        )
        self.put(
            "paper_figure_index.csv",
            "图号,文件\n图1,Figures/paper_figures/01.svg\n",
        )
        self.put(
            "Figures/paper_figures/01.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="80" height="80"/></svg>',
        )
        self.put("Figures/paper_tables/table.csv", "符号,含义\nx,样本\n")
        self.put(
            "Figures/results/problem_1_results/result.csv",
            "样本,结果\n1,2\n",
        )
        (self.private / "raw_result.csv").write_text(
            "样本,结果\n1,2\n", encoding="utf-8"
        )
        for name in ("coverage", "numerical", "visual"):
            self.put(f"{name}.csv", "检查,结论\n夹具,通过\n")
        for name in ("01_model", "02_plot"):
            self.put(
                f"logs/{name}.log",
                "fixture: synthetic record for unit test only\n",
            )
        (self.project / "source.ipynb").write_text(
            json.dumps(
                {"cells": [{"cell_type": "code", "source": ["x = 1\n"], "outputs": []}]}
            ),
            encoding="utf-8",
        )
        self.manifest = {
            "schema_version": 3,
            "paper_versions": ["测试版"],
            "required_sections": ["求解", "绘图"],
            "sources": [
                {
                    "path": "source.ipynb",
                    "sha256": sha256(self.project / "source.ipynb"),
                    "sections": ["求解", "绘图"],
                    "scripts": ["Code/01_model.py", "Code/02_plot.py"],
                }
            ],
            "helpers": [],
            "result_groups": ["problem_1_results"],
            "private_terms": [],
            "artifacts": [
                {
                    "id": "图1",
                    "kind": "paper_figure",
                    "paper_version": "测试版",
                    "path": "Figures/paper_figures/01.svg",
                    "sha256": sha256(self.package / "Figures/paper_figures/01.svg"),
                },
                {
                    "id": "表1",
                    "kind": "paper_table",
                    "paper_version": "测试版",
                    "path": "Figures/paper_tables/table.csv",
                },
                {
                    "id": "完整结果",
                    "kind": "result",
                    "path": "Figures/results/problem_1_results/result.csv",
                    "source_output": "raw_result.csv",
                },
            ],
            "external_data": [],
            "verification": "verification.json",
        }
        self.record = {
            "clean_run": True,
            "command": ["python", "Code/run_all.py"],
            "environment": {"python": sys.version.split()[0]},
            "code_sha256": {
                p.relative_to(self.package).as_posix(): sha256(p)
                for p in (self.package / "Code").glob("*.py")
            },
            "steps": [
                {
                    "script": f"Code/{s}.py",
                    "exit_code": 0,
                    "log": f"logs/{s}.log",
                }
                for s in ("01_model", "02_plot")
            ],
            "checks": {
                name: {"status": "passed", "evidence": f"{name}.csv"}
                for name in ("coverage", "numerical", "visual")
            },
        }

    def put(self, name, text):
        internal = name.startswith("logs/") or name in {
            "manifest.json",
            "verification.json",
            "coverage.csv",
            "numerical.csv",
            "visual.csv",
            "code_sources.csv",
            "paper_figure_index.csv",
        }
        path = (self.private if internal else self.package) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def audit(self):
        self.put(
            "manifest.json",
            json.dumps(self.manifest, ensure_ascii=False),
        )
        self.put(
            "verification.json",
            json.dumps(self.record, ensure_ascii=False),
        )
        return check_package(self.project, self.package, self.private)

    def fails(self, part):
        result = self.audit()
        self.assertFalse(result["通过"])
        self.assertTrue(any(part in message for message in result["错误"]), result)

    def test_valid_structure(self):
        self.assertTrue(self.audit()["通过"])

    def test_extra_root_file(self):
        self.put("README.md", "不应放在根目录")
        self.fails("根目录")

    def test_notebook_not_allowed(self):
        self.put("Code/old.ipynb", "{}")
        self.fails("Notebook")

    def test_other_languages_rejected(self):
        for suffix in ("m", "R", "jl", "js", "cpp", "ps1", "bat"):
            self.put(f"Code/legacy.{suffix}", "legacy source\n")
        self.fails("非PY源码")

    def test_notebook_provenance_is_rejected(self):
        self.put("Code/01_model.py", "print('Original source: source.ipynb')\n")
        self.record["code_sha256"]["Code/01_model.py"] = sha256(
            self.package / "Code/01_model.py"
        )
        result = self.audit()
        self.assertFalse(result["通过"], result)
        self.assertTrue(any("制作来源" in error for error in result["错误"]))

    def test_notebook_path_inside_command_is_warning(self):
        self.put(
            "Code/01_model.py",
            'import subprocess\nsubprocess.run("jupyter nbconvert --execute original.ipynb --to notebook", shell=True, check=True)\n',
        )
        self.record["code_sha256"]["Code/01_model.py"] = sha256(
            self.package / "Code/01_model.py"
        )
        result = self.audit()
        self.assertTrue(result["需人工复核"])

    def test_invalid_command_array(self):
        for command in ([None], [""], ["python", None], "python Code/run_all.py"):
            self.record["command"] = command
            self.fails("运行命令")

    def test_multiple_runs_of_same_script(self):
        repeated = copy.deepcopy(self.record["steps"][0])
        repeated.update(
            command=["python", "Code/01_model.py", "--scenario", "stress"],
            log="logs/stress.log",
        )
        self.put(repeated["log"], "fixture stress execution\n")
        self.record["steps"].append(repeated)
        self.assertTrue(self.audit()["通过"])
        repeated["exit_code"] = 1
        self.fails("未成功")

    def test_missing_figure(self):
        (self.package / "Figures/paper_figures/01.svg").unlink()
        self.fails("文件缺失")

    def test_wrong_figure_hash(self):
        self.put("Figures/paper_figures/01.svg", "changed")
        self.fails("论文图哈希")

    def test_stale_source(self):
        (self.project / "source.ipynb").write_text("{}", encoding="utf-8")
        self.fails("源文件哈希")

    def test_stale_code_record(self):
        self.put("Code/01_model.py", "print('changed')\n")
        self.fails("代码哈希")

    def test_missing_plot_run(self):
        self.record["steps"].pop()
        self.fails("全部功能PY")

    def test_failed_step(self):
        self.record["steps"][0]["exit_code"] = 1
        self.fails("未成功")

    def test_not_clean_run(self):
        self.record["clean_run"] = False
        self.fails("空缓存")

    def test_empty_log(self):
        self.put("logs/01_model.log", "")
        self.fails("文件为空")

    def test_missing_visual_evidence(self):
        (self.private / "visual.csv").unlink()
        self.fails("文件缺失")

    def test_required_module_missing(self):
        self.manifest["required_sections"].append("敏感性")
        self.fails("缺少功能覆盖")

    def test_undeclared_python(self):
        self.put("Code/forgotten.py", "x = 1\n")
        self.fails("未纳入")

    def test_undeclared_external_data(self):
        self.put("User_data/附件.csv", "样本,值\n1,2\n")
        self.fails("User_data")

    def test_external_data_documented(self):
        self.put("User_data/extra.csv", "样本,值\n1,2\n")
        self.manifest["external_data"] = [
            {
                "path": "User_data/extra.csv",
                "source": "模拟来源",
                "use": "夹具测试",
                "license": "自造数据",
            }
        ]
        self.assertTrue(self.audit()["通过"])

    def test_unknown_paper_version(self):
        self.manifest["artifacts"][0]["paper_version"] = "另一个版本"
        self.fails("版本未登记")

    def test_multiple_versions_kept_separate(self):
        self.manifest["paper_versions"].append("PDF版")
        table = copy.deepcopy(self.manifest["artifacts"][1])
        table["paper_version"] = "PDF版"
        self.manifest["artifacts"].append(table)
        self.assertTrue(self.audit()["通过"])

    def test_table_image_rejected(self):
        self.put("Figures/paper_tables/table.svg", "<svg/>")
        self.manifest["artifacts"][1]["path"] = "Figures/paper_tables/table.svg"
        self.fails("不是可编辑数据")

    def test_excel_sheet_missing(self):
        path = self.package / "Figures/paper_tables/table.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "xl/workbook.xml",
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="正确工作表"/></sheets></workbook>',
            )
        self.manifest["artifacts"][1].update(
            path="Figures/paper_tables/table.xlsx", sheet="错表"
        )
        self.fails("工作表缺失")

    def test_traversal_rejected(self):
        for path in (
            "../source.ipynb",
            "C:/outside/file.txt",
            "Code/../../file.txt",
            "\\\\host\\file",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                file_in(self.package, path)

    def test_syntax_and_kernel_state(self):
        self.put("Code/01_model.py", "if:\n")
        self.put("Code/02_plot.py", "get_ipython()\n")
        self.fails("语法")
        self.fails("内核")

    def test_compile_scope_error(self):
        self.put("Code/01_model.py", "return 1\n")
        self.record["code_sha256"]["Code/01_model.py"] = sha256(
            self.package / "Code/01_model.py"
        )
        self.fails("语法")

    def test_qualified_kernel_call(self):
        self.put(
            "Code/01_model.py",
            "import IPython\nIPython.get_ipython().run_line_magic('time', '1+1')\n",
        )
        self.record["code_sha256"]["Code/01_model.py"] = sha256(
            self.package / "Code/01_model.py"
        )
        self.fails("内核")

    def test_string_version_list_rejected(self):
        self.manifest["paper_versions"] = "测试版"
        self.manifest["artifacts"][0]["paper_version"] = "试"
        self.fails("必须是列表")

    def test_excel_entity_missing_and_present(self):
        (self.package / "Figures/paper_tables/table.csv").unlink()
        path = self.package / "Figures/paper_tables/table.xlsx"
        workbook = '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="数据" r:id="rId1"/></sheets></workbook>'
        relations = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>'
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("xl/workbook.xml", workbook)
            archive.writestr("xl/_rels/workbook.xml.rels", relations)
        self.manifest["artifacts"][1].update(
            path="Figures/paper_tables/table.xlsx", sheet="数据"
        )
        self.fails("工作表缺失")
        with zipfile.ZipFile(path, "a") as archive:
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>',
            )
        self.assertTrue(self.audit()["通过"])

    def test_inventory_excludes_output_and_reads_cells(self):
        result = inventory(self.project, [self.package, self.private])
        self.assertEqual(result["文件数"], 1)
        self.assertEqual(result["文件"][0]["代码单元数"], 1)

    def test_public_source_index_rejected(self):
        self.put("Figures/code_sources.csv", "来源,文件\na,b\n")
        self.fails("Figures只能含")

    def test_paper_table_omitted_from_manifest(self):
        self.manifest["artifacts"].pop(1)
        self.fails("论文表格实体与清单不一致")

    def test_paper_table_missing(self):
        (self.package / "Figures/paper_tables/table.csv").unlink()
        self.fails("文件缺失")

    def test_result_reformatted_rejected(self):
        self.put("Figures/results/problem_1_results/result.csv", '"样本","结果"\n1,2\n')
        self.fails("不是程序原样输出")

    def test_result_original_missing(self):
        (self.private / "raw_result.csv").unlink()
        self.fails("文件缺失")

    def test_numbering_gap_rejected(self):
        (self.package / "Figures/paper_figures/01.svg").rename(
            self.package / "Figures/paper_figures/03.svg"
        )
        self.fails("连续")

    def test_extra_process_results_rejected(self):
        self.put("Figures/results/run_logs/trace.txt", "test")
        self.fails("指定题号")

    def test_nested_process_result_rejected(self):
        self.put("Figures/results/problem_1_results/reference/old.csv", "a,b\n1,2\n")
        self.fails("不嵌套")

    def test_personal_path_rejected(self):
        self.put("Code/settings.json", '{"path":"C:/Users/PrivateName/work"}')
        self.fails("个人目录")

    def test_known_private_term_rejected(self):
        self.manifest["private_terms"] = ["PrivateProjectName"]
        self.put("Code/settings.json", '{"project":"PrivateProjectName"}')
        self.fails("已知个人")

    def test_xml_format_tag_is_not_identity(self):
        self.manifest["private_terms"] = ["LX"]
        path = self.package / "Figures/results/problem_1_results/style.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "xl/styles.xml", '<styleSheet><cellXfs count="2"/></styleSheet>'
            )
        self.assertTrue(self.audit()["通过"])

    def test_xml_attribute_identity_rejected(self):
        self.manifest["private_terms"] = ["LX"]
        path = self.package / "Figures/results/problem_1_results/style.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "xl/styles.xml", '<styleSheet><font name="LX"/></styleSheet>'
            )
        self.fails("已知个人")

    def test_xml_comment_identity_rejected(self):
        self.manifest["private_terms"] = ["LX"]
        path = self.package / "Figures/results/problem_1_results/style.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("xl/styles.xml", "<styleSheet><!-- LX --></styleSheet>")
        self.fails("已知个人")

    def test_xlsx_author_rejected(self):
        path = self.package / "Figures/results/problem_1_results/identity.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "docProps/core.xml",
                '<properties xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>PrivateName</dc:creator></properties>',
            )
        self.fails("作者属性")

    def test_generic_generator_is_not_personal_author(self):
        path = self.package / "Figures/results/problem_1_results/generated.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "docProps/core.xml",
                '<properties xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>openpyxl</dc:creator></properties>',
            )
        self.assertTrue(self.audit()["通过"])

    def test_cli_valid_and_missing_manifest(self):
        self.audit()
        command = [
            sys.executable,
            str(Path(__file__).with_name("audit_package.py")),
            "check",
            "--project",
            str(self.project),
            "--package",
            str(self.package),
            "--audit-dir",
            str(self.private),
        ]
        passed = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", timeout=20
        )
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        (self.private / "manifest.json").unlink()
        failed = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", timeout=20
        )
        self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

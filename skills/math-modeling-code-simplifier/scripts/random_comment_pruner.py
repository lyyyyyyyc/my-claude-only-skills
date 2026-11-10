"""按高斯随机采样精简 Python 文件中的中文井号注释。

处理规则：
1. 只处理 Python 词法分析器识别出的 COMMENT 标记；
2. 只处理包含中文字符的注释；
3. 注释正文中的标点参与计数，空白字符不参与计数；
4. 每组第 5 个有效字符接受一次高斯抽样；
5. 抽样值大于阈值时删除该字符；
6. 默认连续处理两轮，后一轮基于前一轮的结果重新计数；
7. 默认生成新文件，不覆盖输入文件。
"""

from __future__ import annotations

import argparse
import io
import random
import re
import tokenize
from pathlib import Path


CHINESE_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def clipped_gaussian(rng: random.Random, mean: float, std: float) -> float:
    """生成高斯随机数，并将结果限制在 0 到 1 之间。"""
    return min(1.0, max(0.0, rng.gauss(mean, std)))


def prune_comment_body(
    body: str,
    rng: random.Random,
    group_size: int,
    mean: float,
    std: float,
    threshold: float,
) -> tuple[str, int]:
    """处理一段井号后的注释正文，并返回新正文和删除数量。"""
    if not CHINESE_PATTERN.search(body):
        return body, 0

    result: list[str] = []
    counted_characters = 0
    deleted_characters = 0

    for character in body:
        # 空格、制表符等空白原样保留，也不计入每 5 个字符的分组。
        if character.isspace():
            result.append(character)
            continue

        counted_characters += 1
        is_group_end = counted_characters % group_size == 0

        if is_group_end:
            sampled_value = clipped_gaussian(rng, mean, std)
            if sampled_value > threshold:
                deleted_characters += 1
                continue

        # 被删除的字符不写入列表，后面的字符会自然向左补齐。
        result.append(character)

    return "".join(result), deleted_characters


def collect_comment_edits(
    source: str,
    rng: random.Random,
    group_size: int,
    mean: float,
    std: float,
    threshold: float,
) -> tuple[dict[int, list[tuple[int, int, str]]], int, int]:
    """使用 tokenize 收集需要应用到各行的注释修改。"""
    edits: dict[int, list[tuple[int, int, str]]] = {}
    processed_comments = 0
    total_deleted = 0

    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue

        comment = token.string
        body = comment[1:]
        new_body, deleted = prune_comment_body(
            body=body,
            rng=rng,
            group_size=group_size,
            mean=mean,
            std=std,
            threshold=threshold,
        )

        if not CHINESE_PATTERN.search(body):
            continue

        processed_comments += 1
        total_deleted += deleted

        if new_body != body:
            line_index = token.start[0] - 1
            edits.setdefault(line_index, []).append(
                (token.start[1], token.end[1], "#" + new_body)
            )

    return edits, processed_comments, total_deleted


def apply_edits(source: str, edits: dict[int, list[tuple[int, int, str]]]) -> str:
    """将注释修改应用到源码，同时保留原有换行符。"""
    lines = source.splitlines(keepends=True)

    for line_index, line_edits in edits.items():
        line = lines[line_index]

        # 从右向左替换，避免前一次替换改变后续位置坐标。
        for start, end, replacement in sorted(line_edits, reverse=True):
            line = line[:start] + replacement + line[end:]

        lines[line_index] = line

    return "".join(lines)


def detect_source_encoding(raw_data: bytes) -> str:
    """按照 Python 源文件编码声明检测文本编码。"""
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw_data).readline)
    return encoding


def build_default_output_path(input_path: Path) -> Path:
    """根据输入文件名生成默认输出路径。"""
    return input_path.with_name(f"{input_path.stem}_comment_pruned{input_path.suffix}")


def process_file(
    input_path: Path,
    output_path: Path,
    seed: int,
    passes: int,
    group_size: int,
    mean: float,
    std: float,
    threshold: float,
) -> list[tuple[int, int]]:
    """读取、处理并写出一个 Python 文件。"""
    if input_path.suffix.lower() != ".py":
        raise ValueError("输入文件必须使用 .py 扩展名")

    if not input_path.is_file():
        raise FileNotFoundError(f"找不到输入文件：{input_path}")

    if input_path.resolve() == output_path.resolve():
        raise ValueError("输出路径不能与输入路径相同，脚本默认禁止覆盖原文件")

    if output_path.exists():
        raise FileExistsError(f"输出文件已存在，请更换路径：{output_path}")

    raw_data = input_path.read_bytes()
    encoding = detect_source_encoding(raw_data)
    source = raw_data.decode(encoding)
    rng = random.Random(seed)
    pass_statistics: list[tuple[int, int]] = []

    # 每轮都处理上一轮产生的新源码，并从每条注释开头重新计数。
    # rng 不会在轮次之间重置，因此每轮抽样不同，但固定种子仍可复现。
    transformed_source = source
    for _ in range(passes):
        edits, processed_comments, deleted_characters = collect_comment_edits(
            source=transformed_source,
            rng=rng,
            group_size=group_size,
            mean=mean,
            std=std,
            threshold=threshold,
        )
        transformed_source = apply_edits(transformed_source, edits)
        pass_statistics.append((processed_comments, deleted_characters))

    # 编译检查在写出前完成，避免生成语法无效的结果文件。
    compile(transformed_source, str(output_path), "exec")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(transformed_source.encode(encoding))

    return pass_statistics


def probability(value: str) -> float:
    """解析并检查 0 到 1 之间的小数参数。"""
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("参数必须位于 0 到 1 之间")
    return number


def positive_integer(value: str) -> int:
    """解析正整数参数。"""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("参数必须是正整数")
    return number


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="按高斯抽样删除 Python 中文注释中每组第 5 个字符。"
    )
    parser.add_argument("input", type=Path, help="需要处理的 Python 文件")
    parser.add_argument("-o", "--output", type=Path, help="新文件的输出路径")
    parser.add_argument("--seed", type=int, default=20260829, help="随机种子")
    parser.add_argument(
        "--passes",
        type=positive_integer,
        default=2,
        help="连续抽样删除的轮数，默认 2",
    )
    parser.add_argument(
        "--group-size",
        type=positive_integer,
        default=5,
        help="字符分组长度，默认 5",
    )
    parser.add_argument("--mean", type=probability, default=0.5, help="高斯均值")
    parser.add_argument("--std", type=probability, default=0.15, help="高斯标准差")
    parser.add_argument(
        "--threshold",
        type=probability,
        default=0.4,
        help="删除阈值，默认 0.4",
    )
    return parser.parse_args()


def main() -> None:
    """命令行入口。"""
    arguments = parse_arguments()
    input_path = arguments.input.resolve()
    output_path = (
        arguments.output.resolve()
        if arguments.output
        else build_default_output_path(input_path)
    )

    pass_statistics = process_file(
        input_path=input_path,
        output_path=output_path,
        seed=arguments.seed,
        passes=arguments.passes,
        group_size=arguments.group_size,
        mean=arguments.mean,
        std=arguments.std,
        threshold=arguments.threshold,
    )

    print(f"处理完成：{output_path}")
    for pass_number, (processed_comments, deleted_characters) in enumerate(
        pass_statistics,
        start=1,
    ):
        print(
            f"第 {pass_number} 轮：处理 {processed_comments} 条中文注释，"
            f"删除 {deleted_characters} 个字符"
        )
    print(f"累计删除的字符数量：{sum(item[1] for item in pass_statistics)}")
    print(f"随机种子：{arguments.seed}")


if __name__ == "__main__":
    main()

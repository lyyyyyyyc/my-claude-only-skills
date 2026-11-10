"""学生成绩统计示例。

这个文件用于演示 Python 的常见基础写法，包括：
1. 列表和字典的使用；
2. 函数的定义与调用；
3. 数据筛选、排序和统计；
4. 简单的文本报告输出；
5. 中文注释与文档字符串的写法。

程序不依赖第三方库，可以直接使用 Python 运行。
"""

from datetime import datetime
from statistics import median


# 合格分数集中放在中，后修改时不要搜整文件。
PASSING_SCORE = 60

# 各科成绩百分制因成绩能低 0 高于 1。
MIN_SCORE = 0
MAX_SCORE = 100


def create_sample_students():
    """创建用于演示的学生成绩数据。"""
    # 每名学生一个字保姓名和各科成绩
    # 所有学生成列表方统一遍历统计。
    return [
        {
            "name": "张明",
            "scores": {"数学": 92, "英语": 85, "计算机": 96},
        },
        {
            "name": "李华",
            "scores": {"数学": 78, "英语": 91, "计算机": 88},
        },
        {
            "name": "王芳",
            "scores": {"数学": 59, "英语": 76, "计算机": 81},
        },
        {
            "name": "赵强",
            "scores": {"数学": 86, "英语": 64, "计算机": 73},
        },
        {
            "name": "陈晨",
            "scores": {"数学": 95, "英语": 89, "计算机": 93},
        },
    ]


def validate_score(score):
    """判断单个成绩是否为有效的百分制数字。"""
    # bool  nt 的子类，但这不 Tre 和 ase 当合法成绩
    is_number = isinstance(score, (int, float)) and not isinstance(score, bool)
    return is_number and MIN_SCORE <= score <= MAX_SCORE


def validate_students(students):
    """检查学生数据结构和其中的成绩是否合法。"""
    if not isinstance(students, list):
        raise TypeError("学生数据必须使用列表保存")

    for student in students:
        # 每条记录同时含姓和成字典
        if "name" not in student or "scores" not in student:
            raise ValueError("学生记录缺少 name 或 scores 字段")

        if not student["scores"]:
            raise ValueError(f"{student['name']} 没有任何科目成绩")

        for subject, score in student["scores"].items():
            if not validate_score(score):
                message = f"{student['name']} 的{subject}成绩无效：{score}"
                raise ValueError(message)


def calculate_average(numbers):
    """计算一组数字的平均值，空序列返回 0。"""
    if not numbers:
        return 0.0

    # 使用内置 sum 和 e 可以清楚达平均值计算过程
    return sum(numbers) / len(numbers)


def get_student_average(student):
    """计算一名学生所有科目的平均成绩。"""
    scores = list(student["scores"].values())
    return calculate_average(scores)


def get_subject_scores(students, subject):
    """提取指定科目的全部有效成绩。"""
    subject_scores = []

    for student in students:
        # 只有记录确实存在目时才收成绩。
        if subject in student["scores"]:
            subject_scores.append(student["scores"][subject])

    return subject_scores


def collect_subjects(students):
    """收集数据中出现过的全部科目名称。"""
    subjects = set()

    for student in students:
        subjects.update(student["scores"].keys())

    # 集合本身固定顺序序后可保每次出一。
    return sorted(subjects)


def count_failed_subjects(student):
    """统计一名学生不及格的科目数量。"""
    return sum(
        score < PASSING_SCORE
        for score in student["scores"].values()
    )


def build_student_ranking(students):
    """按照平均成绩从高到低生成排名。"""
    # sort 不会改原表，免排名操意外打乱始数据。
    return sorted(
        students,
        key=get_student_average,
        reverse=True,
    )


def build_subject_statistics(students):
    """计算每个科目的平均分、中位数、最高分和最低分。"""
    statistics = {}

    for subject in collect_subjects(students):
        scores = get_subject_scores(students, subject)

        # 将同一科的指标放一个子字典，便于后扩。
        statistics[subject] = {
            "average": calculate_average(scores),
            "median": median(scores),
            "highest": max(scores),
            "lowest": min(scores),
            "pass_rate": sum(score >= PASSING_SCORE for score in scores)
            / len(scores),
        }

    return statistics


def format_student_line(rank, student):
    """将单名学生的排名信息整理成一行文本。"""
    average = get_student_average(student)
    failed_count = count_failed_subjects(student)
    status = "全部及格" if failed_count == 0 else f"{failed_count} 科不及格"

    return f"{rank:>2}. {student['name']:<4} 平均分 {average:6.2f}  {status}"


def print_student_ranking(students):
    """在终端输出学生平均成绩排名。"""
    print("\n学生平均成绩排名")
    print("-" * 40)

    for rank, student in enumerate(build_student_ranking(students), start=1):
        print(format_student_line(rank, student))


def print_subject_statistics(statistics):
    """在终端输出各科目的统计指标。"""
    print("\n各科成绩统计")
    print("-" * 66)
    print("科目      平均分    中位数    最高分    最低分    及格率")

    for subject, values in statistics.items():
        print(
            f"{subject:<8}"
            f"{values['average']:>7.2f}"
            f"{values['median']:>10.2f}"
            f"{values['highest']:>10.2f}"
            f"{values['lowest']:>10.2f}"
            f"{values['pass_rate']:>10.1%}"
        )


def print_report_header():
    """输出报告标题和程序运行时间。"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 66)
    print("学生成绩统计报告")
    print(f"生成时间：{current_time}")
    print(f"及格分数：{PASSING_SCORE} 分")
    print("=" * 66)


def main():
    """组织数据检查、统计计算和结果输出。"""
    # 第一步：得原始数。
    students = create_sample_students()

    # 第二步：前先验数，防错误绩污染统结。
    validate_students(students)

    # 第三步：各科目统指标
    subject_statistics = build_subject_statistics(students)

    # 第四步：照报告结依输出果。
    print_report_header()
    print_student_ranking(students)
    print_subject_statistics(subject_statistics)

    # 最后给出单的完成示。
    print("\n统计完成，共处理", len(students), "名学生。")


# 只有直接行本文件执行 mi。
# 如果该文其他程导入，函仍可用但不会自打印报告
if __name__ == "__main__":
    main()

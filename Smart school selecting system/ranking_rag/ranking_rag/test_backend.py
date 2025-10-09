import json
import requests
import json

# 新的前端返回的student profile数据格式
test_student_profile = {
    "academics": {
        "gpa": "3.8",
        "sat": "1450",
        "act": "33",
        "toefl": "105",
        "ielts": "7.5",
        "det": "130"
    },
    "activities": {
        "research_months": 6,
        "research_type": "计算机科学",
        "volunteer_months": 12,
        "volunteer_type": "教育",
        "internship_months": 3,
        "internship_type": "科技公司",
        "art_months": 0,
        "art_type": "",
        "full_time_work_months": 0,
        "full_time_work_type": "",
        "honors": "优秀学生奖学金"
    },
    "preferences": {
        "career_interest": "软件工程",
        "location": "西海岸",
        "size": "大型",
        "tuition": 150000,
        "major": "计算机科学",
        "teacher_student_ratio": "低",
        "school_atmosphere": "创新",
        "international_level": "高"
    }
}

# 保存测试数据到文件
with open('test_student_data.json', 'w', encoding='utf-8') as f:
    json.dump(test_student_profile, f, ensure_ascii=False, indent=2)

print("测试数据已保存到 test_student_data.json")
print("\n测试数据内容:")
print(json.dumps(test_student_profile, ensure_ascii=False, indent=2))

# 测试空字符串处理的学生数据
test_empty_string_profile = {
    "academics": {
        "gpa": "",  # 空字符串测试
        "sat": None,
        "act": "",  # 空字符串测试
        "toefl": None,
        "ielts": "",  # 空字符串测试
        "det": None
    },
    "activities": {
        "research_months": 0,
        "research_type": "",
        "volunteer_months": 0,
        "volunteer_type": "",
        "internship_months": 0,
        "internship_type": "",
        "art_months": 0,
        "art_type": "",
        "full_time_work_months": 0,
        "full_time_work_type": "",
        "honors": ""
    },
    "preferences": {
        "career_interest": "",
        "location": "",
        "size": "",
        "tuition": 0,
        "major": "",
        "teacher_student_ratio": "",
        "school_atmosphere": "",
        "international_level": ""
    }
}

# 保存空字符串测试数据
test_empty_file = 'test_empty_data.json'
with open(test_empty_file, 'w', encoding='utf-8') as f:
    json.dump(test_empty_string_profile, f, ensure_ascii=False, indent=2)

print(f"\n空字符串测试数据已保存到 {test_empty_file}")
print("\n请先启动后端服务器，然后使用以下命令测试API:")
print("curl -X POST http://localhost:8000/recommend -H 'Content-Type: application/json' -d @test_student_data.json")
print(f"\n测试空字符串处理:")
print(f"curl -X POST http://localhost:8000/recommend -H 'Content-Type: application/json' -d @{test_empty_file}")

# 直接测试API（可选）
if __name__ == "__main__":
    print("\n是否直接测试API? (y/n)")
    choice = input().strip().lower()
    if choice == 'y':
        try:
            url = "http://localhost:8000/recommend"
            headers = {'Content-Type': 'application/json'}
            
            print("\n测试标准数据...")
            response = requests.post(url, headers=headers, json=test_student_profile, timeout=30)
            print(f"响应状态码: {response.status_code}")
            print("响应内容:\n", json.dumps(response.json(), ensure_ascii=False, indent=2))
            
            print("\n测试空字符串数据...")
            response = requests.post(url, headers=headers, json=test_empty_string_profile, timeout=30)
            print(f"响应状态码: {response.status_code}")
            print("响应内容:\n", json.dumps(response.json(), ensure_ascii=False, indent=2))
            
        except requests.exceptions.ConnectionError:
            print("\n错误: 无法连接到后端服务器。请先启动后端服务再运行此测试。")
            print("启动命令: python 后端demo.py")
        except Exception as e:
            print(f"\n测试过程中发生错误: {e}")
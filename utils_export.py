import json

def generate_json(data: list[dict]):
    return json.dumps(data, indent=4)

def generate_txt(data: list[dict]):
    lines = ["Student ID\tTimestamp\tIP Address\tManual Entry"]
    for row in data:
        lines.append(f"{row['student_id']}\t{row['created_at']}\t{row['ip_address']}\t{row['manual_entry']}")
    return "\n".join(lines)
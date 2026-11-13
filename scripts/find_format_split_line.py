import json

with open(r'C:\Users\Shourya\.gemini\antigravity\brain\3bc11426-e90f-464a-b76e-06bcfc711545\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if 'Format Split' in line:
            print(f"Line {idx+1}")
            data = json.loads(line)
            tool_calls = data.get('tool_calls', [])
            if tool_calls:
                print("Tool call args Path:", tool_calls[0].get('args', {}).get('Path'))
                content = tool_calls[0].get('args', {}).get('Content', '')
                lines = content.splitlines()
                for i, l in enumerate(lines):
                    if 'Format Split' in l:
                        print("\n".join(lines[max(0, i-5):min(len(lines), i+25)]))
                        break

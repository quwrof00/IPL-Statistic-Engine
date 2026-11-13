import json

with open(r'C:\Users\Shourya\.gemini\antigravity\brain\3bc11426-e90f-464a-b76e-06bcfc711545\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if idx == 474:
            data = json.loads(line)
            tool_calls = data.get('tool_calls', [])
            if tool_calls:
                content = tool_calls[0].get('args', {}).get('Content', '')
                for l in content.splitlines():
                    if 'Format Split' in l or 'Single-format' in l or 'No IPL' in l:
                        print("Found:", l)
            break

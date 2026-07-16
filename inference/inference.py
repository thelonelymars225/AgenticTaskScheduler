import ollama

client = ollama.Client()
client.generate(model='llama3.2:3b', prompt='', keep_alive='60m',  options={
        'temperature': 0.1
    })

def business_analysis(prompt):
    response = client.chat(
        model="llama3.2:3b",
        messages=[
            {"role": "system", "content": "You are a business analyst. Analyze the requirements, scope, and complexity of the task. Do NOT write code. End your analysis with a line 'COMPLEXITY: X' where X is 1000 (trivial), 2000 (simple), 4000 (medium), 8000 (complex), or 12000 (very complex)."},
            {"role": "user", "content": prompt}
        ],
        options={'temperature': 0.1, 'num_predict': 500}
    )
    return response["message"]["content"]

def _to_tokens(char_limit):
    return min(char_limit // 3, 2000)

def write_code(prompt, char_limit):
    max_tokens = _to_tokens(char_limit)
    response = client.chat(
        model="qwen3",
        messages=[
            {"role": "system", "content": f"You are a software engineer. Write code based on the prompt. Maximum {char_limit} characters for the ENTIRE response."},
            {"role": "user", "content": prompt}
        ],
        options={'temperature': 0.1, 'num_predict': max_tokens}
    )
    return response["message"]["content"]
def fix_code(existing_code, feedback, char_limit):
    max_tokens = _to_tokens(char_limit)
    response = client.chat(
        model="qwen3",
        messages=[
            {"role": "system", "content": f"You are a software engineer. Fix the provided code based on the feedback. Return the ENTIRE corrected file — do not omit or truncate anything. Maximum {char_limit} characters."},
            {"role": "user", "content": f"## Existing Code\n```\n{existing_code}\n```\n\n## Feedback\n{feedback}\n\nFix all issues above. Return the complete file."}
        ],
        options={'temperature': 0.1, 'num_predict': max_tokens}
    )
    return response["message"]["content"]

def validate_code(code):
    """Check Python syntax only (fast). Runtime validation is skipped to avoid blocking on GUI apps."""
    try:
        compile(code, "<string>", "exec")
        return ""
    except SyntaxError as e:
        return f"SyntaxError: {e}"

def qa(prompt):
    response = client.chat(
        model="llama3.2:3b",
        messages=[
            {"role": "system", "content": "You are a QA engineer. please find bugs in the following code and provide a concise analysis, if the code has no bugs, state that it has no bugs by saying 'No bugs found.'"},
            {"role": "user", "content": prompt}
        ],
        options={'temperature': 0.5, 'num_predict': 500}
    )
    return response["message"]["content"]
def project_management(prompt, max_retries=5):
    import re
    business_analysis_result = business_analysis(prompt)

    # Extract complexity score from business analysis (no extra LLM call)
    match = re.search(r'COMPLEXITY:\s*(\d+)', business_analysis_result, re.IGNORECASE)
    char_limit = int(match.group(1)) if match else 4000

    code = write_code(business_analysis_result, char_limit)

    for attempt in range(max_retries):
        feedback = qa(code)

        if "No bugs found." in feedback:
            build_errors = validate_code(code)
            if not build_errors:
                return business_analysis_result, code, feedback

        print(f"Issues found, fixing... (attempt {attempt + 1}/{max_retries})")
        code = fix_code(code, feedback, char_limit)

    return business_analysis_result, code, qa(code)
    


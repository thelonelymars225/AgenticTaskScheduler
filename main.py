import re
from inference.inference import project_management

def extract_code(text):
    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
    if code_blocks:
        return code_blocks[-1].strip()
    return text.strip()

def main():
    prompt = "write gui based calculator in python with addition, subtraction, multiplication, division and history of operations"
    business_analysis_result, code, qa_result = project_management(prompt)
    
    with open("output.txt", "w") as f:
        f.write(f"=== Business Analysis ===\n{business_analysis_result}\n\n=== Code ===\n{code}\n\n=== QA Result ===\n{qa_result}\n")
    
    clean_code = extract_code(code)
    with open("output.py", "w") as f:
        f.write(clean_code)

if __name__ == "__main__":
    main()
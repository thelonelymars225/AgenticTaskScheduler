from inference.inferenceLocal import project_management, _strip_code_blocks
from timer import Timer
import os
def main():
    prompt = "write a python game of pong using tkinter and object oriented programming"

    with Timer("pipeline.total"):
        business_analysis_result, code, qa_result = project_management(prompt)

    with open("output.txt", "w") as f:
        f.write(f"=== Business Analysis ===\n{business_analysis_result}\n\n=== Code ===\n{code}\n\n=== QA Result ===\n{qa_result}\n")

    # Try to extract code from the code output first, fall back to business analysis
    clean_code = _strip_code_blocks(code) or _strip_code_blocks(business_analysis_result)
    if clean_code:
        with open("output.py", "w") as f:
            f.write(clean_code)
        print(f"✅ Written {len(clean_code)} chars to output.py")
    else:
        print("⚠️  No code block found in any output. output.py was not written.")

if __name__ == "__main__":
    main()
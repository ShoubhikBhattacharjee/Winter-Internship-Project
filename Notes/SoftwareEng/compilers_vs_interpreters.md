# Compilers vs. Interpreters

Computers don't understand high-level code like `print("Hello")`. They only understand binary (0s and 1s). Compilers and Interpreters are the tools that do the translation.



## Compilers
A compiler takes the **entire** program and converts it into an "executable" file (like an `.exe` on Windows).
- **Speed:** Very fast execution because the translation is already done.
- **Errors:** It shows all syntax errors at once; the program won't run until every error is fixed.
- **Languages:** C, C++, Rust, Go.

## Interpreters
An interpreter reads the code **line-by-line** and executes it immediately.
- **Speed:** Slower than compiled code because it translates while it runs.
- **Errors:** It stops running the moment it hits an error, making it easier to debug specific lines.
- **Languages:** Python, JavaScript, Ruby, PHP.

## Summary Comparison
| Feature | Compiler | Interpreter |
| :--- | :--- | :--- |
| **Execution** | Faster (Pre-translated) | Slower (Real-time translation) |
| **Output** | Generates an intermediate .exe or binary | Does not generate a separate file |
| **Debugging** | Harder (errors shown at the end) | Easier (stops at the exact line) |
| **Portability** | Target-specific (needs re-compiling) | More portable (needs an interpreter) |
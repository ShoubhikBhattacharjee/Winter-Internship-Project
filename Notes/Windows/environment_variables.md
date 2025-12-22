# Windows Environment Variables

Environment variables are "sticky notes" for your operating system. They store information that programs need to run correctly.



## System vs. User Variables
- **System Variables:** Apply to every user on the computer. Only administrators can change these.
- **User Variables:** Specific to the currently logged-in user.

## The PATH Variable
The `PATH` variable is the most famous environment variable. When you type `python` in a terminal, Windows does the following:
1. Looks in the **current folder** for `python.exe`.
2. If not found, it looks through every folder listed in the **PATH** variable one by one.
3. If it finds it in one of those folders, the program runs. If not, you get an error: *"is not recognized as an internal or external command."*

## How to View via CLI
- **Command Prompt:** Type `set` to see all variables.
- **PowerShell:** Type `Get-ChildItem Env:` or `$env:PATH` to see specific ones.
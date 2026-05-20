# Click-Level Test Suite

This directory contains click-flow tests for core user actions.

Covered flow:
1. Open login page
2. Register account
3. Login
4. Create task
5. Complete task
6. Edit task
7. Search by completion status
8. Delete task

Run commands:

```powershell
.\.venv\Scripts\python.exe -m pip install -r tests\requirements.txt
.\.venv\Scripts\python.exe -m pytest
```

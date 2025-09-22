import ast

code = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
"""

tree = ast.parse(code)

print("AST Dump:")
print(ast.dump(tree, indent=2))

print("\n\nWalking through nodes:")
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        print(f"Found function: {node.name}")
        for decorator in node.decorator_list:
            print(f"  Decorator: {ast.dump(decorator)}")

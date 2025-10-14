[tool.pygbag]
name = "mangov3"
version = "0.1.0"
cdn = "https://pygame-web.github.io/archives/0.9/"
build_dir = "build/web"
assets = [
    "./assets/**",
    "./main.py",
    "./project.py"
]
icon = "favicon.png"
package = "web.pygame.mangov3"

exclude = [
    ".venv",
    "__pycache__",
    "tests",
    "build",
    "dist",
    ".pytest_cache"
]

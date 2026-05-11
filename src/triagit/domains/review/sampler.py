from dataclasses import dataclass

from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.github.schemas import RepoInfo

SOURCE_DIR_PRIORITIES: dict[str, list[str]] = {
    "Python": ["src", "lib"],
    "JavaScript": ["src", "lib", "packages", "app"],
    "TypeScript": ["src", "lib", "packages", "app"],
    "Go": ["pkg", "internal", "cmd"],
    "Rust": ["src"],
    "Java": ["src/main/java"],
    "Kotlin": ["src/main/kotlin"],
    "Ruby": ["lib", "app"],
    "C": ["src"],
    "C++": ["src"],
    "C#": ["src"],
}

SOURCE_EXTENSIONS: dict[str, set[str]] = {
    "Python": {".py"},
    "JavaScript": {".js", ".jsx", ".mjs"},
    "TypeScript": {".ts", ".tsx"},
    "Go": {".go"},
    "Rust": {".rs"},
    "Java": {".java"},
    "Kotlin": {".kt"},
    "Ruby": {".rb"},
    "C": {".c", ".h"},
    "C++": {".cpp", ".cc", ".h", ".hpp"},
    "C#": {".cs"},
}

README_FILES = ("README.md", "README.rst", "README.txt", "README")
MANIFEST_FILES = (
    "pyproject.toml",
    "setup.py",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
)

MAX_FILE_BYTES = 64 * 1024  # skip large generated/vendored files


@dataclass(frozen=True)
class SampledSource:
    path: str
    content: str
    loc: int


@dataclass(frozen=True)
class SamplingResult:
    files: list[SampledSource]
    candidate_count: (
        int  # source files we saw in the chosen dir; the denominator for "X of Y"
    )
    note: str


async def sample_repo(
    github: GitHubClient,
    owner: str,
    name: str,
    repo: RepoInfo,
    max_files: int = 8,
) -> SamplingResult:
    language = repo.language or ""
    extensions = SOURCE_EXTENSIONS.get(language, set())
    dir_candidates = SOURCE_DIR_PRIORITIES.get(language, ["src", "lib"])

    root = await github.list_contents(owner, name)
    root_by_name = {e.name: e for e in root}

    picked_paths: list[str] = []

    for readme in README_FILES:
        entry = root_by_name.get(readme)
        if entry and entry.type == "file":
            picked_paths.append(entry.path)
            break

    for manifest in MANIFEST_FILES:
        entry = root_by_name.get(manifest)
        if entry and entry.type == "file":
            picked_paths.append(entry.path)
            break

    chosen_dir: str | None = None
    source_dir_entries: list = []
    for d in dir_candidates:
        entry = root_by_name.get(d)
        if entry and entry.type == "dir":
            chosen_dir = d
            source_dir_entries = await github.list_contents(owner, name, d)
            break

    if not source_dir_entries:
        source_dir_entries = root  # fall back to scanning the root

    candidates = [
        e
        for e in source_dir_entries
        if e.type == "file"
        and (not extensions or any(e.name.endswith(ext) for ext in extensions))
        and 0 < e.size <= MAX_FILE_BYTES
    ]

    remaining = max_files - len(picked_paths)
    for e in candidates[:remaining]:
        picked_paths.append(e.path)

    sampled: list[SampledSource] = []
    for path in picked_paths:
        file = await github.get_file_content(owner, name, path)
        text = file.decoded_text()
        sampled.append(SampledSource(path=path, content=text, loc=text.count("\n") + 1))

    location = f"{chosen_dir}/" if chosen_dir else "repo root"
    lang_label = f"{language} " if language else ""
    note = f"Sampled {len(sampled)} {lang_label}files from {location} plus top-level README/manifest."

    return SamplingResult(files=sampled, candidate_count=len(candidates), note=note)

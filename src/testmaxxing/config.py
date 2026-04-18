from dataclasses import dataclass


@dataclass
class GenerationConfig:
    function_path: str
    lang: str = "python"
    tests: int = 25
    sanity: float = 0.3  # 0.0 = full chaos, 1.0 = corporate cringe
    output: str = ""
    seed: int | None = None

    def __post_init__(self) -> None:
        self.lang = self.lang.lower().strip()
        if self.lang == "js":
            self.lang = "javascript"
        if self.lang not in {"python", "go", "java", "javascript"}:
            raise ValueError("lang must be one of: python, go, java, javascript")
        self.tests = max(1, self.tests)
        self.sanity = max(0.0, min(1.0, self.sanity))

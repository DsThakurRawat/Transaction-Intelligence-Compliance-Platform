from core.analyzer import Analyzer

_analyzers: dict[str, Analyzer] = {}

def register(analyzer: Analyzer):
    _analyzers[analyzer.name] = analyzer

def get_analyzer(name: str) -> Analyzer:
    return _analyzers[name]

def list_analyzers() -> list[str]:
    return list(_analyzers.keys())

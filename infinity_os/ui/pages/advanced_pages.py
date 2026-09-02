from pathlib import Path
_parts = Path(__file__).parent
_source = ''.join(p.read_text(encoding='utf-8') for p in sorted(_parts.glob('_advanced_pages_*.part')))
exec(compile(_source, str(_parts / 'advanced_pages_impl.py'), 'exec'), globals())
del _source, _parts

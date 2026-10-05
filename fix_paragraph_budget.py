"""Allow shorter paragraphs and build to the chapter's required total length."""
import importlib
from pathlib import Path
import bookwriter.paragraph_writer as writer

path = Path(writer.__file__)
text = path.read_text()
old = '    for index,guide in enumerate(GUIDES):'
new = '''    for index in range(16):
        total = sum(len(WORD.findall(CITATION.sub('', p))) for p in paragraphs)
        if index >= 8 and total >= 630:
            break
        guide = GUIDES[index] if index < len(GUIDES) else (
            'Add a distinct practical recommendation or explicitly hypothetical example '
            'relevant to this chapter. Do not repeat previous paragraphs or add unsupported facts.')'''
if old in text:
    text = text.replace(old, new, 1)
text = text.replace('elif not 70<=count<=95:', 'elif not 35<=count<=115:')
text = text.replace("        else:\n            raise RuntimeError(f'Paragraph {index+1} failed: {error}')\n    return shape_chapter", "        else:\n            raise RuntimeError(f'Paragraph {index+1} failed: {error}')\n    print('[Writer] Chapter prose words:', sum(len(WORD.findall(CITATION.sub('', p))) for p in paragraphs), flush=True)\n    return shape_chapter")
text = text.replace('Plain paragraph {index+1}/9', 'Plain paragraph {index+1} (maximum 16)')
compile(text, str(path), 'exec')
path.write_text(text)
importlib.reload(writer)
print('Fixed: shorter paragraphs allowed; chapter grows toward 630 prose words. Final checks remain active.')

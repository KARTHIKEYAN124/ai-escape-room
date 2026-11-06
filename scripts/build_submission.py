"""Run checks and build a three-page report, SVG diagrams and a clean ZIP."""
from pathlib import Path
import hashlib
import html
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.compare_versions import run_all, save_results

SUBMISSION_FILES = (
    'app.py', 'game.py', 'llm.py', 'requirements.txt', 'requirements-dev.txt',
    'README.md', '.gitignore', '.gitattributes', '.env.example',
    'scripts/compare_versions.py', 'scripts/build_submission.py',
    'tests/test_game.py', 'tests/test_errors.py', 'tests/test_ui.py',
    'tests/test_v1.py', 'tests/test_comparisons.py',
    'tests/test_packaging.py',
    'docs/architecture.md', 'docs/architecture-v1.svg', 'docs/architecture-v2.svg',
    'docs/architecture-v1.jpg', 'docs/architecture-v2.jpg',
    'docs/report.md', 'docs/report.pdf', 'docs/deliverables.md',
    'docs/test-cases.md', 'docs/comparison-results.md', 'docs/comparison-results.json',
)

def submission_report():
    """Keep attribution in the editable source; omit it from shared copies."""
    source = (ROOT / 'docs/report.md').read_text(encoding='utf-8')
    return re.sub(r'^(?:Submitted By|Supervised By):[^\n]*\n?', '', source,
                  flags=re.MULTILINE)

def submission_payloads():
    """An explicit allowlist prevents future logs, datasets or secrets entering ZIPs."""
    payloads = {name: (ROOT / name).read_bytes() for name in SUBMISSION_FILES}
    payloads['docs/report.md'] = submission_report().encode('utf-8')
    key_patterns = (r'AIza[0-9A-Za-z_-]{30,}', r'gh[pousr]_[A-Za-z0-9]{30,}',
                    r'github_pat_[A-Za-z0-9_]{30,}',
                    r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')
    for name, data in payloads.items():
        if len(data) > 5 * 1024 * 1024:
            raise RuntimeError(f'Submission file exceeds 5 MB: {name}')
        if not name.endswith(('.jpg', '.pdf')):
            text = data.decode('utf-8')
            if any(re.search(pattern, text) for pattern in key_patterns):
                raise RuntimeError(f'Possible credentials found in submission file: {name}')
    return payloads

def diagrams():
    header = '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="430" viewBox="0 0 1120 430"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#475569"/></marker></defs><rect width="1120" height="430" fill="#f8fafc"/>'
    def box(x, y, title, subtitle):
        return f'<g><rect x="{x}" y="{y}" width="155" height="70" rx="9" fill="#fff" stroke="#334155"/><text x="{x+77}" y="{y+27}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">{html.escape(title)}</text><text x="{x+77}" y="{y+49}" text-anchor="middle" font-family="Arial" font-size="11">{html.escape(subtitle)}</text></g>'
    def arrow(x1, y1, x2, y2):
        return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>'
    def title(text, subtitle):
        return f'<text x="25" y="32" font-family="Arial" font-size="22" font-weight="bold">{html.escape(text)}</text><text x="25" y="58" font-family="Arial" font-size="13">{html.escape(subtitle)}</text>'
    v1 = [header, title('Version 1: conversational Game Master', 'Gemini interprets actions, remembers narrative progress and decides completion.')]
    for x, t, sub in [(25,'Player','Natural-language action'),(205,'Streamlit chat','Input and output'),(385,'Conversation','Session history'),(565,'Gemini Game Master','Prompt + conversation'),(745,'Response','Narrative + escape marker')]:
        v1.append(box(x,110,t,sub))
        if x > 25: v1.append(arrow(x-25,145,x,145))
    v1 += [box(565,260,'Room prompt','Rules and secret codes'),arrow(642,260,642,180),
           '<path d="M822,180 L822,225 L282,225 L282,180" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>',
           '<text x="25" y="385" font-family="Arial" font-size="13">Trust boundary: generated narration and the escape marker are accepted without Python gameplay validation.</text>', '</svg>']
    v2 = [header, title('Version 2: Python validates every action', 'Private rules and structured state remain outside generated model output.')]
    for x,t,sub in [(25,'Player','One requested action'),(205,'Streamlit chat','Input and conversation'),(385,'Gemini interpreter','JSON action only'),(565,'Python engine','Validate + update state'),(745,'Gemini narrator','Select approved outcome'),(925,'Output guard','Approved text or fallback')]:
        v2.append(box(x,110,t,sub))
        if x > 25: v2.append(arrow(x-25,145,x,145))
    v2 += [box(450,260,'Private rules','Codes + prerequisites'),box(650,260,'Structured state','Inventory, puzzles, locks'),
           arrow(528,260,600,180),arrow(720,260,670,180),arrow(650,180,700,260),
           '<path d="M1002,180 L1002,225 L282,225 L282,180" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>',
           '<text x="25" y="385" font-family="Arial" font-size="13">Invalid actions leave puzzle state unchanged. API failures use a labelled offline fallback.</text>', '</svg>']
    (ROOT/'docs/architecture-v1.svg').write_text(''.join(v1), encoding='utf-8')
    (ROOT/'docs/architecture-v2.svg').write_text(''.join(v2), encoding='utf-8')
    from io import BytesIO
    from PIL import Image
    import resvg_py
    for version in (1, 2):
        source = ROOT / f'docs/architecture-v{version}.svg'
        png = resvg_py.svg_to_bytes(svg_path=str(source), width=3360, background='#ffffff')
        with Image.open(BytesIO(png)) as image:
            image.convert('RGB').save(source.with_suffix('.jpg'), 'JPEG', quality=95,
                                      subsampling=0, dpi=(300, 300))

def report_pdf():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from pypdf import PdfReader
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportBody', fontName='Helvetica', fontSize=10.5,
                              leading=14.5, spaceAfter=9, alignment=TA_LEFT))
    story = []
    source = submission_report()
    for block in source.split('\n\n'):
        block = block.strip()
        if not block: continue
        if block.startswith('## 3.') or block.startswith('## 5.'):
            story.append(PageBreak())
        if block.startswith('# '):
            story.extend([Paragraph(html.escape(block[2:]), styles['Title']), Spacer(1,12)])
        elif block.startswith('## '):
            story.append(Paragraph(html.escape(block[3:]), styles['Heading2']))
        else:
            story.append(Paragraph(html.escape(block).replace('\n',' '), styles['ReportBody']))
    def footer(canvas, doc):
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#475569'))
        canvas.drawString(42,25,'The Midnight Library | Design and implementation report')
        canvas.drawRightString(A4[0]-42,25,f'{doc.page} / 3')
    target = ROOT/'docs/report.pdf'
    SimpleDocTemplate(str(target), pagesize=A4, rightMargin=42, leftMargin=42,
                      topMargin=38, bottomMargin=42, title='AI-Powered Escape Room - Project Report',
                      author='The Midnight Library project').build(story,onFirstPage=footer,onLaterPages=footer)
    pages = len(PdfReader(target).pages)
    if pages != 3: raise RuntimeError(f'Report should contain 3 pages, found {pages}')
    print(f'PDF verified: {pages} pages')

def main():
    tests = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],
                           cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    log = tests.stdout + tests.stderr
    (ROOT/'docs/test-results.txt').write_text(log,encoding='utf-8')
    print(log[-350:])
    if tests.returncode: raise SystemExit('Tests failed; submission not packaged.')
    results = run_all()
    if not all(c.get('v2_integrity_pass') for c in results['cases']):
        raise SystemExit('Comparison integrity check failed.')
    save_results(results, ROOT/'docs', 'comparison-results')
    diagrams()
    report_pdf()
    match = re.search(r'Ran (\d+) tests',log)
    if not match: raise RuntimeError('Could not determine test count from the test runner output.')
    count = match.group(1)
    payloads = submission_payloads()
    manifest_path = ROOT/'submission-manifest.json'
    manifest = {'automated_tests_passed':int(count),'fault_injection_cases_passed':len(results['cases']),
                'report_pages':3,'live_adversarial_comparison':'not executed by the agent',
                'files':{name:hashlib.sha256(data).hexdigest() for name,data in payloads.items()}}
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive = ROOT/'AI-Escape-Room-submission.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name, data in payloads.items():
            z.writestr(name, data)
    print(f'Created {archive.name}: {len(payloads)} files, {count} tests, 7 comparison cases, 3-page report.')

if __name__ == '__main__': main()

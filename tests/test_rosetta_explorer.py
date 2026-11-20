"""Keep human mapping projections faithful to canonical records and review gaps."""
import importlib.util
import json
import re
from pathlib import Path

from safe2.framework import data

ROOT=Path(__file__).resolve().parents[1]


def load_script(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_explorer_embeds_exact_relationships_and_unreviewed_status():
    rendered=load_script('generate_rosetta_explorer').outputs()['dashboard/rosetta.html']
    payload=json.loads(re.search(r'<script id="mapping-data" type="application/json">(.*?)</script>',rendered,re.S)[1])
    assert payload['registry']==data('rosetta-v3.5.json')
    assert len(payload['controls'])==173
    assert payload['audit']['approved_relationships']==0
    assert all(r['status']!='approved' for r in payload['registry']['relationships'])
    assert '<script' not in re.search(r'<script id="mapping-data" type="application/json">(.*?)</script>',rendered,re.S)[1]


def test_every_readme_html_and_root_path_has_a_disposition():
    review=load_script('review_repository_surfaces')
    outputs,errors=review.outputs()
    assert errors==[]
    import csv,io
    records=list(csv.DictReader(io.StringIO(outputs['docs/data/repository-surface-review-v35.csv'])))
    actual={r['path'] for r in records}
    expected={n for n in review.names() if Path(n).name.lower()=='readme.md' or n.endswith('.html') or '/' not in n}
    assert actual==expected
    assert next(r for r in records if r['path']=='examples/openclaw/gateway-release-v3.0.html')['disposition']=='historical-or-frozen'
    assert next(r for r in records if r['path']=='tests/fixtures/hostile/README.md')['disposition']=='test-fixture'

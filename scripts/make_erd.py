"""현재 Django 모델에서 영역별 ERD 이미지를 만든다 → docs/erd/ERD_*.png

    python scripts/make_erd.py            # 저장소 루트에서. .env 필요 (DB 접속은 안 함)
    준비물: Graphviz(dot), 글꼴 Noto Sans CJK KR
"""
import os, sys, subprocess, html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from django.apps import apps

OUT = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / 'docs' / 'erd')
os.makedirs(OUT, exist_ok=True)
KO = {'card_approval_review': '카드 승인 확인', 'card_approval_coverage': '카드 승인 확인 범위',
      'budget_adjustment_schedule': '예산 조정 예약'}
GROUPS = [
 ('1_회원_내정보_동의', '회원 · 내 정보 · 동의', '#2459D9',
  ['app_user','financial_profile','category_priority','category_minimum','consent','idempotency_record','privacy_deletion']),
 ('2_기관연결_계좌_카드_대출', '기관 연결 · 계좌 · 카드 · 대출', '#0E8A6A',
  ['connection','bank_account','card','loan','sync_run','card_approval_review','card_approval_coverage']),
 ('3_거래_분류', '거래 · 분류', '#C2410C', ['financial_transaction','transaction_link','category']),
 ('4_카드청구_고정지출_납부', '카드 청구 · 고정지출 · 정기 저축 · 납부', '#7C3AED',
  ['card_bill','card_bill_item','recurring_expense','recurring_saving','payment_due','payment_match']),
 ('5_예산_쿠션_급여', '예산 · 쿠션 · 급여', '#5B7A0A',
  ['budget_cycle','budget_category_setting','reserve_plan','budget','budget_item','budget_adjustment_schedule','spending_allocation','cushion_entry','salary_decision']),
 ('6_챗봇_비동기작업', '챗봇 · 비동기 작업', '#0369A1', ['conversation','chat_message','async_task']),
 ('7_청년정책', '청년 정책', '#B4235A', ['policy','policy_sync','saved_policy']),
]
models = {}
for app in ['users','finance','budgets','chat','policies']:
    for m in apps.get_app_config(app).get_models():
        models[m._meta.db_table] = m
group_of = {t: g for g in GROUPS for t in g[3]}
assert set(group_of) == set(models), set(models) ^ set(group_of)
FONT = 'Noto Sans CJK KR'

def ko(t): return KO.get(t) or str(models[t]._meta.verbose_name)
def ftype(f):
    t = f.get_internal_type().replace('Field', '')
    if f.is_relation: return 'uuid' if f.target_field.get_internal_type()=='UUIDField' else f.target_field.get_internal_type().replace('Field','').lower()
    m = {'UUID':'uuid','Char':'varchar','Text':'text','Integer':'int','PositiveInteger':'int','PositiveSmallInteger':'smallint','SmallInteger':'smallint','BigInteger':'bigint',
         'Boolean':'bool','Date':'date','DateTime':'timestamptz','JSON':'jsonb','Decimal':'numeric','Float':'float','Email':'varchar','BinaryField':'bytea','Binary':'bytea','Time':'time','Duration':'interval'}
    s = m.get(t, t.lower())
    if t == 'Char' and f.max_length: s += f'({f.max_length})'
    return s

def table_node(t, color, full=True, ext=False):
    m = models[t]
    head_bg = '#9CA3AF' if ext else color
    rows = [f'<TR><TD BGCOLOR="{head_bg}" COLSPAN="3" ALIGN="LEFT"><FONT COLOR="white"><B>{html.escape(t)}</B>  {html.escape(ko(t))}</FONT></TD></TR>']
    if full:
        for f in m._meta.concrete_fields:
            key = 'PK' if f.primary_key else ('FK' if f.is_relation else '')
            name = f.column
            null = '' if f.null else ' ●'
            keycell = f'<FONT POINT-SIZE="10" COLOR="{"#B45309" if key=="PK" else "#6B7280"}"><B>{key}</B></FONT>' if key else ' '
            rows.append(f'<TR><TD ALIGN="LEFT">{keycell}</TD>'
                        f'<TD ALIGN="LEFT">{html.escape(name)}</TD>'
                        f'<TD ALIGN="LEFT" PORT="{html.escape(name)}"><FONT COLOR="#6B7280">{html.escape(ftype(f))}{null}</FONT></TD></TR>')
    border = '#9CA3AF' if ext else color
    return f'"{t}" [label=<<TABLE BORDER="1" COLOR="{border}" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">{"".join(rows)}</TABLE>>];'

def fks(t):
    for f in models[t]._meta.concrete_fields:
        if f.is_relation:
            yield f.column, f.related_model._meta.db_table, f.remote_field.on_delete.__name__, f.null

def render(dot, name):
    path = os.path.join(OUT, f'ERD_{name}.png')
    subprocess.run(['dot', '-Tpng', '-Gdpi=110', '-o', path], input=dot.encode(), check=True)
    return path

STYLE = {'CASCADE': 'solid', 'RESTRICT': 'bold', 'PROTECT': 'bold', 'SET_NULL': 'dashed'}
for key, title, color, tables in GROUPS:
    lines = [f'digraph G {{ rankdir=LR; graph [fontname="{FONT}", fontsize=20, labelloc=t, label=<<B>{html.escape(title)}</B><BR/><FONT POINT-SIZE="11">● NOT NULL · 실선 CASCADE · 굵은선 RESTRICT/PROTECT · 점선 SET_NULL · 회색 상자 = 다른 영역 테이블 · 회원(app_user) FK 선은 1번 그림에만</FONT>>, pad=0.4, nodesep=0.6, ranksep=1.4, bgcolor="white"];',
             f'node [shape=plain, fontname="{FONT}", fontsize=11]; edge [fontname="{FONT}", fontsize=9, color="#6B7280", arrowsize=0.7];']
    ext = set()
    edges = []
    for t in tables:
        for col, ref, od, null in fks(t):
            if ref == 'app_user' and t != 'app_user' and key != '1_회원_내정보_동의': continue
            if ref in ('auth_group','auth_permission'): continue
            if ref not in tables: ext.add(ref)
            edges.append((t, col, ref, od))
    for t in tables: lines.append(table_node(t, color))
    for t in sorted(ext): lines.append(table_node(t, color, full=False, ext=True))
    for t, col, ref, od in edges:
        tgt = f'"{ref}"'
        lines.append(f'"{t}":"{col}":e -> {tgt} [style={STYLE.get(od,"solid")}];')
    lines.append('}')
    render('\n'.join(lines), key)

# overview
lines = [f'digraph G {{ rankdir=LR; graph [fontname="{FONT}", fontsize=22, labelloc=t, label=<<B>머니쿠션 전체 ERD (38개 테이블)</B><BR/><FONT POINT-SIZE="12">회원(app_user) 연결선은 생략 · 실선 CASCADE · 굵은선 RESTRICT/PROTECT · 점선 SET_NULL</FONT>>, pad=0.4, nodesep=0.25, ranksep=0.9, compound=true];',
         f'node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=11, color=white]; edge [color="#9CA3AF", arrowsize=0.6];']
for key, title, color, tables in GROUPS:
    lines.append(f'subgraph "cluster_{key}" {{ label=<<B>{html.escape(title)}</B>>; fontsize=14; color="{color}"; style="rounded"; fontcolor="{color}";')
    for t in tables:
        lines.append(f'"{t}" [label=<<B>{t}</B><BR/><FONT POINT-SIZE="9">{html.escape(ko(t))}</FONT>>, fillcolor="{color}", fontcolor=white];')
    lines.append('}')
for t in models:
    for col, ref, od, null in fks(t):
        if ref in ('app_user','auth_group','auth_permission'): continue
        lines.append(f'"{t}" -> "{ref}" [style={STYLE.get(od,"solid")}];')
lines.append('}')
render('\n'.join(lines), '0_전체')
print('ERD 저장:', OUT)

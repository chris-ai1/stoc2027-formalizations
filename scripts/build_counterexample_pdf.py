# Copyright (c) 2026 Christian Reitwiessner. Apache-2.0.
# Authors: Christian Reitwiessner.
"""Build the self-contained submission 1234 counterexample note (requires reportlab)."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'stoc/writeups/submission-1234-counterexample.pdf'
PAPER = 'https://github.com/sigact-stoc/stoc2027/releases/download/papers-2/1234.pdf'
SHA = '4d578733628a41dfc7f550f80725960b87de3c4a'
LEAN = f'https://github.com/cslib-community/complexitylib/blob/{SHA}/Complexity/Crypto/Multiparty/TetrahedralYield.lean#L106'
styles = getSampleStyleSheet()
styles['BodyText'].fontSize = 9.5
styles['BodyText'].leading = 12
styles.add(ParagraphStyle(name='Formula', parent=styles['BodyText'], alignment=TA_CENTER, spaceBefore=9, spaceAfter=9))
story = []
def p(text, style='BodyText'):
    story.append(Paragraph(text, styles[style])); story.append(Spacer(1, 3))
def table(rows, widths):
    t=Table(rows,colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eef4')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#bcc7d1')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('ALIGN',(0,0),(-1,-1),'CENTER'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    story.append(t);story.append(Spacer(1,12))
p('A public-message privacy counterexample', 'Title')
p('STOC submission 1234: the reverse Tetrahedral protocol', 'Heading2')
p('Christian Reitwiessner · 6 November 2026<br/>AI-assisted technical note · Apache-2.0')
p('<b>Claim examined.</b> Donald Beaver, <i>Correlated Group Interactions: Founding Cryptography on S4 and Sn</i>, Theorem 5.1, PDF page 5, Figures 9 and 10. The theorem claims a semi-honest secure reverse construction of a (2,1;1) card deal from oblivious transfer. The counterexample below concerns Bob learning additional information about Alice’s hand through the public message.')
p('1. The experiment and the privacy requirement', 'Heading2')
p('Alice selects an ordered pair A=(a,b) of distinct cards from {0,1,2,3}, uniformly among the 12 possibilities. She announces M using the paper’s Alice table. The OT receiver selection s is an independent uniform bit. Figure 9 specifies Bob’s card C for each pair and selection. For every A, its two cases give the two cards outside A, once each. Consequently (a,b,C,D), with D the remaining card, is uniform over the 24 permutations.')
p('In an ideal deal, Bob receives only C. His real view includes C and the public M (as well as other protocol information). A necessary privacy condition is that the joint law of Alice’s hand and Bob’s view can be simulated from C alone. In particular, M must not reveal additional information about A after C is known:')
p('Pr[A=a | C=c, M=m] = Pr[A=a | C=c]', 'Formula')
p('for conditioning events of positive probability. Failure already for the public part (C,M) suffices; inspecting Bob’s other view components is unnecessary.')
p('2. Six equally likely cases', 'Heading2')
p('Condition on C=0. Figure 9 leaves exactly the following six cases, each with conditional probability 1/6. The discarded card D is determined by the other three cards.')
table([['Alice A','Bob C','Discard D','Public M'],['(1,2)','0','3','Y'],['(1,3)','0','2','X'],['(2,1)','0','3','X'],['(2,3)','0','1','Z'],['(3,1)','0','2','Z'],['(3,2)','0','1','Y']], [110,95,110,110])
story.append(PageBreak())
p('3. Exact leakage calculation', 'Heading2')
p('Before seeing M, Bob assigns probability 1/6 to each ordered pair in the table. If he then sees M=X, only A=(1,3) and A=(2,1) remain, each with probability 1/2. Therefore:')
p('Pr[A=(1,3) | C=0] = 1/6,<br/>Pr[A=(1,3) | C=0, M=X] = 1/2.', 'Formula')
p('The failure persists even when order within Alice’s hand is ignored:')
table([['Unordered Alice hand','Given C=0','Given C=0, M=X'],['{1,2}','1/3','1/2'],['{1,3}','1/3','1/2'],['{2,3}','1/3','0']], [150,130,150])
p('Thus Bob can rule out the previously possible hand {2,3}. This information is unavailable from his ideal dealt card alone. No simulator given only C can reproduce the real joint correlations with Alice’s hand.')
p('4. What the Lean theorem checks', 'Heading2')
p('The declaration <font face="Courier">Cslib.Crypto.Tetrahedral.reverse_message_leakage</font> checks the equivalent division-free conditional-independence identity. Let E be A=(1,3), F be C=0, and G be M=X. Among all 24 shuffles:')
p('|E intersect F intersect G| = 1,  |F| = 6,<br/>|E intersect F| = 1,  |F intersect G| = 2.', 'Formula')
p('Conditional independence would require the product of the first two counts to equal the product of the last two. Instead, 1 times 6 differs from 1 times 2. The Lean proof uses <font face="Courier">by decide</font> to check these exact finite counts. Separate checked declarations establish that the enumerator contains exactly the 24 distinct permutations. The message encoding is X=0, Y=1, Z=2.')
p('5. The faulty inference and scope', 'Heading2')
p('The proof of Theorem 5.1 argues from the fact that M is determined by Alice’s hand to privacy. Determinism given Alice’s hand does not imply independence from that hand given Bob’s card. Checking a joint probability only for a message consistent with a fixed hand does not establish the conditional-independence condition above; incompatible hands are exactly what the observed message excludes.')
p('This counterexample contradicts the stated reverse protocol’s perfect semi-honest privacy. It does not refute the distribution of its dealt outputs, the forward protocol’s checked correctness/privacy, or the possibility of a different secure reverse construction. It is not a claim that the entire paper is false.')
p('Sources and reproducibility', 'Heading2')
p(f'<a href="{PAPER}" color="#165a9e">Primary manuscript: PDF page 5, Figures 9–10 and Theorem 5.1</a>.<br/><a href="{LEAN}" color="#165a9e">Immutable Lean proof: TetrahedralYield.lean, lines 106–116</a>.<br/>Source revision: <font face="Courier" size="8">{SHA}</font>.<br/>Protocol tables: Tetrahedral.lean, Figures 2–3; reverse enumeration: manuscript Figure 9. The linked proof is included in Complexitylib PR 2529. Formal kernel checking establishes the counting inequality; correspondence to the manuscript additionally uses the explicit table mapping above.')
def footer(canvas,doc):
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526171'))
    canvas.drawString(45,25,'Christian Reitwiessner | STOC submission 1234 | Reverse-protocol privacy')
    canvas.drawRightString(A4[0]-45,25,str(doc.page))
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=36,bottomMargin=40,title='A public-message privacy counterexample — STOC submission 1234',author='Christian Reitwiessner').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUTPUT)

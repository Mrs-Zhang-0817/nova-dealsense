import os
from pathlib import Path
from io import BytesIO
from xml.sax.saxutils import escape
from functools import lru_cache
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak

@lru_cache
def font():
    path=Path(os.getenv("REPORT_CJK_FONT","C:/Windows/Fonts/simsun.ttc"))
    pdfmetrics.registerFont(TTFont("ReportChinese",str(path),subfontIndex=0))
    return "ReportChinese"

def render(s):
    output=BytesIO()
    doc=SimpleDocTemplate(output,pagesize=A4,leftMargin=48,rightMargin=48,topMargin=58,bottomMargin=52,title=s["title"])
    family=font()
    def para(value,size=10,color="#182D40"):
        style=ParagraphStyle("text",fontName=family,fontSize=size,leading=size*1.5,textColor=colors.HexColor(color),wordWrap="CJK")
        return Paragraph(escape(str(value)).replace("\n","<br/>"),style)
    story=[Spacer(1,100),para("NOVA DealSense",32),Spacer(1,15),para("跨境交易决策分析报告",26),Spacer(1,32),
           para(s["source"]["deal"]["name"],17),Spacer(1,18),para(s["report_number"]),para(s["generated_at"])]
    if s["demo_inputs"]:story.append(para("演示数据 · 人工输入条件",12,"#97601D"))
    story.extend([Spacer(1,28),para("预计贡献利润   "+s["currency"]+" "+s["selected"]["financials"]["contribution_profit"].rstrip("0").rstrip("."),16),
                  para("预计贡献率   "+s["selected"]["financials"]["contribution_margin_percent"]+"%",16)])
    for i,section in enumerate(s["sections"]):
        if i in (0,2,4,6):story.append(PageBreak())
        story.extend([para(section["title"],17,"#145A63"),Spacer(1,8)])
        data=[[para(k),para(v)] for k,v in section["rows"]]
        table=Table(data,colWidths=[135,doc.width-135],splitByRow=1,splitInRow=1)
        table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E9F2F1")),("LINEBELOW",(0,0),(-1,-1),0.4,colors.HexColor("#CBD8DF")),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
        story.extend([table,Spacer(1,22)])
    def footer(c,d):
        c.setFont(family,9);c.setFillColor(colors.HexColor("#405968"))
        c.drawString(48,30,s["report_number"]);c.drawRightString(A4[0]-48,30,f"第 {d.page} 页")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import random

# 한글 폰트 등록 (시스템에 설치된 폰트나 나눔고딕 등 필요, 여기서는 기본 폰트로 대체될 수 있음)
# 실제 환경에서는 한글 폰트 파일(.ttf)이 필요합니다. 
# 데모를 위해 영문으로 작성하거나, 시스템 폰트를 찾아야 합니다.
# 여기서는 편의상 영문/숫자 위주로 생성하되, 한글이 깨지지 않도록 해야 함.
# 만약 한글 폰트가 없다면 표준 폰트를 사용해야 함.

def generate_feature_pdf(filename="featurelist.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # 타이틀
    story.append(Paragraph("Marketing Feature Dictionary", styles['Title']))
    story.append(Spacer(1, 20))

    categories = {
        "Digital Engagement": [
            "App Launch Frequency", "Session Duration", "Late Night Access", "Scroll Depth", 
            "Search Keywords", "Cart Abandonment", "Login Attempts", "MyPage View", 
            "Banner Click", "Widget Usage"
        ],
        "Usage & Network": [
            "Voice Call Out", "Voice Call In", "Night/Weekend Call", "Data Usage Total", 
            "5G Ratio", "WiFi vs Cellular", "Tethering Usage", "Roaming History"
        ],
        "Content & Media": [
            "TV Watch Time", "VOD Purchase", "Genre Preference", "Binge Watching", 
            "Content Search", "Kids Content", "Adult Content", "Playback Speed"
        ],
        "Commerce & Finance": [
            "ARPU", "High Plan Retention", "Payment Risks", "Micropayment Amount", 
            "Membership Usage", "Affiliate Card", "Auto Pay Method", "Family Combination"
        ],
        "Location & Mobility": [
            "Home Base Time", "Work Base Time", "Daily Moving Dist", "Transport Mode", 
            "POI Visit (Cafe/Mart)", "Travel Spot Visit", "Overseas Roaming"
        ],
        "Device & Tech": [
            "Device Model", "Device Age", "Price Tier", "OS Version", 
            "Battery Pattern", "Wearable Connection", "Change Cycle", "eSIM Usage"
        ],
        "Service & Relation": [
            "VOC Cal Count", "Complaint Type", "Chatbot Usage", "Satisfaction Score", 
            "Long-term Benefit", "SNS Follow", "Churn Defense History"
        ],
        "Marketing Reaction": [
            "Push Click Rate", "SMS Link Click", "Response Latency", "Fatigue Level", "Opt-out History"
        ]
    }

    data = [['Feature Info']] # 단일 컬럼으로 생성하여 파싱 용이성 증대
    
    # 1500개 피처 생성
    count = 0
    while count < 1500:
        cat = random.choice(list(categories.keys()))
        feat_base = random.choice(categories[cat])
        count += 1
        
        # 가독성 높은 피처 이름 생성 (베이스 이름 + 순번)
        feat_name = f"{feat_base} #{count:03d}"
        
        # 설명 생성
        desc = f"{cat} 카테고리의 {feat_base} 분석 지표"
        
        # 0~100 사이 랜덤 값
        value = str(random.randint(0, 100))
        
        # 구조화된 텍스트 행 생성 (| 구분자 사용)
        row_text = f"ID: {feat_name} | CAT: {cat} | DESC: {desc} | VAL: {value}"
        data.append([row_text])

    # 테이블 스타일
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(t)
    doc.build(story)
    print(f"Generated {filename} with {count} features.")

if __name__ == "__main__":
    generate_feature_pdf()

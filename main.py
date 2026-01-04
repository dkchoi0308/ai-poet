import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import streamlit as st
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from pdf_utils import PDFFeatureLoader

# 환경 변수 설정
load_dotenv()

# --- Data Models (from models.py) ---
class DailyQuantity(BaseModel):
    """일자별 발송 수량을 정의하는 모델"""
    day_number: int = Field(description="캠페인 진행 일차 (1~5)")
    quantity: int = Field(description="해당 일차의 발송 수량")

class MarketingPlan(BaseModel):
    """전체 타겟마케팅 기획서 정보를 담는 모델"""
    product_name: str = Field(description="마케팅 대상 상품명")
    start_date: str = Field(description="캠페인 시작일 (YYYY-MM-DD)")
    total_quantity: int = Field(description="총 MMS 발송 수량")
    daily_quantities: List[DailyQuantity] = Field(description="일자별 발송 수량 리스트")
    target_gender: str = Field(default="전체", description="타겟 성별")
    target_age_min: int = Field(default=0, description="최소 연령")
    target_age_max: int = Field(default=100, description="최대 연령")
    campaign_keywords: str = Field(default="", description="캠페인 주요 키워드")

class SelectedFeature(BaseModel):
    """선정된 피처와 그 이유 정보"""
    name: str
    reason: str
    similarity_score: float

# --- Feature Engine (PDF based) ---
class FeatureEngine:
    """피처 추출 및 관리를 담당하는 엔진 클래스 (PDF 기반)"""

    def __init__(self):
        self.pdf_loader = PDFFeatureLoader()

    def select_features_semantically(self, plan: MarketingPlan) -> List[SelectedFeature]:
        """시맨틱 검색 및 유사도 기반 피처 선정"""
        keywords = plan.campaign_keywords.split(",") + [plan.product_name]
        search_query = " ".join(keywords)
        
        # PDF에서 유사 피처 검색
        search_results = self.pdf_loader.search_similar_features(search_query, k=10)
        
        results = []
        for res in search_results:
            # Metadata에서 파싱된 정보 가져오기 (pdf_utils.py에서 설정됨)
            meta = res.get('metadata', {})
            cat = meta.get('category', '')
            base_name = meta.get('feature_name', 'Unknown_Feature')
            
            # 사용자 가독성을 위해 [카테고리] 피처명 형식으로 노출
            feat_name = f"[{cat}] {base_name}"
            feat_desc = meta.get('description', res['raw_text'])
            feat_val = meta.get('value', '0')
            
            # 선정 사유 생성
            reason = f"입력된 키워드와 '{feat_desc}'(값: {feat_val}) 간의 연관성이 높음"
            
            results.append(SelectedFeature(
                name=feat_name,
                reason=reason,
                similarity_score=res['similarity_score'] 
            ))
            
        return results

# --- Targeting Engine Removed ---

# --- Main App ---
def main():
    st.set_page_config(page_title="타겟마케팅 AI 에이전트", layout="wide")
    st.title("🎯 AI 기반 타겟마케팅 세그먼트 생성 에이전트")
    st.markdown("상품 및 캠페인 키워드 정보를 바탕으로 최적의 분석 피처를 추출합니다.")

    # 세션 상태 초기화
    if 'selected_features' not in st.session_state:
        st.session_state.selected_features = None
    if 'targeting_plan' not in st.session_state:
        st.session_state.targeting_plan = None

    # --- 엔진 인스턴스 생성 ---
    feature_engine = FeatureEngine()

    # 입력 영역
    with st.expander("📝 캠페인 기획 정보 입력", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            product_name = st.text_input("상품명", value="프리미엄 무선 헤드셋")
        with col2:
            total_quantity = st.number_input("총 발송 수량", min_value=1, max_value=5000, value=120)
        with col3:
            duration_days = st.slider("캠페인 기간 (일)", 1, 5, 5)

        st.markdown("### 👥 타겟 데모그래픽 및 키워드")
        d_col1, d_col2, d_col3 = st.columns([1, 1, 2])
        with d_col1:
            target_gender = st.radio("타겟 성별", ["전체", "남성", "여성"], index=0, horizontal=True)
        with d_col2:
            age_range = st.slider("타겟 연령대", 0, 80, (20, 50))
        with d_col3:
            campaign_keywords = st.text_input("캠페인 주요 키워드 (쉼표 구분)", value="음향기기, 고음질, 무선, 청각")

    st.divider()

    # 단계 1: 피처 선정
    # 1. 사용자가 버튼을 눌렀을 때
    if st.button("유사 Feature 추출", type="primary", use_container_width=True):
        # 즉시 리스트를 비우고 '검색 대기' 상태로 전환 후 리런
        st.session_state.selected_features = None
        st.session_state.is_searching = True
        st.rerun()

    # 2. 리런 후 '검색 대기' 상태라면 실제 작업을 수행
    if st.session_state.get('is_searching'):
        st.session_state.is_searching = False # 상태 해제
        
        # 기획안 정보 구성
        base_qty = total_quantity // duration_days
        remainder = total_quantity % duration_days
        daily_quantities = [DailyQuantity(day_number=i, quantity=base_qty + (1 if i <= remainder else 0)) for i in range(1, duration_days + 1)]
        
        plan = MarketingPlan(
            product_name=product_name, total_quantity=total_quantity,
            daily_quantities=daily_quantities, target_gender=target_gender,
            target_age_min=age_range[0], target_age_max=age_range[1],
            campaign_keywords=campaign_keywords, start_date=datetime.now().strftime("%Y-%m-%d")
        )
        st.session_state.targeting_plan = plan
        
        with st.spinner("유사 피처를 검색 중입니다..."):
            # 실제 로딩 트리거
            st.session_state.selected_features = feature_engine.select_features_semantically(plan)
            
        st.success("추출 완료!")
        st.rerun()

    # 선정된 피처 표시
    if st.session_state.selected_features:
        st.subheader("📋 PDF 기반 추출 피처 리스트 (Top 10)")
        st.caption(f"PDF 내 총 1500+개 피처 중 '{product_name}' 및 키워드와 가장 연관성 높은 항목을 추출했습니다.")
        feature_data = [{"피처명": f.name, "유사도": f"{f.similarity_score:.4f}", "선정 사유": f.reason} for f in st.session_state.selected_features]
        st.table(feature_data)

if __name__ == "__main__":
    main()

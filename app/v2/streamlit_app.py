"""
ISO 20022 Migration Platform - Streamlit UI
Interactive frontend for MT to MX transformation
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="ISO 20022 GenAI Migration",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #7c3aed 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .agent-card {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .agent-idle { background-color: #f3f4f6; }
    .agent-processing { background-color: #fef3c7; }
    .agent-complete { background-color: #d1fae5; }
    .agent-error { background-color: #fee2e2; }
    .stat-card {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #1e40af;
    }
    .stat-label {
        font-size: 12px;
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Sample MT103 messages
SAMPLE_MESSAGES = {
    "Standard USD Transfer": """:20:TRX2024112001
:23B:CRED
:32A:241118USD50000,00
:50K:/123456789
ACME CORPORATION
123 BUSINESS STREET
NEW YORK, NY 10001
:52A:CHASUS33XXX
:59:/987654321
GLOBAL TRADING LTD
456 COMMERCE AVENUE
LONDON, EC2R 8AH
:70:INVOICE INV-2024-1234
PAYMENT FOR SERVICES
:71A:SHA
:72:/REC/URGENT""",
    
    "High Value EUR Transfer": """:20:TRX2024112002
:23B:CRED
:32A:241118EUR2500000,00
:50K:/DE89370400440532013000
DEUTSCHE MANUFACTURING GMBH
INDUSTRIESTRASSE 45
60329 FRANKFURT
:52A:DEUTDEFFXXX
:59:/GB82WEST12345698765432
BRITISH IMPORTS PLC
789 TRADE LANE
MANCHESTER, M1 2AB
:70:CONTRACT CON-2024-5678
Q4 MACHINERY ORDER
:71A:OUR
:72:/ACC/PRIORITY""",
    
    "Cross-Border GBP Payment": """:20:TRX2024112003
:23B:CRED
:32A:241118GBP175000,00
:50K:/GB29NWBK60161331926819
LONDON TECH VENTURES
10 INNOVATION SQUARE
LONDON, SW1A 1AA
:52A:HSBCGB2LXXX
:59:/US12345678901234567890
SILICON VALLEY INNOVATIONS INC
1 STARTUP BLVD
SAN FRANCISCO, CA 94105
:70:SERIES B INVESTMENT
TRANCHE 2 OF 3
:71A:BEN
:72:/INS/INVESTMENT"""
}

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def transform_message(mt_message: str, approach: str):
    """Call the transformation API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/transform",
            json={
                "mt_message": mt_message,
                "approach": approach
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API. Make sure the backend is running on port 8000."}
    except Exception as e:
        return {"error": str(e)}

def display_agent_status(name: str, result: dict):
    """Display agent status card"""
    status = result.get('status', 'idle')
    status_colors = {
        'idle': '⚪',
        'processing': '🟡',
        'complete': '🟢',
        'warning': '🟠',
        'error': '🔴'
    }
    
    icon = status_colors.get(status, '⚪')
    confidence = result.get('confidence')
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{icon} {name}**")
        st.caption(result.get('message', 'Waiting...'))
    with col2:
        if confidence:
            st.metric("Confidence", f"{confidence*100:.0f}%")
        if result.get('duration_ms'):
            st.caption(f"{result['duration_ms']}ms")

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔄 ISO 20022 GenAI Migration Platform</h1>
        <p>Real-time MT to MX Transformation with Agentic AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Status
        api_status = check_api_health()
        if api_status:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Disconnected")
            st.info("Run: `uvicorn main:app --reload`")
        
        st.divider()
        
        # Approach selection
        approach = st.selectbox(
            "🎯 Transformation Approach",
            ["hybrid", "rules", "llm"],
            format_func=lambda x: {
                "hybrid": "⚡ Hybrid (Recommended)",
                "rules": "🔧 Rule-Based Only",
                "llm": "🧠 LLM-Based Only"
            }[x]
        )
        
        # Approach info
        approach_info = {
            "hybrid": "Rules for known fields, LLM for edge cases. Best balance of speed and accuracy.",
            "rules": "Deterministic mapping with 98%+ confidence. Fast but less flexible.",
            "llm": "GPT-4o semantic inference. Handles unknowns but higher latency."
        }
        st.info(approach_info[approach])
        
        st.divider()
        
        # Sample message selection
        st.subheader("📋 Sample Messages")
        selected_sample = st.selectbox(
            "Choose a sample",
            list(SAMPLE_MESSAGES.keys())
        )
        
        if st.button("📥 Load Sample", use_container_width=True):
            st.session_state['mt_input'] = SAMPLE_MESSAGES[selected_sample]
            st.rerun()
    
    # Main content
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📥 Input: MT103 (SWIFT)")
        
        # MT Message input
        mt_input = st.text_area(
            "Enter MT message",
            value=st.session_state.get('mt_input', SAMPLE_MESSAGES["Standard USD Transfer"]),
            height=400,
            key="mt_message_input",
            label_visibility="collapsed"
        )
        
        # Transform button
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            transform_clicked = st.button(
                "▶️ Transform",
                type="primary",
                use_container_width=True,
                disabled=not api_status
            )
        with col_btn2:
            if st.button("🔄 Clear", use_container_width=True):
                st.session_state['result'] = None
                st.rerun()
    
    with col_right:
        st.subheader("📤 Output: pacs.008 (ISO 20022)")
        
        # Output display
        if 'result' in st.session_state and st.session_state['result']:
            result = st.session_state['result']
            
            if 'error' in result:
                st.error(result['error'])
            else:
                # Tabs for different views
                tab_json, tab_xml = st.tabs(["📊 JSON Structure", "📄 XML"])
                
                with tab_json:
                    st.json(result.get('mx_structure', {}))
                
                with tab_xml:
                    st.code(result.get('mx_xml', ''), language='xml')
        else:
            st.info("👆 Click 'Transform' to see the MX output")
    
    # Process transformation
    if transform_clicked and mt_input:
        with st.spinner("🔄 Processing transformation..."):
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🤖 Initializing agents...")
            progress_bar.progress(10)
            time.sleep(0.3)
            
            status_text.text("📝 Parsing MT message...")
            progress_bar.progress(25)
            
            # Call API
            result = transform_message(mt_input, approach)
            
            if 'error' not in result:
                status_text.text("🧠 Mapping fields...")
                progress_bar.progress(50)
                time.sleep(0.2)
                
                status_text.text("✨ Enriching data...")
                progress_bar.progress(75)
                time.sleep(0.2)
                
                status_text.text("✅ Validation complete!")
                progress_bar.progress(100)
            
            st.session_state['result'] = result
            time.sleep(0.5)
            st.rerun()
    
    # Agent Pipeline Status
    if 'result' in st.session_state and st.session_state['result'] and 'error' not in st.session_state['result']:
        result = st.session_state['result']
        
        st.divider()
        st.subheader("🤖 AI Agent Pipeline")
        
        agent_cols = st.columns(4)
        agents = ['parser', 'mapping', 'enrichment', 'validation']
        agent_names = ['MT Parser', 'Mapping Agent', 'Enrichment Agent', 'Validation Agent']
        
        for i, (agent_key, agent_name) in enumerate(zip(agents, agent_names)):
            with agent_cols[i]:
                agent_result = result.get('agent_results', {}).get(agent_key, {})
                if isinstance(agent_result, dict):
                    display_agent_status(agent_name, agent_result)
                else:
                    # Handle Pydantic model
                    display_agent_status(agent_name, {
                        'status': agent_result.status if hasattr(agent_result, 'status') else 'complete',
                        'message': agent_result.message if hasattr(agent_result, 'message') else '',
                        'confidence': agent_result.confidence if hasattr(agent_result, 'confidence') else None,
                        'duration_ms': agent_result.duration_ms if hasattr(agent_result, 'duration_ms') else 0
                    })
        
        # Statistics
        st.divider()
        st.subheader("📊 Transformation Statistics")
        
        stats = result.get('statistics', {})
        stat_cols = st.columns(6)
        
        stat_items = [
            ("Fields Parsed", stats.get('fields_parsed', 0), "📝"),
            ("Fields Mapped", stats.get('fields_mapped', 0), "🔗"),
            ("Fields Enriched", stats.get('fields_enriched', 0), "✨"),
            ("Confidence", f"{stats.get('overall_confidence', 0)*100:.0f}%", "🎯"),
            ("Validation", f"{stats.get('validation_score', 0)}%", "✅"),
            ("Duration", f"{stats.get('total_duration_ms', 0)}ms", "⏱️")
        ]
        
        for i, (label, value, icon) in enumerate(stat_items):
            with stat_cols[i]:
                st.markdown(f"""
                <div class="stat-card">
                    <div style="font-size: 20px;">{icon}</div>
                    <div class="stat-value">{value}</div>
                    <div class="stat-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Download buttons
        st.divider()
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            st.download_button(
                "📥 Download JSON",
                json.dumps(result.get('mx_structure', {}), indent=2),
                file_name=f"mx_output_{result.get('message_id', 'unknown')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col_dl2:
            st.download_button(
                "📥 Download XML",
                result.get('mx_xml', ''),
                file_name=f"mx_output_{result.get('message_id', 'unknown')}.xml",
                mime="application/xml",
                use_container_width=True
            )
        
        with col_dl3:
            st.download_button(
                "📥 Full Report",
                json.dumps(result, indent=2, default=str),
                file_name=f"transformation_report_{result.get('message_id', 'unknown')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Approach comparison
    with st.expander("📚 Approach Comparison", expanded=False):
        comp_cols = st.columns(3)
        
        with comp_cols[0]:
            st.markdown("### 🔧 Rule-Based")
            st.markdown("""
            - Deterministic mapping
            - High performance (~50ms)
            - 98%+ confidence
            - Limited flexibility
            - Best for standard messages
            """)
        
        with comp_cols[1]:
            st.markdown("### 🧠 LLM-Based")
            st.markdown("""
            - Semantic understanding
            - Handles edge cases
            - 90-95% confidence
            - Higher latency (~300ms)
            - Best for complex/unknown fields
            """)
        
        with comp_cols[2]:
            st.markdown("### ⚡ Hybrid (Recommended)")
            st.markdown("""
            - Rules for known fields
            - LLM fallback for unknowns
            - 95-98% confidence
            - Balanced latency (~150ms)
            - Best overall performance
            """)

if __name__ == "__main__":
    main()

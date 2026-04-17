import sys
import os
import time
# Thêm đường dẫn gốc để import được src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from src.utils.db_connection import DBManager

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="F1 Racing Analytics - Quốc Lâm", layout="wide", page_icon="🏎️")

@st.cache_resource
def get_engine():
    return DBManager().get_engine()

engine = get_engine()

# --- 2. HÀM LẤY DỮ LIỆU ---
@st.cache_data(ttl=3600)
def get_telemetry_data(year, event):
    query = f"""
        SELECT driver, session_time, location_x, location_y, speed, rpm, gear, throttle, brake 
        FROM f1_raw_telemetry 
        WHERE year = {year} AND event_name = '{event}'
        ORDER BY session_time
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Xử lý Brake: Chuyển Boolean/Object về số 100/0
        # if df['brake'].dtype == 'bool' or df['brake'].dtype == 'object':
        #     df['brake'] = df['brake'].apply(lambda x: 100 if x is True or str(x).lower() == 'true' else 0)
        
        df['session_time'] = pd.to_timedelta(df['session_time'])
        df['rel_time'] = (df['session_time'].dt.total_seconds() - df['session_time'].dt.total_seconds().min()).round(2)
        
        for col in ['speed', 'rpm', 'throttle', 'brake', 'gear']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 3. BỘ LỌC SIDEBAR (ĐIỀU HƯỚNG) ---
st.sidebar.header("🛠️ Điều hướng Dashboard")
try:
    years_df = pd.read_sql("SELECT DISTINCT year FROM f1_raw_telemetry ORDER BY year DESC", engine)
    sel_year = st.sidebar.selectbox("Chọn Năm", years_df['year'].tolist())
    
    events_df = pd.read_sql(f"SELECT DISTINCT event_name FROM f1_raw_telemetry WHERE year = {sel_year} ORDER BY event_name", engine)
    sel_event = st.sidebar.selectbox("Chọn Cuộc đua", events_df['event_name'])
    
    # Load toàn bộ dữ liệu chặng để làm Report
    df_all = get_telemetry_data(sel_year, sel_event)
    drivers_list = sorted(df_all['driver'].unique().tolist())
    st.sidebar.success(f"✅ Tìm thấy {len(drivers_list)} tay đua")
except Exception as e:
    st.sidebar.error(f"Lỗi kết nối: {e}")
    st.stop()

# --- 4. GIAO DIỆN CHÍNH ---
st.title(f"🏁 {sel_event} - {sel_year}")

# TỔ CHỨC 3 TABS: REPORT -> SIMULATOR -> CHARTS (Từ tổng quan đến chi tiết)
tab_report, tab_sim, tab_charts = st.tabs(["📊 Race Report", "🎮 Live Simulator", "📈 Performance Charts"])

# --- TAB 1: RACE REPORT (BỔ SUNG) ---
with tab_report:
    # Tính toán Leaderboard dựa trên Avg Speed
    leaderboard = df_all.groupby('driver').agg(
        Avg_Speed=('speed', 'mean'),
        Max_Speed=('speed', 'max')
    ).sort_values(by='Avg_Speed', ascending=False).reset_index()
    leaderboard['Rank'] = leaderboard.index + 1
    winner = leaderboard.iloc[0]

    st.subheader(f"🥇 Winner: {winner['driver']}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Vận tốc TB Winner", f"{int(winner['Avg_Speed'])} km/h")
    m2.metric("Top Speed Chặng", f"{int(leaderboard['Max_Speed'].max())} km/h")
    m3.metric("Số xe tham gia", f"{len(leaderboard)} xe")

    st.write("### Bảng xếp hạng chi tiết (Leaderboard)")
    st.dataframe(
        leaderboard[['Rank', 'driver', 'Avg_Speed', 'Max_Speed']].style.format({
            'Avg_Speed': '{:.1f}', 'Max_Speed': '{:.0f}'
        }).background_gradient(subset=['Avg_Speed'], cmap='Greens'),
        use_container_width=True
    )

# --- TAB 2: LIVE SIMULATOR ---
with tab_sim:
    target_driver_sim = st.selectbox("🎯 Chọn tay đua để mô phỏng", drivers_list, key="driver_sim_tab")
    d_df_sim = df_all[df_all['driver'] == target_driver_sim].copy().reset_index(drop=True)

    # 1. Tính toán phạm vi cố định (Cực kỳ quan trọng để không bị nhảy hình)
    x_min, x_max = d_df_sim['location_x'].min(), d_df_sim['location_x'].max()
    y_min, y_max = d_df_sim['location_y'].min(), d_df_sim['location_y'].max()
    padding = 500

    st.subheader(f"📊 Thông số tổng quan: {target_driver_sim}")
    o1, o2, o3, o4, o5 = st.columns(5)
    o1.metric("Max Speed", f"{int(d_df_sim['speed'].max())} km/h")
    o2.metric("Max RPM", f"{int(d_df_sim['rpm'].max())}")
    o3.metric("Max Gear", f"L{int(d_df_sim['gear'].max())}")
    o4.metric("Avg Throttle", f"{int(d_df_sim['throttle'].mean())}%")
    o5.metric("Brake Action", f"{len(d_df_sim[d_df_sim['brake'] > 0])} pts")

    col_sim, col_ctrl = st.columns([3, 1])
    
    with col_ctrl:
        st.write("#### 🕹️ Điều khiển")
        run_btn = st.button("🚀 Bắt đầu mô phỏng", key="run_sim_btn_trigger")
        progress_bar = st.progress(0)

    # 2. Hàm vẽ frame (Ép tạo Object mới mỗi lần gọi)
    def get_current_frame(index):
        row = d_df_sim.iloc[index]
        fig = go.Figure()

        # Vẽ đường đua Heatmap (Nền)
        fig.add_trace(go.Scatter(
            x=d_df_sim['location_x'], y=d_df_sim['location_y'],
            mode='markers',
            marker=dict(size=4, color=d_df_sim['speed'], colorscale='Inferno', showscale=True,
                        colorbar=dict(title="Speed", x=-0.15)),
            name="Track", hoverinfo='skip'
        ))

        # Vẽ xe (Marker) tại vị trí index hiện tại
        fig.add_trace(go.Scatter(
            x=[row['location_x']], y=[row['location_y']],
            mode='markers+text',
            marker=dict(size=22, color='#00D2BE', symbol='triangle-up', line=dict(width=2, color='white')),
            text=[target_driver_sim], textposition="top center",
            name="Car"
        ))

        # Layout cố định khung hình
        fig.update_layout(
            height=650, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(range=[x_min - padding, x_max + padding], visible=False, scaleanchor="y"),
            yaxis=dict(range=[y_min - padding, y_max + padding], visible=False),
            showlegend=False
        )
        return fig

    with col_sim:
        sim_placeholder = st.empty()
        # Hiển thị vạch xuất phát ban đầu
        sim_placeholder.plotly_chart(get_current_frame(0), use_container_width=True, key="sim_start")

    # 3. Vòng lặp chạy simulator
    if run_btn:
        total_steps = len(d_df_sim)
        step_size = 10  # Tăng lên 10 để mượt hơn nữa (giảm số lần render)
        
        for i in range(0, total_steps, step_size):
            # Tạo Figure mới hoàn toàn cho frame này
            current_fig = get_current_frame(i)
            
            # Đẩy lên placeholder với key duy nhất
            sim_placeholder.plotly_chart(current_fig, use_container_width=True, key=f"active_frame_{i}")
            
            # Cập nhật progress
            progress_bar.progress(min(i / total_steps, 1.0))
            
            # Nghỉ một chút để trình duyệt kịp vẽ
            time.sleep(0.01)
        
        # Sau khi chạy xong, hiển thị frame cuối cùng
        sim_placeholder.plotly_chart(get_current_frame(total_steps - 1), use_container_width=True, key="sim_end")
        st.success("🏁 Hoàn thành mô phỏng!")

# --- TAB 3: PERFORMANCE CHARTS ---
with tab_charts:
    # BỔ SUNG: Thanh chọn tay đua riêng cho biểu đồ
    target_driver_chart = st.selectbox("📈 Chọn tay đua để phân tích biểu đồ", drivers_list, key="driver_chart_tab")
    d_df_chart = df_all[df_all['driver'] == target_driver_chart].copy().reset_index(drop=True)

    st.subheader(f"📊 Phân tích kỹ thuật: {target_driver_chart}")
    c1, c2 = st.columns(2)
    
    with c1:
        fig_speed = go.Figure()
        fig_speed.add_trace(go.Scatter(x=d_df_chart['rel_time'], y=d_df_chart['speed'], name="Speed", line=dict(color='#FF5733', width=2)))
        fig_speed.add_trace(go.Scatter(x=d_df_chart['rel_time'], y=d_df_chart['rpm'], name="RPM", yaxis="y2", line=dict(color='#00D2BE', dash='dot')))
        fig_speed.update_layout(
            title="Biểu đồ Tốc độ & Vòng tua", template="plotly_dark", height=450,
            yaxis=dict(title="Speed (km/h)"),
            yaxis2=dict(title="RPM", overlaying="y", side="right"),
            hovermode="x unified"
        )
        st.plotly_chart(fig_speed, use_container_width=True)

    with c2:
        fig_pedal = go.Figure()
        fig_pedal.add_trace(go.Scatter(x=d_df_chart['rel_time'], y=d_df_chart['throttle'], name="Throttle", fill='tozeroy', line=dict(color='#2ECC71')))
        fig_pedal.add_trace(go.Scatter(x=d_df_chart['rel_time'], y=d_df_chart['brake'], name="Brake", fill='tozeroy', line=dict(color='#E74C3C')))
        fig_pedal.update_layout(title="Tỉ lệ Đạp Ga & Phanh (%)", template="plotly_dark", height=450, hovermode="x unified")
        st.plotly_chart(fig_pedal, use_container_width=True)

    st.divider()
    with st.expander("📝 Xem bảng dữ liệu chi tiết"):
        st.dataframe(
            d_df_chart[['rel_time', 'speed', 'rpm', 'gear', 'throttle', 'brake']].style.background_gradient(subset=['speed'], cmap='OrRd'), 
            use_container_width=True
        )
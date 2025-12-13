import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ---------------------------------------------------------
# 1. 網頁設定
# ---------------------------------------------------------
st.set_page_config(
    page_title="台海周邊共機動態追蹤",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ 台海周邊海、空域動態追蹤")
st.markdown("資料來源：國防部即時軍事動態（自動化追蹤）")

# ---------------------------------------------------------
# 2. 資料讀取區
# ---------------------------------------------------------
@st.cache_data
def load_data():
    """
    這裡現在設定為讀取 GitHub 上的 cleaned_data.csv
    """
    # --- [設定讀取模式] ---
    # 這裡我們用 'production' 模式，但在 url 填入相對路徑
    # Streamlit Cloud 會直接在你的 GitHub 倉庫裡找這個檔案
    file_path = "cleaned_data.csv" 
    
    try:
        # 讀取 CSV
        df = pd.read_csv(file_path)
        
        # --- [資料清理與對應] ---
        # 1. 重新命名欄位，讓它們跟我們的程式碼對接
        # B 給的欄位是: "日期", "共機架次"
        # 我們需要的欄位是: "date", "total_aircraft", "enter_adiz", "ships"
        df = df.rename(columns={
            '日期': 'date',
            '共機架次': 'total_aircraft'
        })
        
        # 2. 處理日期格式 (B 的格式是 2025/2/3)
        df['date'] = pd.to_datetime(df['date'])
        
        # 3. 處理缺少的欄位 (B 還沒清出來的部分)
        # 我們暫時先補 0，這樣程式才不會壞掉
        if 'enter_adiz' not in df.columns:
            df['enter_adiz'] = 0  # 暫時補 0
        
        if 'ships' not in df.columns:
            df['ships'] = 0       # 暫時補 0

        # 4. 確保日期由新到舊排序
        df = df.sort_values(by='date', ascending=False)
        
        return df

    except FileNotFoundError:
        # 如果找不到檔案，回傳一個空的 DataFrame 或丟出錯誤
        st.error("找不到 cleaned_data.csv！請確認你有把這個檔案上傳到 GitHub。")
        st.stop()

# 載入資料
try:
    df = load_data()
    
    # 確保資料只有日期部分（去掉時間）
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

except Exception as e:
    st.error(f"資料載入失敗，請檢查資料來源或欄位名稱。\n錯誤訊息: {e}")
    st.stop() # 停止執行

# ---------------------------------------------------------
# 3. 關鍵指標呈現 (最新一日)
# ---------------------------------------------------------
# 取得最新一筆資料
if not df.empty:
    latest = df.iloc[0]
    # 如果有上一筆資料，就計算漲跌，否則設為 0
    if len(df) > 1:
        prev = df.iloc[1]
        delta_aircraft = int(latest['total_aircraft'] - prev['total_aircraft'])
        delta_adiz = int(latest['enter_adiz'] - prev['enter_adiz'])
        delta_ships = int(latest['ships'] - prev['ships'])
    else:
        delta_aircraft = 0
        delta_adiz = 0
        delta_ships = 0

    st.subheader(f"📅 最新動態：{latest['date_str']}")

    # 建立三欄佈局
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="偵獲共機總數 (架次)",
            value=int(latest['total_aircraft']),
            delta=delta_aircraft
        )

    with col2:
        st.metric(
            label="其中逾越中線/進入西南空域",
            value=int(latest['enter_adiz']),
            delta=delta_adiz,
            delta_color="inverse",
            help="⚠️ 目前資料尚未串接，暫顯示為 0"
        )

    with col3:
        st.metric(
            label="共艦 (艘次)",
            value=int(latest['ships']),
            delta=delta_ships,
            help="⚠️ 目前資料尚未串接，暫顯示為 0"
        )

    st.divider()

    # ---------------------------------------------------------
    # 4. 趨勢圖表 (Plotly)
    # ---------------------------------------------------------
    st.subheader("📊 近期趨勢圖")

    # 建立折線圖
    fig = go.Figure()

    # 共機總數 (只有這個是真的)
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['total_aircraft'],
        mode='lines+markers', name='共機總數',
        line=dict(color='#FF5733', width=2)
    ))

    # 進入 ADIZ (暫時隱藏或顯示為 0)
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['enter_adiz'],
        mode='lines+markers', name='進入 ADIZ (待補)',
        line=dict(color='#C70039', width=2, dash='dot')
    ))

    # 共艦
    fig.add_trace(go.Bar(
        x=df['date'], y=df['ships'],
        name='共艦艘次 (待補)',
        marker_color='#33C4FF',
        opacity=0.3,
        yaxis='y2' 
    ))

    # 設定圖表版面
    fig.update_layout(
        title='共機/共艦 數量變化趨勢',
        xaxis_title='日期',
        yaxis_title='架次',
        yaxis2=dict(
            title='艘次',
            overlaying='y',
            side='right'
        ),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # 5. 詳細資料表格
    # ---------------------------------------------------------
    with st.expander("查看詳細數據表格"):
        st.dataframe(
            df[['date_str', 'total_aircraft', 'enter_adiz', 'ships']],
            column_config={
                "date_str": "日期",
                "total_aircraft": st.column_config.NumberColumn("共機總數", format="%d"),
                "enter_adiz": st.column_config.NumberColumn("進入 ADIZ", format="%d"),
                "ships": st.column_config.NumberColumn("共艦", format="%d"),
            },
            use_container_width=True,
            hide_index=True
        )
else:
    st.warning("目前沒有資料可顯示。")
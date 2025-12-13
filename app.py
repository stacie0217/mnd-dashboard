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
# 2. 資料讀取區 (關鍵！)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    """
    這裡負責載入資料。
    目前設為「模擬資料模式」，等 B 完成後，
    我們只要把下面的 mode 改成 'production' 就可以連上 GitHub 了。
    """
    mode = 'mock'  # 選項: 'mock' (假資料), 'production' (真實 GitHub 資料), 'local' (你手邊的 Excel)
    
    df = pd.DataFrame()

    if mode == 'mock':
        # --- [模擬資料] ---
        # 這是做給你看效果用的，模擬 B 之後會產出的格式
        dates = pd.date_range(end=datetime.today(), periods=30)
        data = {
            'date': dates,
            'total_aircraft': np.random.randint(5, 40, size=30), # 共機總數
            'enter_adiz': np.random.randint(0, 20, size=30),     # 進入 ADIZ
            'ships': np.random.randint(3, 10, size=30)           # 共艦
        }
        df = pd.DataFrame(data)
        # 確保進入 ADIZ 不會超過總數 (邏輯修正)
        df['enter_adiz'] = df.apply(lambda x: min(x['enter_adiz'], x['total_aircraft']), axis=1)
        
    elif mode == 'local':
        # --- [本機檔案] ---
        # 如果你想讀取 B 傳給你的 Excel/CSV
        # 請確保檔案有對應的欄位名稱
        df = pd.read_csv("cleaned_data.csv") # 假設檔名
        df['date'] = pd.to_datetime(df['date'])

    elif mode == 'production':
        # --- [最終串接] ---
        # B 完成後，填入 GitHub Raw Link
        # URL 範例: "https://raw.githubusercontent.com/USER/REPO/main/final_stats.csv"
        url = "請填入_GITHUB_RAW_LINK" 
        df = pd.read_csv(url)
        df['date'] = pd.to_datetime(df['date'])

    # 確保日期由新到舊排序
    df = df.sort_values(by='date', ascending=False)
    return df

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
latest = df.iloc[0]
prev = df.iloc[1] if len(df) > 1 else latest # 用來比對漲跌

st.subheader(f"📅 最新動態：{latest['date_str']}")

# 建立三欄佈局
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="偵獲共機總數 (架次)",
        value=int(latest['total_aircraft']),
        delta=int(latest['total_aircraft'] - prev['total_aircraft'])
    )

with col2:
    st.metric(
        label="其中逾越中線/進入西南空域",
        value=int(latest['enter_adiz']),
        delta=int(latest['enter_adiz'] - prev['enter_adiz']),
        delta_color="inverse" # 越多越不好，所以顏色反轉
    )

with col3:
    st.metric(
        label="共艦 (艘次)",
        value=int(latest['ships']),
        delta=int(latest['ships'] - prev['ships'])
    )

st.divider()

# ---------------------------------------------------------
# 4. 趨勢圖表 (Plotly)
# ---------------------------------------------------------
st.subheader("📊 近期趨勢圖")

# 建立折線圖
fig = go.Figure()

# 共機總數
fig.add_trace(go.Scatter(
    x=df['date'], y=df['total_aircraft'],
    mode='lines+markers', name='共機總數',
    line=dict(color='#FF5733', width=2)
))

# 進入 ADIZ
fig.add_trace(go.Scatter(
    x=df['date'], y=df['enter_adiz'],
    mode='lines+markers', name='進入 ADIZ',
    line=dict(color='#C70039', width=2, dash='dot')
))

# 共艦 (可以用 Bar 或 Line，這裡示範用 Bar 混合圖)
fig.add_trace(go.Bar(
    x=df['date'], y=df['ships'],
    name='共艦艘次',
    marker_color='#33C4FF',
    opacity=0.3,
    yaxis='y2' # 設定第二個 Y 軸，避免比例差太多
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
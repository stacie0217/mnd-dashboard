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
st.markdown("資料更新：GitHub Actions 自動化串接")

# ---------------------------------------------------------
# 2. 資料讀取區 (串接組員 B 的自動化資料)
# ---------------------------------------------------------
@st.cache_data(ttl=3600) # 設定 ttl=3600，代表每小時會重新去 GitHub 抓一次新資料
def load_data():
    # 這是組員 B 的自動化檔案連結 (去除 token 的永久連結)
    # 前提：組員 A 的 Repo 必須是 Public (公開) 的
    url = "https://raw.githubusercontent.com/viviankoko/mnd_crawler/main/mnd_pla_wrangled.csv"
    
    try:
        # 直接從網址讀取 CSV
        df = pd.read_csv(url)
        
        # --- [欄位對應] ---
        # 把 B 的中文欄位名稱，換成我們程式用的英文名稱
        # 注意：這裡我有處理 B 的錯字 "AIDZ"
        df = df.rename(columns={
            '日期': 'date',
            '共機架次': 'total_aircraft',
            '共艦架次': 'ships',
            '進入AIDZ共機架次': 'enter_adiz', # 配合 B 的 CSV 欄位名稱
            '進入ADIZ共機架次': 'enter_adiz'  # 預防萬一她之後改對了，兩者都通吃
        })
        
        # 處理日期格式
        df['date'] = pd.to_datetime(df['date'])
        
        # 確保日期由新到舊排序
        df = df.sort_values(by='date', ascending=False)
        
        # 處理空值 (如果有的話補 0)
        df = df.fillna(0)
        
        return df

    except Exception as e:
        # 這裡專門抓讀取失敗的問題
        st.error("⚠️ 資料讀取失敗！")
        st.info("可能原因：\n1. 組員 A 的 GitHub Repo 不是 Public (公開) 的，導致連結無法讀取。\n2. 欄位名稱有變動。")
        st.error(f"錯誤訊息: {e}")
        st.stop()

# 載入資料
df = load_data()

# 確保資料只有日期部分（去掉時間）
df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

# ---------------------------------------------------------
# 3. 關鍵指標呈現 (最新一日)
# ---------------------------------------------------------
if not df.empty:
    latest = df.iloc[0] # 最新一筆
    
    # 嘗試抓上一筆來做比較 (如果有昨天的資料)
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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="偵獲共機總數 (架次)",
            value=int(latest['total_aircraft']),
            delta=delta_aircraft,
            delta_color="inverse" # 越多越危險，顏色反轉
        )

    with col2:
        st.metric(
            label="其中逾越中線/進入西南空域",
            value=int(latest['enter_adiz']),
            delta=delta_adiz,
            delta_color="inverse"
        )

    with col3:
        st.metric(
            label="共艦 (艘次)",
            value=int(latest['ships']),
            delta=delta_ships,
            delta_color="inverse"
        )

    st.divider()

    # ---------------------------------------------------------
    # 4. 趨勢圖表 (Plotly)
    # ---------------------------------------------------------
    st.subheader("📊 近期趨勢圖")

    # 建立圖表物件
    fig = go.Figure()

    # 線圖：共機總數
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['total_aircraft'],
        mode='lines+markers', name='共機總數',
        line=dict(color='#FF5733', width=2)
    ))

    # 線圖：進入 ADIZ
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['enter_adiz'],
        mode='lines+markers', name='進入 ADIZ',
        line=dict(color='#C70039', width=2, dash='dot')
    ))

    # 柱狀圖：共艦 (使用右側 Y 軸)
    fig.add_trace(go.Bar(
        x=df['date'], y=df['ships'],
        name='共艦艘次',
        marker_color='#33C4FF',
        opacity=0.3,
        yaxis='y2' 
    ))

    # 設定版面細節
    fig.update_layout(
        title='共機/共艦 數量變化趨勢',
        xaxis_title='日期',
        yaxis_title='架次',
        yaxis2=dict(
            title='艘次',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            y=1.1,
            x=0.5,
            xanchor='center'
        )
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
    st.warning("目前沒有資料可顯示，請檢查資料來源連結。")
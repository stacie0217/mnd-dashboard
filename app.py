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

# [新功能] 加入說明文字
st.info(
    """
    本網頁偵測之數字來自國防部每天發布之公告，共機數量代表所有國防部所偵測到在台海周邊活動的數量，船艦亦然。
    本視覺化圖表提供大眾與研究者自國防部發布報告以來的長期趨勢圖，也建立一鍵下載所有數據的功能以利後續研究，歡迎自行取用。
    """
)

st.markdown("資料來源：**國防部即時軍事動態** | 資料更新：**GitHub Actions 自動化串接**")

# ---------------------------------------------------------
# 2. 資料讀取區
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    # 這是組員 A 的 Repo (公開連結)
    url = "https://raw.githubusercontent.com/viviankoko/mnd_crawler/main/mnd_pla_wrangled.csv"
    
    try:
        df = pd.read_csv(url)
        
        # 欄位對應
        df = df.rename(columns={
            '日期': 'date',
            '共機架次': 'total_aircraft',
            '共艦架次': 'ships',
            '進入AIDZ共機架次': 'enter_adiz',
            '進入ADIZ共機架次': 'enter_adiz'
        })
        
        # 處理日期與空值
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # 過濾年份範圍：只保留 2000 ~ 2050 年
        df = df[df['date'].notna()]
        df = df[ (df['date'].dt.year >= 2000) & (df['date'].dt.year <= 2050) ]

        df = df.sort_values(by='date', ascending=False)
        df = df.fillna(0)
        return df

    except Exception as e:
        st.error("⚠️ 資料讀取失敗！")
        st.info("可能原因：\n1. 組員 A 的 GitHub Repo 不是 Public (公開) 的。\n2. 欄位名稱有變動。")
        st.error(f"錯誤訊息: {e}")
        st.stop()

# 載入原始資料
df = load_data()
df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

# ---------------------------------------------------------
# ✨ [修改] 日期篩選器 (搬到主畫面，並放大顯示)
# ---------------------------------------------------------
st.divider() # 加一條分隔線
st.subheader("🔎 選擇時間範圍")

# 找出資料中最早和最晚的日期
if not df.empty:
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
else:
    min_date = datetime.today().date()
    max_date = datetime.today().date()

# 建立兩欄佈局，讓選擇器不要佔滿整行
col_filter_1, col_filter_2 = st.columns([1, 2])

with col_filter_1:
    # 日期選擇器
    date_range = st.date_input(
        "請選擇起始與結束日期",
        value=(min_date, max_date), # 預設選取全部
        min_value=min_date,
        max_value=max_date
    )

# 處理日期選擇邏輯 (防呆：使用者可能只選了一個日期還沒選第二個)
if len(date_range) == 2:
    start_date, end_date = date_range
    # 根據選擇過濾資料
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
    filtered_df = df.loc[mask]
else:
    # 如果使用者只點了一下還沒點第二下，先暫時顯示全部，避免報錯
    start_date, end_date = min_date, max_date
    filtered_df = df

with col_filter_2:
    # 顯示目前狀態
    st.write("") # 為了排版對齊空一行
    st.write(f"📊 目前顯示區間： **{start_date}** 到 **{end_date}**")
    st.write(f"📈 資料筆數： **{len(filtered_df)}** 筆")


# ---------------------------------------------------------
# 3. 關鍵指標呈現 (顯示篩選範圍內最新的一天)
# ---------------------------------------------------------
st.divider()

if not filtered_df.empty:
    latest = filtered_df.iloc[0] 
    
    # 計算漲跌
    if len(filtered_df) > 1:
        prev = filtered_df.iloc[1]
        delta_aircraft = int(latest['total_aircraft'] - prev['total_aircraft'])
        delta_adiz = int(latest['enter_adiz'] - prev['enter_adiz'])
        delta_ships = int(latest['ships'] - prev['ships'])
    else:
        delta_aircraft = 0
        delta_adiz = 0
        delta_ships = 0

    st.subheader(f"📅 最新動態 ({latest['date_str']})")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="偵獲共機總數 (架次)",
            value=int(latest['total_aircraft']),
            delta=delta_aircraft,
            delta_color="inverse"
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

    # ---------------------------------------------------------
    # 4. 趨勢圖表 (字體放大版)
    # ---------------------------------------------------------
    st.subheader("📊 數量變化趨勢")

    fig = go.Figure()

    # 線圖：共機總數
    fig.add_trace(go.Scatter(
        x=filtered_df['date'], y=filtered_df['total_aircraft'],
        mode='lines+markers', name='共機總數',
        line=dict(color='#FF5733', width=3) # 線條加粗
    ))

    # 線圖：進入 ADIZ
    fig.add_trace(go.Scatter(
        x=filtered_df['date'], y=filtered_df['enter_adiz'],
        mode='lines+markers', name='進入 ADIZ',
        line=dict(color='#C70039', width=3, dash='dot') # 線條加粗
    ))

    # 柱狀圖：共艦
    fig.add_trace(go.Bar(
        x=filtered_df['date'], y=filtered_df['ships'],
        name='共艦艘次',
        marker_color='#33C4FF',
        opacity=0.4,
        yaxis='y2' 
    ))

    # [修改] 設定圖表版面 & 字體放大
    fig.update_layout(
        height=500, # 圖表高度
        xaxis_title='日期',
        yaxis_title='架次',
        yaxis2=dict(
            title='艘次',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        hovermode="x unified",
        
        # [這裡] 設定圖例 (Legend) 的字體大小和位置
        legend=dict(
            orientation="h",
            y=1.1,
            x=0.5,
            xanchor='center',
            font=dict(size=16) # 字體改大到 16px
        ),
        
        # 設定座標軸字體大小
        xaxis=dict(tickfont=dict(size=14)),
        yaxis=dict(tickfont=dict(size=14))
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # 5. 詳細資料表格 & 下載功能
    # ---------------------------------------------------------
    st.subheader("📝 詳細數據")
    
    # 製作下載 CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')

    st.download_button(
        label="📥 下載目前篩選的資料 (CSV)",
        data=csv,
        file_name='mnd_filtered_data.csv',
        mime='text/csv',
    )
    
    st.dataframe(
        filtered_df[['date_str', 'total_aircraft', 'enter_adiz', 'ships']],
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
    st.warning("⚠️ 目前沒有資料可顯示，請檢查資料來源連結或調整篩選日期。")
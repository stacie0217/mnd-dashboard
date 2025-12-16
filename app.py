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
# 2. 資料讀取區
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    # 這是組員 B 的自動化檔案連結 (去除 token 的永久連結)
    # 前提：組員 A 的 Repo 必須是 Public (公開) 的
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
        # errors='coerce' 代表如果有轉換失敗的日期（例如亂碼），會變成 NaT (空值) 而不是報錯
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # ⚠️ [新功能] 過濾年份範圍：只保留 2000 ~ 2050 年的資料
        # 這可以避免誤植成 3000 年或 1900 年的資料破壞圖表
        df = df[df['date'].notna()] # 先移除日期是空值的
        df = df[ (df['date'].dt.year >= 2000) & (df['date'].dt.year <= 2050) ]

        df = df.sort_values(by='date', ascending=False)
        df = df.fillna(0)
        return df

    except Exception as e:
        st.error("⚠️ 資料讀取失敗！")
        st.info("可能原因：\n1. 組員 A 的 GitHub Repo 不是 Public (公開) 的，導致連結無法讀取。\n2. 欄位名稱有變動。")
        st.error(f"錯誤訊息: {e}")
        st.stop()

# 載入原始資料
df = load_data()
df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

# ---------------------------------------------------------
# ✨ 新功能 1：側邊欄日期篩選器
# ---------------------------------------------------------
st.sidebar.header("🔎 篩選條件")

# 找出資料中最早和最晚的日期 (現在保證在 2000-2050 之間)
if not df.empty:
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
else:
    min_date = datetime.today().date()
    max_date = datetime.today().date()

# 建立日期選擇器 (預設選取全部範圍)
start_date, end_date = st.sidebar.date_input(
    "選擇日期範圍",
    value=(min_date, max_date), # 預設值
    min_value=min_date,
    max_value=max_date
)

# 根據選擇的日期過濾資料
# mask 是一個篩選網 (True/False)
mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
filtered_df = df.loc[mask]

# 顯示目前篩選筆數
st.sidebar.info(f"顯示資料筆數：{len(filtered_df)} 筆")


# ---------------------------------------------------------
# 3. 關鍵指標呈現 (顯示篩選範圍內最新的一天)
# ---------------------------------------------------------
if not filtered_df.empty:
    # 注意：這裡改成用 filtered_df (篩選後的資料)
    latest = filtered_df.iloc[0] 
    
    # 嘗試抓上一筆來做比較 (如果有昨天的資料)
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

    st.divider()

    # ---------------------------------------------------------
    # 4. 趨勢圖表 (連動篩選後的資料)
    # ---------------------------------------------------------
    st.subheader("📊 數量變化趨勢")

    # 建立圖表物件
    fig = go.Figure()

    # 線圖：共機總數
    fig.add_trace(go.Scatter(
        x=filtered_df['date'], y=filtered_df['total_aircraft'],
        mode='lines+markers', name='共機總數',
        line=dict(color='#FF5733', width=2)
    ))

    # 線圖：進入 ADIZ
    fig.add_trace(go.Scatter(
        x=filtered_df['date'], y=filtered_df['enter_adiz'],
        mode='lines+markers', name='進入 ADIZ',
        line=dict(color='#C70039', width=2, dash='dot')
    ))

    # 柱狀圖：共艦
    fig.add_trace(go.Bar(
        x=filtered_df['date'], y=filtered_df['ships'],
        name='共艦艘次',
        marker_color='#33C4FF',
        opacity=0.3,
        yaxis='y2' 
    ))

    # 設定版面細節
    fig.update_layout(
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
    # 5. 詳細資料表格 & 下載功能
    # ---------------------------------------------------------
    st.subheader("📝 詳細數據")
    
    # --- ✨ 新功能 2：資料下載按鈕 ---
    # 把篩選後的資料轉成 CSV
    # encoding='utf-8-sig' 是為了讓 Excel 打開中文不亂碼
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')

    st.download_button(
        label="📥 下載篩選後的資料 (CSV)",
        data=csv,
        file_name='mnd_filtered_data.csv',
        mime='text/csv',
    )
    
    # 顯示表格
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
```

### 修改重點：
我在第 45 行左右加了這段邏輯：
```python
# ⚠️ [新功能] 過濾年份範圍：只保留 2000 ~ 2050 年的資料
df = df[df['date'].notna()] # 先移除日期是空值的
df = df[ (df['date'].dt.year >= 2000) & (df['date'].dt.year <= 2050) ]
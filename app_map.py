import streamlit as st
from PIL import Image, ExifTags
import pandas as pd

st.title("🗺️ 照片 GPS 足跡地圖產生器")
st.write("上傳包含定位資訊的手機照片，系統會自動萃取座標並標示於地圖上！")

# --- 輔助函式：將度分秒 (DMS) 轉換為十進位經緯度 ---
def convert_to_decimal(value, ref):
    """
    將 EXIF 中的 GPS 格式 (度, 分, 秒) 轉換為 Google Map 看得懂的十進位浮點數
    """
    try:
        # 依據不同 PIL 版本，取值方式可能略有不同
        degrees = float(value[0])
        minutes = float(value[1])
        seconds = float(value[2])
        
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        # 如果是南半球 (S) 或西半球 (W)，座標要轉為負數
        if ref in ['S', 'W']:
            decimal = -decimal
            
        return decimal
    except Exception as e:
        return None

# --- 輔助函式：從圖片中讀取 GPS 座標 ---
def get_gps_coordinates(image):
    try:
        exif_data = image._getexif()
        if not exif_data:
            return None

        gps_info = {}
        # 走訪 EXIF 標籤，尋找 GPSInfo (Tag ID: 34853)
        for tag, value in exif_data.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                # 將 GPSInfo 內部的 ID 轉為可讀的標籤
                for t in value:
                    sub_decoded = ExifTags.GPSTAGS.get(t, t)
                    gps_info[sub_decoded] = value[t]
                break

        if not gps_info:
            return None

        # 確保有經緯度資料
        if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
            lat = convert_to_decimal(gps_info['GPSLatitude'], gps_info['GPSLatitudeRef'])
            lon = convert_to_decimal(gps_info['GPSLongitude'], gps_info['GPSLongitudeRef'])
            return lat, lon
            
    except Exception as e:
        return None
        
    return None

# --- 主程式區塊 ---
uploaded_files = st.file_uploader("請選擇手機拍攝的照片 (需開啟定位功能)", type=["jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    locations = []
    no_gps_files = []

    with st.spinner("正在分析照片座標資訊..."):
        for f in uploaded_files:
            img = Image.open(f)
            coords = get_gps_coordinates(img)
            
            if coords:
                locations.append({
                    "filename": f.name,
                    "latitude": coords[0],
                    "longitude": coords[1]
                })
            else:
                no_gps_files.append(f.name)

    # 如果有成功抓到座標的照片
    if locations:
        st.success(f"✅ 成功讀取 {len(locations)} 張照片的 GPS 座標！")
        
        # 轉換為 Pandas DataFrame，因為 st.map 需要這種格式，且欄位必須包含 latitude 與 longitude
        df_locations = pd.DataFrame(locations)
        
        # 顯示地圖
        st.markdown("### 📍 你的足跡地圖")
        st.map(df_locations, size=20, color="#FF0000", zoom=12)
        
        # 顯示座標資料表 (選用)
        with st.expander("查看詳細座標資料"):
            st.dataframe(df_locations)
            
    else:
        st.warning("⚠️ 在上傳的照片中找不到 GPS 資訊。請確認手機拍照時有開啟「位置資訊 / 定位」功能，且檔案未經會抹除 EXIF 的軟體壓縮 (例如 LINE 的一般畫質傳送)。")

    # 提示沒有 GPS 資訊的照片
    if no_gps_files and locations:
        st.info(f"ℹ️ 其中有 {len(no_gps_files)} 張照片沒有定位資訊，已略過。")
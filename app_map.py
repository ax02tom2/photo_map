import streamlit as st
from PIL import Image, ExifTags
import pandas as pd
import folium
from streamlit_folium import st_folium
import base64
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🗺️ 照片 GPS 足跡地圖產生器 (進階預覽版)")
st.write("上傳包含定位資訊的手機照片，可切換衛星底圖，並點選圖標預覽照片！")

# --- 輔助函式：將度分秒 (DMS) 轉換為十進位經緯度 ---
def convert_to_decimal(value, ref):
    try:
        degrees = float(value[0])
        minutes = float(value[1])
        seconds = float(value[2])
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal
    except Exception:
        return None

# --- 輔助函式：從圖片中讀取 GPS 座標 ---
def get_gps_coordinates(image):
    try:
        exif_data = image._getexif()
        if not exif_data:
            return None
        gps_info = {}
        for tag, value in exif_data.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for t in value:
                    sub_decoded = ExifTags.GPSTAGS.get(t, t)
                    gps_info[sub_decoded] = value[t]
                break
        if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
            lat = convert_to_decimal(gps_info['GPSLatitude'], gps_info['GPSLatitudeRef'])
            lon = convert_to_decimal(gps_info['GPSLongitude'], gps_info['GPSLongitudeRef'])
            return lat, lon
    except Exception:
        return None
    return None

# --- 輔助函式：將圖片轉為 Base64 以便在地圖上顯示 ---
def get_image_base64(image, max_size=(250, 250)):
    img_copy = image.copy()
    img_copy.thumbnail(max_size)
    buffered = BytesIO()
    # 統一轉為 RGB 避免 RGBA 存 JPEG 報錯
    img_copy.convert("RGB").save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# --- 側邊欄：地圖底圖設定 ---
st.sidebar.header("🗺️ 地圖設定")
map_style = st.sidebar.selectbox(
    "選擇地圖底圖",
    ["預設街道圖 (OpenStreetMap)", "衛星航空圖 (Esri World Imagery)", "深色模式 (CartoDB Dark Matter)"]
)

# --- 主程式區塊 ---
uploaded_files = st.file_uploader("請選擇手機拍攝的照片 (需開啟定位功能)", type=["jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    locations = []
    
    with st.spinner("正在分析照片座標並產生縮圖..."):
        for f in uploaded_files:
            img = Image.open(f)
            coords = get_gps_coordinates(img)
            
            if coords:
                img_b64 = get_image_base64(img)
                locations.append({
                    "filename": f.name,
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "image_b64": img_b64
                })

    if locations:
        st.success(f"✅ 成功讀取 {len(locations)} 張照片的 GPS 座標！")
        
        # 計算地圖中心點
        avg_lat = sum(loc["latitude"] for loc in locations) / len(locations)
        avg_lon = sum(loc["longitude"] for loc in locations) / len(locations)
        
        # 建立基礎地圖
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
        
        # 根據選擇套用不同底圖
        if map_style == "衛星航空圖 (Esri World Imagery)":
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Esri Satellite',
                max_zoom=18
            ).add_to(m)
        elif map_style == "深色模式 (CartoDB Dark Matter)":
            folium.TileLayer('cartodbdark_matter').add_to(m)
            
        # 將照片標記加入地圖
        for loc in locations:
            # 建立包含 Base64 圖片的 HTML 標籤
            html = f'<img src="data:image/jpeg;base64,{loc["image_b64"]}" style="width: 250px; border-radius: 8px;">'
            iframe = folium.IFrame(html, width=270, height=270)
            popup = folium.Popup(iframe, max_width=270)
            
            folium.Marker(
                location=[loc["latitude"], loc["longitude"]],
                popup=popup,
                tooltip=loc["filename"],
                icon=folium.Icon(color="red", icon="camera", prefix="fa")
            ).add_to(m)
            
        # 顯示互動式地圖
        st_folium(m, width=1000, height=600, returned_objects=[])
        
    else:
        st.warning("⚠️ 找不到 GPS 資訊。請確認檔案未經壓縮。")

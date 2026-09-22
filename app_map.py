import streamlit as st
from PIL import Image, ExifTags
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import st_folium
import base64
from io import BytesIO

# --- 更新網頁標題 ---
st.set_page_config(layout="wide", page_title="GPS 影像定位儀")
st.title("🗺️ GPS 影像定位儀")
st.write("上傳包含定位資訊的照片，自動生成專屬足跡地圖！(支援台灣官方圖資、成果匯出與浮水印功能)")

# --- 輔助函式：將度分秒 (DMS) 轉換為高精度十進位經緯度 ---
def convert_to_decimal(value, ref):
    try:
        degrees = float(value[0])
        minutes = float(value[1])
        seconds = float(value[2])
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 7)
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

# --- 輔助函式：將圖片轉為 Base64 縮圖 ---
def get_image_base64(image, max_size=(300, 300)):
    img_copy = image.copy()
    img_copy.thumbnail(max_size)
    buffered = BytesIO()
    img_copy.convert("RGB").save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode()

# --- 側邊欄：地圖底圖選擇 ---
st.sidebar.header("🗺️ 地圖底圖切換")
map_style = st.sidebar.selectbox(
    "選擇底圖來源",
    [
        "內政部正射影像圖 (臺灣航空空照圖)",
        "內政部通用電子地圖套疊正射圖 (空照+地名)",
        "內政部臺灣通用電子地圖 (EMAP)",
        "Esri 全球衛星影像圖 (World Imagery)",
        "OpenStreetMap (國際標準街圖)"
    ]
)

# --- 側邊欄：新增浮水印功能 ---
st.sidebar.markdown("---")
st.sidebar.header("©️ 地圖浮水印設定")
enable_watermark = st.sidebar.checkbox("在地圖加入專屬浮水印 / Logo", value=False)

watermark_html = ""
if enable_watermark:
    wm_type = st.sidebar.radio("浮水印類型", ["文字", "圖片 Logo"])
    wm_position = st.sidebar.selectbox("浮水印位置", ["右下", "左下", "右上", "左上"])
    
    # 計算 CSS 定位
    pos_css = ""
    if wm_position == "右下": pos_css = "bottom: 25px; right: 25px;"
    elif wm_position == "左下": pos_css = "bottom: 30px; left: 15px;"
    elif wm_position == "右上": pos_css = "top: 25px; right: 60px;" 
    elif wm_position == "左上": pos_css = "top: 25px; left: 60px;"  

    if wm_type == "文字":
        wm_text = st.sidebar.text_input("輸入浮水印文字", "我的專屬足跡")
        wm_color = st.sidebar.color_picker("文字顏色", "#FFFFFF")
        
        watermark_html = f"""
        <div style="position: fixed; {pos_css} z-index: 9999; font-size: 26px; font-weight: bold; color: {wm_color}; opacity: 0.85; text-shadow: 2px 2px 5px rgba(0,0,0,0.8); pointer-events: none; font-family: sans-serif;">
            {wm_text}
        </div>
        """
    else:
        logo_file = st.sidebar.file_uploader("上傳 Logo (建議使用背景透明的 PNG)", type=["png", "jpg", "jpeg"])
        logo_size = st.sidebar.slider("Logo 顯示大小 (像素)", 50, 300, 120)
        
        if logo_file:
            logo_b64 = base64.b64encode(logo_file.read()).decode()
            watermark_html = f"""
            <div style="position: fixed; {pos_css} z-index: 9999; pointer-events: none; opacity: 0.9;">
                <img src="data:image/png;base64,{logo_b64}" style="width: {logo_size}px; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.5));">
            </div>
            """

# --- 側邊欄：溫馨提醒區塊 ---
st.sidebar.markdown("---")
st.sidebar.info("💡 **如何將地圖存成圖片？**\n\n受限於互動地圖技術，建議點擊地圖右上角的 **「全螢幕按鈕 ⛶」**，並使用電腦內建截圖工具保存高畫質圖片。")
st.sidebar.info("📌 **定位有點落差？**\n\n手機 GPS 原本即有 3~10 公尺不等的訊號飄移誤差，此為正常硬體限制。")

# --- 主程式區塊 ---
uploaded_files = st.file_uploader(
    "請選擇手機拍攝的照片 (支援 JPG/JPEG，需開啟拍照定位)", 
    type=["jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    locations = []
    
    with st.spinner("正在分析照片座標並產生縮圖..."):
        for f in uploaded_files:
            img = Image.open(f)
            coords = get_gps_coordinates(img)
            
            if coords:
                img_b64 = get_image_base64(img)
                locations.append({
                    "檔名": f.name,
                    "緯度 (Latitude)": coords[0],
                    "經度 (Longitude)": coords[1],
                    "image_b64": img_b64
                })

    if locations:
        st.success(f"✅ 成功讀取 {len(locations)} 張照片的 GPS 座標！")
        
        # 計算中心點
        avg_lat = sum(loc["緯度 (Latitude)"] for loc in locations) / len(locations)
        avg_lon = sum(loc["經度 (Longitude)"] for loc in locations) / len(locations)
        
        # 初始化 Folium 地圖
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=14, tiles=None)

        # 載入所選底圖 (WMTS / TileLayer)
        if map_style == "內政部正射影像圖 (臺灣航空空照圖)":
            folium.TileLayer(
                tiles='https://wmts.nlsc.gov.tw/wmts/PHOTO2/default/GoogleMapsCompatible/{z}/{y}/{x}',
                attr='內政部國土測繪中心', name='正射影像圖', max_zoom=20
            ).add_to(m)
        elif map_style == "內政部通用電子地圖套疊正射圖 (空照+地名)":
            folium.TileLayer(
                tiles='https://wmts.nlsc.gov.tw/wmts/PHOTO_MIX/default/GoogleMapsCompatible/{z}/{y}/{x}',
                attr='內政部國土測繪中心', name='混合正射影像圖', max_zoom=20
            ).add_to(m)
        elif map_style == "內政部臺灣通用電子地圖 (EMAP)":
            folium.TileLayer(
                tiles='https://wmts.nlsc.gov.tw/wmts/EMAP/default/GoogleMapsCompatible/{z}/{y}/{x}',
                attr='內政部國土測繪中心', name='臺灣通用電子地圖', max_zoom=20
            ).add_to(m)
        elif map_style == "Esri 全球衛星影像圖 (World Imagery)":
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri', name='Esri Satellite', max_zoom=18
            ).add_to(m)
        else:
            folium.TileLayer(
                tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                attr='OpenStreetMap', name='OSM', max_zoom=19
            ).add_to(m)

        # 標記照片點位並優化彈出視窗排版 (緊湊版)
        for loc in locations:
            html = f"""
            <div style="margin: 0; padding: 0; text-align: center; font-family: sans-serif;">
                <div style="font-size: 13px; font-weight: bold; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {loc["檔名"]}
                </div>
                <img src="data:image/jpeg;base64,{loc['image_b64']}" 
                     style="width: 100%; border-radius: 4px; display: block; margin: 0 auto;">
            </div>
            """
            iframe = folium.IFrame(html, width=220, height=190)
            popup = folium.Popup(iframe, max_width=220)
            
            folium.Marker(
                location=[loc["緯度 (Latitude)"], loc["經度 (Longitude)"]],
                popup=popup,
                tooltip=loc["檔名"],
                icon=folium.Icon(color="red", icon="camera", prefix="fa")
            ).add_to(m)
            
        # 加入全螢幕按鈕
        plugins.Fullscreen(position='topright', title='展開全螢幕以方便截圖', titleCancel='退出全螢幕').add_to(m)

        # 渲染浮水印 (如果有設定的話)
        if watermark_html:
            m.get_root().html.add_child(folium.Element(watermark_html))

        # 顯示網頁地圖 (高度提升至 800，並強制填滿寬度)
        st_folium(m, use_container_width=True, height=800, returned_objects=[])

        # --- 📤 成果匯出區塊 ---
        st.markdown("---")
        st.subheader("📤 成果資料打包下載")
        col1, col2 = st.columns(2)

        map_html_bytes = m.get_root().render().encode("utf-8")
        with col1:
            st.download_button(
                label="📥 下載互動地圖 (HTML 網頁檔)",
                data=map_html_bytes, file_name="photo_map.html", mime="text/html",
                help="離線也能查看照片與座標點位。浮水印也會一併保留！"
            )

        df_export = pd.DataFrame(locations)[["檔名", "緯度 (Latitude)", "經度 (Longitude)"]]
        csv_bytes = df_export.to_csv(index=False).encode('utf-8-sig')
        with col2:
            st.download_button(
                label="📊 下載 GPS 座標清單 (CSV 檔)",
                data=csv_bytes, file_name="photo_coordinates.csv", mime="text/csv",
                help="可匯入 QGIS 或 Excel 使用。"
            )
            
    else:
        st.warning("⚠️ 找不到 GPS 資訊。請確認相機設定有開啟定位權限，且不是用 LINE 傳送的壓縮圖。")

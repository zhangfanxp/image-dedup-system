import streamlit as st
from pathlib import Path
import shutil
from PIL import Image, UnidentifiedImageError

from utils.unzip import unzip
from utils.image_scan import scan_images
from utils.hash import calc_md5
from utils.similarity import is_similar_cnn
from db.image_repo import get_image_by_md5
from db.session import SessionLocal
from sqlalchemy import text

# =====================
# 页面配置
# =====================
st.set_page_config(
    page_title="图片查重系统（CNN + MPS）",
    layout="wide"
)
st.title("📷 图片查重 / 相似检测系统（CNN + MPS）")

# =====================
# 目录配置
# =====================
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
LIB_DIR = BASE_DIR / "image_library"

UPLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
LIB_DIR.mkdir(exist_ok=True)

# =====================
# 图片格式过滤
# =====================
VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}

# =====================
# Session State
# =====================
if "results" not in st.session_state:
    st.session_state.results = None

# =====================
# 上传 ZIP
# =====================
uploaded = st.file_uploader("上传 ZIP 压缩包", type=["zip"])
if uploaded:
    zip_path = UPLOAD_DIR / uploaded.name
    with open(zip_path, "wb") as f:
        f.write(uploaded.getbuffer())
    st.success(f"ZIP 已上传：{uploaded.name}")

# =====================
# 开始检测
# =====================
if uploaded and st.button("🚀 开始检测"):
    with st.spinner("⏳ 正在运行检测，请稍候..."):
        # 清理临时目录
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
        TEMP_DIR.mkdir()

        # 解压 ZIP
        unzip(zip_path, TEMP_DIR)

        # 扫描图片并过滤非图片文件
        images = [f for f in scan_images(TEMP_DIR) if f.suffix.lower() in VALID_EXTS]
        if not images:
            st.warning("未发现合法图片")
            st.stop()

        # 获取库中图片，过滤非图片文件
        library_images = [f for f in LIB_DIR.iterdir() if f.suffix.lower() in VALID_EXTS]

        results = []
        total_images = len(images)
        progress_bar = st.progress(0)  # 创建进度条
        status_text = st.empty()       # 显示文字进度

        # 检测重复 + 填充结果
        for idx, img in enumerate(images):
            md5 = calc_md5(img)
            record = get_image_by_md5(md5)
            status = "重复" if record else "正常"
            results.append({
                "path": img,
                "md5": md5,
                "status": status,
                "db_record": record,
                "similar_ratio": None,
                "db_similar_image": None
            })
            progress_bar.progress((idx + 1) / total_images * 0.5)
            status_text.text(f"🔍 重复检测中：{idx + 1}/{total_images}")

        # 检测相似
        similar_idx = 0
        for r in results:
            if r["status"] != "正常":
                similar_idx += 1
                continue
            for lib_img in library_images:
                try:
                    similar, sim_ratio = is_similar_cnn(r["path"], lib_img, threshold=0.85)
                except UnidentifiedImageError:
                    continue  # 跳过无法识别的图片
                if similar:
                    r["status"] = "相似"
                    r["similar_ratio"] = int(sim_ratio * 100)
                    r["db_similar_image"] = lib_img.name
                    break
            similar_idx += 1
            progress_bar.progress(0.5 + (similar_idx / total_images * 0.5))
            status_text.text(f"🔍 相似检测中：{similar_idx}/{total_images}")

        # 按状态排序
        status_order = {"相似": 0, "重复": 1, "正常": 2}
        results.sort(key=lambda x: status_order.get(x["status"], 3))

        st.session_state.results = results
        progress_bar.progress(1.0)
        status_text.text("✅ 检测完成！")

# =====================
# 没结果就退出
# =====================
if not st.session_state.results:
    st.info("请先点击「开始检测」")
    st.stop()

results = st.session_state.results

# =====================
# 统计
# =====================
total = len(results)
dup_count = sum(1 for r in results if r["status"] == "重复")
sim_count = sum(1 for r in results if r["status"] == "相似")

st.markdown(
    f"""
    ### 📊 检测统计
    - 图片总数：**{total}**
    - 🟠 相似图片：**{sim_count}**
    - 🔴 重复图片：**{dup_count}**
    - 🟢 正常图片：**{total - dup_count - sim_count}**
    """
)

# =====================
# 重复 / 相似路径（实时计算）
# =====================
problem_paths = [
    str(r["path"].relative_to(TEMP_DIR))
    for r in results
    if r["status"] in ("重复", "相似")
]

st.markdown("### 📋 重复 / 相似图片路径")

if problem_paths:
    st.text_area(
        "请复制以下内容（Cmd + A → Cmd + C）",
        value="\n".join(problem_paths),
        height=220
    )
else:
    st.success("🎉 当前没有需要处理的重复或相似图片")

# =====================
# 正常图片入库
# =====================
if st.button("📥 正常图片入库"):
    session = SessionLocal()
    inserted = 0
    try:
        for r in results:
            if r["status"] != "正常":
                continue
            src = r["path"]
            dst = LIB_DIR / src.name
            if dst.exists():
                dst = LIB_DIR / f"{r['md5']}_{src.name}"
            shutil.copy2(src, dst)

            with Image.open(dst) as im:
                w, h = im.size

            session.execute(
                text("""
                INSERT INTO image_library
                (image_name,image_path,md5,width,height)
                VALUES (:n,:p,:m,:w,:h)
                """),
                {
                    "n": dst.name,
                    "p": str(dst),
                    "m": r["md5"],
                    "w": w,
                    "h": h
                }
            )
            inserted += 1

        session.commit()
        st.success(f"✅ 成功入库 {inserted} 张图片")
    except Exception as e:
        session.rollback()
        st.error(f"❌ 入库失败：{e}")
    finally:
        session.close()

# =====================
# 图片展示 + 相似对比
# =====================
st.markdown("### 🖼 图片详情")
cols = st.columns(4)

for i, r in enumerate(results):
    with cols[i % 4]:
        if r["status"] == "重复":
            st.error("🔴 重复")
        elif r["status"] == "相似":
            st.warning(f"🟠 相似 {r['similar_ratio']}%")
            st.caption(f"库中图片：{r['db_similar_image']}")
        else:
            st.success("🟢 正常")

        st.image(
            str(r["path"]),
            caption=str(r["path"].relative_to(TEMP_DIR)),
            width=180
        )

        if r["status"] == "相似":
            with st.expander(f"🔍 对比: {r['path'].name}", expanded=False):
                lib_img_path = LIB_DIR / r["db_similar_image"]
                col1, col2 = st.columns(2)
                with col1:
                    st.image(str(r["path"]), caption="上传图片", width=300)
                with col2:
                    st.image(str(lib_img_path), caption="库中图片", width=300)

                if st.button("✅ 确认不相似，标记为正常", key=f"mark_{i}"):
                    st.session_state.results[i]["status"] = "正常"
                    st.session_state.results[i]["similar_ratio"] = None
                    st.session_state.results[i]["db_similar_image"] = None
                    st.rerun()

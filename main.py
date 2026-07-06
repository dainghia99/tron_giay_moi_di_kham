# -*- coding: utf-8 -*-
"""
Lam sach & doi chieu du lieu kham suc khoe theo ho dan.  (BAN CAP NHAT)

Thay doi so voi ban truoc:
- DOC COT THEO TEN TIEU DE (khong theo vi tri co dinh) -> chiu duoc file xep cot khac nhau,
  tu dong xu ly dong tieu de phu 'Ban'/'Xa'. In bang "phat hien cot" de kiem chung.
- CHU HO luon dung DAU moi ho, sau do moi den thanh vien (gom ho theo ten chu ho).
- Van: loc xa Muong Toong, doi chieu CCCD + Ho ten + Nam sinh, STT chi cho chu ho,
  moi ban 1 file, canh bao trung ten chu ho / thieu ban.
"""

import os
import re
import unicodedata
from datetime import datetime
import pandas as pd

# ---------------------------------------------------------------------------
# CAU HINH
# ---------------------------------------------------------------------------
INPUT_DIR  = "."         # thu muc chua data_nguoi_dan.csv & data_kham.csv
OUTPUT_DIR = "output"    # thu muc xuat ket qua

FILE_NGUOI_DAN = os.path.join(INPUT_DIR, "data/cay_sat.csv")
FILE_KHAM      = os.path.join(INPUT_DIR, "data_kham.csv")

TARGET_XA = "Mường Toong"
PROVINCE  = "tỉnh Điện Biên"

# ---------------------------------------------------------------------------
# HAM TIEN ICH
# ---------------------------------------------------------------------------
def strip_accents(s: str) -> str:
    if s is None:
        return ""
    s = str(s).replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def norm_key(s: str) -> str:
    """So khop TEN: gop khoang trang + khong phan biet hoa/thuong (giu dau)."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip()).casefold()

def norm_ascii(s: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(s).strip()).lower()

def parse_year(v):
    if v is None:
        return None
    m = re.search(r"\d{4}", str(v))
    return int(m.group()) if m else None

def slugify_ban(ban: str) -> str:
    b = re.sub(r"^\s*bản\s+", "", str(ban).strip(), flags=re.IGNORECASE)
    b = strip_accents(b).lower()
    b = re.sub(r"[^a-z0-9]+", "_", b).strip("_")
    return b or "khong_ro_ban"

def format_dob(year_value, full_date_value=None):
    if full_date_value:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(str(full_date_value).strip(), fmt).strftime("%d/%m/%Y")
            except ValueError:
                continue
    y = parse_year(year_value)
    return str(y) if y is not None else ""

def format_address(ban: str, xa: str) -> str:
    ban_name = re.sub(r"^\s*bản\s+", "", str(ban).strip(), flags=re.IGNORECASE).strip()
    xa_name  = re.sub(r"^\s*xã\s+",  "", str(xa).strip(),  flags=re.IGNORECASE).strip()
    ban_name = " ".join(w.capitalize() for w in ban_name.split())
    xa_name  = " ".join(w.capitalize() for w in xa_name.split())
    return f"Bản {ban_name}, xã {xa_name}, {PROVINCE}"

# ---------------------------------------------------------------------------
# DOC data_nguoi_dan.csv -> danh sach nguoi (doc cot theo TEN tieu de)
# ---------------------------------------------------------------------------
def read_nguoi_dan(path):
    raw = pd.read_csv(path, header=None, dtype=str, encoding="utf-8-sig",
                      keep_default_na=False).fillna("")
    nrows = len(raw)

    # 1) Tim dong tieu de chinh (dong co chua 'Ho va ten')
    header_row = None
    for i in range(min(6, nrows)):
        cells = [norm_ascii(x) for x in raw.iloc[i].tolist()]
        if "ho va ten" in cells or "ho ten" in cells:
            header_row = i
            break
    if header_row is None:
        raise SystemExit("LỖI: Không tìm thấy dòng tiêu đề chứa 'Họ và tên' trong " + path)

    main = [norm_ascii(x) for x in raw.iloc[header_row].tolist()]
    ncols = len(main)

    # 2) Dong tieu de phu (Ban/Xa) - neu co
    sub = None
    if header_row + 1 < nrows:
        nxt = [norm_ascii(x) for x in raw.iloc[header_row + 1].tolist()]
        if ("ban" in nxt or "xa" in nxt) and not ("ho va ten" in nxt or "ho ten" in nxt):
            sub = nxt

    def find(pred):
        for j in range(ncols):
            if pred(main[j]):
                return j
        if sub:
            for j in range(len(sub)):
                if pred(sub[j]):
                    return j
        return None

    col = {
        "name":   find(lambda s: s in ("ho va ten", "ho ten")),
        "year":   find(lambda s: s in ("nam sinh", "ngay sinh", "ngay thang nam sinh")),
        "cccd":   find(lambda s: ("can cuoc" in s) or ("cccd" in s) or ("cmnd" in s)),
        "chu_ho": find(lambda s: "chu ho" in s),
        "ban":    find(lambda s: s == "ban"),
        "xa":     find(lambda s: s == "xa"),
    }
    if col["ban"] is None:  # du phong khi khong co dong phu
        col["ban"] = find(lambda s: ("noi dktt" in s) or s.startswith("ban "))

    data_start = header_row + (2 if sub else 1)

    # 3) In bang chuan doan phat hien cot
    labels = {"name": "Họ và tên", "year": "Năm sinh", "cccd": "Số căn cước",
              "chu_ho": "Họ tên chủ hộ", "ban": "Bản", "xa": "Xã"}
    print("─" * 64)
    print("PHÁT HIỆN CỘT trong data_nguoi_dan.csv (kiểm tra giúp mình dòng này):")
    for k in ["name", "year", "cccd", "chu_ho", "ban", "xa"]:
        j = col[k]
        if j is None:
            print(f"   - {labels[k]:14s}: *** KHÔNG TÌM THẤY ***")
        else:
            shown = main[j] if (j < len(main) and main[j]) else (sub[j] if sub and j < len(sub) else "")
            print(f"   - {labels[k]:14s}: cột #{j}  ('{shown}')")
    print(f"   Dữ liệu bắt đầu từ dòng {data_start + 1}")
    print("─" * 64)

    if col["name"] is None or col["chu_ho"] is None:
        raise SystemExit("LỖI: Thiếu cột 'Họ và tên' hoặc 'Họ tên chủ hộ' — không xác định được "
                         "chủ hộ. Vui lòng kiểm tra tiêu đề cột trong file.")

    def cell(row, key):
        j = col[key]
        return "" if (j is None or j >= len(row)) else str(row[j]).strip()

    persons = []
    for i in range(data_start, nrows):
        row = raw.iloc[i].tolist()
        name = cell(row, "name")
        if name == "":
            continue
        chu_ho = cell(row, "chu_ho")
        persons.append({
            "name": name,
            "year": parse_year(cell(row, "year")),
            "dob": format_dob(cell(row, "year")),
            "cccd": cell(row, "cccd"),
            "ban": cell(row, "ban"),
            "xa": cell(row, "xa"),
            "chu_ho": chu_ho,
            "is_head": (chu_ho != "" and norm_key(name) == norm_key(chu_ho)),
        })
    return persons

# ---------------------------------------------------------------------------
# DOC data_kham.csv -> tra cuu trang thai
# ---------------------------------------------------------------------------
df_kham = pd.read_csv(FILE_KHAM, encoding="utf-8-sig", dtype=str).fillna("")
kham_by_cccd, kham_by_name_year = {}, {}
for _, r in df_kham.iterrows():
    cccd = str(r.get("CMND/CCCD", "")).strip()
    ten  = str(r.get("Họ Tên", "")).strip()
    nam  = parse_year(r.get("Năm Sinh", ""))
    rec = {"ten": ten, "nam": nam}
    if cccd:
        kham_by_cccd.setdefault(cccd, []).append(rec)
    kham_by_name_year.setdefault((norm_key(ten), nam), []).append(rec)

def tra_trang_thai(cccd, ten, nam, canh_bao):
    cccd = (cccd or "").strip()
    ten_k = norm_key(ten)
    if cccd and cccd in kham_by_cccd:
        cand = kham_by_cccd[cccd]
        if not any((norm_key(c["ten"]) == ten_k and c["nam"] == nam) for c in cand):
            canh_bao.append(f"  ⚠ CCCD {cccd} khớp nhưng Họ tên/Năm sinh không trùng ({ten}-{nam}). "
                            f"Vẫn tính 'Đã khám' theo CCCD.")
        return "Đã khám"
    cand = kham_by_name_year.get((ten_k, nam), [])
    if len(cand) == 1:
        return "Đã khám"
    if len(cand) > 1:
        canh_bao.append(f"  ⚠ {ten}-{nam}: {len(cand)} bản ghi khám trùng Họ tên+Năm sinh -> 'Chưa khám'.")
        return "Chưa khám"
    return "Chưa khám"

# ---------------------------------------------------------------------------
# XU LY
# ---------------------------------------------------------------------------
persons = read_nguoi_dan(FILE_NGUOI_DAN)   # CHUA loc xa, giu nguyen thu tu goc de gom khoi cho dung

canh_bao, thieu_ban = [], []
for p in persons:
    p["status"] = tra_trang_thai(p["cccd"], p["name"], p["year"], canh_bao)

# ---------------------------------------------------------------------------
# GOM HO THEO KHOI LIEN KE VI TRI DONG (KHONG so ten tren toan file)
# ---------------------------------------------------------------------------
# Ly do: file goc xep cac dong CUNG MOT HO nam SAT NHAU; chu ho co the o dau,
# giua hay cuoi khoi. Neu 2 chu ho trung ten o 2 vi tri khac nhau trong file,
# so ten toan cuc se gan nham thanh vien. Thay vao do: moi khi gap 1 dong la
# CHU HO (Ho ten == Ho ten chu ho) thi luon MO HO MOI tai vi tri do; cac dong
# thanh vien lien ke (co "Ho ten chu ho" khop ten voi chu ho cua khoi dang mo)
# duoc gom vao dung khoi dang liet ke ngay ben canh no trong file.
order, hh = [], {}
current_key = None  # key cua "khoi dang mo" (co the chua co chu ho - dang cho)

def _new_block(chu_ho_text, ban_default):
    key = ("B", len(order))
    hh[key] = {"head": None, "chu_ho_text": chu_ho_text, "members": [], "ban": ban_default}
    order.append(key)
    return key

for p in persons:
    if p["is_head"]:
        cur = hh.get(current_key) if current_key else None
        if cur is not None and cur["head"] is None and norm_key(cur["chu_ho_text"]) == norm_key(p["name"]):
            # Khop voi khoi dang cho chu ho (co thanh vien da xuat hien truoc)
            cur["head"] = p
            cur["ban"] = p["ban"]
            p["ho_key"] = current_key
        else:
            # Dong CHU HO luon mo mot HO MOI (ke ca khi trung ten voi ho truoc do)
            current_key = _new_block(p["name"], p["ban"])
            hh[current_key]["head"] = p
            p["ho_key"] = current_key
    else:
        cur = hh.get(current_key) if current_key else None
        if cur is not None and norm_key(cur["chu_ho_text"]) == norm_key(p["chu_ho"]):
            # Cung khoi voi dong truoc (dang cho chu ho HOAC da co chu ho dung ten)
            cur["members"].append(p)
            p["ho_key"] = current_key
        else:
            # Bat dau mot khoi CHO CHU HO MOI (chu ho se xuat hien ngay sau day)
            current_key = _new_block(p["chu_ho"], p["ban"])
            hh[current_key]["members"].append(p)
            p["ho_key"] = current_key

# Loc theo XA o CAP DO HO (sau khi gom khoi, de khong lam gay tinh lien ke)
def _block_xa(block):
    ref = block["head"] if block["head"] is not None else (block["members"][0] if block["members"] else None)
    return ref["xa"] if ref else ""

order = [k for k in order if norm_ascii(TARGET_XA) in norm_ascii(_block_xa(hh[k]))]

# Canh bao cac khoi KHONG TIM THAY chu ho + log thieu Ban (CHI trong pham vi xa da loc)
for k in order:
    for p in ([hh[k]["head"]] if hh[k]["head"] else []) + hh[k]["members"]:
        if p["ban"] == "":
            thieu_ban.append(f"  - {p['name']} (CCCD {p['cccd'] or 'trống'}, năm sinh {p['year'] or '?'})")
    if hh[k]["head"] is None:
        ten_ds = ", ".join(m["name"] for m in hh[k]["members"])
        canh_bao.append(
            f"  ⚠ Không tìm thấy dòng chủ hộ '{hh[k]['chu_ho_text']}' cho (các) thành viên: {ten_ds}. "
            f"Nhóm này không có chủ hộ nên KHÔNG được đánh STT — cần bổ sung dữ liệu, kiểm tra lại.")

# ---------------------------------------------------------------------------
# GOM THEO BAN & GHI FILE (chu ho dung dau moi ho)
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_COLS = ["STT", "Họ và tên", "Ngày tháng năm sinh", "CMND/CCCD",
               "Địa chỉ", "Thành phần", "Trạng thái"]

ban_order, by_ban = [], {}
for k in order:
    slug = slugify_ban(hh[k]["ban"]) if hh[k]["ban"] else "khong_ro_ban"
    if slug not in by_ban:
        by_ban[slug] = {"ten_ban": hh[k]["ban"], "households": []}
        ban_order.append(slug)
    by_ban[slug]["households"].append(k)

files_created, tong_ket = [], []
for slug in ban_order:
    stt, out_rows, so_da_kham = 0, [], 0
    for k in by_ban[slug]["households"]:
        head = hh[k]["head"]
        group = ([head] if head else []) + hh[k]["members"]   # CHU HO DUNG DAU
        for p in group:
            if p["is_head"]:
                stt += 1
                stt_val = str(stt)
            else:
                stt_val = ""
            if p["status"] == "Đã khám":
                so_da_kham += 1
            out_rows.append({
                "STT": stt_val,
                "Họ và tên": p["name"],
                "Ngày tháng năm sinh": p["dob"],
                "CMND/CCCD": p["cccd"],
                "Địa chỉ": format_address(p["ban"], p["xa"]),
                "Thành phần": "Chủ hộ" if p["is_head"] else "Thành viên",
                "Trạng thái": p["status"],
            })
    df_out = pd.DataFrame(out_rows, columns=OUTPUT_COLS)
    path = os.path.join(OUTPUT_DIR, f"{slug}.csv")
    df_out.to_csv(path, index=False, encoding="utf-8-sig")
    files_created.append(path)
    tong_ket.append((by_ban[slug]["ten_ban"], slug, len(out_rows), stt, so_da_kham))

# ---------------------------------------------------------------------------
# IN KET QUA
# ---------------------------------------------------------------------------
print("=" * 64)
print("KẾT QUẢ XỬ LÝ")
print("=" * 64)
for ten_ban, slug, tong, so_ho, so_kham in tong_ket:
    print(f"• {ten_ban or '(thiếu bản)'}  ->  {slug}.csv")
    print(f"    Số hộ: {so_ho} | Tổng người: {tong} | Đã khám: {so_kham} | Chưa khám: {tong - so_kham}")

print("\n[LOG] Người THIẾU thông tin Bản:")
print("\n".join(thieu_ban) if thieu_ban else "  (không có)")

print("\n[ĐỐI CHIẾU / CẢNH BÁO]:")
print("\n".join(canh_bao) if canh_bao else "  Tất cả khớp sạch, không có cảnh báo.")

print(f"\nĐã ghi {len(files_created)} file:")
for p in files_created:
    print("  -", p)
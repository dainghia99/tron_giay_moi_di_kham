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
import csv
import unicodedata
from datetime import datetime
import pandas as pd

# ---------------------------------------------------------------------------
# CAU HINH
# ---------------------------------------------------------------------------
INPUT_DIR  = "."         
OUTPUT_DIR = "output"    

FILE_NGUOI_DAN = os.path.join(INPUT_DIR, "data/16_ban_muong_toong/muong_toong_1.csv")
FILE_KHAM      = os.path.join(INPUT_DIR, "data_kham.csv")

# File thong ke tong hop: moi ban 1 dong, cong don qua nhieu lan chay.
# Chay xong ban nao -> them/CAP NHAT DE dong cua ban do trong file nay.
FILE_THONG_KE  = os.path.join(INPUT_DIR, "thong_ke.csv")

# Tieu de cot GIU NGUYEN nhu file mau (chu y: 'Nhan khau...xong ' co 1 dau cach cuoi).
THONG_KE_COLS = [
    "STT", "Tên bản", "Số hộ", "Tổng số người", "Đã khám", "Chưa khám",
    "Số hộ đã khám xong (tính cả hộ)", "Nhân khẩu trong hộ đã khám xong ",
    "Số hộ bị lỗi", "Số hộ chuẩn", "Ghi chú",
]

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
# THONG KE: dung 1 dong ket qua cho 1 ban & ghi vao mau_thong_ke.csv
# ---------------------------------------------------------------------------
def _thong_ke_row(rec):
    """Doi 1 phan tu tong_ket -> dict theo dung cot cua file thong ke."""
    (ten_ban, slug, tong, so_ho, so_kham,
     so_ho_xong, so_ho_chua, khau_ho_xong, khau_ho_chua, so_ho_thieu, ghi_chu) = rec
    return {
        "Tên bản": ten_ban or "(thiếu bản)",
        "Số hộ": so_ho_xong + so_ho_chua,          # tong khoi ho (gom ca nhom thieu chu ho)
        "Tổng số người": tong,
        "Đã khám": so_kham,                          # so NGUOI da kham
        "Chưa khám": tong - so_kham,
        "Số hộ đã khám xong (tính cả hộ)": so_ho_xong,
        "Nhân khẩu trong hộ đã khám xong ": khau_ho_xong,
        "Số hộ bị lỗi": so_ho_thieu,                 # nhom khong tim thay dong chu ho
        "Số hộ chuẩn": so_ho,                        # so ho co chu ho (duoc danh STT)
        "Ghi chú": ghi_chu,
    }

def _canon_row(row):
    """Doc lai 1 dong cu tu file -> chuan hoa ve dung cot (chiu duoc lech dau cach/hoa thuong)."""
    lut = {re.sub(r"\s+", " ", str(k).strip()).casefold(): v for k, v in row.items()}
    def g(col):
        return lut.get(re.sub(r"\s+", " ", col.strip()).casefold(), "")
    return {c: g(c) for c in THONG_KE_COLS}

def ghi_thong_ke(tong_ket, path=FILE_THONG_KE):
    """Ghi ket qua vao file thong ke: moi ban 1 dong, cong don qua cac lan chay.
    Neu ban da co trong file -> CAP NHAT DE dong cu (giu nguyen vi tri). STT danh lai 1..N."""
    existing, order = {}, []          # ten_ban -> dict dong ; thu tu xuat hien
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ten = re.sub(r"\s+", " ", str(row.get("Tên bản", "")).strip())
                if ten == "":
                    continue
                if ten not in existing:
                    order.append(ten)
                existing[ten] = _canon_row(row)

    so_moi, so_cap_nhat = 0, 0
    for rec in tong_ket:
        d = _thong_ke_row(rec)
        ten = d["Tên bản"]
        if ten in existing:
            so_cap_nhat += 1
        else:
            order.append(ten)
            so_moi += 1
        existing[ten] = d

    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=THONG_KE_COLS, extrasaction="ignore")
        w.writeheader()
        for i, ten in enumerate(order, start=1):
            r = dict(existing[ten])
            r["STT"] = i
            w.writerow({c: r.get(c, "") for c in THONG_KE_COLS})
    return path, len(order), so_moi, so_cap_nhat

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
        canh_bao.append(f"  ⚠ {ten}-{nam}: {len(cand)} bản ghi khám trùng Họ tên+Năm sinh -> 'Đã khám'.")
        return "Đã khám"
    return "Chưa khám"

# ---------------------------------------------------------------------------
# XU LY
# ---------------------------------------------------------------------------
persons = read_nguoi_dan(FILE_NGUOI_DAN)   # CHUA loc xa, giu nguyen thu tu goc de gom khoi cho dung

canh_bao, thieu_ban = [], []
for p in persons:
    p["status"] = tra_trang_thai(p["cccd"], p["name"], p["year"], canh_bao)

# ---------------------------------------------------------------------------
# GOM HO THEO TEN CHU HO (vi tri dong chi de PHAN GIAI khi trung ten)
# ---------------------------------------------------------------------------
# Bai hoc: file goc KHONG bao dam cac dong cung ho nam sat nhau. Vi du co ho
# 1 nguoi (chi co chu ho) chen giua chu ho va cac thanh vien cua ho khac:
#     MUA A SINH (chu ho)  <- ho A
#     MUA A THONG (chu ho)  <- ho B, 1 nguoi, chen vao giua
#     MUA A LONG ... (thanh vien, chu ho = MUA A SINH)  <- van thuoc ho A
# Neu chi gan theo "khoi dang mo gan nhat" thi cac thanh vien nay se khong tim
# duoc chu ho MUA A SINH (da di qua) -> sai.
#
# Tin hieu DANG TIN duy nhat la cot 'Ho ten chu ho'. Vi vay:
#   1) Moi dong CHU HO (Ho ten == Ho ten chu ho) mo mot HO rieng, nho vi tri dong.
#   2) Moi THANH VIEN duoc gan vao chu ho CUNG TEN o GAN NHAT theo khoang cach dong;
#      neu bang nhau thi uu tien chu ho o PHIA TREN (giai quyet trung ten chu ho,
#      vi du hai nguoi cung ten 'Dang Duc Phuc').
#   3) Thanh vien khong co chu ho cung ten nao -> nhom "mo coi" (canh bao, khong STT).

order, hh = [], {}

heads_by_name = {}   # norm_key(ten chu ho) -> list vi tri (index trong persons)
for idx, p in enumerate(persons):
    if p["is_head"]:
        key = ("H", idx)
        hh[key] = {"head": p, "chu_ho_text": p["name"], "members": [], "ban": p["ban"]}
        order.append(key)
        p["ho_key"] = key
        heads_by_name.setdefault(norm_key(p["name"]), []).append(idx)

for idx, p in enumerate(persons):
    if p["is_head"]:
        continue
    cands = heads_by_name.get(norm_key(p["chu_ho"]), [])
    if cands:
        # Chon chu ho GAN NHAT; neu hoa khoang cach -> uu tien chu ho o PHIA TREN.
        best_idx = min(cands, key=lambda h: (abs(h - idx), 0 if h < idx else 1))
        key = ("H", best_idx)
        hh[key]["members"].append(p)
        p["ho_key"] = key
    else:
        # Mo coi: khong tim thay dong chu ho cung ten -> gom chung theo ten chu ho.
        okey = ("O", norm_key(p["chu_ho"]))
        if okey not in hh:
            hh[okey] = {"head": None, "chu_ho_text": p["chu_ho"], "members": [], "ban": p["ban"]}
            order.append(okey)
        hh[okey]["members"].append(p)
        p["ho_key"] = okey

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
    so_ho_xong, so_ho_chua = 0, 0        # dem theo HO trong ban nay
    khau_ho_xong, khau_ho_chua = 0, 0    # so khau (nhan khau) THUOC cac ho tuong ung
    so_ho_thieu_chu = 0                  # so khoi ho KHONG tim thay dong chu ho
    ghi_chu_ban = []                     # noi dung cot "Ghi chu" cho ban nay
    for k in by_ban[slug]["households"]:
        head = hh[k]["head"]
        if head is None:
            so_ho_thieu_chu += 1
            ghi_chu_ban.append(f"{hh[k]['chu_ho_text']} Không tìm thấy thông tin chi tiết chủ hộ ")
        group = ([head] if head else []) + hh[k]["members"]   # CHU HO DUNG DAU
        # HO "da kham xong" = TAT CA nguoi trong ho deu "Da kham";
        # nguoc lai (con it nhat 1 nguoi chua kham) = "chua kham".
        if group and all(p["status"] == "Đã khám" for p in group):
            so_ho_xong += 1
            khau_ho_xong += len(group)
        else:
            so_ho_chua += 1
            khau_ho_chua += len(group)
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
    ghi_chu = "; ".join(ghi_chu_ban)
    tong_ket.append((by_ban[slug]["ten_ban"], slug, len(out_rows), stt, so_da_kham,
                     so_ho_xong, so_ho_chua, khau_ho_xong, khau_ho_chua, so_ho_thieu_chu,
                     ghi_chu))

# ---------------------------------------------------------------------------
# IN KET QUA
# ---------------------------------------------------------------------------
print("=" * 64)
print("KẾT QUẢ XỬ LÝ")
print("=" * 64)
for (ten_ban, slug, tong, so_ho, so_kham,
     so_ho_xong, so_ho_chua, khau_ho_xong, khau_ho_chua, so_ho_thieu, ghi_chu) in tong_ket:
    tong_ho = so_ho_xong + so_ho_chua        # tong so KHOI HO (= xong + chua)
    print(f"• {ten_ban or '(thiếu bản)'}  ->  {slug}.csv")
    if so_ho_thieu:
        print(f"    Số hộ: {tong_ho} ({so_ho} hộ có chủ hộ được đánh STT "
              f"+ {so_ho_thieu} nhóm THIẾU chủ hộ không có thông tin chi tiết của chủ hộ) | Tổng người: {tong}")
    else:
        print(f"    Số hộ: {tong_ho} | Tổng người: {tong}")
    print(f"    Trạng thái cá nhân → Đã khám: {so_kham} | Chưa khám: {tong - so_kham}")
    print(f"    ├─ ĐÃ KHÁM XONG : {so_ho_xong} hộ | {khau_ho_xong} khẩu (nhân khẩu trong các hộ này)")
    # print(f"    └─ CHƯA KHÁM    : {so_ho_chua} hộ | {khau_ho_chua} khẩu (nhân khẩu trong các hộ này)")

print("\n[LOG] Người THIẾU thông tin Bản:")
print("\n".join(thieu_ban) if thieu_ban else "  (không có)")

print("\n[ĐỐI CHIẾU / CẢNH BÁO]:")
print("\n".join(canh_bao) if canh_bao else "  Tất cả khớp sạch, không có cảnh báo.")

print(f"\nĐã ghi {len(files_created)} file:")
for p in files_created:
    print("  -", p)

# ---------------------------------------------------------------------------
# GHI THONG KE TONG HOP (moi ban 1 dong, cong don qua cac lan chay)
# ---------------------------------------------------------------------------
tk_path, tk_tong, tk_moi, tk_capnhat = ghi_thong_ke(tong_ket)
print("\n" + "─" * 64)
print(f"[THỐNG KÊ] Đã cập nhật '{tk_path}': "
      f"+{tk_moi} bản mới, {tk_capnhat} bản ghi đè, tổng {tk_tong} dòng.")
print("─" * 64)
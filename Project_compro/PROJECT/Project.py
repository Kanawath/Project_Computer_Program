import struct
import os
import datetime

# ---------------- Struct definitions (little-endian '<') ----------------
BOOK_STRUCT = struct.Struct("<i100s100s100si50s50s20si")
MEMBER_STRUCT = struct.Struct("<i100s10s1s200s15s100s10s")
BORROW_STRUCT = struct.Struct("<ii10s10s10s20sf200s")

BOOK_FILE = "books.dat"
MEMBER_FILE = "members.dat"
BORROW_FILE = "borrows.dat"

# ---------------- Helpers: packing/unpacking fixed-length strings ----------------
def pack_str(s: str, length: int) -> bytes:
    if s is None:
        s = ""
    b = s.encode("utf-8")[:length]
    return b.ljust(length, b'\x00')

def unpack_str(b: bytes) -> str:
    return b.decode("utf-8", errors="ignore").rstrip(" \x00")

# ---------------- Input validators ----------------
def get_int(prompt: str, minv=None, maxv=None) -> int:
    while True:
        v = input(prompt).strip()
        if v == "":
            print("กรุณากรอกข้อมูล")
            continue
        try:
            n = int(v)
        except ValueError:
            print(" ต้องกรอกตัวเลขจำนวนเต็มเท่านั้น — ลองใหม่")
            continue
        if minv is not None and n < minv:
            print(f" ค่าต้อง >= {minv}")
            continue
        if maxv is not None and n > maxv:
            print(f" ค่าต้อง <= {maxv}")
            continue
        return n

def get_float(prompt: str, minv=None, maxv=None) -> float:
    while True:
        v = input(prompt).strip()
        if v == "":
            print("กรุณากรอกข้อมูล")
            continue
        try:
            f = float(v)
        except ValueError:
            print(" ต้องกรอกตัวเลข (ทศนิยมได้) เท่านั้น — ลองใหม่")
            continue
        if minv is not None and f < minv:
            print(f" ค่าต้อง >= {minv}")
            continue
        if maxv is not None and f > maxv:
            print(f" ค่าต้อง <= {maxv}")
            continue
        return f

def get_date(prompt: str, allow_empty=False) -> str:
    while True:
        s = input(prompt).strip()
        if allow_empty and s == "":
            return ""
        try:
            datetime.datetime.strptime(s, "%Y-%m-%d")
            return s
        except Exception:
            print(" รูปแบบวันที่ต้องเป็น YYYY-MM-DD เช่น 2025-09-07")

def get_str(prompt: str, maxlen: int, allow_empty=False) -> str:
    while True:
        s = input(prompt).rstrip()
        if not allow_empty and s == "":
            print(" ห้ามเว้นว่าง — ลองใหม่")
            continue
        if len(s.encode("utf-8")) > maxlen:
            print(f" ความยาวเกิน {maxlen} bytes — จะถูกตัด")
            s = s.encode('utf-8')[:maxlen].decode('utf-8', 'ignore')
        return s

# ---------------- File operations ----------------
def add_record(filename: str, st: struct.Struct, packed_tuple: tuple):
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "ab") as f:
        f.write(st.pack(*packed_tuple))

def read_raw_records(filename: str, st: struct.Struct):
    records = []
    if not os.path.exists(filename):
        return records
    size = st.size
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(size)
            if not chunk:
                break
            if len(chunk) != size:
                break
            records.append(st.unpack(chunk))
    return records

def write_raw_records(filename: str, st: struct.Struct, records: list):
    with open(filename, "wb") as f:
        for r in records:
            f.write(st.pack(*r))

# ---------------- Conversion helpers ----------------
def decode_record(raw_tuple):
    return tuple(unpack_str(x) if isinstance(x, (bytes, bytearray)) else x for x in raw_tuple)

# ---------------- Book & Member operations (Update/Delete included for completeness) ----------------
def add_book():
    print("\n== Add Book ==")
    book_id = get_int("Book ID (ตัวเลข): ")
    if any(b[0] == book_id for b in read_raw_records(BOOK_FILE, BOOK_STRUCT)):
        print(" Book ID นี้มีอยู่แล้ว")
        return
    title = get_str("Title: ", 100)
    author = get_str("Author: ", 100, allow_empty=True)
    publisher = get_str("Publisher: ", 100, allow_empty=True)
    year_pub = get_int("Year (เช่น 2023): ", 0, 9999)
    category = get_str("Category: ", 50, allow_empty=True)
    language = get_str("Language: ", 50, allow_empty=True)
    shelf_no = get_str("Shelf No.: ", 20, allow_empty=True)
    total_copies = get_int("Total copies: ", 0)
    packed = (
        book_id, pack_str(title, 100), pack_str(author, 100), pack_str(publisher, 100),
        year_pub, pack_str(category, 50), pack_str(language, 50),
        pack_str(shelf_no, 20), total_copies
    )
    add_record(BOOK_FILE, BOOK_STRUCT, packed)
    print(" เพิ่มหนังสือสำเร็จ")

def view_books():
    print("\n== View Books ==")
    raws = read_raw_records(BOOK_FILE, BOOK_STRUCT)
    if not raws:
        print("ไม่มีข้อมูลหนังสือ")
        return
    print(f"{'ID':<6} {'Title':<30} {'Author':<20} {'Year':<6} {'Copies':<6}")
    print("-" * 80)
    for r in raws:
        rr = decode_record(r)
        print(f"{rr[0]:<6} {rr[1][:30]:<30} {rr[2][:20]:<20} {rr[4]:<6} {rr[8]:<6}")

def update_book():
    print("\n== Update Book ==")
    book_id = get_int("Book ID ที่ต้องการแก้ไข: ")
    raws = read_raw_records(BOOK_FILE, BOOK_STRUCT)
    found = False
    for idx, r in enumerate(raws):
        if r[0] == book_id:
            found = True
            rr = decode_record(r)
            print("ข้อมูลเดิม:", rr)
            # ... (Logic to get new values)
            new_title = get_str("New Title (Enter=ไม่เปลี่ยน): ", 100, allow_empty=True) or rr[1]
            new_author = get_str("New Author (Enter=ไม่เปลี่ยน): ", 100, allow_empty=True) or rr[2]
            # ... (Rest of the fields)
            raws[idx] = (
                book_id, pack_str(new_title, 100), pack_str(new_author, 100), r[3], r[4], r[5], r[6], r[7], r[8]
            ) # Simplified for brevity
            write_raw_records(BOOK_FILE, BOOK_STRUCT, raws)
            print(" แก้ไขเรียบร้อย")
            break
    if not found:
        print(" ไม่พบ Book ID")

def delete_book():
    print("\n== Delete Book ==")
    book_id = get_int("Book ID ที่ต้องการลบ: ")
    raws = read_raw_records(BOOK_FILE, BOOK_STRUCT)
    new_raws = [r for r in raws if r[0] != book_id]
    if len(raws) == len(new_raws):
        print(" ไม่พบ Book ID")
    else:
        write_raw_records(BOOK_FILE, BOOK_STRUCT, new_raws)
        print(" ลบสำเร็จ")

def add_member():
    print("\n== Add Member ==")
    member_id = get_int("Member ID (ตัวเลข): ")
    if any(m[0] == member_id for m in read_raw_records(MEMBER_FILE, MEMBER_STRUCT)):
        print(" Member ID นี้มีอยู่แล้ว")
        return
    name = get_str("Name Surname: ", 100)
    birth_date = get_date("Birth date (YYYY-MM-DD): ")
    gender = get_str("Gender (M/F/O): ", 1)
    address = get_str("Address: ", 200, allow_empty=True)
    mobile = get_str("Mobile: ", 15, allow_empty=True)
    email = get_str("Email: ", 100, allow_empty=True)
    reg_date = get_date("Reg date (YYYY-MM-DD): ")
    packed = (
        member_id, pack_str(name, 100), pack_str(birth_date, 10), pack_str(gender, 1),
        pack_str(address, 200), pack_str(mobile, 15), pack_str(email, 100),
        pack_str(reg_date, 10)
    )
    add_record(MEMBER_FILE, MEMBER_STRUCT, packed)
    print(" เพิ่มสมาชิกสำเร็จ")

def view_members():
    print("\n== View Members ==")
    raws = read_raw_records(MEMBER_FILE, MEMBER_STRUCT)
    if not raws:
        print("ไม่มีข้อมูลสมาชิก")
        return
    print(f"{'ID':<6} {'Name':<25} {'Birth Date':<12} {'Mobile':<15} {'Email':<25}")
    print("-" * 90)
    for r in raws:
        rr = decode_record(r)
        print(f"{rr[0]:<6} {rr[1][:25]:<25} {rr[2]:<12} {rr[5]:<15} {rr[6][:25]:<25}")

def update_member():
    print("\n== Update Member ==")
    member_id = get_int("Member ID ที่ต้องการแก้ไข: ")
    raws = read_raw_records(MEMBER_FILE, MEMBER_STRUCT)
    found = False
    for idx, r in enumerate(raws):
        if r[0] == member_id:
            found = True
            rr = decode_record(r)
            print("ข้อมูลเดิม:", rr)
            # ... (Logic to get new values)
            new_name = get_str("New Name (Enter=ไม่เปลี่ยน): ", 100, allow_empty=True) or rr[1]
            # ... (Rest of the fields)
            raws[idx] = (
                member_id, pack_str(new_name, 100), r[2], r[3], r[4], r[5], r[6], r[7]
            ) # Simplified for brevity
            write_raw_records(MEMBER_FILE, MEMBER_STRUCT, raws)
            print(" แก้ไขข้อมูลสมาชิกเรียบร้อย")
            break
    if not found:
        print(" ไม่พบ Member ID")


def delete_member():
    print("\n== Delete Member ==")
    member_id = get_int("Member ID ที่ต้องการลบ: ")
    raws = read_raw_records(MEMBER_FILE, MEMBER_STRUCT)
    new_raws = [r for r in raws if r[0] != member_id]
    if len(raws) == len(new_raws):
        print(" ไม่พบ Member ID")
    else:
        write_raw_records(MEMBER_FILE, MEMBER_STRUCT, new_raws)
        print(" ลบข้อมูลสมาชิกสำเร็จ")


# ---------------- Borrows (REWRITTEN) ----------------

def add_borrow():
    print("\n== Add Borrow (Multiple books) ==")
    member_id = get_int("Member ID: ")
    if not any(r[0] == member_id for r in read_raw_records(MEMBER_FILE, MEMBER_STRUCT)):
        print(" ไม่พบ Member ID")
        return
    
    books_to_borrow = []
    while True:
        book_id_str = input(f"Book ID ที่จะยืม (สำหรับ Member {member_id}) (พิมพ์ 'done' เพื่อสิ้นสุด): ").strip().lower()
        if book_id_str == 'done':
            if not books_to_borrow:
                print("ยังไม่ได้เพิ่มหนังสือเลย ยกเลิกการยืม")
            break
        
        try:
            book_id = int(book_id_str)
            if not any(b[0] == book_id for b in read_raw_records(BOOK_FILE, BOOK_STRUCT)):
                print(f" ไม่พบ Book ID {book_id}")
                continue
            books_to_borrow.append(book_id)
            print(f"  เพิ่ม Book ID {book_id} ในรายการ")
        except ValueError:
            print(" ต้องกรอก Book ID เป็นตัวเลข")

    if books_to_borrow:
        date_out = get_date("Date out (YYYY-MM-DD) สำหรับหนังสือทั้งหมด: ")
        date_due = get_date("Date due (YYYY-MM-DD) สำหรับหนังสือทั้งหมด: ")
        
        for book_id in books_to_borrow:
            packed = (
                member_id, book_id, pack_str(date_out, 10), pack_str(date_due, 10),
                pack_str("", 10), pack_str("Borrow", 20), 0.0, pack_str("", 200)
            )
            add_record(BORROW_FILE, BORROW_STRUCT, packed)
        print(f"\nเพิ่มการยืมหนังสือ {len(books_to_borrow)} เล่มสำหรับ Member ID {member_id} สำเร็จ")

def view_borrows():
    print("\n== View Borrows (Grouped) ==")
    borrows_raw = read_raw_records(BORROW_FILE, BORROW_STRUCT)
    if not borrows_raw:
        print("ไม่มีข้อมูลการยืม")
        return

    grouped_borrows = {}
    for r in borrows_raw:
        rr = decode_record(r)
        member_id = rr[0]
        if member_id not in grouped_borrows:
            grouped_borrows[member_id] = []
        grouped_borrows[member_id].append(rr)

    members_map = {m[0]: decode_record(m) for m in read_raw_records(MEMBER_FILE, MEMBER_STRUCT)}
    books_map = {b[0]: decode_record(b) for b in read_raw_records(BOOK_FILE, BOOK_STRUCT)}

    for member_id, borrows in grouped_borrows.items():
        member_info = members_map.get(member_id, (None, "Unknown Member"))
        print("-" * 80)
        print(f"Member ID: {member_id} | Name: {member_info[1]}")
        print(f"{'':<4}{'BookID':<7} | {'Title':<40} | {'Status'}")
        
        for borrow_item in borrows:
            book_id = borrow_item[1]
            book_info = books_map.get(book_id, (None, "Unknown Book"))
            title = book_info[1]
            status = borrow_item[5]
            print(f"{'':<4}{book_id:<7} | {title[:40]:<40} | {status}")
    print("-" * 80)

def update_borrow():
    print("\n== Update Borrow Record ==")
    view_borrows() # แสดงข้อมูลทั้งหมดก่อน
    borrows_raw = read_raw_records(BORROW_FILE, BORROW_STRUCT)
    if not borrows_raw:
        return

    member_id_to_edit = get_int("ใส่ Member ID ที่ต้องการแก้ไข: ")
    
    # กรองรายการยืมเฉพาะของสมาชิกคนนี้
    member_borrows_raw = [r for r in borrows_raw if r[0] == member_id_to_edit]
    if not member_borrows_raw:
        print(f"ไม่พบรายการยืมสำหรับ Member ID {member_id_to_edit}")
        return

    books_map = {b[0]: decode_record(b) for b in read_raw_records(BOOK_FILE, BOOK_STRUCT)}
    print(f"\nรายการหนังสือสำหรับ Member ID {member_id_to_edit}:")
    for i, r in enumerate(member_borrows_raw):
        rr = decode_record(r)
        book_info = books_map.get(rr[1], (None, "Unknown Book"))
        print(f"  {i+1}: Book ID {rr[1]} ({book_info[1][:30]}) - Status: {rr[5]}")

    rec_num = get_int("เลือกลำดับหนังสือที่ต้องการแก้ไข: ", minv=1, maxv=len(member_borrows_raw))
    record_to_update_raw = member_borrows_raw[rec_num - 1]
    
    # หา index ของ record นี้ใน list ดั้งเดิมทั้งหมด
    original_index = -1
    for i, r in enumerate(borrows_raw):
        if r == record_to_update_raw:
            original_index = i
            break
            
    if original_index == -1:
        print("เกิดข้อผิดพลาด: ไม่พบข้อมูลที่ต้องการแก้ไขในไฟล์หลัก")
        return
    
    rr = decode_record(record_to_update_raw)
    print("\nข้อมูลเดิม:", rr)
    
    new_date_out = get_date("New Date Out (Enter=ไม่เปลี่ยน): ", allow_empty=True) or rr[2]
    new_date_due = get_date("New Date Due (Enter=ไม่เปลี่ยน): ", allow_empty=True) or rr[3]
    new_date_return = get_date("New Date Return (Enter=ไม่เปลี่ยน): ", allow_empty=True) or rr[4]
    new_status = get_str("New Status (Enter=ไม่เปลี่ยน): ", 20, allow_empty=True) or rr[5]
    
    new_fine_str = input(f"New Fine (Enter=ไม่เปลี่ยน, Current={rr[6]}): ").strip()
    fine_amount = float(new_fine_str) if new_fine_str else rr[6]
            
    new_notes = get_str("New Notes (Enter=ไม่เปลี่ยน): ", 200, allow_empty=True) or rr[7]
    
    new_packed = (
        rr[0], rr[1],
        pack_str(new_date_out, 10), pack_str(new_date_due, 10), pack_str(new_date_return, 10),
        pack_str(new_status, 20), fine_amount, pack_str(new_notes, 200)
    )
    
    borrows_raw[original_index] = new_packed
    write_raw_records(BORROW_FILE, BORROW_STRUCT, borrows_raw)
    print(" แก้ไขข้อมูลการยืมเรียบร้อย")

def delete_borrow():
    print("\n== Delete Borrow Record ==")
    view_borrows() # แสดงข้อมูลทั้งหมดก่อน
    borrows_raw = read_raw_records(BORROW_FILE, BORROW_STRUCT)
    if not borrows_raw:
        return

    member_id_to_delete = get_int("ใส่ Member ID ที่ต้องการลบรายการ: ")
    
    member_borrows_raw = [r for r in borrows_raw if r[0] == member_id_to_delete]
    if not member_borrows_raw:
        print(f"ไม่พบรายการยืมสำหรับ Member ID {member_id_to_delete}")
        return

    books_map = {b[0]: decode_record(b) for b in read_raw_records(BOOK_FILE, BOOK_STRUCT)}
    print(f"\nรายการหนังสือสำหรับ Member ID {member_id_to_delete}:")
    for i, r in enumerate(member_borrows_raw):
        rr = decode_record(r)
        book_info = books_map.get(rr[1], (None, "Unknown Book"))
        print(f"  {i+1}: Book ID {rr[1]} ({book_info[1][:30]}) - Status: {rr[5]}")

    rec_num = get_int("เลือกลำดับหนังสือที่ต้องการลบ: ", minv=1, maxv=len(member_borrows_raw))
    record_to_delete_raw = member_borrows_raw[rec_num - 1]

    confirm = input(f"ต้องการลบรายการยืมนี้ใช่หรือไม่? (y/n): ").strip().lower()
    if confirm == 'y':
        borrows_raw.remove(record_to_delete_raw)
        write_raw_records(BORROW_FILE, BORROW_STRUCT, borrows_raw)
        print(" ลบข้อมูลการยืมสำเร็จ")
    else:
        print("ยกเลิกการลบ")

# ---------------- Report ----------------
def generate_report():
    print("\nGenerating reports...")
    books_raw = read_raw_records(BOOK_FILE, BOOK_STRUCT)
    books = [decode_record(r) for r in books_raw]
    books_map = {b[0]: b for b in books}
    
    members_map = {m[0]: decode_record(m) for m in read_raw_records(MEMBER_FILE, MEMBER_STRUCT)}
    borrows_raw = read_raw_records(BORROW_FILE, BORROW_STRUCT)
    borrows = [decode_record(r) for r in borrows_raw]
    
    now = datetime.datetime.now()

    with open("books_report.txt", "w", encoding="utf-8") as f:
        # ... (same as before)
        f.write("Library Borrow System – Book Summary Report\n")
        f.write(f"Generated At : {now.strftime('%Y-%m-%d %H:%M')} (+07:00)\n\n")
        f.write(f"{'BookID':<6} | {'Title':<30} | {'Author':<20} | {'Year':<5} | {'Copies':<7} | {'Borrowed':<9} | {'Status'}\n")
        f.write("-" * 95 + "\n")
        borrowed_counts = {b_id: 0 for b_id in books_map.keys()}
        active_borrows_list = [br for br in borrows if br[5].lower() == 'borrow']
        for br in active_borrows_list:
            book_id = br[1]
            if book_id in borrowed_counts:
                borrowed_counts[book_id] += 1
        total_copies_sum = sum(b[8] for b in books)
        for b in books:
            book_id, title, author, _, year, _, _, _, total_copies = b
            borrowed = borrowed_counts.get(book_id, 0)
            f.write(f"{book_id:<6} | {title[:30]:<30} | {author[:20]:<20} | {str(year):<5} | {total_copies:<7} | {borrowed:<9} | {'Active'}\n")
        f.write("\n\nSummary (Active Books Only)\n")
        f.write(f"- Total Book Titles : {len(books)}\n")
        f.write(f"- Total Copies      : {total_copies_sum}\n")
        f.write(f"- Borrowed Now      : {sum(borrowed_counts.values())}\n")
        f.write(f"- Available Now     : {total_copies_sum - sum(borrowed_counts.values())}\n")

    with open("borrows_report.txt", "w", encoding="utf-8") as f:
        # ... (same as before, grouped)
        f.write("Library Borrow System – Borrowed Report\n")
        f.write(f"Generated At : {now.strftime('%Y-%m-%d %H:%M')} (+07:00)\n\n")
        grouped_borrows = {}
        for br in active_borrows_list:
            member_id = br[0]
            if member_id not in grouped_borrows:
                grouped_borrows[member_id] = []
            grouped_borrows[member_id].append(br)
        for member_id, borrows_list in grouped_borrows.items():
            member_info = members_map.get(member_id)
            if not member_info: continue
            f.write("-" * 120 + "\n")
            f.write(f"MemberID: {member_id:<5} | Name: {member_info[1]:<30} | Email: {member_info[6]}\n")
            f.write(f"{'':<4}{'BookID':<7} | {'Title':<40} | {'Author':<20} | {'Date Out':<12} | {'Due Date':<12} | {'Fine'}\n")
            f.write(f"{'':<4}{'-'*110}\n")
            for item in borrows_list:
                book_id, book_info = item[1], books_map.get(item[1], (None, "N/A", "N/A"))
                title, author = book_info[1], book_info[2]
                date_out, date_due, fine = item[2], item[3], item[6]
                f.write(f"{'':<4}{book_id:<7} | {title[:40]:<40} | {author[:20]:<20} | {date_out:<12} | {date_due:<12} | {fine:.2f}\n")
            f.write("\n")
        f.write("-" * 120 + "\n")
        f.write("Summary (Borrowed Only)\n")
        f.write(f"- Total Borrowed Books : {len(active_borrows_list)}\n")
        f.write(f"- Members with Borrows : {len(grouped_borrows)}\n")

    print(" รายงานถูกสร้าง: books_report.txt, borrows_report.txt")

# ---------------- Menu ----------------
def main_menu():
    while True:
        print("\n===== Library System =====")
        print("1. Books")
        print("2. Members")
        print("3. Borrows")
        print("4. Generate Report")
        print("0. Exit")
        c = input("เลือก: ").strip()
        if c == "1":
            # ... (Book Menu)
            while True:
                print("\n-- Books Menu --")
                print("1. Add Book")
                print("2. View Books")
                print("3. Update Book")
                print("4. Delete Book")
                print("0. Back")
                cc = input("เลือก: ").strip()
                if cc == "1": add_book()
                elif cc == "2": view_books()
                elif cc == "3": update_book()
                elif cc == "4": delete_book()
                elif cc == "0": break
        elif c == "2":
            # ... (Member Menu)
            while True:
                print("\n-- Members Menu --")
                print("1. Add Member")
                print("2. View Members")
                print("3. Update Member")
                print("4. Delete Member")
                print("0. Back")
                cc = input("เลือก: ").strip()
                if cc == "1": add_member()
                elif cc == "2": view_members()
                elif cc == "3": update_member()
                elif cc == "4": delete_member()
                elif cc == "0": break
        elif c == "3":
            while True:
                print("\n-- Borrows Menu --")
                print("1. Add Borrow")
                print("2. View Borrows")
                print("3. Update Borrow")
                print("4. Delete Borrow")
                print("0. Back")
                cc = input("เลือก: ").strip()
                if cc == "1": add_borrow()
                elif cc == "2": view_borrows()
                elif cc == "3": update_borrow()
                elif cc == "4": delete_borrow()
                elif cc == "0": break
                else: print(" เลือกไม่ถูกต้อง")
        elif c == "4":
            generate_report()
        elif c == "0":
            print("Bye")
            break
        else:
            print(" เลือกไม่ถูกต้อง")

if __name__ == "__main__":
    main_menu()
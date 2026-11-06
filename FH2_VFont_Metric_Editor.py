# -*- coding: utf-8 -*-
"""
FH2 VFont Metric Editor — independent experimental tool.
Parser is written from scratch for the FH2 Verdana VFONT record layout
verified against the supplied original and metric-test files.

Safety:
- Opens a VFONT as bytes.
- Locates Cyrillic character records by their Unicode scalar stored in the
  record table and validates the 28-byte record stride.
- Changes ONLY the 32-bit float at record + 4 (advance candidate).
- Saves to a new file; never overwrites the source unless the user explicitly
  chooses the same path.
- Does not rebuild geometry, indices, glyph count, or container structure.
"""
import math
import os
import struct
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

RECORD_SIZE = 28
ADVANCE_OFFSET = 4
TABLE_OFFSET = 0xC0
COUNT_OFFSET = 0x80
MIN_ADVANCE = 0.02
MAX_ADVANCE = 2.50

def is_plausible_advance(value):
    return math.isfinite(value) and MIN_ADVANCE <= value <= MAX_ADVANCE

class VFontDocument:
    """Conservative FH2 Verdana reader: reads every entry in the 28-byte glyph table."""
    def __init__(self, path, data):
        self.path = path
        self.data = bytearray(data)
        self.glyphs = self._parse_all_records()

    def _parse_all_records(self):
        if len(self.data) < COUNT_OFFSET + 4:
            raise ValueError("Файл слишком мал: отсутствует поле количества глифов.")
        count = struct.unpack_from("<I", self.data, COUNT_OFFSET)[0]
        if not (1 <= count <= 4096):
            raise ValueError(f"Недопустимое число записей в заголовке: {count}.")
        table_end = TABLE_OFFSET + count * RECORD_SIZE
        if table_end > len(self.data):
            raise ValueError(
                f"Таблица глифов выходит за границы файла "
                f"(ожидалось до 0x{table_end:X}, размер 0x{len(self.data):X})."
            )

        found = {}
        for index in range(count):
            pos = TABLE_OFFSET + index * RECORD_SIZE
            cp = struct.unpack_from("<I", self.data, pos)[0]
            adv = struct.unpack_from("<f", self.data, pos + ADVANCE_OFFSET)[0]

            if cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
                raise ValueError(
                    f"Некорректный Unicode-код в записи {index}: U+{cp:04X}. "
                    "Файл не изменён."
                )
            if cp in found:
                raise ValueError(f"Повторяющийся код U+{cp:04X} в таблице глифов.")
            if not is_plausible_advance(adv):
                raise ValueError(
                    f"Подозрительное значение Advance у U+{cp:04X}: {adv!r}. "
                    "Файл не изменён."
                )
            found[cp] = {"offset": pos, "original": adv, "value": adv, "index": index}

        if len(found) != count:
            raise ValueError("Не все записи таблицы удалось прочитать.")
        return found

    def set_advance(self, cp, value):
        if cp not in self.glyphs:
            raise KeyError(cp)
        if not is_plausible_advance(value):
            raise ValueError("Advance должен быть в диапазоне 0.02–2.50.")
        pos = self.glyphs[cp]["offset"] + ADVANCE_OFFSET
        struct.pack_into("<f", self.data, pos, float(value))
        self.glyphs[cp]["value"] = float(value)

    def reset_glyph(self, cp):
        self.set_advance(cp, self.glyphs[cp]["original"])

    def save(self, path):
        with open(path, "wb") as f:
            f.write(self.data)

def char_name(cp):
    try:
        ch = chr(cp)
        if cp < 0x20 or cp == 0x7F:
            return f"<U+{cp:04X}>"
        return ch
    except ValueError:
        return "?"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FH2 VFONT Metric Editor 0.3 — все глифы")
        self.geometry("1120x760")
        self.minsize(900, 620)
        self.doc = None
        self.reference = None
        self.selected_cp = None
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Button(top, text="Открыть VFONT…", command=self.open_file).pack(side="left")
        ttk.Button(top, text="Открыть оригинал для сравнения…", command=self.open_reference).pack(side="left", padx=6)
        ttk.Button(top, text="Сохранить как…", command=self.save_as).pack(side="left", padx=6)
        self.file_label = ttk.Label(top, text="Файл не открыт")
        self.file_label.pack(side="left", padx=12)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=(0,8))
        left = ttk.Frame(body, padding=6)
        right = ttk.Frame(body, padding=8)
        body.add(left, weight=1)
        body.add(right, weight=3)

        ttk.Label(left, text="Все глифы VFONT", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        filter_row = ttk.Frame(left)
        filter_row.pack(fill="x", pady=(4,2))
        ttk.Label(filter_row, text="Фильтр:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.populate_tree())
        ttk.Entry(filter_row, textvariable=self.filter_var).pack(side="left", fill="x", expand=True, padx=4)
        self.count_label = ttk.Label(left, text="—")
        self.count_label.pack(anchor="w")
        self.tree = ttk.Treeview(left, columns=("cp","unicode","advance","delta"), show="headings", height=24)
        self.tree.heading("cp", text="Глиф")
        self.tree.heading("unicode", text="Unicode")
        self.tree.heading("advance", text="Advance")
        self.tree.heading("delta", text="Δ")
        self.tree.column("cp", width=54, anchor="center")
        self.tree.column("unicode", width=76, anchor="center")
        self.tree.column("advance", width=82, anchor="e")
        self.tree.column("delta", width=72, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.status = ttk.Label(left, text="Откройте VFONT.", wraplength=250)
        self.status.pack(anchor="w", pady=4)

        ttk.Label(right, text="Настройка выбранной буквы", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.glyph_title = ttk.Label(right, text="—", font=("Segoe UI", 22, "bold"))
        self.glyph_title.pack(anchor="w", pady=(8,2))
        self.metric_info = ttk.Label(right, text="Исходное значение: —    Текущее значение: —")
        self.metric_info.pack(anchor="w")

        controls = ttk.Frame(right)
        controls.pack(fill="x", pady=12)
        ttk.Label(controls, text="Advance:").grid(row=0,column=0,sticky="w")
        self.value_var = tk.DoubleVar(value=0.5)
        self.scale = ttk.Scale(controls, from_=0.05, to=1.5, variable=self.value_var, command=self.on_scale)
        self.scale.grid(row=0,column=1,sticky="ew",padx=8)
        self.value_entry = ttk.Entry(controls, width=12)
        self.value_entry.grid(row=0,column=2,sticky="e")
        self.value_entry.bind("<Return>", self.apply_entry)
        ttk.Button(controls, text="Применить", command=self.apply_entry).grid(row=0,column=3,padx=6)
        ttk.Button(controls, text="Сбросить букву", command=self.reset_one).grid(row=0,column=4,padx=6)
        controls.columnconfigure(1,weight=1)

        ttk.Separator(right).pack(fill="x", pady=8)
        ttk.Label(right, text="Предпросмотр интервалов (условный)", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(right, text="Контуры — системный шрифт-заглушка; Advance берётся из VFONT. Масштаб предпросмотра настраивается отдельно и не меняет файл.").pack(anchor="w", pady=(2,5))
        scale_row = ttk.Frame(right)
        scale_row.pack(fill="x", pady=(0,6))
        ttk.Label(scale_row, text="Масштаб Advance:").pack(side="left")
        self.preview_scale_var = tk.DoubleVar(value=52.5)
        self.preview_scale = ttk.Scale(scale_row, from_=25.0, to=140.0, variable=self.preview_scale_var, command=lambda _v: self.draw_preview())
        self.preview_scale.pack(side="left", fill="x", expand=True, padx=8)
        self.preview_scale_label = ttk.Label(scale_row, text="52.5 px / unit")
        self.preview_scale_label.pack(side="left")
        self.sample_var = tk.StringVar(value="FH2 2026 — БОЛЬШИЕ ГОНКИ! © € ™ →")
        sample_row = ttk.Frame(right)
        sample_row.pack(fill="x")
        ttk.Entry(sample_row, textvariable=self.sample_var).pack(side="left", fill="x", expand=True)
        ttk.Button(sample_row, text="Показать", command=self.draw_preview).pack(side="left", padx=6)
        self.canvas = tk.Canvas(right, height=190, background="#202631", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=8)
        self.canvas.bind("<Configure>", lambda e: self.draw_preview())

        batch = ttk.LabelFrame(right, text="Быстрая групповая настройка", padding=8)
        batch.pack(fill="x", pady=6)
        ttk.Label(batch, text="Изменить Advance выбранных букв на:").pack(side="left")
        self.delta_var = tk.StringVar(value="0.005")
        ttk.Entry(batch, textvariable=self.delta_var, width=10).pack(side="left", padx=6)
        ttk.Button(batch, text="Добавить ко всем глифам", command=self.batch_delta).pack(side="left")
        ttk.Button(batch, text="Сбросить все", command=self.reset_all).pack(side="left", padx=6)

        self.footer = ttk.Label(self, text="Таблица читается целиком по счётчику заголовка. Редактируется только 4-байтовое поле Advance выбранной записи; геометрия и остальные данные сохраняются.")
        self.footer.pack(fill="x", padx=10, pady=(0,8))

    def open_file(self):
        path = filedialog.askopenfilename(title="Открыть FH2 VFONT", filetypes=[("VFONT","*.vfont"),("Все файлы","*.*")])
        if not path: return
        try:
            data = open(path,"rb").read()
            doc = VFontDocument(path,data)
        except Exception as e:
            messagebox.showerror("Ошибка разбора", str(e))
            return
        self.doc = doc
        self.file_label.config(text=os.path.basename(path))
        self.populate_tree()
        self.status.config(text=f"Прочитано записей таблицы: {len(doc.glyphs)}")
        self.draw_preview()

    def open_reference(self):
        path = filedialog.askopenfilename(title="Открыть оригинальный VFONT", filetypes=[("VFONT","*.vfont"),("Все файлы","*.*")])
        if not path: return
        try:
            self.reference = VFontDocument(path, open(path,"rb").read())
            self.status.config(text=f"Файл сравнения: {os.path.basename(path)}")
            self.populate_tree()
        except Exception as e:
            messagebox.showerror("Ошибка разбора оригинала", str(e))

    def populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.doc:
            return
        query = self.filter_var.get().strip().lower() if hasattr(self, "filter_var") else ""
        shown = 0
        for cp, item in sorted(self.doc.glyphs.items()):
            ch = char_name(cp)
            unicode_text = f"U+{cp:04X}"
            ref = self.reference.glyphs.get(cp, {}).get("value") if self.reference else None
            shown_delta = (item["value"] - ref) if ref is not None else (item["value"] - item["original"])
            searchable = f"{ch} {unicode_text} {cp} {item['index']}".lower()
            if query and query not in searchable:
                continue
            self.tree.insert(
                "", "end", iid=str(cp),
                values=(ch, unicode_text, f'{item["value"]:.6f}', f'{shown_delta:+.5f}')
            )
            shown += 1
        if hasattr(self, "count_label"):
            self.count_label.config(text=f"Показано: {shown} / {len(self.doc.glyphs)}")
        if self.selected_cp is not None and str(self.selected_cp) in self.tree.get_children():
            self.tree.selection_set(str(self.selected_cp))

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel or not self.doc: return
        cp = int(sel[0])
        self.selected_cp = cp
        item = self.doc.glyphs[cp]
        self.glyph_title.config(text=f'{char_name(cp)}   U+{cp:04X}')
        self.metric_info.config(text=f'Исходное значение: {item["original"]:.6f}    Текущее значение: {item["value"]:.6f}')
        self.value_var.set(item["value"])
        self.value_entry.delete(0,"end")
        self.value_entry.insert(0,f'{item["value"]:.6f}')
        self.draw_preview()

    def on_scale(self, _value=None):
        if not self.doc or self.selected_cp is None: return
        val = float(self.value_var.get())
        self.value_entry.delete(0,"end")
        self.value_entry.insert(0,f"{val:.6f}")
        self._apply_value(val)

    def apply_entry(self, _event=None):
        if not self.doc or self.selected_cp is None: return
        try: val = float(self.value_entry.get().replace(",","."))
        except ValueError:
            messagebox.showerror("Некорректное число","Введите число, например 0.625.")
            return
        if not is_plausible_advance(val):
            messagebox.showerror("Недопустимое значение","Допустимый диапазон: 0.02–2.50.")
            return
        self.value_var.set(val)
        self._apply_value(val)

    def _apply_value(self,val):
        try: self.doc.set_advance(self.selected_cp,val)
        except Exception as e:
            messagebox.showerror("Ошибка",str(e)); return
        self.metric_info.config(text=f'Исходное значение: {self.doc.glyphs[self.selected_cp]["original"]:.6f}    Текущее значение: {val:.6f}')
        self.populate_tree()
        self.draw_preview()

    def reset_one(self):
        if self.doc and self.selected_cp is not None:
            self.doc.reset_glyph(self.selected_cp)
            self.on_select()
            self.populate_tree()

    def batch_delta(self):
        if not self.doc: return
        try: delta=float(self.delta_var.get().replace(",","."))
        except ValueError:
            messagebox.showerror("Ошибка","Введите числовую поправку."); return
        for cp,item in self.doc.glyphs.items():
            val=item["value"]+delta
            if not is_plausible_advance(val):
                messagebox.showerror("Операция отменена",f"Для {char_name(cp)} получится недопустимое значение.")
                return
        for cp,item in list(self.doc.glyphs.items()):
            self.doc.set_advance(cp,item["value"]+delta)
        self.populate_tree(); self.draw_preview()

    def reset_all(self):
        if not self.doc: return
        for cp in self.doc.glyphs: self.doc.reset_glyph(cp)
        self.populate_tree()
        if self.selected_cp is not None: self.on_select()
        self.draw_preview()

    def save_as(self):
        if not self.doc:
            messagebox.showinfo("Нет файла","Сначала откройте VFONT."); return
        path=filedialog.asksaveasfilename(title="Сохранить изменённый VFONT",defaultextension=".vfont",initialfile=os.path.splitext(os.path.basename(self.doc.path))[0]+"_edited.vfont",filetypes=[("VFONT","*.vfont")])
        if not path: return
        try:
            self.doc.save(path)
            messagebox.showinfo("Сохранено",f"Файл записан:\n{path}\n\nИсходный файл не изменён.")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения",str(e))

    def draw_preview(self):
        c=self.canvas
        c.delete("all")
        if not self.doc:
            c.create_text(16,18,anchor="nw",fill="#cbd5e1",text="Откройте VFONT, чтобы увидеть предпросмотр.")
            return
        text=self.sample_var.get()
        if not text: return
        # Advance values are normalized font units. Scale chosen for readable
        # layout; system glyph outlines are only a visual placeholder.
        scale=float(self.preview_scale_var.get())
        self.preview_scale_label.config(text=f"{scale:.1f} px / unit")
        x=18.0
        y=94
        c.create_line(12,y+34, max(c.winfo_width()-12,100), y+34, fill="#526071", dash=(3,4))
        for ch in text:
            cp=ord(ch)
            if cp in self.doc.glyphs:
                adv=self.doc.glyphs[cp]["value"]
            else:
                # Character is not in this font: use a visual placeholder width only.
                adv=0.48 if ch!=" " else 0.30
            if ch==" ":
                x += adv*scale
                continue
            c.create_text(x,y,text=ch,anchor="nw",font=("Arial",36,"bold"),fill="#f4f6fa")
            c.create_line(x,y+46,x+adv*scale,y+46,fill="#f2c94c",width=2)
            x += adv*scale
            if x > c.winfo_width()-25: break
        c.create_text(14,8,anchor="nw",fill="#9fb0c4",text=f"Строка: {text}")
        c.create_text(14,166,anchor="nw",fill="#9fb0c4",text="Жёлтые отрезки — Advance для символов, присутствующих в таблице VFONT.")

if __name__ == "__main__":
    App().mainloop()

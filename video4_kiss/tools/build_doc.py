"""Build the Word document (analysis + ideas + competitor breakdown + block plan + full script with timecodes)."""
import json, os, sys
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
sys.path.insert(0, os.path.dirname(__file__))
from parse_script import load
root = os.path.join(os.path.dirname(__file__), "..")
tim = json.load(open(os.path.join(root, "voiceover", "timings.json")))
blocks = load(root)
tc = lambda s: f"{int(s)//60}:{int(s)%60:02d}"

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
for s in doc.sections: s.left_margin = s.right_margin = Cm(2)

def h(t, l=1): doc.add_heading(t, level=l)
def p(t, bold=False, italic=False, size=None, color=None):
    para = doc.add_paragraph(); r = para.add_run(t); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor(*color)
    return para
def bullets(items):
    for it in items: doc.add_paragraph(it, style="List Bullet")
def table(head, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(head)); t.style = "Light Grid Accent 1"
    for c, x in zip(t.rows[0].cells, head): c.text = x
    for r in rows:
        cells = t.add_row().cells
        for c, x in zip(cells, r): c.text = str(x)
    if widths:
        t.autofit = False
        for col, w in zip(t.columns, widths): col.width = Cm(w)
        for row in t.rows:
            for c, w in zip(row.cells, widths): c.width = Cm(w)
    doc.add_paragraph()

C = json.load(open(os.path.join(root, "doc_content.json"), encoding="utf-8"))
title = doc.add_heading(C["title"], 0)
p(C["subtitle"], bold=True, size=13)
p(f"Длительность ролика конкурента: 20:21  ·  Длительность нового сценария (по готовой озвучке): {tc(tim[-1]['end'])}  ·  "
  f"Слов: {sum(len(l['text'].split()) for b in blocks for l in b['lines'])}  ·  Кадров (картинок): {len(tim)}", italic=True)

h("1. Почему эта идея")
bullets(C["why"])
p(C["title_line"], bold=True)

# ---------------- 3. Competitor script breakdown
h("2. Разбор сценария конкурента «How Ancient Humans Actually Created Dogs?» (20:21)")
table(["Таймкод", "Блок", "Что происходит / приём"], [
    ["0:00–0:41", "Хук-погружение", "«15 000 лет назад. Вы — охотник-собиратель…» Второе лицо, ритм-шутка «try not to die», ночь, шорох, жёлтые глаза — и неожиданный поворот: зверь не нападает"],
    ["0:41–1:09", "Тезис", "«Всё было не так, как думают». Абсурдная картинка из современности (зверь спит на подушке и плачет, когда ты выходишь на 30 секунд)"],
    ["1:09–1:45", "Базовый факт", "Собака — подвид серого волка; от чихуахуа до овчарки — все потомки волков"],
    ["1:45–2:44", "Когда?", "Учёные спорят (15–40 тыс. лет); собаки — первые одомашненные, раньше лошадей и земледелия"],
    ["2:44–3:39", "Развенчание мифа", "Романтическая версия «нашли волчат — вырастили» → «Completely not how it happened»; взрослого волка не приручить"],
    ["3:39–5:41", "Главный ответ", "Волки одомашнили себя сами: мусор у стоянок, смелые особи получают еду, отбор по спокойствию"],
    ["5:41–8:35", "История учёного", "Эксперимент Беляева с лисами + абсурдная деталь (генетика — «буржуазная лженаука»), синдром одомашнивания"],
    ["8:35–10:17", "Улица с двусторонним движением", "Люди тоже изменились; одомашнивание происходило несколько раз в разных местах; ко-эволюция"],
    ["10:17–12:38", "Мозг и «хаки»", "Указательный жест, взгляд и окситоцин, мышца «щенячьих глаз» → «Вы думали, что выбрали собаку. Это она 10 000 лет училась, чтобы вы её выбрали»"],
    ["12:38–14:01", "Эмоции", "Совместные погребения людей и собак — дружба старше земледелия"],
    ["14:01–16:21", "Породы", "Человек «взял руль»: работа, размеры, викторианские стандарты пород, юмор про бульдога-батон"],
    ["16:21–17:49", "Современность", "Собаки в инстаграме, в завещаниях, носок интереснее всего на свете, корм за $40"],
    ["17:49–19:46", "Главный поворот", "Собаки — участники собственного одомашнивания; «мы не просто создали собак — собаки помогли создать нас»"],
    ["19:46–20:21", "Финал-кольцо", "Возврат к волку у костра; «в следующий раз, когда собака уснёт у вас на ногах…»"],
], [2.3, 3.2, 11.5])
h("Приёмы, которые делают ролик вирусным", 2)
bullets([
    "Погружение во втором лице с первой секунды («It's 15,000 years ago. You're…») и визуальный клиффхэнгер (глаза в темноте).",
    "Обещание разрушить миф («it didn't happen the way most people think») и прямой разворот «Beautiful. Heartwarming. Completely not how it happened.»",
    "Перезагрузка внимания каждые 60–90 секунд: «Here's the thing», «Here's where it gets really interesting», «But here's the question nobody asks».",
    "Юмор через контраст древнее ↔ современное (подушка, носок, корм за $40) — каждые 2–3 минуты.",
    "Конкретные цифры и имена (15 000 лет, 1950-е, Беляев, levator anguli oculi medialis) создают ощущение достоверности.",
    "Мини-история с героем и абсурдной деталью в середине ролика (учёный, советская цензура).",
    "Переворот перспективы: «вы думали, что выбирали вы — на самом деле выбирали вас».",
    "Эмоциональный третий акт (погребения, любовь, горе) и финал-кольцо с обращением к питомцу зрителя.",
    "Короткие фразы, фрагменты, паузы — удобно ложится на смену картинок каждые 2–3 секунды.",
])
h("Как приёмы конкурента перенесены в новый сценарий", 2)
table(["Приём конкурента", "В новом сценарии"], C["transfer"], [7, 10])

# ---------------- 4. Block plan
h("3. Разделение нового сценария на блоки")
BLOCK_RU = {k: tuple(v) for k, v in C["blocks_ru"].items()}
for b in blocks:
    bt = [t for t in tim if t["block"] == b["id"]]
    ru = BLOCK_RU[b["id"]]
    h(f"{b['id']}  {tc(bt[0]['start'])}–{tc(bt[-1]['end'])}  ·  {ru[0]}", 2)
    para = doc.add_paragraph(); r = para.add_run("Тема блока: "); r.bold = True; para.add_run(b["title"])
    para = doc.add_paragraph(); r = para.add_run("Основные смыслы: "); r.bold = True; para.add_run(ru[1])
    para = doc.add_paragraph(); r = para.add_run("Краткое содержание: "); r.bold = True; para.add_run(ru[2])

# ---------------- 5. Full script
h("4. Полный сценарий с таймкодами (английский, для озвучки)")
p("Таймкоды взяты из готовой озвучки (voiceover/voiceover.mp3). Каждая строка = одна картинка (кадр); номер в скобках совпадает с номером строки в image_prompts.txt.", italic=True)
for b in blocks:
    bt = [t for t in tim if t["block"] == b["id"]]
    h(f"{b['id']} · {tc(bt[0]['start'])} · {b['title']}", 2)
    for sent in b["sentences"]:
        para = doc.add_paragraph(); para.paragraph_format.space_after = Pt(2)
        first = bt[sent[0]]
        r = para.add_run(f"[{tc(first['start'])}]  "); r.font.color.rgb = RGBColor(0x88, 0x88, 0x88); r.font.size = Pt(9)
        para.add_run(" ".join(b["lines"][i]["text"] for i in sent))

# ---------------- 6. Fact-check & production
h("5. Факты, которые стоит перепроверить перед публикацией")
bullets(C["facts"])
h("6. Производство", 1)
bullets(C["production"])
doc.save(os.path.join(root, C["docx_name"]))
print("saved")

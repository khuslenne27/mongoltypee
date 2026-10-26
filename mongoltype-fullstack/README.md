# MONGOLTYPE — Next.js + Django v2

## Windows дээр асаах
ZIP-ийг **шинэ хавтаст** задлаарай. Өмнөх төслийн database руу хуулж солихгүй. Энэ багц шинэ initial migration-тай, тусдаа database үүсгэнэ.
Python 3.12+, 64-bit Node.js 20.9+ шаардлагатай.

Хялбар арга: үндсэн `mongoltype-fullstack` хавтас дотор terminal нээгээд:
```powershell
powershell -ExecutionPolicy Bypass -File .\start-backend.ps1
```
Шинэ terminal дээр:
```powershell
powershell -ExecutionPolicy Bypass -File .\start-frontend.ps1
```
Энэ execution policy зөвхөн тухайн process-д үйлчилнэ; системийн тохиргоо өөрчлөхгүй.
Хоёр terminal-ийг нээлттэй үлдээгээд http://localhost:3000 нээнэ.
Backend асаах скрипт dependency суулгана, migration хийнэ, үгс оруулна. Давтан ажиллуулахад үгийг давхардуулахгүй.

### Гараар ажиллуулах
Terminal 1:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py setup_typing
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```
Terminal 2 (үндсэн хавтаснаас):
```powershell
cd frontend
npm ci
npm run dev
```
`requirements.txt` зөвхөн backend хавтаст байна. `next` олдохгүй бол frontend дотор `npm ci` ажиллуулна.

## Хийгдсэн өөрчлөлт
- Монгол бичгийн үгийг задлахгүй DOM Range ашиглан дундах бичилтийн байрлалд хөндлөн cursor харуулна. Англи, кириллд босоо cursor.
- Текстийг үг бичих бүрд slice хийж солихгүй. Бүх эх DOM-д тогтвортой үлдэнэ. Мөр/багана солигдоход viewport нэг мөр/баганаар шилжинэ. Backspace хийхэд буцаж харагдана.
- Хугацаагаар: 15, 30, 60, 120 секунд. Үгийн тоогоор: 10, 25, 50, 100 үг.
- Хэл тус бүрд: энгийн үг, цэг/тэмдэгт, тоо, холимог. Монгол бичигт U+1802/U+1803 зэрэг цэг тэмдэг ашиглана. Тооны дасгалд 0–9 араб цифр ашиглана.
- Эхний оролтоос хугацаа эхэлнэ; ESC болон restart товч шинэ дасгал авна.
- Босоо бичгийн доорх keyboard: 2 Windows layout, Shift түвшин, physical code дээр даралтын өнгө, дараагийн үсгийн тэмдэглэгээ, дэлгэцийн товчоор input.
- Үр дүн backend-д хадгалагдана. Түүхийг хэл, горим, ангиллаар шүүнэ. Profile-ийн график нь бодит сүүлийн шалгалтууд.
- Чансаа: хэл тус бүрийн 30 секунд, энгийн үг, хянагдсан сангийн үр дүнгээр нэг браузерийн хамгийн өндөр оноог харуулна. Demo босоо бичгийн үр дүн чансаанд орохгүй.

## Монгол бичгийн гар
Төхөөрөмжийн OS гарын байрлалтай ижил нэрийг dropdown-оос сонго:
- Windows Traditional Mongolian (Standard)
- Windows Mongolian (Mongolian Script)
Байрлалын эх сурвалж: https://unicode.org/cldr/charts/43/keyboards/layouts/mn.html (Unicode CLDR 43).
Энэ keyboard OS байрлалыг өөрчилдөггүй. OS гаргүй бол дэлгэцийн товчоор бичиж болно. Shift-ийг дэлгэц дээр дарж нэмэлт үсэг харуулна. Caps Lock/AltGr-ийн тусгай давхарга дэмжээгүй. FVS1/2/3, MVS, NNBSP, ZWJ, ZWNJ харагдах нэртэй.
Стандартын түүхэн хувилбарууд өөр байж болно; өөр layout (MNS, Keyman гэх мэт) ашигладаг бол зураглалын өгөгдлийг тусад нь нэмэх шаардлагатай.
Фонт: Noto Sans Mongolian, SIL OFL (@fontsource). Үсгийн залгалтыг хадгалахын тулд босоо бичгийн зөв/буруу өнгө бүхэл дууссан үг дээр өөрчлөгдөнө; үгийн дундах байрлалыг cursor дагана. Grapheme ба ligature-ээс шалтгаалан тусдаа key бүрд харагдах cursor зай адилгүй байж болно.

## Үгийн сан ба Admin
Эхлэх сан: англи/кирилл хөгжүүлэлтийн үгс, босоо бичгийн 10 **хянагдаагүй** туршилтын үг. Том external сан энэ багцад импортлоогүй. Сайт дээр энэ талаар тэмдэглэсэн.
```powershell
cd backend
.\.venv\Scripts\python.exe manage.py createsuperuser
```
http://127.0.0.1:8000/admin/ — үг, verified, эх сурвалж, тест, үр дүн удирдана.
CSV UTF-8: `text,cyrillic,verified,source`.
```powershell
.\.venv\Scripts\python.exe manage.py import_words words.csv --language mn-Mong
```
Хүн хянасан зөв бичлэгт л verified=true өгнө. FVS/MVS/NNBSP-г устгахгүй. Private-use legacy кодчиллыг хориглоно. Худам зэрэг гаднын өгөгдлийн лицензийг баримталж, эх сурвалж тэмдэглэ. Хянагдсан сан оруулсны дараа frontend app/page.tsx дахь demo:true-г false болго.

## Backend, өгөгдөл
Local хурдан асаахын тулд SQLite. PostgreSQL ашиглах бол backend/.env.example-ийн хувьсагчдыг process environment-д тохируул. Backend .env-ийг автоматаар уншихгүй. Node .env.local дахь DJANGO_API_URL-ээр backend хаягийг сольж болно. Next.js /api хүсэлтийг Django руу proxy хийнэ.
API: POST /api/tests; POST /api/tests/{uuid}/start; POST /api/results; GET /api/history; GET /api/leaderboard?language=mn-Cyrl.
Дасгал/үр дүн client-ээс өгсөн санамсаргүй UUID visitor-т хамаарна. Энэ UUID localStorage-д, үр дүн database-д. LocalStorage устгахад хуучин түүхтэй холболт алга болно. Authentication/account болон олон төхөөрөмжийн sync хараахан нэмээгүй. Үүнийг баталгаажсан нийтийн тэмцээн гэж үзэхгүй.
Backend оноог дахин тооцож, эхэлсэн цаг, дууссан нөхцөл, language/mode/category-ийг шалгана. Давтан хадгалалт idempotent. Client timestamp болон input-ийг бүрэн баталгаажуулдаг anti-cheat биш. Rate limit нь local cache/IP дээр ажиллах хөгжүүлэлтийн түвшний хамгаалалт.

## Оноо
WPM = зөв grapheme cluster / 5 / минут. Accuracy = одоо байгаа текстийн зөв cluster / нийт cluster. Үг бүрийг тусдаа харьцуулдаг тул нэг үгийн илүү тэмдэг дараагийн үгсийг буруу болгохгүй. Засч арилгасан алдааг хуримтлуулдаггүй. Хэлбэр сонгогчийг base үсэгтэй нэг cluster гэж тоолно. Backend regex \\X ба frontend Intl.Segmenter нь Unicode хувилбараар зөрөх магадлалтай; хадгалсан backend үр дүн эцсийнх.
Үгийн горим сүүлийн үгийн уртыг хүрэхэд дуусна (алдаатай байсан ч дуусч болно). Хугацааны горим 600 үгийн эхийг ашигладаг; эхийг бүхэлд нь дуусгавал эрт дуусна. Үгийн горимын дээд хугацаа 60 минут.

## Шалгалт
```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
cd ..\frontend
npm run typecheck
npm run build
```
Production: Python hosting шаардлагатай; DEBUG=0, шинэ secret, HTTPS, зөв hosts, production database ба cache тохируулна. Admin CSRF хамгаалалттай; anonymous API нь UUID bearer identity-тэй. Жинхэнэ account нэвтрэлт нэмэхдээ ownership/auth/CSRF-ийг тусад нь хэрэгжүүлнэ.

### v2.1 — Монгол бичгийн шууд шалгалт
Идэвхтэй үгийн typed grapheme бүрийн зөв/бурууг ногоон/улаан давхаргаар шууд өнгөлнө. Бүхэл үгийг давхар зурж glyph range-аар clip хийдэг тул үндсэн текстийг үсэг тус бүрээр таслахгүй, залгалтыг хадгална. Scroll баганыг үсгийн хэлбэрийн хайрцгаас бус тогтвортой үгийн баганаас тооцно; зай авахад нэг баганад хэвээр байвал viewport хөдлөхгүй.

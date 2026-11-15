%% kisim_no: IX
%% kisim_ad: Otomata & Derleme
%% bolum_no: 37
%% baslik: Derleyici Nasıl Çalışır

## Giriş: Kaynak kodun yolculuğu

Bölüm 4.4'te `gcc kaynak.c -o uygulama` komutunun dört aşamalı bir konveyör bandı olduğunu gördün: ön işlemci, derleyici, assembler, bağlayıcı. O bölümde derleyicinin içini açmadık; "saf C'yi assembly'ye çeviren kutu" olarak bıraktık. Bu bölüm o kutuyu açıyor. Derleyici yazmak, en eski ve en yoğun yazılım sorunlarından birini çözmek demektir: insanın yazdığı, sınırlı ve kurallı bir metni, bilgisayarın tam olarak doğru yürüteceği bir biçime çevirmek.

Bu bilgi üç yerde karşına çıkar. Birincisi mülakatlarda: "Operatör önceliği nasıl kodlanır?", "bir değişkenin kapsamını nasıl bulursun?", "neden bazı hatalar derleme zamanında, bazıları çalışma zamanında görülür?" soruları derleyici sorularıdır. İkincisi günlük işinde: bir hata mesajını ("tanımsız referans", "tür uyuşmazlığı", "beklenmeyen dosya sonu") doğru okuyabilmek, o mesajın hangi aşamadan geldiğini bilmeye bağlıdır. Üçüncüsü gömülü ve savunma sanayiinde: hedef işlemci için çapraz derleme yaparken, ürettiğin kodun boyutunu, zamanlamasını ve hatalarını anlamak zorundasın. STM32 üzerinde çalışan bir uçuş kontrol yazılımında bir optimizasyonun döngü süresini nasıl değiştirdiğini bilmeden "derleyici zaten hızlandırır" demek, sorumluluktan kaçmaktır.

Bu bölümde hem teoriyi hem de pratiği yapacağız. Teoride, derleyicinin boru hattını (ön uç, orta katman, arka uç) ve her aşamanın hangi sorunu çözdüğünü göreceğiz. Pratikte, Python'da küçük bir dil olan **Mini**'yi sıfırdan yazacağız: sözcük çözümleyici, Pratt ayrıştırıcı, anlamsal denetim, yığın makinesi bayt kodu ve sanal makine. Aynı programları bir ağaç gezen yorumlayıcıyla da çalıştırıp sonuçların aynı olduğunu rastgele ifadelerle test edeceğiz ve hızlarını ölçeceğiz. Ana referans olarak Mert'in kendi projesi **Doruk**'u kullanacağız: Türkçe anahtar kelimeli bu dilin ayrıştırıcısı, anlamsal analizcisi ve ağaç gezen yorumlayıcısı C++ ile yazılmış ve gerçek bir derleyici yapısı taşıyor.

Burada bir sınır koyalım. Gerçek bir üretim derleyicisi (GCC, Clang, LLVM) yüz binlerce satırdır; onlarca yılın optimizasyonunu içerir. Biz onların **fikirlerini** ve küçük ölçekteki gerçeklerini göreceğiz. Gerçek derleyicinin davranışını anlatırken, ölçtüğümüz değerleri ve gcc'nin ürettiği assembly'yi gösteriyoruz; ölçmediğimiz her iddiayı "genel bilgi" diye işaretliyoruz.

::: not
Bu bölümün ön koşulu Bölüm 8'deki yığın ve Bölüm 10'daki ağaç kavramlarıdır. Dilbilgisi, düzenli ifade ve sonlu otomat ayrıntılarını Bölüm 36'da işledik; burada yalnızca sözcüksel çözümlemeyi hatırlatıp üstüne kuruyoruz. Assembly okuma ve çağrı kurallarını Bölüm 24'ten biliyoruz kabul ediyoruz.
:::

## 37.1 Derleyici, yorumlayıcı, JIT ve bayt kodu: bir spektrum

Bir programı çalıştırmanın yolu tek değildir. Dört temel strateji var ve bunlar bir spektrumun uçlarıdır.

**Derleyici (compiler)** kaynak kodu, çalışmadan önce, hedef makinenin komutlarına çevirir. Çıktı bir çalıştırılabilir dosyadır; çalıştırıldığında makine doğrudan bu komutları yürütür. C ve C++ bu yolu izler.

**Yorumlayıcı (interpreter)** kaynak kodu (ya da ondan çıkarılmış bir ağacı) doğrudan okuyup çalıştırır. Hiçbir makine kodu üretilmez. Kolay yazılır, kolay hata ayıklanır, ama her adımda "bu düğüm ne?" sorusunu yeniden sormak gerekir.

**Bayt kodu sanal makinesi (bytecode VM)** ortada durur. Kaynak önce, makineden bağımsız, daha basit bir komut dizisine (bayt kodu) çevrilir; bu dizi bir sanal makine tarafından yürütülür. CPython, Java'nın JVM'si ve Lua bu yolu seçti.

**JIT (just-in-time, çalışma anında derleme)** bayt kodunu ya da ağacı çalışma sırasında, sık çalışan parçalar için makine koduna çevirir. V8 (JavaScript), HotSpot (Java) ve PyPy bu yaklaşımı kullanır.

Bu ayrımı somut görmek için CPython'un bayt kodunu okuyalım. Python kaynak kodunu derlerken, her fonksiyon için bir bayt kodu nesnesi üretir. `dis` modülü bunu insan okunabilir biçimde döker. Aşağıdaki program, bu dökümü ve iki konuyu birlikte gösteriyor: bayt kodunun yığın tabanlı yapısını ve derleme aşamasında sabit katlamayı.

```python
import ast, dis, gc, sys
print(sys.version.split()[0])
def f(a, b):
    return a + b * 2
dis.dis(f)
def g():
    return 2 * 3 + 4
print("---- g (sabit katlama)")
dis.dis(g)
print("---- ast")
agac = ast.parse("x = 2 + 3 * 4")
print(ast.dump(agac, indent=2))
print("---- gc")
class Dugum:
    def __init__(self):
        self.kom = None
a = Dugum(); b = Dugum(); a.kom = b; b.kom = a
del a, b
print("toplanan:", gc.collect())
x = []
y = x
print("refcount:", sys.getrefcount(x))
```

Programın çıktısı şöyledir. Sürüm satırı ve `dis` dökümü, Python 3.12.10 üzerinde alındı:

```term
$ python pydemo.py
3.12.10
  3           0 RESUME                   0

  4           2 LOAD_FAST                0 (a)
              4 LOAD_FAST                1 (b)
              6 LOAD_CONST               1 (2)
              8 BINARY_OP                5 (*)
             12 BINARY_OP                0 (+)
             16 RETURN_VALUE
---- g (sabit katlama)
  6           0 RESUME                   0

  7           2 RETURN_CONST             1 (10)
---- ast
Module(
  body=[
    Assign(
      targets=[
        Name(id='x', ctx=Store())],
      value=BinOp(
        left=Constant(value=2),
        op=Add(),
        right=BinOp(
          left=Constant(value=3),
          op=Mult(),
          right=Constant(value=4))))],
  type_ignores=[])
---- gc
toplanan: 8
refcount: 3
```

`f(a, b)` fonksiyonunun dökümünde iki şey dikkatini çekmeli. Birincisi, `a + b * 2` ifadesi `LOAD_FAST a`, `LOAD_FAST b`, `LOAD_CONST 2`, `BINARY_OP *`, `BINARY_OP +` komut dizisine dönüşmüş. Komutlar değerleri bir **yığında** (stack) saklar: `LOAD` yığına iter, `BINARY_OP` iki değeri yığından çekip sonucu geri iter. Bu, Bölüm 8'deki ifade değerlendirme yöntemiyle aynı fikirdir; postfix biçimine dönüşmüş bir ifadeyi yığınla hesaplamak. İkincisi, `g()` fonksiyonunda `2 * 3 + 4` ifadesi çalışma anında hesaplanmamış; derleme sırasında `10` olarak katlanmış ve tek komutla (`RETURN_CONST 10`) dönülmüş. Bu, derleyicinin ilk optimizasyonudur ve Bölüm 37.7'de geri döneceğiz.

Aynı kaynağın ağaç yapısını görmek için `ast.parse` kullanıyoruz. Dökümde `2 + 3 * 4` ifadesi hâlâ bir `BinOp` ağacıdır; derleyici bu ağacı katlamadan önce oluşturmuş. Yani ağaç, katlama ve bayt kodu üretiminin ortak girdisidir.

Spektrumun hangi ucunu seçeceğin, iki değerin dengesine bağlı: **başlangıç maliyeti** ve **yürütme hızı**. Derleyici başlangıçta en pahalıdır (uzun derleme) ama çalışma anında en hızlıdır. Yorumlayıcı başlangıçta en ucuzdur, çalışma anında en yavaştır. Bayt kodu ortadadır. JIT ise iki dünyanın en iyisini hedefler, ama karmaşıklığı ve bellek kullanımı yüksektir. Bu bölümde Mini için iki yürütme yolu kuracağız: ağaç yorumlayıcı ve bayt kodu VM. Sonunda hangisinin hangi koşulda kazandığını ölçümle göreceğiz.

## 37.2 Derleyici boru hattı: ön uç, orta katman, arka uç

Bir derleyici tek bir büyük program değil, bir **boru hattıdır**. Her aşama bir girdi biçimini başka bir biçime çevirir ve bir sonraki aşama bu çıktıyı alır. Bu ayrım, derleyici mühendisliğinin temel organizasyon ilkesidir: aşamalar birbirinden bağımsız geliştirilebilir, test edilebilir ve değiştirilebilir.

Boru hattı üç büyük parçaya ayrılır. **Ön uç (front end)** dile özgüdür: kaynak metni alır, sözdizimini ve anlamı denetler, bir soyut ağaç üretir. **Orta katman (middle end)** ise artık dile ve hedefe bakmaz; ara bir gösterim üzerinde optimizasyon yapar. **Arka uç (back end)** hedef makineye özgüdür: ara gösterimi kayıtlara, komutlara ve bellek düzenine çevirir.

![Şekil 37.1: Derleyici boru hattı. Ön uç (kaynak, sözcük, ayrıştırma, anlam) dile özgüdür; orta katman ara gösterim üzerinde çalışır ve hedeften bağımsızdır; arka uç ara gösterimi makine koduna çevirir.](gorseller/b37_boru_hatti.png)

Bu üçlemenin mühendislik değeri şuradadır: yeni bir dil eklemek istediğinde yalnızca ön ucu yazarsın; GCC'nin ve LLVM'in neden birden çok dili (C, C++, Fortran, Rust) aynı arka uçla desteklediğini bu açıklar (genel bilgi). Yeni bir işlemci hedeflemek istediğinde ise arka ucu yazarsın; ön uç ve orta katman değişmez. Doruk'un kaynak dizinine baktığında bu ayrımı görebilirsin: `Lexer.cpp`, `Parser.cpp` ve `SemanticAnalyzer.cpp` ön uca aittir; `Interpreter.cpp` ise AST üzerinde doğrudan çalışan bir yürütücüdür. Doruk'ta arka uç yoktur, çünkü Doruk bir yorumlayıcı olarak tasarlanmıştır. Bu bölümün sonunda bu yapıyı bayt kodu VM ile nasıl genişletebileceğini göstereceğiz.

Mini'nin boru hattı da aynı biçimdedir:

1. **Sözcüksel çözümleme:** metin → token dizisi.
2. **Ayrıştırma:** token dizisi → AST.
3. **Anlamsal analiz:** AST → sembol tablosu ve tür denetimi (aynı AST, ek bilgiyle).
4. **Kod üretimi:** AST → yığın makinesi bayt kodu.
5. **Yürütme:** bayt kodu → VM çıktısı. Karşılaştırma için: AST → ağaç yorumlayıcı çıktısı.

Bu sıralamayı Bölüm 37.3'ten Bölüm 37.10'a kadar adım adım kuracağız.

## 37.3 Sözcüksel çözümleme ve ayrıştırma

Ayrıştırmanın amacı, düz bir karakter dizisinden **yapı** çıkarmaktır. `2 + 3 * 4` düz bir metindir; ama bizim için bu, "çarpma önce, sonra toplama" kuralıyla bir ağaç anlamına gelir. İki aşamada yapılır.

**Sözcüksel çözümleme (lexing)** metni token'lara böler: sayı, tanımlayıcı, anahtar kelime, işleç, parantez. Bu aşamanın teorisi düzenli ifadeler ve sonlu otomatla çalışır; ayrıntısını Bölüm 36'da gördük. Burada Mini'nin sözcük çözümleyicisini tek bir düzenli ifade ile yazıyoruz. Her eşleşmenin hangi gruba ait olduğunu `lastgroup` ile öğreniyoruz; satır ve sütun bilgisini de her token'a taşıyoruz, çünkü hata mesajları bunsuz işe yaramaz.

```python
# -*- coding: utf-8 -*-
"""Mini dili: sözcüksel çözümleme ve AST düğümleri."""
import re
from dataclasses import dataclass


class HataDerleme(Exception):
    """Derleme hatasi: konum (satir, sutun) tasir."""

    def __init__(self, mesaj, satir, sutun):
        super().__init__(f"{satir}:{sutun}  {mesaj}")
        self.satir = satir
        self.sutun = sutun


ANAHTAR = {"let", "fn", "if", "else", "while", "return",
           "print", "true", "false"}
DESEN = re.compile(r"""
    (?P<bos>[ \t\r]+)
  | (?P<yeni>\n)
  | (?P<sayı>\d+)
  | (?P<kimlik>[A-Za-z_]\w*)
  | (?P<op>==|!=|<=|>=|[-+*/%<>=(){};,])
""", re.VERBOSE)


@dataclass
class Tok:
    tur: str        # "let", "SAYI", "KIMLIK", "==", "EOF", ...
    lexem: str
    satir: int
    sutun: int
```

Sözcük çözümleyicinin ana döngüsü aşağıdadır. Her token, başladığı satır ve sütunla birlikte saklanır. Yeni satırda satır numarası artar ve sütun sayacı sıfırlanır.

```python
def tokenize(kaynak):
    toks, satir, bas, i = [], 1, 0, 0
    while i < len(kaynak):
        m = DESEN.match(kaynak, i)
        if m is None:
            raise HataDerleme(f"tanınmayan karakter {kaynak[i]!r}",
                              satir, i - bas + 1)
        grup, metin = m.lastgroup, m.group()
        sut = i - bas + 1
        if grup == "yeni":
            satir, bas = satir + 1, m.end()
        elif grup == "bos":
            pass
        elif grup == "kimlik" and metin in ANAHTAR:
            toks.append(Tok(metin, metin, satir, sut))
        elif grup == "kimlik":
            toks.append(Tok("KIMLIK", metin, satir, sut))
        elif grup == "sayı":
            toks.append(Tok("SAYI", metin, satir, sut))
        else:
            toks.append(Tok(metin, metin, satir, sut))
        i = m.end()
    toks.append(Tok("EOF", "", satir, i - bas + 1))
    return toks


# ---------------- AST ----------------
# Her dugum, kaynak konumu (satir, sutun) tasir. Yorum: Turkce adlar
```

**Ayrıştırma (parsing)** token dizisini, dilbilgisine uygun bir yapıya çevirir. Bu aşamanın en yaygın yöntemi **özyinelemeli iniş (recursive descent)**dir: her dilbilgisi kuralı (örneğin `ifade`, `terim`, `çarpan`) bir fonksiyon olur ve kural bir başka kurala referans veriyorsa fonksiyon o fonksiyonu çağırır. Bölüm 15.10'da bu fikri küçük bir ifade ayrıştırıcısında görmüştük. Doruk'un ayrıştırıcısı da bu biçimdedir; yorum satırları gramerini BNF benzeri biçimde saklar:

```
ifade          → atama
mantıksalVeya  → mantıksalVe  ( ( "||" | "veya" ) mantıksalVe  )*
toplama        → carpma        ( ( "+"  | "-"   ) carpma       )*
carpma         → tekli         ( ( "*"  | "/"   | "%"  ) tekli )*
```

Bu gramerde `toplama` kuralı kendi kendisini sol uçta çağırmaz, ama bir sorun var: sol özyineleme. Düz bir ifadeyi şöyle yazmak doğal görünür: `E → E + T | T`. Ancak bir özyinelemeli iniş ayrıştırıcısı bu kuralı çevirdiğinde, `E()` fonksiyonu ilk iş olarak yine `E()`'yi çağırır ve asla bir token tüketmez; yığın taşana kadar sonsuza gider. Bu yüzden LL ayrıştırıcılarda sol özyineleme **kaldırılmak** zorundadır.

Kuralın genel biçimi şudur. `A → Aα | β` kuralını (burada α ve β dizgiler, β özyinelemeli olmayan) şu iki kurala çevirirsin:

- `A → β A'`
- `A' → α A' | ε`

`E → E + T | T` için: `α = + T`, `β = T`. Dönüşüm sonucu `E → T E'`, `E' → + T E' | ε` olur. Benzer biçimde `T → T * F | F` da `T → F T'`, `T' → * F T' | ε` olur. Dilbilgisinin yeni biçimi, sol özyineleme olmadan hem doğru dili üretir hem de her adımda en az bir token tüketir.

LL(1) ayrıştırıcının kararını hangi kuralı seçeceğini **bir sonraki token'a bakarak** verdiğini düşün. Bu karar için iki küme gerekir: **FIRST** (bir kuralın üretebileceği ilk token'lar) ve **FOLLOW** (bir kuralın hemen ardından gelebilecek token'lar). Bunların tanımı ve hesabı Bölüm 36'daki gibidir. Aşağıdaki tablo, iki gramer için bir betikle hesaplanmıştır (betik `mini/ll1.py`): solda özyinelemeli olan ve kaldırılmış olan.

| Kural | Sol özyinelemeli gramer: FIRST | FOLLOW | Kaldırılmış: FIRST | FOLLOW |
|---|---|---|---|---|
| E | `(`, `id` | `$`, `)`, `+` | `(`, `id` | `$`, `)` |
| E' | — | — | `+`, ε | `$`, `)` |
| T | `(`, `id` | `$`, `)`, `*`, `+` | `(`, `id` | `$`, `)`, `+` |
| T' | — | — | `*`, ε | `$`, `)`, `+` |
| F | `(`, `id` | `$`, `)`, `*`, `+` | `(`, `id` | `$`, `)`, `*`, `+` |

Sol özyinelemeli gramerde LL(1) tablosunu kurmaya çalıştığımızda 4 çakışma çıkıyor: `M[E, id]` hem `E → E + T` hem `E → T` ile doldurulmak istenir. Kaldırılmış gramerde çakışma yoktur. Tablo şöyle okunur: `M[E', +] = E' → + T E'` ve `M[E', $] = E' → ε`. ε üretimi, FOLLOW kümesindeki token'larda seçilir; bu yüzden `E'`'nin FOLLOW'u tabloda ε satırlarını belirler.

Ayrıştırmanın bir başka yaygın yöntemi **öncelik tırmanma (precedence climbing)** ve onun en temiz biçimi **Pratt ayrıştırmasıdır**. Pratt yaklaşımında her işleç bir **bağlama gücü (binding power)** taşır; ayrıştırıcı, bir sonraki işlecin gücü mevcut düzeyden büyükse onu sağa doğru tüketir. Böylece öncelik kuralları ayrı fonksiyonlara dağılmak yerine tek bir tabloda toplanır. Mini'nin ayrıştırıcısı bu yöntemi kullanır:

```python
# -*- coding: utf-8 -*-
"""Pratt (ustten isleyen operator önceligi) ayrıştırıcısi."""
from mini_on import (HataDerleme, Sayi, Degisken, Ikili, Tekli, Cagri,
                     Let, Ata, Yaz, Eger, Dongu, Don, Fonksiyon,
                     Ifade)

# Baglama gucu: büyük sayı = daha sikı bağlar.
GUC = {"==": 10, "!=": 10,
       "<": 20, "<=": 20, ">": 20, ">=": 20,
       "+": 30, "-": 30,
       "*": 40, "/": 40, "%": 40,
       "(": 60}            # çağrı parantezi en sikı bağlar
ONEK_GUC = 50              # tekli eksi: '*'dan sıkı, çağrıdan gevşek
```

Güç tablosu, daha büyük sayının daha sıkı bağlandığı anlamına gelir: `*` (40) `+`ten (30) sıkı bağlanır. Çağrı parantezi (60) en sıkı bağlanandır; tekli eksi (50) ise çarpmadan sıkı, çağrıdan gevşektir. Ayrıştırıcı sınıfı ve Pratt'ın çekirdeği şöyledir:

```python
class Ayristirici:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def bak(self, ileri=0):
        return self.toks[self.i + ileri]

    def ilerle(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def bekle(self, tur):
        t = self.bak()
        if t.tur != tur:
            raise HataDerleme(f"'{tur}' bekleniyordu, "
                              f"'{t.lexem}' bulundu",
                              t.satir, t.sutun)
        return self.ilerle()

    def program(self):
        out = []
        while self.bak().tur != "EOF":
            out.append(self.deyim())
        return out

    def blok(self):
        self.bekle("{")
        out = []
        while self.bak().tur != "}":
            out.append(self.deyim())
        self.bekle("}")
        return out
```

Deyimler (`let`, `print`, `if`, `while`, `return`, `fn`) ayrı bir `deyim()` fonksiyonunda, her biri kendi anahtar kelimesine bakılarak seçilir. Atama (`x = ...`) biçiminde ise karar için iki token ileri bakmak gerekir: önce bir `KIMLIK`, sonra bir `=`. Bu, ayrıştırıcının bir token'a değil, iki token'a bakan bir **LL(2)** kararı verdiği anlamına gelir. Yalnızca tek bir token'a bakmak isteseydik `x = 1` ile `x + 1` ayırt edilemezdi.

```python
    def deyim(self):
        t = self.bak()
        if t.tur == "let":
            self.ilerle()
            ad = self.bekle("KIMLIK").lexem
            self.bekle("=")
            e = self.ifade()
            self.bekle(";")
            return Let(ad, e, t.satir, t.sutun)
        if t.tur == "KIMLIK" and self.bak(1).tur == "=":
            self.ilerle()
            self.ilerle()
            e = self.ifade()
            self.bekle(";")
            return Ata(t.lexem, e, t.satir, t.sutun)
        if t.tur == "print":
            self.ilerle()
            e = self.ifade()
            self.bekle(";")
            return Yaz(e)
        if t.tur == "return":
            self.ilerle()
```

Deyimin devamı ve fonksiyon tanımı aşağıdadır. Bir `if` yalnızca `else` anahtar kelimesi görülürse ikinci bloğu okur; bu, `else`'in isteğe bağlı olduğunu kodda yansıtır.

```python
            e = self.ifade()
            self.bekle(";")
            return Don(e, t.satir, t.sutun)
        if t.tur == "if":
            self.ilerle()
            kosul = self.ifade()
            dal = self.blok()
            dal_degil = None
            if self.bak().tur == "else":
                self.ilerle()
                dal_degil = self.blok()
            return Eger(kosul, dal, dal_degil)
        if t.tur == "while":
            self.ilerle()
            kosul = self.ifade()
            return Dongu(kosul, self.blok())
        if t.tur == "fn":
            return self.fonksiyon()
        e = self.ifade()
        self.bekle(";")
        return Ifade(e)
```

```python
    def fonksiyon(self):
        t = self.ilerle()                       # 'fn'
        ad = self.bekle("KIMLIK").lexem
        self.bekle("(")
        params = []
        if self.bak().tur != ")":
            params.append(self.bekle("KIMLIK").lexem)
            while self.bak().tur == ",":
                self.ilerle()
                params.append(self.bekle("KIMLIK").lexem)
        self.bekle(")")
        return Fonksiyon(ad, params, self.blok(), t.satir, t.sutun)

    # ---------- Pratt cekirdegi ----------
```

Asıl iş `ifade(guc)` fonksiyonundadır. Önce bir öneki (sayı, tanımlayıcı, parantez, tekli eksi) okur. Sonra, sıradaki işlecin gücü `guc`'tan büyük olduğu sürece işlemeye devam eder. Kritik satır, sağ işlenenin `GUC[op.tur]` gücüyle özyinelemeli çağrılmasıdır: aynı güçteki bir işleç sağ tarafta durur, bu yüzden `1 - 2 - 3` soldan birleşir ve `(1 - 2) - 3` olur.

```python
    def ifade(self, guc=0):
        sol = self.oneki()
        while GUC.get(self.bak().tur, 0) > guc:
            op = self.ilerle()
            if op.tur == "(":
                if not isinstance(sol, Degisken):
                    raise HataDerleme("yalnız isimler çağrılabilir",
                                      op.satir, op.sutun)
                sol = Cagri(sol.ad, self.argumanlar(),
                            sol.satir, sol.sutun)
            else:
                sag = self.ifade(GUC[op.tur])   # sol birleşim için
                sol = Ikili(op.tur, sol, sag, op.satir, op.sutun)
        return sol
```

Aşağıdaki kesit öneki ve argüman listesini okur. Parantez, tekli eksi ve sayı/tanımlayıcı durumları burada ele alınır. `true` ve `false` `Sayi` düğümüne `bool` olarak girer; bu, anlamsal analizde tür denetimi için bir ayrım yaratır.

```python
    def oneki(self):
        t = self.ilerle()
        if t.tur == "SAYI":
            return Sayi(int(t.lexem), t.satir, t.sutun)
        if t.tur in ("true", "false"):
            return Sayi(t.tur == "true", t.satir, t.sutun)
        if t.tur == "KIMLIK":
            return Degisken(t.lexem, t.satir, t.sutun)
        if t.tur == "(":
            e = self.ifade()
            self.bekle(")")
            return e
        if t.tur == "-":
            return Tekli("-", self.ifade(ONEK_GUC), t.satir, t.sutun)
        raise HataDerleme(f"ifade bekleniyordu, "
                          f"'{t.lexem or t.tur}' bulundu",
                          t.satir, t.sutun)

    def argumanlar(self):
        args = []
        if self.bak().tur != ")":
            args.append(self.ifade())
            while self.bak().tur == ",":
                self.ilerle()
                args.append(self.ifade())
        self.bekle(")")
        return args


def ayristir(kaynak):
    from mini_on import tokenize
    return Ayristirici(tokenize(kaynak)).program()
```

Pratt'ın nasıl çalıştığını kendi gözünle görmek için, `2 + 3 * (4 - 1)` ifadesinde her `ifade(guc)` çağrısını ve dönüş değerini yazdıran küçük bir izleyici kullanalım. İzleyici `Ayristirici` sınıfını miras alır ve yalnızca çağrıları yazdırır.

```python
# -*- coding: utf-8 -*-
"""Pratt izi: ifade(guc) çağrılarini girintili yazdirir."""
from mini_on import tokenize
from mini_ayr import Ayristirici, GUC

class Izli(Ayristirici):
    derin = 0
    def ifade(self, guc=0):
        pad = "  " * Izli.derin
        print(f"{pad}ifade(guc={guc}) başlar, "
              f"şimdiki='{self.bak().lexem}'")
        Izli.derin += 1
        sonuc = super().ifade(guc)
        Izli.derin -= 1
        print(f"{pad}-> döndü: {sonuc_yaz(sonuc)}")
        return sonuc

def sonuc_yaz(d):
    from mini_on import Sayi, Degisken, Ikili, Tekli
    if isinstance(d, Sayi): return str(d.deger)
    if isinstance(d, Degisken): return d.ad
    if isinstance(d, Tekli): return f"({d.op}{sonuc_yaz(d.ey)})"
    return f"({sonuc_yaz(d.sol)} {d.op} {sonuc_yaz(d.sag)})"

if __name__ == "__main__":
    Izli(tokenize("2 + 3 * (4 - 1)")).ifade()
```

Programın çıktısı ağacın nasıl kurulduğunu gösteriyor:

```term
$ python iz_pratt.py
ifade(guc=0) başlar, şimdiki='2'
  ifade(guc=30) başlar, şimdiki='3'
    ifade(guc=40) başlar, şimdiki='('
      ifade(guc=0) başlar, şimdiki='4'
        ifade(guc=30) başlar, şimdiki='1'
        -> döndü: 1
      -> döndü: (4 - 1)
    -> döndü: (4 - 1)
  -> döndü: (3 * (4 - 1))
-> döndü: (2 + (3 * (4 - 1)))
```

İzde en önemli nokta, `3` sayısından sonra gelen `*`'ın (güç 40) çağrının gücünden (30) büyük olması nedeniyle `3`'ü sağa doğru "çekmesidir". `(` gördüğümüzde yeni bir `ifade(40)` açılır; ama parantez içi `ifade(0)` ile yeniden başlar ve `)` görülene kadar sürer. Şekil 37.2, aynı ağacı ve güç tablosunu yan yana gösteriyor.

![Şekil 37.2: Pratt bağlama güçleri ve 2 + 3 * (4 - 1) ağacı. Sol sütun işleçleri ve gücünü, sağ sütun ağacı gösterir: çarpma (40) toplamadan (30) önce bağlanır, parantez içi ifade ayrı bir alt ağaç olur.](gorseller/b37_pratt.png)

Doruk'ta aynı öncelik, Pratt yerine **katman katman fonksiyonlarla** kodlanmıştır. `Parser.cpp` dosyasında `ifade()` `atama()`ya, o da `mantiksalVeya()`ya, `mantiksalVe()`ye, `esitlik()`e, `karsilastirma()`ya, `toplama()`ya, `carpma()`ya ve `tekli()`ye çağrı yapar. Önceliği çağrı zinciri belirler: `toplama()` `carpma()`yı çağırır, `carpma()` `tekli()`yi çağırır; bu yüzden çarpma ağaçta toplamadan daha derine iner. Bu yaklaşımın avantajı açıklığıdır: her katman bir dilbilgisi kuralıdır ve doğrudan gramerle eşleşir. Dezavantajı, yeni bir öncelik seviyesi eklemenin bütün zinciri değiştirmek anlamına gelmesidir; Pratt'ta ise yalnızca tabloya bir satır eklenir.

Ayrıştırmanın üçüncü yolu **LR** ailesidir. LR ayrıştırıcılar soldan sağa okur ve bir **yığın** tutar; her adımda iki eylemden birini seçer: **kaydır (shift)**, yani sıradaki token'ı yığına it; ya da **indirge (reduce)**, yani yığının tepesindeki bir dizgiyi bir kuralın sol tarafıyla değiştir. Bölüm 37'nin bu kısmı sezgiseldir; LR tablolarının hesabı (LR(0), SLR, LALR) Bölüm 36'nın ve bir derleyici kursunun konusudur. Aşağıdaki iz, `id + id * id` girdisini sol özyinelemeli gramerle (`E → E + T | T`, `T → T * F | F`, `F → id`) bir kaydır-indirge ayrıştırıcısının nasıl işlediğini gösterir. İz elle yazılmıştır ve standart ders kitaplarındaki örnekle aynıdır.

| Yığın | Girdi | Eylem |
|---|---|---|
| `$` | `id + id * id $` | kaydır |
| `$ id` | `+ id * id $` | indirge `F → id` |
| `$ F` | `+ id * id $` | indirge `T → F` |
| `$ T` | `+ id * id $` | indirge `E → T` |
| `$ E` | `+ id * id $` | kaydır `+` |
| `$ E +` | `id * id $` | kaydır `id` |
| `$ E + id` | `* id $` | indirge `F → id` |
| `$ E + F` | `* id $` | indirge `T → F` |
| `$ E + T` | `* id $` | kaydır `*` |
| `$ E + T *` | `id $` | kaydır `id` |
| `$ E + T * id` | `$` | indirge `F → id` |
| `$ E + T * F` | `$` | indirge `T → T * F` |
| `$ E + T` | `$` | indirge `E → E + T` |
| `$ E` | `$` | kabul |

Bu izde önemli bir an, `$ E + T` durumunda `*` girdisini görünce **indirge yerine kaydır** kararı vermektir. Bu karar, LR tablosunun `*`'ın `+`tan daha sıkı bağlandığını bilmesinden gelir; eğer indirgeseydik `(E + T) * id` yapısı elde edilirdi. Bu, öncelik çakışmasının LR'daki karşılığıdır ve yacc/bison gibi araçlar bu çakışmaları çözmek için öncelik ve birleşme bildirimleri alır (genel bilgi).

Hata kurtarma, bir derleyicinin kullanıcıya gerçekten yardım edip etmediğini belirler. Bir hata bulunduğunda ayrıştırıcının iki seçeneği vardır: durmak ya da devam etmek. Durmak kolaydır ama kullanıcı yalnızca ilk hatayı görür. Devam etmek için **panik modu** kullanılır: ayrıştırıcı hatayı kaydeder, sonra bir **senkronizasyon** noktasına kadar token'ları atlar. Senkronizasyon noktaları genellikle noktalı virgül ve anahtar kelimelerdir, çünkü bunlar bir sonraki deyimin başlangıcını işaret eder. Doruk'un `senkronize()` fonksiyonu tam olarak bunu yapar:

```cpp
void Parser::senkronize() {
    while (!bitti()) {
        // Önceki token noktalı virgülse — yeni bir deyim başlıyor
        if (onceki().tur == TokenTuru::NOKTALI_VIRGUL) return;

        // Mevcut token bir deyim başlangıcıysa — duraksama noktası
        switch (mevcut().tur) {
            case TokenTuru::FONKSIYON:
            case TokenTuru::DEGISKEN:
            case TokenTuru::SINIF:
            case TokenTuru::EGER:
            case TokenTuru::ICIN:
            case TokenTuru::DONGU:
            case TokenTuru::DONDUR:
            case TokenTuru::YAZDIR:
            case TokenTuru::SAG_SUSE:
                return;
            default:
                break;
        }
        ilerle();
    }
}

// ============================================================
```

Bu fonksiyon, önceki token noktalı virgülse yeni bir deyimin başladığını varsayar ve dönüş yapar; mevcut token bir deyim anahtar kelimesiyse (`değişken`, `eğer`, `yazdır` ...) orada durur; değilse token'ı atlar. Bunun işe yaradığını görmek için Doruk'un CLI'sine iki hatalı satır içeren bir dosya verelim. Dosyanın içeriği aşağıdadır.

```term
$ cat hata.drk
eğer (x > 1 {
    yazdır(1)
}
değişken = 5 +
yazdır("tamam")
```

Dosya iki ayrı sözdizimi hatası içeriyor: `eğer (x > 1 {` ifadesinde `)` eksik, `değişken = 5 +` ifadesinde isim ve sağ taraf eksik. Derleyicinin çıktısı şöyle:

```term
$ ./doruk hata.drk
[HATA] hata.drk:1:14  Koşul ifadesi ')' ile kapatılmalı.
[HATA] hata.drk:4:12  'değişken' sonrasında değişken ismi bekleniyor.
          Örnek: değişken x = 5
```

İki hata da raporlandı; beşinci satırdaki `yazdır("tamam")` deyimi ise hata vermeden kabul edildi. Bu, panik modunun işe yaradığının kanıtıdır: ilk hatadan sonra ayrıştırıcı çökmedi, sonraki deyimden devam etti.

İyi bir hata mesajı üç şey taşır: **nerede** (satır ve sütun), **ne** (ne beklendiği ve ne bulunduğu) ve mümkünse **nasıl düzelir** (ipucu). Doruk'un ilk mesajı tam olarak bunu yapar: konum, sorun ve beklenen kalıp. Konumda dikkat etmen gereken bir ayrıntı var: sütun numarası karakter değil **bayt** sayar. Bu, Türkçe karakterli satırlarda kaymaya yol açar; bu konuyu Bölüm 37.10'da Doruk'ta ölçerek göstereceğiz.

## 37.4 AST: somut ağaçtan soyut ağaca

Ayrıştırıcı bitince elinde bir ağaç olur, ama bu ağacın hangi biçimde olacağına karar vermen gerekir. Bir **somut sözdizimi ağacı (concrete syntax tree, CST)** gramerin her kuralını bir düğüm yapar: parantezler, öncelik katmanları, noktalı virgüller hepsi düğüm olur. Bu ağaç ayrıştırmanın birebir kaydıdır, ama fazladır: `2 + 3` ifadesinin CST'sinde `ifade`, `toplama`, `carpma`, `birincil` gibi katman düğümleri vardır ve anlam taşımazlar.

Bir **soyut sözdizimi ağacı (abstract syntax tree, AST)** yalnızca anlamlı düğümleri tutar: işleçler, değişkenler, sabitler, çağrılar. Parantez bir düğüm değildir; ağacın yapısı zaten önceliği taşır. Derleyicinin geri kalanı (anlamsal analiz, kod üretimi, yorumlayıcı) yalnızca AST üzerinde çalışır; CST üzerinde çalışmak hem daha yavaş hem de daha karmaşık olur.

![Şekil 37.3: Aynı ifadenin somut ve soyut ağacı. Sol ağaçta gramerin her katmanı bir düğümdür (ifade, toplama, çarpma, birincil); sağ ağaçta yalnızca işleçler ve yapraklar vardır: 7 düğüm.](gorseller/b37_agac.png)

Mini'nin AST'si bir dizi veri sınıfıdır. Her düğüm, Bölüm 37.3'te gördüğümüz gibi konumunu (satır, sütun) taşır. Düğüm türleri ikiye ayrılır: **ifadeler** değer üretir (`Sayi`, `Degisken`, `Ikili`, `Tekli`, `Cagri`), **deyimler** yan etki üretir (`Let`, `Ata`, `Yaz`, `Eger`, `Dongu`, `Don`, `Fonksiyon`). Analizci ve derleyici bu iki kümeye ayrı ayrı bakar.

```python
@dataclass
class Sayi:          # tam sayi ve dogru/yanlis sabitleri
    deger: object; satir: int = 0; sutun: int = 0

@dataclass
class Degisken:      # slot: analizci doldurur
    ad: str; satir: int = 0; sutun: int = 0; slot: int = -1

@dataclass
class Ikili:         # a op b
    op: str; sol: object; sag: object; satir: int = 0; sutun: int = 0

@dataclass
class Tekli:         # -a
    op: str; ey: object; satir: int = 0; sutun: int = 0

@dataclass
class Cagri:         # f(a, b)
    ad: str; args: list; satir: int = 0; sutun: int = 0

@dataclass
class Let:           # let x = e;
    ad: str; ifade: object
    satir: int = 0; sutun: int = 0; slot: int = -1
```

Deyim düğümlerinin geri kalanı şöyledir. `Degisken` ve `Let`/`Ata` düğümlerindeki `slot` alanı, ayrıştırıcı tarafından boş bırakılır; anlamsal analiz bu alanı doldurur. Bu, bir düğümün hem sözdizimini hem de sonraki aşamaların hesapladığı bilgiyi taşıyabileceğini gösterir.

```python

@dataclass
class Ata:           # x = e;
    ad: str; ifade: object
    satir: int = 0; sutun: int = 0; slot: int = -1

@dataclass
class Yaz:           # print e;
    ifade: object

@dataclass
class Eger:          # if (k) {..} else {..}
    kosul: object; dal: list; dal_degil: list

@dataclass
class Dongu:         # while (k) {..}
    kosul: object; govde: list

@dataclass
class Don:           # return e;
    ifade: object; satir: int = 0; sutun: int = 0

@dataclass
class Fonksiyon:     # fn ad(p...) {..}
    ad: str; params: list; govde: list
    satir: int = 0; sutun: int = 0; nlocals: int = 0

@dataclass
```

Python'un kendi AST'sini gördük (Bölüm 37.1'deki `pydemo` döküm). CPython'un `ast` modülü de aynı fikri kullanır ve ziyaretçi kalıbı için bir taban sınıf sağlar. `NodeVisitor` sınıfı her düğüm türü için `visit_<Tür>` adında bir metot arar; bulamazsa `generic_visit` çalışır. Aşağıdaki kesit CPython 3.12.10'un kaynağındandır:

```python
    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)
```

Sınıfın `generic_visit` metodu, bulunamayan düğümler için alt düğümleri özyinelemeli olarak ziyaret eder; bu iki metot birlikte ağacın tam bir dolaşımını verir.

Bu kalıbın gücü, ağaç yapısını değiştirmeden yeni bir işlem eklemektir: anlamsal analizi, kod üretimini ya da bir yazdırıcıyı aynı ağaç üzerinde ayrı ziyaretçi sınıfları olarak yazarsın. Doruk bu kalıbı C++'ta kullanır. `AST.h` dosyasındaki `Ziyaretci` sınıfı, her düğüm türü için saf sanal bir metot tanımlar; her düğüm ise bir `kabul` (accept) metodu taşır ve kendisini ziyaretçiye tanıtır:

```cpp
class Ziyaretci {
public:
    virtual ~Ziyaretci() = default;

    // ── İfadeler ────────────────────────────────────────────
    virtual void ziyaretSayi     (SayiLiteralIfade&    d) = 0;
```

Düğümün tarafı şöyle görünür. `IkiliIfade` bir `kabul` metodu taşır; bu metot kendi türünü ziyaretçiye bildirir. Böylece hangi ziyaretçi metodunun çağrılacağı, çalışma anında düğümün gerçek türüne göre seçilir (çift yönlü dispatch):

```cpp
// İkili ifade: a + b, x == y, i < 10, a && b
struct IkiliIfade : Ifade {
    IfadePtr sol;
    Token    op;
    IfadePtr sag;

    IkiliIfade(IfadePtr sol, Token op, IfadePtr sag)
        : Ifade(sol->satir, sol->sutun)
        , sol(std::move(sol))
        , op(std::move(op))
        , sag(std::move(sag))
    {}

    void kabul(Ziyaretci& z) override { z.ziyaretIkili(*this); }
```

Doruk'ta `SemanticAnalyzer` sınıfı bu `Ziyaretci` arayüzünü uygular (`SemanticAnalyzer.h`, 37. satır: `class SemanticAnalyzer : public Ziyaretci`). Yani anlamsal analiz ve yorumlama, aynı ağaç üzerinde iki ayrı ziyaretçidir. Bunu Bölüm 22'deki kalıp dilinde söylersek, ağacın yapısı sabit, işlemler değişkendir. Bölüm 22'de `Command` ve `State` kalıplarında davranışı nesneye çevirmeyi gördük; burada işlemi ağaç düğümlerinin dışına taşıyan başka bir biçimi görüyoruz. Interpreter kalıbı (GoF) ile bu ziyaretçi-yorumlayıcı fikri birbirine çok yakındır: bir dilin gramerini bir sınıf hiyerarşisi olarak modelleyip her düğüme `yorumla` metodu eklemek. Bu bölümde Mini'nin ağaç yorumlayıcısı bu fikrin bir uygulamasıdır (genel bilgi: Interpreter kalıbı Bölüm 22'de ayrıca işlenmedi).

## 37.5 Anlamsal analiz: kapsam, sembol tablosu ve tür denetimi

Bir programın sözdizimi doğru olabilir ve yine de anlamsız olabilir. `print z;` cümlesi sözdizimi açısından geçerlidir; ama `z` hiç tanımlanmamışsa program çalışamaz. `1 + true` da geçerli bir ifadedir, ama bir sayıyla bir doğru/yanlış değerini toplamanın bir anlamı yoktur. **Anlamsal analiz (semantic analysis)** bu tür kuralları denetler ve derleyiciye iki şey kazandırır: hataları çalıştırmadan yakalamak ve sonraki aşamalar için bilgi toplamak.

Anlamsal analizin iki ana aracı vardır. Birincisi **sembol tablosudur**: her tanımlayıcının hangi kapsamda tanımlandığını, hangi türde olduğunu ve bellekte nerede tutulacağını (bu bölümde "slot" diyeceğiz) saklar. İkincisi **kapsam (scope)** kavramıdır: bir tanım, hangi bloğun içinde görünür? Mini'de her blok (`{ ... }`) yeni bir kapsam açar ve kapsamlar iç içe geçebilir. Bu bir **yığın** yapısıdır: blok açılınca bir sözlük itilir, kapanınca çekilir. Bir isim aranırken en üstten (en içten) başlanır; ilk bulunan kazanır. Bu, **gölgeleme (shadowing)** kuralıdır: iç blokta aynı adla yeni bir değişken, dıştakini geçici olarak gizler.

![Şekil 37.4: Kapsam yığını. Üstteki iç blok kapsamı `x`i gizler; ad araması en üstten başlar. Blok bitince üst kapsam geri gelir ve dıştaki `x` yeniden görünür.](gorseller/b37_kapsam.png)

```python
# -*- coding: utf-8 -*-
"""Anlamsal analiz: kapsam, tur denetimi, slot atamasi."""
from mini_on import (HataDerleme, Sayi, Degisken, Ikili, Tekli, Cagri,
                     Let, Ata, Yaz, Eger, Dongu, Don, Fonksiyon,
                     Ifade)

KARSILASTIRMA = {"<", "<=", ">", ">="}
ARITMETIK = {"+", "-", "*", "/", "%"}


class Analizci:
    def __init__(self, program):
        self.program = program
        self.fonksiyonlar = {}
        self.kapsam = []        # yığın: her blok bir sozluk
        self.slot_sayaci = 0
        self.en_fazla = 0       # bu govdenin yerel slot sayısi
        self.fn_icinde = False

    def analiz(self):
        for d in self.program:              # 1. imzalar (ileri atif)
            if isinstance(d, Fonksiyon):
                if d.ad in self.fonksiyonlar:
                    raise HataDerleme(f"'{d.ad}' zaten tanımlı",
                                      d.satir, d.sutun)
                self.fonksiyonlar[d.ad] = d
        for d in self.program:              # 2. govdeler
            if isinstance(d, Fonksiyon):
                self.fonksiyon(d)
        # 3. ust duzey deyimler: "__main__" govdesi
        self.kapsam, self.slot_sayaci, self.en_fazla = [{}], 0, 0
        self.fn_icinde = False
        for d in self.program:
            if not isinstance(d, Fonksiyon):
                self.deyim(d)
        return self.en_fazla
```

Analizcinin çekirdeği üç işlev taşır: `bildir` (yeni bir isim tanımlar, aynı kapsamda tekrar tanımlanmasına izin vermez), `bul` (ismi içten dışa doğru arar), `beklenen` (iki türün eşleşip eşleşmediğini denetler). Bir değişkenin slot numarası burada atanır; bu numara daha sonra yerel değişkenlerin nerede saklanacağını belirler.

```python
    def fonksiyon(self, d):
        ust = (self.kapsam, self.slot_sayaci, self.en_fazla)
        self.kapsam, self.slot_sayaci, self.en_fazla = [{}], 0, 0
        self.fn_icinde = True
        for p in d.params:
            self.bildir(p, "int", d.satir, d.sutun)
        for s in d.govde:
            self.deyim(s)
        d.nlocals = self.en_fazla
        self.kapsam, self.slot_sayaci, self.en_fazla = ust
        self.fn_icinde = False

    def bildir(self, ad, tur, satir, sutun):
        cari = self.kapsam[-1]
        if ad in cari:
            raise HataDerleme(f"'{ad}' bu kapsamda zaten var",
                              satir, sutun)
        slot = self.slot_sayaci
        self.slot_sayaci += 1
        self.en_fazla = max(self.en_fazla, self.slot_sayaci)
        cari[ad] = (slot, tur)
        return slot

    def bul(self, ad, satir, sutun):
        for kap in reversed(self.kapsam):   # ic kapsamdan disa
            if ad in kap:
                return kap[ad]
        raise HataDerleme(f"tanımsız değişken '{ad}'",
                          satir, sutun)
```

Deyimlerin denetimi, kapsamları ve türleri birlikte kullanır. Dikkat edilmesi gereken bir sıra vardır: `let x = e;` deyiminde önce `e` analiz edilir, sonra `x` tanımlanır. Böylece `let x = x + 1;` içindeki sağ taraftaki `x` dıştaki `x`'e bağlanır. Bu sıra değişseydi program, kendi tanımını kendi başlangıç değeri için kullanmaya çalışırdı.

```python
    def beklenen(self, gercek, bekl, dugum):
        if gercek != bekl:
            raise HataDerleme(f"tür uyuşmazlığı: {bekl} "
                              f"bekleniyordu, "
                              f"{gercek} bulundu",
                              getattr(dugum, "satir", 0),
                              getattr(dugum, "sutun", 0))

    def blok(self, ss):
        self.kapsam.append({})
        for s in ss:
            self.deyim(s)
        self.kapsam.pop()
```

Deyim denetimi, aynı kapsam ve tür fonksiyonlarını kullanır. Atama için hedef değişkenin türü, sağ taraf ile karşılaştırılır.

```python
    def deyim(self, s):
        if isinstance(s, Let):
            tur = self.ifade(s.ifade)       # önce ifade, sonra tanım
            s.slot = self.bildir(s.ad, tur, s.satir, s.sutun)
        elif isinstance(s, Ata):
            slot, tur0 = self.bul(s.ad, s.satir, s.sutun)
            self.beklenen(self.ifade(s.ifade), tur0, s)
            s.slot = slot
        elif isinstance(s, Yaz):
            self.ifade(s.ifade)
        elif isinstance(s, Ifade):
            self.ifade(s.ifade)
        elif isinstance(s, Eger):
            self.beklenen(self.ifade(s.kosul), "bool", s.kosul)
            self.blok(s.dal)
            if s.dal_degil is not None:
                self.blok(s.dal_degil)
        elif isinstance(s, Dongu):
            self.beklenen(self.ifade(s.kosul), "bool", s.kosul)
            self.blok(s.govde)
        elif isinstance(s, Don):
            if not self.fn_icinde:
                raise HataDerleme("'return' yalnız fn içinde",
                                  s.satir, s.sutun)
            self.beklenen(self.ifade(s.ifade), "int", s.ifade)
        else:
            raise AssertionError(f"bilinmeyen deyim {type(s)}")
```

Son kesit ifadelerin türünü hesaplar. Sayılar `int`, `true` ve `false` `bool`dur; işleçler ya `int` ya `bool` üretir; çağrı her zaman `int` döndürür (bu, Mini'de bilinçli bir sadeleştirmedir). Karşılaştırma işleçleri (`<`, `>`) `bool` üretir ama yalnızca `int` alabilir; eşitlik işleçleri (`==`, `!=`) iki tarafın aynı türde olmasını ister.

```python
    def ifade(self, e):
        if isinstance(e, Sayi):
            return "bool" if isinstance(e.deger, bool) else "int"
        if isinstance(e, Degisken):
            slot, tur = self.bul(e.ad, e.satir, e.sutun)
            e.slot = slot
            return tur
        if isinstance(e, Tekli):
            self.beklenen(self.ifade(e.ey), "int", e.ey)
            return "int"
        if isinstance(e, Ikili):
            a = self.ifade(e.sol)
            b = self.ifade(e.sag)
            if e.op in ("==", "!="):
                self.beklenen(b, a, e.sag)
                return "bool"
            self.beklenen(a, "int", e.sol)
            self.beklenen(b, "int", e.sag)
            return "bool" if e.op in KARSILASTIRMA else "int"
        if isinstance(e, Cagri):
            f = self.fonksiyonlar.get(e.ad)
            if f is None:
                raise HataDerleme(f"tanımsız fonksiyon '{e.ad}'",
                                  e.satir, e.sutun)
            if len(e.args) != len(f.params):
                raise HataDerleme(
                    f"'{e.ad}' {len(f.params)} argüman ister, "
                    f"{len(e.args)} verildi", e.satir, e.sutun)
            for a in e.args:
                self.beklenen(self.ifade(a), "int", a)
            return "int"
        raise AssertionError(f"bilinmeyen ifade {type(e)}")
```

Analizcinin nasıl davrandığını üç hatalı ve bir doğru programla görelim. Her program ayrı bir `vm_ile_calistir` çağrısıyla çalışır; hatalı olanlar `HataDerleme` fırlatır ve konumu taşır.

```python
# -*- coding: utf-8 -*-
"""Kapsam ve hata örnekleri: çıktıları bölümde gösterilir."""
from mini import vm_ile_calistir
from mini_on import HataDerleme

kapsam = """
let x = 1;
let y = x + 1;
if (y > 1) {
    let x = y * 10;
    print x;
}
print x;
"""
print("kapsam:", vm_ile_calistir(kapsam).ciktilar)

hatalar = [
    "let a = 1;\nprint z;",
    "let a = 1;\nlet b = a + true;",
    "fn f(x) { return x; }\nprint f(1, 2);",
]
for k in hatalar:
    try:
        vm_ile_calistir(k)
    except HataDerleme as e:
        print("HATA", e)
```

Çıktı şöyle:

```term
$ python anlam_ornek.py
kapsam: [20, 1]
HATA 2:7  tanımsız değişken 'z'
HATA 2:13  tür uyuşmazlığı: int bekleniyordu, bool bulundu
HATA 2:7  'f' 1 argüman ister, 2 verildi
```

Birinci sonuç gölgelemeyi gösteriyor: iç bloktaki `x` (değeri 20) yalnızca o blokta görünür; dıştaki `x` (değeri 1) blok bittikten sonra geri gelir. İkinci üç hata iyi bir hata mesajının üç parçasını taşır: konum (`2:7`), sorun (tanımsız değişken), bağlam (hangi isim). Üçüncüsünde mesaj sayıları da söylüyor: `f` bir argüman bekliyor, iki verildi. Derleyici bu bilgiyi bilir, çünkü imza toplama aşamasında kaydedilmiştir (`analiz` fonksiyonunun ilk döngüsü).

Doruk'ta anlamsal analiz `SemanticAnalyzer.cpp` içindedir ve aynı `Ziyaretci` arayüzünü uygular; her düğüm türü için bir ziyaretçi metodu vardır. Bu sayede hem tür denetimi hem de tanımsız isim tespiti aynı ağaç dolaşımında yapılır. Bu bölümün Kod Okuma egzersizinde bu sınıfın bir kesitini okuyacaksın.

## 37.6 Ara gösterim: üç adresli kod, temel bloklar ve SSA

AST, insan için iyi bir biçimdir ama optimizasyon için kötüdür: düğümler dallanır, her optimizasyon ağacı yeniden yazmak zorunda kalır. Bu yüzden derleyiciler **ara gösterim (intermediate representation, IR)** kullanır. En yaygın IR biçimi **üç adresli kod (three-address code)**dur: her komutun en çok üç operandı vardır ve çoğu zaman `x = y op z` biçimindedir. Karmaşık bir ifade, geçici değişkenlere (`t1`, `t2`) bölünerek düz bir dizi olur:

```
x = 2 * 3          ; t1 = x + 4 gibi her ara sonuç bir isme yazılır
t1 = x + 4
y = t1 * a
```

Üç adresli kodun gücü, her komutun tek bir işlem yapması ve her ara değerin bir isme sahip olmasıdır. Bu, optimizasyonların (sabit katlama, ortak alt ifade eleme, ölü kod silme) kolay yazılmasını sağlar. Dezavantajı, ara değerler çok olduğunda program gövdesinin kalabalıklaşmasıdır; ama bu bir optimizasyon sorunudur, biçim sorunu değildir.

Üç adresli kodda **dallanma** iki komutla yapılır: koşulsuz atlama (`goto L`) ve koşullu atlama (`if_false t goto L`). Bu komutların arasında kalan düz komut dizilerine **temel blok (basic block)** denir. Bir temel bloğun iki özelliği vardır: yalnızca başından girilir (ilk komut bir etiket olabilir) ve yalnızca sonundan çıkılır (son komut bir atlama olabilir). Temel bloklar bir **kontrol akış grafının (control-flow graph, CFG)** düğümleri olur; kenarlar olası atlama yollarını gösterir.

Aşağıdaki örnek IR programı, Bölüm 37.7'deki optimizasyonun girdisidir. Program `x = 2 * 3` ile başlar, `t2 = 5 * 5` sonucuna göre dallanır ve bir bölümü hiç erişilemeyen `y = 0` komutu içerir.

```term
$ cat ornek.ir
x = 2 * 3
t1 = x + 4
y = t1 * a
t2 = 5 * 5
if_false t2 goto L1
goto L2
y = 0
L1:
print y
L2:
print x
```

Bu programın temel blokları ve kontrol akış grafı Şekil 37.5'te gösterilmiştir. `blok_bol` işlevi, lider adı verilen komutları (ilk komut, her atlamanın hedefi ve her atlamadan hemen sonraki komut) bulup blokları bu liderlere göre keser.

![Şekil 37.5: Örnek IR programının temel blokları ve kontrol akış grafı. B0 koşullu dallanır; B2 hiçbir kenarla ulaşılmaz (ölü blok). N = 5 blok, E = 5 kenar ve P = 1 bileşen için döngüsel karmaşıklık V(G) = E - N + 2P = 2 çıkar (Bölüm 23'teki McCabe ölçüsü).](gorseller/b37_temel_blok.png)

Şekildeki ölü blok, optimizasyonun ilk hedeflerinden biridir: hiçbir kenar ona ulaşmadığı için içindeki komut hiçbir zaman çalışmaz ve silinebilir. Bölüm 23'te gördüğümüz döngüsel karmaşıklık ölçüsü, kontrol akış grafından aynı biçimde hesaplanır; ölü bloklar bu sayıyı yanıltabilir, çünkü grafa girerler ama çalışmazlar.

Modern derleyicilerin çoğu, optimizasyonları kolaylaştırmak için **SSA (static single assignment)** biçimini kullanır: her değişken programda tam bir kez atanır. Bir değişken birden çok yerde atanıyorsa, her atama yeni bir isim alır (`x1`, `x2`), ve iki yol birleştiğinde hangi değerin geçerli olduğunu seçen özel bir **φ (fi)** düğümü konur:

![Şekil 37.6: SSA'da φ düğümü. if ve else dallarında x'e iki farklı değer yazılır (x1, x2); birleşme noktasında x3 = φ(x1, x2) kararı, gelinen kenara göre doğru değeri seçer. φ bir makine komutu değildir; kavramsaldır.](gorseller/b37_ssa_phi.png)

SSA'nın değeri, "bu değişkenin değeri nereden geliyor?" sorusunun cevabını her kullanımda tek bir atamaya bağlamasıdır. Sabit yayılımı, ölü kod eleme ve birçok döngü optimizasyonu bu tek-atama özelliğiyle çok daha basit yazılır. Makine koduna inmeden önce φ düğümleri kaldırılır; bu, kayıt tahsisi sırasında birleşme noktasında değerlerin aynı yazmaca konmasıyla yapılır (genel bilgi).

Bu teoriyi gerçek bir derleyicide gözlemleyebiliriz. GCC, `-fdump-tree-gimple` bayrağıyla kendi ara gösterimini (GIMPLE) bir dosyaya döker. Aşağıdaki küçük C fonksiyonunda, `olu` değişkeninin hiç kullanılmadığına dikkat et:

```c
int ara(int x) {
    int a = 2 * 3 + 4;
    int olu = x * 9;
    return a * x + 0;
}
```

GCC'nin GIMPLE dökümü, ön işlemeden ve ayrıştırmadan sonra, ama optimizasyondan önceki hâli gösterir:

```term
$ gcc -O2 -fdump-tree-gimple -c ara.c
int ara (int x)
{
  int D.2744;
  int a;
  int olu;

  a = 10;
  olu = x * 9;
  D.2744 = a * x;
  return D.2744;
}
```

Bu dökümde iki şey görünüyor. `2 * 3 + 4` ifadesi zaten `a = 10` olmuş: katlama ön uçta yapılmış. Ama `olu = x * 9` hâlâ duruyor; ölü kod silme henüz çalışmadı. Dökümün sonraki (optimize edilmiş) hâli, Bölüm 37.7'de gösterilecek.

## 37.7 Optimizasyon: programı aynı sonucu veren daha hızlı bir biçime çevirmek

Optimizasyon, programın anlamını değiştirmeden daha az iş yapmasını sağlayan dönüşümlerdir. "Anlamı değiştirmeden" kısıtı kritiktir: hızlı ama yanlış sonuç veren bir derleyici, hiç derleyici olmamasından daha kötüdür. Bu yüzden her optimizasyon bir **güvenlik koşulu** taşır ve bu koşul sağlanmadıkça uygulanmaz.

Optimizasyonların bazıları tek bir temel bloğun içinde yapılır (**yerel**), bazıları kontrol akış grafının tamamına bakar (**global**), bazıları döngülerin içini hedefler, bazıları da fonksiyon sınırlarını aşar (**fonksiyonlar arası**). Aşağıdaki liste, bu bölümde konuşacağımız başlıca dönüşümleri ve nerede uygulandıklarını gösteriyor:

- **Sabit katlama (constant folding):** `2 * 3 + 4` derleme zamanında `10` olur. Güvenlik koşulu: işlenenler bilinen sabitler olmalı ve işlem bir hata üretmemeli (sıfıra bölme gibi).
- **Sabit yayılımı (constant propagation):** `x = 6` sonrasında `x` kullanılan yerlere `6` yazılır. Güvenlik koşulu: atama ile kullanım arasında `x` değişmemeli.
- **Ölü kod eleme (dead code elimination):** değeri hiç okunmayan atamalar ve hiçbir yoldan ulaşılamayan bloklar silinir.
- **Ortak alt ifade eleme (CSE, common subexpression elimination):** aynı ifadeyi iki kez hesaplamak yerine ilk sonucu saklarsın (genel bilgi).
- **Döngüden değişmez kod çıkarma (LICM):** döngü içinde değeri döngü boyunca değişmeyen bir ifade, döngünün dışına taşınır (genel bilgi).
- **Satır içine alma (inlining):** küçük bir fonksiyonun çağrısı, gövdesiyle değiştirilir; çağrı yükü kalkar (genel bilgi).
- **Kuyruk çağrısı optimizasyonu (TCO):** bir fonksiyonun son işi kendi kendini çağırmaksa, çağrı bir döngüye dönüşür. Bölüm 15.4'te bunu gördük.

Bu listenin her maddesi bir öğrenme deneyi olarak yazılabilir, ama biz en temel üçünü gerçekten yazıp ölçeceğiz: sabit katlama, sabit yayılımı ve ölü kod. Mini'nin ara gösterimi üzerinde çalışan küçük bir optimize edici yazıyoruz. Bu modül `ir_opt.py` dosyasında; önce ayrıştırma ve yorumlama, sonra geçişler.

```python
# -*- coding: utf-8 -*-
"""Küçük üç adresli IR: sabit katlama, ölü kod ve temel bloklar.

Komutlar (her satır bir komut):
  x = y          kopyalama (y sabit ya da isim)
  x = y op z     ikili işlem, op: + - *
  if_false x goto L
  goto L
  L:             etiket
  print x
"""
OPS = {"+": lambda a, b: a + b, "-": lambda a, b: a - b,
       "*": lambda a, b: a * b}


def sayi(x):
    return x.lstrip("-").isdigit()


def ayristir(metin):
    out = []
    for s in metin.strip().splitlines():
        p = s.split()
        if p[0].endswith(":"):
            out.append(("LABEL", p[0][:-1]))
        elif p[0] == "goto":
            out.append(("GOTO", p[1]))
        elif p[0] == "print":
            out.append(("PRINT", p[1]))
        elif p[0] == "if_false":
            out.append(("IFFALSE", p[1], p[3]))
        elif len(p) == 3:                    # x = y
            out.append(("COPY", p[0], p[2]))
        else:                                # x = y op z
            out.append(("BIN", p[0], p[3], p[2], p[4]))
    return out
```

IR'ın yorumcusu, optimizasyonun doğruluğunu ölçmek için gereklidir: aynı girdi ile önce ve sonra aynı çıktıyı üretmelidir. Yorumcu ayrıca çalıştırılan komut sayısını döndürür; bu, optimizasyonun işini ne kadar azalttığını gösteren ikinci bir ölçüdür.

```python
def calistir(prog, girdi):
    """Yorumcu: (print çıktıları, çalışan komut sayısı)."""
    env = dict(girdi)
    etiket = {k[1]: i for i, k in enumerate(prog) if k[0] == "LABEL"}

    def v(x):
        return int(x) if sayi(x) else env[x]
    pc, cikti, adim = 0, [], 0
    while pc < len(prog):
        k = prog[pc]
        pc += 1
        adim += 1
        if k[0] == "COPY":
            env[k[1]] = v(k[2])
        elif k[0] == "BIN":
            env[k[1]] = OPS[k[2]](v(k[3]), v(k[4]))
        elif k[0] == "IFFALSE" and not v(k[1]):
            pc = etiket[k[2]]
        elif k[0] == "GOTO":
            pc = etiket[k[1]]
        elif k[0] == "PRINT":
            cikti.append(v(k[1]))
    return cikti, adim
```

Sabit katlama ve sabit yayılımı birlikte yapılır. Bir blok içinde, bilinen sabit değerler bir sözlükte tutulur. Bir komut sabit işlenenlerle çalışıyorsa hesaplanır ve sonucu bir `COPY` olarak yazılır. Koşullu dallanmada koşul bir sabitse dal kaldırılır (koşul sıfırsa koşulsuz atlamaya dönüşür, sıfır değilse hiç oluşmaz). Blok sınırında (her etiket) sözlük sıfırlanır, çünkü bir bloğa birden çok yoldan girilebilir ve o noktada değerlerin ne olduğu bilinmez.

```python
def _kaydet(sabit, ad, a):
    if sayi(a):
        sabit[ad] = int(a)
    else:
        sabit.pop(ad, None)


def sabit_katla(prog):
    """Blok içi sabit yayılımı ve katlama; koşulu sadeleştirir."""
    out, sabit = [], {}

    def c(x):
        return str(sabit[x]) if x in sabit else x
    for k in prog:
        if k[0] == "LABEL":
            sabit = {}                       # bloğa giriş: sıfırla
            out.append(k)
        elif k[0] == "COPY":
            a = c(k[2])
            _kaydet(sabit, k[1], a)
            out.append(("COPY", k[1], a))
        elif k[0] == "BIN":
            a, b = c(k[3]), c(k[4])
            if sayi(a) and sayi(b):
                v = str(OPS[k[2]](int(a), int(b)))
                _kaydet(sabit, k[1], v)
                out.append(("COPY", k[1], v))
```

```python
            else:
                sabit.pop(k[1], None)
                out.append(("BIN", k[1], k[2], a, b))
        elif k[0] == "IFFALSE":
            kosul = c(k[1])
            if not sayi(kosul):
                out.append(("IFFALSE", kosul, k[2]))
            elif int(kosul) == 0:            # her zaman atlar
                out.append(("GOTO", k[2]))   # sıfırsa dal yok
        elif k[0] == "PRINT":
            out.append(("PRINT", c(k[1])))
        else:
            out.append(k)
    return out
```

Erişilemez kod, bir `goto`'dan sonra gelen ve hedefi olan bir etikete kadar uzanan komutlardır. Hedefi olmayan etiketler de (artık hiçbir atlama onları işaret etmiyorsa) gereksiz olur. Bu iki geçiş birlikte çalışır: erişilemez kodu silmek, bazı etiketleri hedefsiz bırakır; hedefsiz etiketleri silmek, bazı atlamaları gereksiz kılar.

```python
def hedefler(prog):
    return {k[-1] for k in prog if k[0] in ("GOTO", "IFFALSE")}


def erisilemez_sil(prog):
    """goto'dan sonra, HEDEFİ OLAN bir etikete kadar sil."""
    hedef = hedefler(prog)
    out, olu = [], False
    for k in prog:
        if k[0] == "LABEL" and k[1] in hedef:
            olu = False
        if not olu:
            out.append(k)
            if k[0] == "GOTO":
                olu = True
    return out


def gereksiz_atlama_sil(prog):
    """'goto L' hemen 'L:' önceyse atlama boştur: sil."""
    out = []
    for i, k in enumerate(prog):
        sonraki = prog[i + 1] if i + 1 < len(prog) else None
        if k[0] == "GOTO" and sonraki == ("LABEL", k[1]):
            continue
        out.append(k)
    return out


def etiket_sil(prog):
    hedef = hedefler(prog)
    return [k for k in prog if k[0] != "LABEL" or k[1] in hedef]
```

Ölü atama silme, canlı değişken analizi denen bir geri yönlü veri akışı çözümlemesi gerektirir. Bir değişken, bir noktadan sonra okunacaksa **canlıdır**. Bir atama, yazdığı değişken o noktada canlı değilse ölüdür ve silinebilir. Analiz, kontrol akışının tersine doğru ilerler: bir komutun canlı girdisi, kendi okumalarıyla ve çıkışındaki canlı değişkenlerden yazdığı değişkenin çıkarılmasıyla bulunur. Kümeler değişmeyene kadar tekrarlanır (sabit nokta).

```python
def ardil(prog, i, etiket):
    k = prog[i]
    if k[0] == "GOTO":
        return [etiket[k[1]]]
    if k[0] == "IFFALSE":
        return [i + 1, etiket[k[2]]]
    return [i + 1] if i + 1 < len(prog) else []


def kullanim(k):
    """(okunan isimler, yazılan isim): sabitler okunmaz."""
    if k[0] == "COPY":
        oku, yaz = [k[2]], k[1]
    elif k[0] == "BIN":
        oku, yaz = [k[3], k[4]], k[1]
    elif k[0] in ("IFFALSE", "PRINT"):
        oku, yaz = [k[1]], None
    else:
        oku, yaz = [], None
    return {x for x in oku if not sayi(x)}, yaz
```

```python
def olu_atamalari_sil(prog):
    """Canlı değişken analizi (geriye doğru sabit nokta)."""
    etiket = {k[1]: i for i, k in enumerate(prog) if k[0] == "LABEL"}
    n = len(prog)
    canli = [set() for _ in range(n)]
    degisti = True
    while degisti:
        degisti = False
        for i in range(n - 1, -1, -1):
            cikis = set().union(*[canli[j]
                                  for j in ardil(prog, i, etiket)])
            oku, yaz = kullanim(prog[i])
            giris = oku | (cikis - {yaz})
            if giris != canli[i]:
                canli[i] = giris
                degisti = True
    out = []
    for i, k in enumerate(prog):
        if k[0] in ("COPY", "BIN"):
            cikis = set().union(*[canli[j]
                                  for j in ardil(prog, i, etiket)])
            if k[1] not in cikis:            # hiç okunmuyor: ölü
                continue
        out.append(k)
    return out
```

Blok bölme ve geçişleri sabit noktaya kadar çalıştıran sürücü son iki kesittedir. Sürücü, bir tur tüm geçişleri uygular ve sonuç bir öncekiyle aynıysa durur. Bu döngü neden gerekli? Çünkü bir geçişin ürettiği fırsat, diğerinin işine yarar: sabit yayılımı bir atlamayı sabit koşulla kaldırır, bu da bir bloğu erişilemez kılar, bu da bir değişkeni ölü bırakır. Yalnızca bir kez çalıştırırsan bu zincirin tamamını yakalayamazsın.

```python
def blok_bol(prog):
    """Lider: ilk komut, atlama hedefleri, atlamadan sonraki komut."""
    etiket = {k[1]: i for i, k in enumerate(prog) if k[0] == "LABEL"}
    lider = {0} | set(etiket.values())
    for i, k in enumerate(prog):
        if k[0] in ("GOTO", "IFFALSE"):
            lider |= {i + 1, etiket[k[-1]]}
    lider = sorted(x for x in lider if x < len(prog))
    return [(a, prog[a:b])
            for a, b in zip(lider, lider[1:] + [len(prog)])]


def optimize(prog):
    """Geçişleri değişiklik kalmayana dek uygula."""
    while True:
        t = prog
        for g in (sabit_katla, erisilemez_sil, gereksiz_atlama_sil,
                  etiket_sil, olu_atamalari_sil):
            t = g(t)
        if t == prog:
            return prog
        prog = t
```

```python
ORNEK = """
x = 2 * 3
t1 = x + 4
y = t1 * a
t2 = 5 * 5
if_false t2 goto L1
goto L2
y = 0
L1:
print y
L2:
print x
"""

if __name__ == "__main__":
    once = ayristir(ORNEK)
    sonra = optimize(once)
    girdi = {"a": 7}
    c1, a1 = calistir(once, girdi)
    c2, a2 = calistir(sonra, girdi)
    say = lambda p: len([k for k in p if k[0] != "LABEL"])
    print("önce  komut:", say(once), " çalışma adımı:", a1)
    print("sonra komut:", say(sonra), " çalışma adımı:", a2)
    print("çıktı önce :", c1, " sonra:", c2)
    assert c1 == c2
    for i, (b, komutlar) in enumerate(blok_bol(sonra)):
        print(f"B{i} (komut {b}): {komutlar}")
```

Örnek programı çalıştırdığımızda çıktı şöyledir:

```term
$ python ir_opt.py
önce  komut: 9  çalışma adımı: 8
sonra komut: 1  çalışma adımı: 1
çıktı önce : [6]  sonra: [6]
B0 (komut 0): [('PRINT', '6')]
```

Dokuz komutluk program, bir komuta indi ve çıktısı değişmedi. Her geçişin sayıya etkisini görmek için, geçişlerin tur tur uygulanmasını ölçtük; sonuçlar `engine/veri/b37_ir.csv` dosyasındadır ve Şekil 37.7'de çizilmiştir:

| Tur | Geçiş | Komut sayısı |
|---|---|---|
| 0 | başlangıç | 9 |
| 1 | sabit katlama ve yayılım | 8 |
| 1 | erişilemez kod silme | 6 |
| 1 | gereksiz atlama silme | 5 |
| 1 | etiket silme | 5 |
| 1 | ölü atama silme | 2 |
| 2 | (birinci tur sonrası geçişler) | 2, 2, 2, 2, 1 |
| 3 | (sabit nokta: değişiklik yok) | 1 |

![Şekil 37.7: IR optimizasyonunda her geçişten sonra komut sayısı. İlk tur sabit katlamayla başlar ve erişilemez kodu siler; ikinci tur ölü atamayı kaldırır; sabit noktada program tek bir PRINT komutuna iner.](gorseller/b37_optimizasyon.png)

Tablo bir gerçeği gösteriyor: geçişler birbirini besler. İlk tur sabit katlamayla başlar ama `print x` komutu hâlâ `x`'e bakar, çünkü blok sınırında sözlük sıfırlandı. Erişilemez kod silinince etiket ve atlama sadeleşir; ikinci turda `x`'in değeri bloklar arasında bilinir hâle gelir ve `print 6` olur. Bu zincir yalnızca sabit noktaya kadar tekrarlandığında yakalanır.

Bu sonuç, derleyicinin kendi davranışıyla karşılaştırılabilir. GCC'nin `-O0` ve `-O2` çıktılarını aynı kaynakta görelim. Önce `sabit()` fonksiyonu: `return 2 * 3 + 4;` ifadesi, `-O0`'da bile tek bir `movl $10` komutuna dönüşüyor. (Aşağıdaki listelerde `.cfi` ve hizalama yönergeleri, okunabilirlik için çıkarılmıştır.) Yani katlama, optimizasyon bayrağından bağımsız olarak ön uçta yapılmış.

```term
$ gcc -O0 -S toplam.c
sabit:
	endbr64
	pushq	%rbp
	movq	%rsp, %rbp
	movl	$10, %eax
	popq	%rbp
	ret

$ gcc -O2 -S toplam.c
sabit:
	endbr64
	movl	$10, %eax
	ret
```

`-O0`'da fonksiyon bir çerçeve kurup (`pushq %rbp`, `movq %rsp, %rbp`) sonra çerçeveyi kapatıyor; `-O2`'de yalnızca `movl $10, %eax` ve `ret` var. Çerçeve kurmanın maliyeti ve `-O0`'ın neden hata ayıklamaya uygun olduğu Bölüm 24'te anlatıldı; burada yalnızca katlamanın her iki düzeyde de yapıldığını görüyoruz.

Ölü kod eleme ve sabit yayılımın gcc'deki karşılığını Bölüm 37.6'daki GIMPLE dökümünün optimize edilmiş hâlinde görebilirsin (dökümün `;; Function` başlık satırı okunabilirlik için çıkarılmıştır). `ara` fonksiyonunda `olu` değişkeni kaybolmuş ve `a * x` ifadesi `x * 10`'a dönüşmüş:

```term
$ gcc -O2 -fdump-tree-optimized -c ara.c
int ara (int x)
{
  int _2;

  <bb 2> [local count: 1073741824]:
  _2 = x_1(D) * 10;
  return _2;

}
```

Bu dökümde `a = 10` sabit yayılımıyla `a * x`'e geçti, ardından `olu` ölü olduğu için silindi. Makine kodu da buna uyuyor. `-O2` ile `ara` fonksiyonunun derlenmiş hâli şöyle:

```term
$ gcc -O2 -S ara.c
ara:
	endbr64
	leal	(%rdi,%rdi,4), %eax
	addl	%eax, %eax
	ret
```

Bu üç komut, `x * 10` işlemini bir çarpma komutu yerine `lea` ve `add` ile yapar: `x * 5` (`leal (%rdi,%rdi,4)`) ve ardından iki katına çıkarma (`addl %eax, %eax`). Bu bir **güç azaltma (strength reduction)** örneğidir: pahalı bir çarpma, daha ucuz komutlarla değiştirilmiştir. Derleyici bunu hedef makinenin komut maliyetlerine göre seçer (genel bilgi).

Son olarak kuyruk çağrısı. Bölüm 15.4'te Python'un bu optimizasyonu yapmadığını ve gcc'nin `-O2`'de bir kuyruk özyinelemesini döngüye çevirdiğini görmüştük. Aynı fonksiyonu burada da derleyip çağrı komutunun kalıp kalmadığına bakıyoruz:

```c
long fak(long n, long acc) {
    return n <= 1 ? acc : fak(n - 1, acc * n);
}
```

`-O0`'da fonksiyon kendini çağırır (`call` komutu bir kez görünür); `-O2`'de hiç `call` yoktur, fonksiyon bir döngüye dönüşmüştür. Bu, Bölüm 15'teki kuyruk özyinelemesi kuralının makine düzeyindeki karşılığıdır: çağrı son iş olduğunda çerçeveyi açık tutmaya gerek kalmaz.

## 37.8 Kod üretimi: yığın makinesi, yazmaçlar ve çalışma zamanı

Optimize edilmiş ara gösterim artık makine koduna inmeye hazırdır. Bu adımda iki soru var: **hedef** ne olacak, ve **değerler nerede tutulacak**?

Hedef olarak iki ana model vardır. **Yığın makinesi (stack machine)**, işlenenleri bir yığında tutar; komutlar yığından çeker ve yığına iter. CPython ve JVM bu modeli kullanır; Bölüm 37.1'deki `dis` dökümünde gördüğün `LOAD_FAST` ve `BINARY_OP` komutları budur. **Yazmaç makinesi (register machine)**, değerleri adlandırılmış yazmaçlarda tutar; x86-64 ve ARM bu modeldedir. Yığın makinesinin kodu kısadır ve kolay üretilir, çünkü bir ifadenin değerlendirme sırası zaten yığın düzeniyle belirlenir. Yazmaç makinesi ise daha hızlıdır, çünkü yazmaç erişimi bellek erişiminden çok daha ucuzdur; ama yazmaçların sınırlı sayıda olması bir tahsis problemi yaratır.

Mini için yığın makinesini seçiyoruz; hem öğretici hem de hedefsiz. Derleyici, AST'yi dolaşıp her düğüm için yığın komutları yayar. İkili bir işlem, iki işleneni derleyip ardından işleci yayar; komutların sırası yığının doğru kurulmasını sağlar.

```python
# -*- coding: utf-8 -*-
"""Yigin makinesi bayt kodu derleyicisi ve sanal makine (VM)."""
import operator
from mini_on import (Sayi, Degisken, Ikili, Tekli, Cagri, Let, Ata,
                     Yaz, Eger, Dongu, Don, Ifade, Fonksiyon)


class CalismaHatasi(Exception):
    pass


def c_bol(a, b):
    """C99 gibi: tam sayı bölme sıfıra doğru yuvarlar (-7/2=-3)."""
    if b == 0:
        raise CalismaHatasi("sıfıra bölme")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def c_mod(a, b):
    return a - b * c_bol(a, b)


BIN = {"ADD": operator.add, "SUB": operator.sub,
       "MUL": operator.mul, "DIV": c_bol, "MOD": c_mod,
       "LT": operator.lt, "LE": operator.le,
       "GT": operator.gt, "GE": operator.ge,
       "EQ": operator.eq, "NE": operator.ne}
IKILI_OP = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
            "%": "MOD", "<": "LT", "<=": "LE", ">": "GT",
            ">=": "GE", "==": "EQ", "!=": "NE"}
```

Derleyicinin temel yapısı bir `Kod` nesnesi ve komut listesi üzerine kuruludur. Atlama hedefleri, hedef henüz bilinmediğinde bir yer tutucu ile yayılır ve sonra `yama` ile doldurulur. Bu, `if` ve `while` gibi ileri dallanmalar için gereklidir.

```python
class Kod:
    def __init__(self, ad, nlocals, nargs):
        self.ad = ad
        self.nlocals = nlocals
        self.nargs = nargs
        self.komutlar = []      # [op, arg] listesi


class Derleyici:
    def __init__(self):
        self.kod = None
        self.kodlar = {}

    def yay(self, op, arg=None):
        self.kod.komutlar.append([op, arg])
        return len(self.kod.komutlar) - 1

    def yama(self, idx):
        """Atlama hedefini simdiki konuma (sonraki komut) bağla."""
        self.kod.komutlar[idx][1] = len(self.kod.komutlar)

    def derle(self, program, main_locals):
        for d in program:
            if isinstance(d, Fonksiyon):
                self.kod = Kod(d.ad, d.nlocals, len(d.params))
                for s in d.govde:
                    self.deyim(s)
                self.yay("PUSH", 0)     # dusersen 0 dondur
                self.yay("RET")
                self.kodlar[d.ad] = self.kod
        self.kod = Kod("__main__", main_locals, 0)
        for d in program:
            if not isinstance(d, Fonksiyon):
                self.deyim(d)
        self.yay("HALT")
        self.kodlar["__main__"] = self.kod
        return self.kodlar
```

Deyimlerin derlenmesi, dallanma komutlarının nasıl kurulduğunu gösterir. `if` yalnızca `JZ` (sıfırsa atla) ve `JMP` ile yazılır; `while` ise başa dönen bir `JMP` ile biter. Bu iki kalıp, bütün yapısal kontrol akışının temelidir.

```python
    def deyim(self, s):
        if isinstance(s, (Let, Ata)):
            self.ifade(s.ifade)
            self.yay("STORE", s.slot)
        elif isinstance(s, Yaz):
            self.ifade(s.ifade)
            self.yay("PRINT")
        elif isinstance(s, Ifade):
            self.ifade(s.ifade)
            self.yay("POP")
        elif isinstance(s, Don):
            self.ifade(s.ifade)
            self.yay("RET")
        elif isinstance(s, Eger):
            self.ifade(s.kosul)
            jz = self.yay("JZ")
            for x in s.dal:
                self.deyim(x)
            if s.dal_degil is None:
                self.yama(jz)
            else:
                jmp = self.yay("JMP")
                self.yama(jz)
                for x in s.dal_degil:
                    self.deyim(x)
                self.yama(jmp)
        elif isinstance(s, Dongu):
            bas = len(self.kod.komutlar)
            self.ifade(s.kosul)
            jz = self.yay("JZ")
            for x in s.govde:
                self.deyim(x)
            self.yay("JMP", bas)
            self.yama(jz)
```

İfadelerin derlenmesi, AST'nin özyinelemeli dolaşımının doğrudan karşılığıdır: bir ikili düğüm, iki alt ifadeyi derler ve işleci yayar. Sayı `PUSH`, değişken `LOAD` olur.

```python
    def ifade(self, e):
        if isinstance(e, Sayi):
            self.yay("PUSH", e.deger)
        elif isinstance(e, Degisken):
            self.yay("LOAD", e.slot)
        elif isinstance(e, Tekli):
            self.ifade(e.ey)
            self.yay("NEG")
        elif isinstance(e, Ikili):
            self.ifade(e.sol)
            self.ifade(e.sag)
            self.yay(IKILI_OP[e.op])
        elif isinstance(e, Cagri):
            for a in e.args:
                self.ifade(a)
            self.yay("CALL", (e.ad, len(e.args)))
        else:
            raise AssertionError(type(e))
```

Yazmaç tahsisi ise bu bölümde yapmadığımız bir işlemdir. Bir yazmaç makinesi için derleyici, her değişkeni bir yazmaca (ya da bellek yerine) atamalıdır. Klasik yaklaşım **graf boyamadır**: iki değişken aynı anda canlıysa, bir kenarla bağlanırlar (girişim grafı); her renk bir yazmaca karşılık gelir ve komşu düğümler farklı renk almalıdır. Graf k renkle boyanamıyorsa bazı değişkenler belleğe **dökülür (spill)**. Bu problem NP-zordur, ama sezgisel algoritmalar pratikte iyi çalışır (genel bilgi; graf kavramı için Bölüm 11).

### VM: bayt kodunu çalıştırmak

Bayt kodu bir sanal makine tarafından yürütülür. VM'in durumu üç parçadan oluşur: işlenen yığını, çerçeveler (her çağrı için bir çerçeve: kod, komut sayacı ve yerel değişkenler) ve çıktı listesi. Aşağıdaki sınıf bu üçünü yönetir. Komutlar bir `if-elif` zinciriyle dallanır; her komut yığını ve çerçeveyi kendi kuralına göre değiştirir.

```python
class VM:
    def __init__(self, kodlar):
        self.kodlar = kodlar
        self.ciktilar = []
        self.komut_sayisi = 0

    def calistir(self, izle=None):
        """izle bir listeyse her komut için bilgi eklenir."""
        ana = self.kodlar["__main__"]
        yigin = []                             # islenen yığın
        # Cerceve: [kod, pc, yerel_slotlar]; çağrı = yeni çerçeve
        cerceve = [[ana, 0, [0] * ana.nlocals]]
        while True:
            c = cerceve[-1]
            op, arg = c[0].komutlar[c[1]]
            c[1] += 1
            self.komut_sayisi += 1
            if izle is not None:
                izle.append((c[0].ad, op, arg, list(yigin),
                             len(cerceve)))
            if op == "PUSH":
                yigin.append(arg)
            elif op == "LOAD":
                yigin.append(c[2][arg])
            elif op == "STORE":
                c[2][arg] = yigin.pop()
            elif op == "POP":
                yigin.pop()
            elif op in BIN:
                b = yigin.pop()
                a = yigin.pop()
                yigin.append(BIN[op](a, b))
            elif op == "NEG":
                yigin.append(-yigin.pop())
```

Döngünün geri kalanı, komutların anlamını tek tek verir. `CALL` komutunda argümanlar yığından alınıp yeni çerçevenin ilk yerel slotlarına yerleştirilir; `RET` ise dönüş değerini yığına geri koyarak çerçeveyi kapatır. Bu, çağrı yığınını Python'un kendi özyinelemesinden bağımsız bir veri yapısı olarak tutar; yani VM, Python'un özyineleme sınırına takılmadan derin çağrıları çalıştırabilir.

```python
            elif op == "JZ":
                if not yigin.pop():
                    c[1] = arg
            elif op == "JMP":
                c[1] = arg
            elif op == "PRINT":
                self.ciktilar.append(yigin.pop())
            elif op == "CALL":
                ad, argc = arg
                hedef = self.kodlar[ad]
                ilk = len(yigin) - argc
                args = yigin[ilk:]
                del yigin[ilk:]
                yerel = args + [0] * (hedef.nlocals - argc)
                cerceve.append([hedef, 0, yerel])
            elif op == "RET":
                deger = yigin.pop()
                cerceve.pop()
                yigin.append(deger)
            elif op == "HALT":
                return self.ciktilar
            else:
```

VM'in `izle` parametresi, her komuttan önceki durumu bir listeye kaydeder. Bu, çalışma zamanının iç işleyişini görmenin en doğrudan yoludur. Aşağıdaki küçük program `fn kare(x) { return x * x; } print kare(3) + 1;` ifadesini çalıştırıp her adımdaki yığını ve çerçeve derinliğini yazdırır:

```python
# -*- coding: utf-8 -*-
"""Yığın ve çerçeve izi: VM'in her komuttan önceki durumu."""
from mini import on_isle
from derle import Derleyici, VM

ornek = "fn kare(x) { return x * x; } print kare(3) + 1;"
program, ml = on_isle(ornek)
vm = VM(Derleyici().derle(program, ml))
iz = []
vm.calistir(iz)
for ad, op, arg, yigin, derinlik in iz:
    print(f"{ad:9} {op:6} {str(arg or ''):10} "
          f"yigin={yigin} derinlik={derinlik}")
```

Çıktı şöyle:

```term
$ python iz_yigin.py
__main__  PUSH   3          yigin=[] derinlik=1
__main__  CALL   ('kare', 1) yigin=[3] derinlik=1
kare      LOAD              yigin=[] derinlik=2
kare      LOAD              yigin=[3] derinlik=2
kare      MUL               yigin=[3, 3] derinlik=2
kare      RET               yigin=[9] derinlik=2
__main__  PUSH   1          yigin=[9] derinlik=1
__main__  ADD               yigin=[9, 1] derinlik=1
__main__  PRINT             yigin=[10] derinlik=1
__main__  HALT              yigin=[] derinlik=1
```

Bu izi Şekil 37.8'de yığın ve çerçeve olarak görselleştirdik. İz üç şeyi açık gösteriyor. Birincisi, `CALL` komutu argümanı (3) yığından alıp `kare` çerçevesinin 0. slotuna yerleştirir: `LOAD 0` komutları değeri oradan okur. İkincisi, `kare` içinde yığın, `MUL` sonucu olan `9` ile biter ve `RET` bu değeri yığına bırakır. Üçüncüsü, çağıran çerçevenin derinliği `2`'den `1`'e düşer; `ADD` sonucu `10`, `PRINT` ile çıktıya gider.

![Şekil 37.8: kare(3) + 1 programının yığın ve çerçeve izi. Sol sütun komutu ve çerçeveyi, sağ sütun komuttan sonraki işlenen yığınını gösterir. CALL argümanı yeni çerçeveye taşır; RET sonucu çağıranın yığınına geri koyar.](gorseller/b37_yigin_izi.png)

Bu yapı, gerçek bir makinedeki çağrı kurallarının bir modelidir. Gerçek işlemcilerde argümanlar yazmaçlarda ya da yığında, dönüş değeri bir yazmaçta taşınır; hangi argümanın hangi yazmaca gideceği ABI (uygulama ikili arayüzü) ile belirlenir. Bölüm 24.4'te System V AMD64 ve Windows x64 çağrı kurallarını görmüştük. Mini'nin kuralı kendi tasarımımızdır ve gerçek bir ABI değildir; ama aynı soruları cevaplar: argümanlar nerede, dönüş değeri nerede, yerel değişkenler nerede?

### Çalışma zamanı: çerçeveler, kapanışlar ve bellek

Bir fonksiyon çağrıldığında yerel değişkenleri ve dönüş bilgisini tutan bir **aktivasyon kaydı** (çerçeve) açılır; dönünce kapanır. Mini'de çerçeveler bir Python listesinde durur, ama gerçek makinelerde bu, yığın bölgesinde ardışık bellek adresleri olarak yaşar. Derinlemesine recursion ve yığın taşması Bölüm 15'te ayrıntılı işlendi.

**Kapanış (closure)** ise bir fonksiyonun, tanımlandığı kapsamdaki değişkenleri yakalayıp çağrıldığı yerde kullanabilmesidir. Mini'de iç içe fonksiyon yoktur, bu yüzden kapanış gerekmez; ama Python'da `def` içinde `def` yazıp dış değişkeni okuduğunda, iç fonksiyon dış çerçevenin o değişkenine bir referans taşır. Bu referans, dış çerçeve çağrı bittikten sonra da yaşamaya devam edebilir: kapanış, çerçevenin ömrünü uzatır (genel bilgi).

Bellek yönetimi, çalışma zamanının son büyük parçasıdır. Bölüm 3'te CPython'un **referans sayma** ile bellek yönettiğini gördük: her nesne kendisine bağlı isim sayısını tutar ve sayı sıfırlanınca bellek geri verilir. Döngüsel referansları bu yöntem yakalayamaz; bunun için CPython ayrıca bir çöp toplayıcı çalıştırır. Bölüm 37.1'deki gc demosu bunu gösteriyor: iki nesne birbirini gösteriyordu, `gc.collect()` `8` nesneyi topladı (bu sayı Python sürümüne ve nesne sayısına göre değişir).

Diğer iki temel yaklaşım şunlardır (genel bilgi). **İşaretle-süpür (mark-and-sweep)**: kök nesnelerden başlayıp erişilebilen her nesneyi işaretlersin, işaretsiz nesneler süpürülür. Referans sayının döngü sorununu çözer, ama duraklama üretebilir. **Nesil (generational)** toplayıcılar, çoğu nesnenin kısa ömürlü olduğu gözleminden yararlanır: yeni nesneler sık, eskiler seyrek taranır. JVM ve .NET bu yaklaşımı kullanır. Gömülü ve gerçek zamanlı sistemlerde, Bölüm 2'de söylediğimiz gibi, toplayıcının duraklaması kabul edilemezse bellek elle ya da bölgesel (arena) ayırıcılarla yönetilir.

Python'un referans sayacının bir bedeli de vardır: her atamada sayacı güncellemek gerekir, ve bu, çok iş parçacıklı programlarda bir kilit (GIL) ihtiyacı doğurur. Bu konu Bölüm 53'te açılacak.

## 37.9 Bağlayıcı ve yükleyici: sembol, yer değiştirme ve çalışma anı

Derleyici bir kaynak dosyayı bitirdiğinde, çıktısı genellikle çalıştırılabilir bir program değil, bir **nesne dosyasıdır**. Nesne dosyası makine kodunu ve verileri taşır, ama iki eksiği vardır: bazı adresler henüz bilinmez (başka dosyalarda tanımlanan fonksiyonlar ve veriler) ve hiçbir bellek adresi kesin değildir (program nerede yüklenecek?). Bağlayıcı (linker) bu eksikleri kapatır; yükleyici (loader) programı belleğe yerleştirir ve bağlanmamış kalan dış referansları çalışma anında çözer.

Bu süreci bir örnek üzerinde görelim. İki kaynak dosyamız var. `toplam.c` iki fonksiyon tanımlar; `prog.c` bunlardan birini çağırır ve `printf` kullanır.

```c
int kare_topla(int a, int b) { return a * a + b; }
int sabit(void) { return 2 * 3 + 4; }
```

```c
#include <stdio.h>
int kare_topla(int a, int b);
int main(void) {
    printf("%d\n", kare_topla(3, 4));
    return 0;
}
```

Bu dosyaları WSL'de (Ubuntu 24.04, GCC 13.3) derleyip inceledik. Önce her dosyayı nesne dosyasına çevirdik, sonra sembolleri ve yer değiştirmeleri okuduk, sonra bağladık ve çalıştırdık:

```term
$ nm prog.o
                 U kare_topla
0000000000000000 T main
                 U printf

$ gcc prog.o toplam.o -o prog
$ nm prog | grep -E " (main|kare_topla|sabit|printf)"
000000000000117d T kare_topla
0000000000001149 T main
                 U printf@GLIBC_2.2.5
000000000000119a T sabit

$ ldd ./prog
	linux-vdso.so.1 (0x00007ffcee3f3000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007e17dcc00000)
	/lib64/ld-linux-x86-64.so.2 (0x00007e17dcef8000)

$ ./prog
13
```

Çıktıda üç şeyi ayırt et. `nm` komutu sembol tablosunu gösterir: `T` harfi bu dosyada **tanımlı** bir sembol (metin bölümünde), `U` harfi **tanımsız** (başka yerde tanımlanacak) demektir. `prog.o`'da `kare_topla` ve `printf` U'dur; `main` ise T'dir.

Yer değiştirme (relocation) kayıtları, bağlayıcının neyi düzeltmesi gerektiğini söyler. `readelf -r prog.o` komutu `prog.o` için üç kayıt gösterir; `main` içindeki iki çağrı ve bir veri referansı:

| Ofset | Tür | Sembol |
|---|---|---|
| `0x13` | `R_X86_64_PLT32` | `kare_topla` |
| `0x1c` | `R_X86_64_PC32` | `.rodata` |
| `0x29` | `R_X86_64_PLT32` | `printf` |

Her kayıt, o ofsetteki dört baytlık değerin (bir `call` komutunun göreli hedefi ya da bir veri adresi) bağlayıcı tarafından yeniden hesaplanması gerektiğini söyler. Bağlantı sonrası `nm prog` çıktısında `kare_topla` artık `0x117d` adresinde tanımlıdır; `call` komutunun hedefi bu adrese göre hesaplanır.

![Şekil 37.9: Bağlama öncesi nesne dosyası (solda) ve bağlama sonrası çalıştırılabilir (sağda). Nesnede çağrının hedefi boştur ve yer değiştirme kaydıyla işaretlenir; bağlayıcı hedefi kare_topla'nın gerçek adresiyle doldurur. printf ise libc içindeki bir PLT girişine yönlenir.](gorseller/b37_baglayici.png)

`printf` farklıdır: onun kodu programın içine gömülmez. `ldd` çıktısı bunu açıklar: program `libc.so.6` paylaşımlı kütüphanesine bağlıdır ve bu kütüphane çalışma anında yüklenir. Yükleyici (`ld-linux-x86-64.so.2`) başlarken `printf`'in gerçek adresini bulur ve PLT/GOT tablosuna yazar; ilk çağrıda bu çözümleme yapılabilir (genel bilgi). Bu, **dinamik bağlama**dır: program küçük kalır, kütüphane güncellenirse yeni sürüm kullanılır. Bunun karşıtı **statik bağlama**dır: `printf` de programın içine kopyalanır.

Statik bağlamanın boyutunu ölçtük: `gcc -static prog.o toplam.o -o prog_static` ile üretilen dosya 785 408 bayt, dinamik bağlı `prog` ise 16 056 bayt. Statik dosya büyüktür ama dağıtımı kolaydır (libc yüklü olmasa da çalışır). Gömülü sistemlerde bu seçim doğrudan flash belleği etkiler; Bölüm 43'te bare-metal C'de bu konuya döneceğiz (bağlayıcı betiği, bölüm yerleşimi ve başlangıç kodu orada işlenecek).

Bağlayıcının iki yaygın hatası vardır ve ikisini de Bölüm 4.4'te gördün. Sembol tanımlı değilse `undefined reference` hatası çıkar (`U` var, `T` yok); aynı sembol iki dosyada tanımlıysa `multiple definition` hatası çıkar. Hata mesajındaki sembol adını gördüğünde, ilk soru şudur: bu sembolün tanımı hangi nesne dosyasında olmalı ve bağlama komutuna o dosya eklendi mi?

## 37.10 Gerçek dünya: iki yürütücünün ölçümü ve Doruk'ta doğrulanan bulgular

Bu bölümün son adımı, Mini'nin iki yürütücüsünü aynı programlarda karşılaştırmaktır. Ağaç yorumlayıcı AST'yi doğrudan çalıştırır; VM ise bayt kodunu çalıştırır. İkisi aynı anlamı vermelidir. Yorumlayıcı, VM'in kullandığı aynı işlemleri (`c_bol`, `c_mod`) kullanır ve aynı analiz çıktısını (slot numaraları) tüketir; böylece farkı yalnızca yürütme biçimi belirler.

```python
# -*- coding: utf-8 -*-
"""Agac gezen yorumlayici: AST'yi doğrudan çalıştırir."""
from mini_on import (Sayi, Degisken, Ikili, Tekli, Cagri, Let, Ata,
                     Yaz, Eger, Dongu, Don, Ifade, Fonksiyon)
from derle import BIN, IKILI_OP


class DonusSinyali(Exception):
    """'return' için: üst çağrıya değer taşır."""

    def __init__(self, deger):
        self.deger = deger
```

Yorumlayıcının düğüm türüne göre dağıtımı bir sözlükle yapılır. Bu, Doruk'un `Ziyaretci` kalıbındaki sanal dağıtımın Python karşılığıdır: her düğüm türü için bir metot.

```python
class AgacYorumcu:
    def __init__(self):
        self.ciktilar = []
        self.fonk = {}
        # Dugum turunden metoda: ziyaretci kalibinin dict hali
        self.ifade_tablo = {
            Sayi: self.e_sayi, Degisken: self.e_deg,
            Tekli: self.e_tekli, Ikili: self.e_ikili,
            Cagri: self.e_cagri}
        self.deyim_tablo = {
            Let: self.d_ata, Ata: self.d_ata, Yaz: self.d_yaz,
            Ifade: self.d_ifade, Eger: self.d_eger,
            Dongu: self.d_dongu, Don: self.d_don}

    def calistir(self, program, main_locals):
        self.fonk = {d.ad: d for d in program
                     if isinstance(d, Fonksiyon)}
        env = [0] * main_locals
        for d in program:
            if not isinstance(d, Fonksiyon):
                self.deyim(d, env)
        return self.ciktilar

    # ---- deyimler ----
```

```python
    def deyim(self, s, env):
        self.deyim_tablo[type(s)](s, env)

    def d_ata(self, s, env):
        env[s.slot] = self.ifade(s.ifade, env)

    def d_yaz(self, s, env):
        self.ciktilar.append(self.ifade(s.ifade, env))

    def d_ifade(self, s, env):
        self.ifade(s.ifade, env)

    def d_don(self, s, env):
        raise DonusSinyali(self.ifade(s.ifade, env))

    def d_eger(self, s, env):
        if self.ifade(s.kosul, env):
            govde = s.dal
        else:
            govde = s.dal_degil or []
        for x in govde:
            self.deyim(x, env)

    def d_dongu(self, s, env):
        while self.ifade(s.kosul, env):
            for x in s.govde:
                self.deyim(x, env)

    # ---- ifadeler ----
```

```python
    def ifade(self, e, env):
        return self.ifade_tablo[type(e)](e, env)

    def e_sayi(self, e, env):
        return e.deger

    def e_deg(self, e, env):
        return env[e.slot]

    def e_tekli(self, e, env):
        return -self.ifade(e.ey, env)

    def e_ikili(self, e, env):
        a = self.ifade(e.sol, env)
        b = self.ifade(e.sag, env)
        return BIN[IKILI_OP[e.op]](a, b)

    def e_cagri(self, e, env):
        f = self.fonk[e.ad]
        args = [self.ifade(a, env) for a in e.args]
        yerel = args + [0] * (f.nlocals - len(args))
        try:
            for x in f.govde:
                self.deyim(x, yerel)
        except DonusSinyali as r:
            return r.deger
        return 0
```

Bayt kodu VM'in hız farkını ölçmek için iki sürüm yazdık: `derle.VM` (naif if-elif dağıtımı) ve `vm2.VMHizli` (sayaç yok, sık komutlar başta, yerel değişkenler). Dağıtımın maliyetini gösterebilmek için hızlı sürümü ayrıca koyduk.

```python
# -*- coding: utf-8 -*-
"""VM'in hizlandirilmis surumu: ayni bayt kodu, ayni anlam."""
from derle import VM, BIN

class VMHizli(VM):
    """Sayac yok, sik komutlar basta, yerel değişkenler."""
    def calistir(self):
        ana = self.kodlar["__main__"]
        yigin = []
        pop = yigin.pop
        push = yigin.append
        cerceve = [[ana, 0, [0] * ana.nlocals]]
        ciktilar = self.ciktilar
        while True:
            c = cerceve[-1]
            op, arg = c[0].komutlar[c[1]]
            c[1] += 1
            if op == "LOAD":
                push(c[2][arg])
            elif op == "PUSH":
                push(arg)
            elif op in BIN:
                b = pop()
                push(BIN[op](pop(), b))
            elif op == "STORE":
                c[2][arg] = pop()
            elif op == "JZ":
                if not pop():
                    c[1] = arg
            elif op == "JMP":
                c[1] = arg
            elif op == "PRINT":
                ciktilar.append(pop())
            elif op == "POP":
                pop()
            elif op == "NEG":
                push(-pop())
            elif op == "CALL":
                ad, argc = arg
                hedef = self.kodlar[ad]
```

```python
                ilk = len(yigin) - argc
                args = yigin[ilk:]
                del yigin[ilk:]
                cerceve.append([hedef, 0,
                                args + [0] * (hedef.nlocals - argc)])
            elif op == "RET":
                deger = pop()
                cerceve.pop()
                push(deger)
            elif op == "HALT":
                return ciktilar
```

Ana program, uçtan uca çalışan üç yürütücüyü dört farklı döngü boyutunda çalıştırır. Döngü gövdesi, her iterasyonda toplama, çarpma, mod ve bölme içerir; böylece hem tek komutlu hem de bölme (C semantiğiyle) işlemleri ölçülür. Her ölçüm üç tekrar alır ve en iyi süre kaydedilir. Ölçüm, sonuçların eşit olduğunu da `assert` ile doğrular.

```python
# -*- coding: utf-8 -*-
"""Ağaç yorumcusu ile bayt kodu VM'in hız ölçümü (deterministik)."""
import csv
import sys
import time
from mini import vm_ile_calistir, agacla_calistir, on_isle
from derle import Derleyici
from vm2 import VMHizli
from mini_ayr import Ayristirici
from mini_on import tokenize

KAYNAK = """
let i = 0;
let s = 0;
while (i < {n}) {{
    s = s + i * 3 % 7 - (i / 5);
    i = i + 1;
}}
print s;
"""

def en_iyi(f, tekrar=3):
    en = None
    for _ in range(tekrar):
        t0 = time.perf_counter()
        sonuc = f()
        dt = time.perf_counter() - t0
        en = dt if en is None or dt < en else en
    return en, sonuc

def ana(cikti):
    satirlar = [("n", "agac_s", "vm_s", "vm_hizli_s", "sonuç")]
    for n in (10000, 30000, 100000, 300000):
        k = KAYNAK.format(n=n)
        prog, ml = on_isle(k)
        kod = Derleyici().derle(prog, ml)
        ta, sa = en_iyi(lambda: agacla_calistir(k))
        tv, sv = en_iyi(lambda: vm_ile_calistir(k).ciktilar)
        th, sh = en_iyi(lambda: VMHizli(kod).calistir())
        assert sa == sv == sh, (n, sa, sv, sh)
```

```python
        satirlar.append((n, f"{ta:.4f}", f"{tv:.4f}", f"{th:.4f}",
                         sv[0]))
        print(n, f"agac={ta:.4f}s vm={tv:.4f}s vmhizli={th:.4f}s",
              "sonuç", sv[0])
    with open(cikti, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(satirlar)

def derinlik_siniri():
    """İç içe parantezde ayrıştırıcı hangi derinlikte patlar?"""
    lo, hi = 1, 2000
    while lo < hi:
        orta = (lo + hi + 1) // 2
        kaynak = "(" * orta + "1" + ")" * orta
        try:
            Ayristirici(tokenize(kaynak)).ifade()
            lo = orta
        except RecursionError:
            hi = orta - 1
    return lo

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "derinlik":
        print("maks parantez derinligi:", derinlik_siniri())
    else:
        ana(sys.argv[1] if len(sys.argv) > 1 else "b37_zaman.csv")
```

Ölçüm, `engine/veri/b37_zaman.csv` dosyasını üretir. Dosya ölçümümüzde şu değerleri verdi (CPython 3.12.10, Windows 11, tek makine; süreler saniye, en iyi of üç tekrar):

| n (döngü) | Ağaç yorumcusu | VM (naif) | VM (hızlı) |
|---|---|---|---|
| 10 000 | 0,0236 | 0,0520 | 0,0356 |
| 30 000 | 0,0680 | 0,1232 | 0,1038 |
| 100 000 | 0,2352 | 0,4157 | 0,3364 |
| 300 000 | 0,6800 | 1,2365 | 1,0121 |

![Şekil 37.10: Mini'nin üç yürütücüsünün süresi döngü sayısına göre. Ağaç yorumcusu bu ölçümde en hızlıdır; naif VM en yavaştır; hızlı VM, sayaç ve dal sırası iyileştirmesiyle naif VM'den belirgin biçimde hızlıdır ama ağaç yorumcusunu geçemez.](gorseller/b37_olcum.png)

Ölçüm, beklenen sonuçla çelişiyor: CPython üzerinde yazılmış bayt kodu VM, ağaç yorumcusundan **yavaş**. Bu durumun nedenini tahmin etmek yerine saydık. Aynı programda VM kaç komut çalıştırıyor, ağaç yorumcusu kaç düğüm ziyaret ediyor?

```python
# -*- coding: utf-8 -*-
"""Komut sayısı ve ziyaret sayısı: neden iki yürütücü farklı hızda?"""
from mini import on_isle
from derle import Derleyici, VM
from agac import AgacYorumcu
from olcum import KAYNAK


class Sayan(AgacYorumcu):
    sayac = 0

    def ifade(self, e, env):
        Sayan.sayac += 1
        return super().ifade(e, env)

    def deyim(self, s, env):
        Sayan.sayac += 1
        return super().deyim(s, env)


n = 100000
program, ml = on_isle(KAYNAK.format(n=n))
vm = VM(Derleyici().derle(program, ml))
vm.calistir()
Sayan().calistir(program, ml)
print("iterasyon:", n)
print("VM komut sayısı:", vm.komut_sayisi,
      "-> iterasyon başına", vm.komut_sayisi // n)
print("ağaç ziyaret sayısı:", Sayan.sayac,
      "-> iterasyon başına", Sayan.sayac // n)
```

```term
$ python sayim.py
iterasyon: 100000
VM komut sayısı: 2100011 -> iterasyon başına 21
ağaç ziyaret sayısı: 1900010 -> iterasyon başına 19
```

Sayılar yakın: iterasyon başına 21 komut ve 19 düğüm ziyareti. Fark, sayıda değil, **adım başına maliyette**. Naif VM her komut için Python düzeyinde bir döngü turu çalıştırır, bir tuple açar, ardından `if-elif` zincirinde sırayla karşılaştırma yapar (`PUSH`, `LOAD`, `STORE`, ... ve en sonda `BIN`). Ağaç yorumcusu ise her düğüm için tek bir sözlük aramasıyla doğrudan doğru metoda gider. Hızlı VM zincirin başına sık komutları koyarak ve sayacı kaldırarak farkı azalttı ama kapatamadı. Bu, CPython'un bayt kodu yürütme döngüsünün kendi maliyetinin, Python ile yazılmış bir VM'in kazancını yediğini gösterir. Bayt kodu VM'lerin asıl kazancı, döngünün C'de yazıldığı ve dağıtımın bir tablo atlamasına indirgendiği ortamlarda ortaya çıkar (genel bilgi: CPython'un kendisi C ile yazılmış bir bayt kodu VM'dir; yürütme döngüsü C'dedir). Dolayısıyla Mini'nin sonucu, "bayt kodu daha hızlıdır" sözünün koşullu olduğunu gösterir: dilin yürütme dili, dağıtımın maliyetini belirler.

Bu sonucu Doruk'a taşıyalım. Doruk'un yorumlayıcısı C++ ile yazılmıştır ve ziyaretçi sınıflarının sanal dağıtımını kullanır. Doruk'u bayt koduna çevirmenin kazancını ölçmedik; burada yalnızca bunun bir hipotez olduğunu ve Kendin Yap projelerinin bu ölçümü yapmanı istediğini söylüyoruz. Ölçmeden "daha hızlı olur" demek, bu bölümün öğrettiği hatanın tam kendisidir.

### Doruk'ta doğrulanan bulgular

Bu bölümde Doruk'u yalnızca okumadık: derledik, testlerini çalıştırdık ve birkaç küçük programla davranışını ölçtük. Derleme, `doruk` deposundaki `BUILD.md` ve `CMakeLists.txt` yönergelerine uygun olarak yapıldı, ancak CMake yerine WSL'de `g++ -std=c++17` ile; Catch2 Ubuntu paketinden alındı; `Surum.h` dosyası CMake tarafından üretildiği için bir kopyası elle oluşturuldu. Derleme çıktıları depoya yazılmadı; Temp dizininde yapıldı.

**Bulgu 1: test_parser.cpp derlenmiyor.** Catch2 3.4.0 ile `Catch::Approx` kullanan satır, `<catch2/catch_approx.hpp>` başlığı olmadan derlenmez. Başlık eklendiğinde test çalışır. Bu, kodun başka bir Catch2 sürümüyle dolaylı olarak gelen bir başlığa dayandığını gösterir: açık include, taşınabilirlik için şarttır.

**Bulgu 2: iki test başarısız.** `test_interpreter` içindeki "Bölme ondalık sonuç" testi `7 / 2` ifadesinin `3.5` vermesini bekliyor; ama yorumlayıcı `7 / 2` için `3` üretiyor. Kaynakta bunun bilinçli olduğu belli: `Interpreter.cpp` 481. satırdaki yorum "Her iki taraf da TAM_SAYI ise → tam sayi bolmesi (5/2=2)" diyor. Yani test ile uygulama çelişiyor ve hangisinin doğru olduğuna dil tasarımcısı karar vermeli: ya tam sayı bölmesi korunur ve test düzeltilir, ya da bölme ondalık yapılır ve yorum değişir. `test_parser`'daki "Sözlük literali" testi de başarısız: deyim başında `{` görülünce ayrıştırıcı bunu bir **blok** olarak okur (gramerdeki `deyim → blok | ifadeDeyim` sırası gereği). `değişken s = {"a": 1}` biçimi ise doğru çalışır. Yani test beklentisi, gramerle çelişiyor.

```term
$ ./test_lexer
All tests passed (277 assertions in 82 test cases)

$ ./test_interpreter
tests/test_interpreter.cpp:132: FAILED:
  REQUIRE( c.cikti == ("3.5\n") )
with expansion:
  "3
  "
  ==
  "3.5
  "
test cases: 40 | 39 passed | 1 failed

$ g++ ... tests/test_parser.cpp   (Catch::Approx için başlık eksik)
tests/test_parser.cpp:85:34: error: 'Approx' is not a member of 'Catch'

$ ./test_parser        (başlık eklenmiş kopyada)
tests/test_parser.cpp:508: FAILED:
  REQUIRE( s.basarili() )
test cases:  60 | 59 passed | 1 failed
```

**Bulgu 3: tam sayı bölmesinde çökme.** En dikkat çekici bulgu budur. En küçük `int64` değeri (`-9223372036854775807 - 1`) `-1`'e bölününce program çöküyor. C++ standardında işaretli tam sayı bölmesinde bu tür bir taşma tanımsız davranıştır (UB); x86-64'te `idiv` komutu bir istisna üretir ve işletim sistemi programı sonlandırır. Taşma tek başına zararsız görünüyor: `9223372036854775807 + 1` programda sessizce sarar (`-9223372036854775808`), ama bu da C++'ta tanımsız davranıştır ve derleyici ayarına göre farklı sonuç verebilir.

```term
$ cat bolme.drk
yazdır((-9223372036854775807 - 1) / -1)
$ ./doruk bolme.drk
Floating point exception (core dumped)
[çıkış kodu 136]

$ cat taşma.drk
yazdır(9223372036854775807 + 1)
$ ./doruk taşma.drk
-9223372036854775808
```

Düzeltme, bölmeden önce koşulu denetlemektir: `sl == INT64_MIN && sr == -1` ise hata fırlat. `%` işleci için de aynı durum geçerlidir. Bu, Bölüm 37.5'teki anlamsal denetimin dil düzeyinde bir örneğidir: hata çalışma zamanında değil, işlemden önce ele alınmalıdır.

**Bulgu 4: sütun numarası bayt sayıyor.** `Lexer::ilerle()` her çağrıda `sutun_` değerini bir artırır; bu, UTF-8 çok baytlı karakterleri (ğ, ş, ı) bir değil iki ya da daha fazla sütun sayar. Sonuç: `değ = 5` satırında `=` karakteri beşinci karakterdir, ama Doruk onu altıncı sütunda raporlar. ASCII bir isim aynı yapıda doğru sütunu verir.

```term
$ printf 'değ = 5\n' > a.drk ; ./doruk a.drk
[HATA] a.drk:1:6  Tanımsız değişken: 'değ'
$ printf 'degi = 5\n' > b.drk ; ./doruk b.drk
[HATA] b.drk:1:6  Tanımsız değişken: 'degi'
$ printf 'değişken x = 5 +\n' > e.drk ; ./doruk e.drk
[HATA] e.drk:2:1  Beklenmedik token: <dosya sonu>
```

**Bulgu 5: dosya sonu hatası yanlış satırda.** `değişken x = 5 +` satırının sonunda beklenen operand eksik. Hata, satırın sonundaki `+`ta değil, dosyanın bittiği `2:1` konumunda raporlanıyor. Bu, "dosya sonu" hatalarında konumun son satırın sonuna sabitlenmesi gerektiğini gösterir.

Bu beş bulgunun hepsi Doruk'un kendi kodunda, kendi testleriyle ve küçük programlarla doğrulandı. Hiçbiri bir hata yargısı değil; her biri bir tasarım kararı ya da bir kenar durum. Kendin Yap bölümünde bu bulguların bir kısmını düzeltmeni ve testle kanıtlamanı istiyoruz.

Son olarak, Doruk ile derleyici zincirleri arasındaki ilişkiyi bir cümleyle özetleyelim. Doruk bir yorumlayıcıdır: AST'yi doğrudan çalıştırır, makine kodu üretmez. GCC ve LLVM ise çok daha geniş bir boru hattıdır: ön uçları (C, C++, Rust), ara gösterimleri (GCC'de GIMPLE ve RTL; LLVM'de SSA biçimli LLVM IR) ve dilden bağımsız optimizasyon geçişlerini ayrı ayrı taşır (genel bilgi). Bu bölümde gördüğün her fikir, bu büyük sistemlerde de vardır; yalnızca ölçekleri farklıdır.

Gömülü hedefler için çapraz derleme, bu zincirin son adımında hedef mimariyi değiştirmekten ibarettir: ARM Cortex-M için `arm-none-eabi-gcc` gibi bir derleyici, aynı C kaynağını Thumb komutlarına çevirir ve STM32'nin bellek haritasına uygun bağlama betiğiyle bağlar (genel bilgi). Savunma sanayiinde bu zincirin her adımını bilmek, bir yazılımın hangi koşulda hangi davranışı göstereceğini öngörmenin yoludur; Bölüm 43'te bu zinciri gömülü bir hedef için kuracağız.

## Çözümlü Örnekler

Her örnek Bölüm 5'in altı adımını izler. Adım 6'da elle iz sürme tablosu vardır; kodu çalıştırmadan önce tabloyu kâğıtta kendin doldurmayı dene. Dört örnek, Pratt ayrıştırmasından çerçeve izine doğru zorluk artışını izler.

### Örnek 1 (★): Pratt ile bağlama gücü izi

**Problem.** `2 + 3 * (4 - 1)` ifadesinin değeri nedir ve ağaç nasıl kurulur? Ayrıştırıcı bu ifadeyi soldan sağa tek tek okusaydı ne olurdu, bunu da göster.

**Adım 1 — Anla.** Girdi tek bir aritmetik ifadedir. Çıktı bir sayıdır ve bu sayıyı ağacın yapısı belirler. İki olası sonuç var: işleçler sırayla (soldan sağa) uygulanırsa `(2 + 3) * (4 - 1) = 15`; işleç önceliği uygulanırsa `2 + (3 * 3) = 11`. Doğru olan ikincisidir, çünkü çarpma toplamadan sıkı bağlanır.

**Adım 2 — Örnekle.** Daha küçük bir örnek: `1 + 2 * 3`. Önceliksiz okumada `(1 + 2) * 3 = 9`; önceliklilikte `1 + (2 * 3) = 7`. Matematikte ve Mini'de sonuç 7'dir.

**Adım 3 — Kaba çöz.** Soldan sağa ilerleyip her işleci hemen uygulamak en basit yöntemdir. Bu yöntem `2 + 3 * 4` için 20 üretir (önce `2 + 3 = 5`, sonra `5 * 4 = 20`), ama doğru değer 14'tür. Kaba yöntem, bir işlecin sağındaki işlenenin kime ait olduğunu bilmez.

**Adım 4 — Örüntü.** Pratt yönteminde her işlecin bir gücü var (`*` 40, `+` 30). Ayrıştırıcı bir işleç gördüğünde, sağ işlenenini, o işlecin gücüyle özyinelemeli olarak okur. Sağdaki bir sonraki işlecin gücü mevcut işlecinkinden büyükse, o işleç sağ işleneni "çeker". Bu tek kural hem öncelik hem de birleşme yönünü verir.

**Adım 5 — İyileştir.** Güç tablosunu tek bir sözlükte tutmak, yeni bir işleç eklemeyi bir satır değişikliğine indirger. Parantez için de ayrı bir kural yazmak gerekmez: `(` bir öneki olarak okunur ve içindeki ifade `ifade(0)` ile baştan ayrıştırılır, bu yüzden parantez içi her zaman önce biter.

**Adım 6 — Doğrula.** Aşağıdaki tablo, `iz_pratt.py` çıktısındaki her `ifade(guc)` çağrısını ve döndürdüğü ağaç parçasını gösterir. Son satır ifadenin tamamına karşılık gelir.

| Çağrı | Şimdiki token | Döndürülen |
|---|---|---|
| `ifade(0)` | `2` | `(2 + (3 * (4 - 1)))` |
| `ifade(30)` (sağ `+`) | `3` | `(3 * (4 - 1))` |
| `ifade(40)` (sağ `*`) | `(` | `(4 - 1)` |
| `ifade(0)` (parantez içi) | `4` | `(4 - 1)` |
| `ifade(30)` (sağ `-`) | `1` | `1` |

Tablo, `*` işlecinin `3`ü sağa çektiğini ve parantezin bağımsız bir alt ağaç olduğunu doğruluyor. Programın sonucu, `print 2 + 3 * (4 - 1);` ile `[11]` olarak doğrulandı: `3 * 3 = 9`, `2 + 9 = 11`.

**Bunu AI'sız yazabilir misin?** `a - b - c` ile `a - (b - c)` için ağaçları kâğıtta çiz. Ayrıştırıcının `-` için hangi birleşme yönünü seçtiğini, `guc` parametresinin sağ tarafta neden `GUC[op]` olarak geçtiğini açıklayarak göster.

### Örnek 2 (★★): Kapsam ve gölgeleme

**Problem.** Aşağıdaki programın çıktısı nedir? İç bloktaki `x` ile dıştaki `x` nasıl ayrışır, ve her `x` hangi slot numarasına bağlanır?

```
let x = 1;
let y = x + 1;
if (y > 1) {
    let x = y * 10;
    print x;
}
print x;
```

**Adım 1 — Anla.** Programda iki `x` tanımı var: biri en dış kapsamda, biri `if` bloğunun içinde. Çıktı iki sayıdır; ilki iç `x`, ikincisi dış `x` olmalı.

**Adım 2 — Örnekle.** `y` değeri `x + 1 = 2`'dir; `y > 1` doğru olduğu için blok çalışır. İç blokta `x = y * 10 = 20` olur. Blok bitince dış `x` (değeri 1) geri gelir. Beklenen çıktı `20`, sonra `1`.

**Adım 3 — Kaba çöz.** Tek bir sözlükte `x` anahtarını kullanmak, iç bloktaki atamanın dış değeri ezmesine yol açar: ikinci `print x` 20 yazardı. Blok kapsamı, bu ezmeyi engellemek için ayrı bir sözlük ister.

**Adım 4 — Örüntü.** Her blok bir kapsam sözlüğü açar ve kapanınca onu atar. Bir isim aranırken en içten dışa doğru bakılır (`reversed(self.kapsam)`). Bu bir yığın yapısıdır: itme ve çekme, blok girişi ve çıkışına karşılık gelir.

**Adım 5 — İyileştir.** Analizci her yeni yerel değişkene yeni bir slot numarası verir ve slot sayacını hiçbir zaman geri çevirmez. Bu basit ve güvenlidir, ama yerel değişken sayısını gereksiz büyütür. Bir blok bittiğinde sayacı geri almak daha az yerel alan kullanır; bu, bu bölümün Ek alıştırmalarından biridir.

**Adım 6 — Doğrula.** Her satır için kapsam yığınını ve `x`'in çözümlendiği slotu izledik. Slot numaraları analizcinin sayacına göre dış `x` = 0, `y` = 1, iç `x` = 2 olur ve fonksiyonun yerel alanı 3 slot tutar.

| Satır | Olay | Kapsam yığını | Çözümlenen `x` |
|---|---|---|---|
| 1 | `let x = 1` | `[{x:0}]` | slot 0 (değer 1) |
| 2 | `let y = x + 1` | `[{x:0, y:1}]` | slot 0 |
| 3 | `if` bloğu açılır | `[{x:0, y:1}, {}]` | slot 0 |
| 4 | `let x = y * 10` | `[{x:0, y:1}, {x:2}]` | slot 2 (değer 20) |
| 5 | `print x` | aynı | slot 2 → `20` |
| 6 | blok kapanır | `[{x:0, y:1}]` | — |
| 7 | `print x` | aynı | slot 0 → `1` |

Gerçek çalıştırma `[20, 1]` çıktısını verdi; hem VM hem ağaç yorumcusu aynı sonucu üretti. Hata durumunu da gördük: `print z;` eklenirse `tanımsız değişken 'z'` hatası satır ve sütunla raporlanır (bu, `anlam_ornek.py` çıktısında vardır).

**Bunu AI'sız yazabilir misin?** Blok bittiğinde slot sayacını geri alan ve iki blokta aynı slotu kullanan bir analizci yaz. Hangi durumda bu güvensizdir? (İpucu: bir kapsamın bir değişkeni, bloğun bitişinden sonra bir kapanış tarafından yakalanıyorsa ne olur?)

### Örnek 3 (★★): Üç adresli kod, sabit katlama ve ölü kod

**Problem.** Aşağıdaki üç adresli programı optimize et. Hangi komutlar silinir, hangileri sabit olur ve çıktı değişir mi? Girdi `a = 7`.

```
x = 2 * 3
t1 = x + 4
y = t1 * a
t2 = 5 * 5
if_false t2 goto L1
goto L2
y = 0
L1:
print y
L2:
print x
```

**Adım 1 — Anla.** Program bir koşula bağlı iki yoldan birine gider. `t2 = 25` olduğu için koşul her zaman doğrudur; dal hiçbir zaman atlamaz. Yani `y = 0` ve `print y` hiçbir zaman çalışmaz. Çıktı tek bir sayıdır: `x = 6`.

**Adım 2 — Örnekle.** `a`'nın değeri çıktıyı etkilemez, çünkü `y` yalnızca ölü bir yolda `print` edilir. Bu, optimizasyonun `a`'ya hiç bakmadan `y`'yi silebileceğinin ilk ipucudur.

**Adım 3 — Kaba çöz.** Her komutu tek tek elle çalıştırmak 9 komut sürer. Bu, hem doğruluk kontrolü hem de optimizasyonun karşılaştırma tabanıdır: `calistir` fonksiyonu tam bu sayıyı verir.

**Adım 4 — Örüntü.** Üç geçiş görülüyor: (a) sabit işlenenli işlemleri katla ve sabitleri yay, (b) sabit koşullu dalı kaldır, (c) değeri hiç okunmayan atamaları sil. Geçişler birbirini besler; bu yüzden sabit noktaya kadar tekrarlanırlar.

**Adım 5 — İyileştir.** Tek turda bitmeyen zincir, sabit noktaya kadar tekrarlanarak çözülür. Son sonuç tek bir `PRINT 6` komutudur.

**Adım 6 — Doğrula.** Her geçişten sonra komut sayısı (etiketler hariç) ve programın kendisi:

| Geçiş | Yaptığı değişiklik | Komut sayısı |
|---|---|---|
| başlangıç | — | 9 |
| sabit katlama | `x=6`, `t1=10`, `t2=25`; `if_false` sabit → `goto L2` | 8 |
| erişilemez kod | `goto L2`'den sonra `y=0` ve `L1` bloğu silinir | 6 |
| gereksiz atlama | `goto L2` hemen `L2:`'den önce: silindi | 5 |
| etiket silme | hedefsiz `L1` silindi | 5 |
| ölü atama | `t1`, `t2`, `y` hiç okunmuyor: silindi | 2 |
| 2. tur sabit katlama | `print x` → `print 6` (blok sınırı kalktı) | 2 |
| 2. tur ölü atama | `x = 6` artık okunmuyor: silindi | 1 |

Sonuç: `önce komut: 9`, `sonra komut: 1`, çıktılar `[6]` ve `[6]`. Yorumcu, önce ve sonra için sırasıyla 8 ve 1 adım saydı. Aynı kuralın 2000 rastgele ileri atlamalı IR programında da (`test_ir.py`, seed 37) çıktıyı değiştirmediği doğrulandı.

**Bunu AI'sız yazabilir misin?** Yukarıdaki tabloyu yalnızca `x = y op z` biçiminde bir sabit katlama geçişiyle yapmayı dene. Hangi durumda `a * 0` ifadesini `0`'a katlamak yanlış olur? (İpucu: `a` bir fonksiyon çağrısının sonucu ve yan etkisi varsa ne olur?)

### Örnek 4 (★★★): Yığın makinesinde fonksiyon çağrısının çerçeve izi

**Problem.** `fn kare(x) { return x * x; } print kare(3) + 1;` programı yığın makinesinde nasıl çalışır? Her komutta yığın ne, çerçeveler ne, argüman nereye gider ve dönüş değeri nerede kalır?

**Adım 1 — Anla.** Program bir fonksiyon tanımlar ve onu `3` ile çağırır, dönüş değerine `1` ekler ve yazdırır. Beklenen çıktı `10`'dur (`9 + 1`).

**Adım 2 — Örnekle.** `kare(2) + 1` olsaydı `5` olurdu. Argümanın değeri değişse de mekanizma aynıdır: argüman bir değerdir ve çağrının başında bir yerel slota kopyalanır.

**Adım 3 — Kaba çöz.** Bir fonksiyon çağrısını, argümanları ve dönüş değerini bir yığında taşıyan bir çağrı protokolü olarak düşün. Her çağrı bir çerçeve açar; dönüş onu kapatır.

**Adım 4 — Örüntü.** Çağrı üç aşamadan oluşur: (a) argümanlar yığında hazırlanır, (b) `CALL` argümanları yığından çekip yeni çerçevenin ilk slotlarına koyar ve çerçeveyi açar, (c) `RET` yığının tepesindeki değeri alıp çerçeveyi kapatır ve değeri çağırana geri verir.

**Adım 5 — İyileştir.** Argümanları yığından kopyalamak yerine, çerçeveyi yığının üstünde ortaklaşa kullanmak kopyalamayı önler. Gerçek derleyiciler bunu yazmaçlarla ve ABI kurallarıyla yapar (Bölüm 24.4). Bu, ayrıca bir alıştırma olarak bırakılmıştır.

**Adım 6 — Doğrula.** Aşağıdaki tablo `iz_yigin.py` çıktısıdır. "Yığın (önce)" sütunu her komut çalışmadan önceki işlenen yığınını gösterir.

| Adım | Çerçeve | Komut | Yığın (önce) | Derinlik |
|---|---|---|---|---|
| 1 | `__main__` | `PUSH 3` | `[]` | 1 |
| 2 | `__main__` | `CALL kare` | `[3]` | 1 |
| 3 | `kare` | `LOAD 0` | `[]` | 2 |
| 4 | `kare` | `LOAD 0` | `[3]` | 2 |
| 5 | `kare` | `MUL` | `[3, 3]` | 2 |
| 6 | `kare` | `RET` | `[9]` | 2 |
| 7 | `__main__` | `PUSH 1` | `[9]` | 1 |
| 8 | `__main__` | `ADD` | `[9, 1]` | 1 |
| 9 | `__main__` | `PRINT` | `[10]` | 1 |
| 10 | `__main__` | `HALT` | `[]` | 1 |

Tablo üç şeyi doğruluyor. Adım 2'de argüman yığından çekilmiş ve adım 3'te yeni çerçevenin 0. slotu `3` olmuştur. Adım 6'da `RET` çağrıyı kapatır ve `9`'u yığına bırakır; derinlik 1'e düşer. Adım 9'da `PRINT` `10`'u çıktıya gönderir. Gerçek çalıştırma `[10]` çıktısını verdi. Bu, Şekil 37.8'de görselleştirilmiştir.

**Bunu AI'sız yazabilir misin?** Programa `fn iki(x) { return kare(x) + kare(x); }` ekle ve `print iki(3);` çağrısının çerçeve izini yaz. İç içe çağrıda derinliğin en fazla kaç olacağını ve her çerçevenin hangi slot değerlerini taşıyacağını önceden hesapla, sonra çalıştır.

## Kendin Yap Projeleri

::: dikkat
Bu iki projeyi bir yapay zekâ aracının kodunu kopyalayarak değil, kendi kâğıdında tasarlayıp sıfırdan yazarak yap. Önce dilbilgisini, öncelik tablosunu ve her komutun yığına etkisini elle yaz; kodu bunların üstüne kur. Bölüm 37'nin amacı, bir derleyicinin boru hattını boş bir dosyada kurabilmektir.
:::

### Proje 1 (★★): Doruk'un bir alt kümesi için bayt kodu derleyicisi ve VM

**Amaç:** Doruk dilinin tamsayı, değişken, `yazdır`, `eğer` ve `döngü` içeren bir alt kümesi için bir bayt kodu derleyicisi ve sanal makine yaz. Sonuçları, Doruk'un kendi yorumlayıcısı ile aynı programlarda karşılaştır ve hız farkını ölç.

**Beklenen davranış:**

1. `değişken x = 10` ve `yazdır(x * 2 + 1)` gibi programlar, Doruk CLI'sinin verdiği çıktıyla birebir aynı çıktıyı verir.
2. `7 / 2` ifadesinin sonucu, Doruk'un bilinçli tam sayı bölmesi kuralına göre `3` olur; `-7 / 2` ise `-3` (sıfıra doğru yuvarlama). Bu kuralı Doruk'un `Interpreter.cpp` 481. satırındaki yorumundan doğrula.
3. Sıfıra bölme, derleyici bayt kodu üretmeden önce yakalanmalıdır; yalnızca çalışma zamanında değil.
4. Aynı programda, yorumlayıcı ile VM'in çıktısı rastgele 500 ifade için eşit olmalıdır (sabit tohum kullan).
5. Döngü içeren bir programda iki yürütücünün süresi ölçülüp bir CSV dosyasına yazılır.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Dilbilgisini Doruk'un `Parser.cpp` dosyasındaki yorum satırlarından al; ayrıştırıcıyı ilk olarak Mini'deki gibi Pratt yöntemiyle yazabilirsin. Sembol tablosunu bir kapsam yığınında tut ve her yerel değişkene bir slot ver. Derleyicinin ilk sürümünde yalnızca `PUSH`, `LOAD`, `STORE`, ikili işlemler ve `JZ/JMP` komutları yeterlidir. Test için Mini'deki `test_mini.py` yaklaşımını kullan: rastgele ifade üret, bağımsız bir referans değerlendirme ile karşılaştır.

**Başarı kriterleri:**

- Doruk'un `tests/` dizinindeki tamsayı ve aritmetik testlerinden en az yarısı, bayt kodu VM'de de geçer.
- Rastgele 500 ifade için VM ve yorumlayıcı sonuçları eşittir (tohum belirtilmiş).
- Hız ölçümünde iki yürütücünün süresi, döngü sayısına göre en az üç farklı boyutta CSV olarak kaydedilmiştir; sonuçların yorumu "ölçümüne göre" diye yazılmıştır.

### Proje 2 (★★★): İHA görev betik dili: lexer, parser, anlamsal denetim ve simülatör

**Amaç:** Bir insansız hava aracının görevini yazmak için küçük bir betik dili tasarla ve uygula. Dil, `KALK 50`, `GIT 39.9 32.8`, `BEKLE 10` gibi komutlar ve `EGER batarya < 20 ISE DON` gibi koşullar içersin. Anlamsal denetim, fiziksel sınırları (irtifa, batarya yüzdesi, koordinat aralığı) çalıştırmadan önce yakalasın. Bir simülatör, programın uçuş profilini adım adım yazdırsın.

**Beklenen davranış:**

1. `KALK 50` komutu bir irtifa hedefi taşır; irtifa tanımlı bir üst sınırın üzerindeyse anlamsal denetim, programı çalıştırmadan reddeder ve satır numarasıyla bildirir.
2. `GIT x y` komutunda koordinatlar tanımlı bir alanın içinde değilse aynı şekilde reddedilir.
3. `EGER batarya < 20 ISE DON` koşulu, simülatörde batarya değerine göre çalışır; `DON` komutu eve dönüş rotası üretir (ayrıntıyı sen tanımla).
4. Hatalı bir dosya için birden çok hata varsa, panik modu ile hepsi raporlanır (Bölüm 37.3).
5. Simülatör, her adımda konum, irtifa ve bataryayı bir tablo olarak yazar.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Önce yalnızca `KALK` ve `BEKLE` ile bir ayrıştırıcı yaz, sonra yeni komutları ekle. Komut türlerini bir AST sınıf hiyerarşisi olarak modelle (Bölüm 22'deki Command kalıbı işe yarayabilir). Anlamsal denetimde her komutun parametrelerini bir tablodan kontrol et. Simülatörü, Bölüm 37.8'deki çağrı çerçevesi fikriyle "görev alt rutinleri" olarak düşünebilirsin.

**Başarı kriterleri:**

- En az 10 farklı hatalı girdi için, hata satır ve sütunuyla doğru raporlanır (test dosyası ile).
- Üç farklı görev dosyası, simülatörde beklenen son konumu ve bataryayı verir.
- Sınır değerler (irtifa üst sınırında, batarya tam 20 iken) için testler yazılmıştır.

## Ek Alıştırmalar

Aşağıdaki alıştırmalar cevapsız. Her birini önce kâğıtta çöz; kodu yazdıktan sonra kontrol et. (Mülakat) etiketli olanlar klasik mülakat sorularıdır.

1. ★ `2 - 3 - 4` ifadesi için Pratt ayrıştırıcının ürettiği ağacı çiz. Sonuç `-5` mi, `3` mü? Hangi değişiklik soldan birleşmeyi sağdan birleşmeye çevirir? (Üs işleci `^` için aynı soruyu sor.)
2. ★ Mini'deki `c_bol` fonksiyonu sıfıra doğru yuvarlar. Python'un `//` işleci aşağı yuvarlar. `-7 // 2` ve `-7 / 2` (C semantiği) farkını bir tabloya yaz ve hangi programlarda hangisinin istendiğini açıkla.
3. ★ Bir kapsamın değişkenlerini blok bittiğinde geri veren bir analizci yaz. Örnek 2'deki programda kaç slot kullanılır?
4. ★★ Sol özyinelemeyi kaldıran dönüşümü `A → Aα | Aβ | γ` (çok sayıda `α` ve `β`) için genelleştir. Yeni gramerin FIRST ve FOLLOW kümelerini bir örnekte hesapla. (Mülakat)
5. ★★ Shunting-yard algoritmasını (Bölüm 8'in Kendin Yap bölümündeki yığın fikriyle) Mini'nin dilbilgisine uygula. Pratt ile aynı ağacı ürettiğini üç ifade üzerinde doğrula.
6. ★★ Üç adresli kodda ortak alt ifade eleme (CSE) geçişi yaz: `a = b + c; d = b + c` yerine ikinci atamayı `d = a` yap. Bu geçişin güvenlik koşulu nedir? (İpucu: `b` veya `c` arada değişirse ne olur?) (Mülakat)
7. ★★ IR'ına döngü ekle (geriye atlama) ve sabit katlama geçişinin döngüde neden yanlış sonuç verebileceğini bir örnekle göster. Bloklar arası veri akışı gerektiren bu durumu nasıl çözersin?
8. ★★ `ll1.py` betiğinden faydalanarak, `S → ( S ) S | ε` gramerinin LL(1) olup olmadığını hesapla. Bu gramer neden dengeli parantez dillerine karşılık gelir ve neden LL(1)'dir? (Mülakat)
9. ★★ Yığın makinesi bayt kodunda `DUP` (tepeyi çoğalt) komutu ekle. `x = y = 5` gibi zincirleme atamayı bu komutla derle. Hangi derleme sırası gerekir?
10. ★★★ Mini'nin çağrı çerçevesine `ret` olmadan düşen bir fonksiyonun dönüş değerini `0` yapar. Bunu bir derleme uyarısına dönüştür: yalnızca bazı yolların `return` içerdiği fonksiyonlarda uyarı ver. Bunu yapmak için kontrol akış grafının hangi özelliğine bakarsın? (Mülakat)
11. ★★★ Bir yazmaç tahsisi yaz: yerel değişkenlerin girişim grafını çıkar ve en çok `k` yazmaçla boyamaya çalış. Boyanamazsa bir değişkeni belleğe döken (spill) basit bir sezgi uygula. Sonucu üç farklı programda test et.
12. ★★★ Doruk'un yorumlayıcısındaki bölme ve mod işlemlerine `INT64_MIN` / `-1` kontrolünü ekle; test yaz; `ornek.drk` ile regresyon kontrolü yap. (Mülakat: "Tanımsız davranış nedir ve hangi durumda bir derleyici onu optimize edebilir?")

## Kod Okuma Egzersizi

Bu egzersizde Mert'in kendi derleyici projesi Doruk'un ayrıştırıcısından bir kesit okuyacaksın. Kesit birebir kopyadır: `Doruk/engine/src/Parser.cpp` dosyasının 700–727. satırları (`toplama` ve `carpma` fonksiyonları). Dosya, Doruk'un ayrıştırıcısının öncelik kodlamasının çağrı zinciriyle nasıl yapıldığını gösterir.

**Doruk, `engine/src/Parser.cpp`, satır 700–727 (toplama ve çarpma):**

```cpp
IfadePtr Parser::toplama() {
    auto sol = carpma();

    while (kontrol(TokenTuru::ARTI) || kontrol(TokenTuru::EKSI)) {
        Token op  = ilerle();
        auto  sag = carpma();
        sol = std::make_unique<IkiliIfade>(
            std::move(sol), op, std::move(sag));
    }

    return sol;
}

// ── Çarpma / Bölme / Mod ──────────────────────────────────
IfadePtr Parser::carpma() {
    auto sol = tekli();

    while (kontrol(TokenTuru::CARPIM) ||
           kontrol(TokenTuru::BOLUM)  ||
           kontrol(TokenTuru::MOD)) {
        Token op  = ilerle();
        auto  sag = tekli();
        sol = std::make_unique<IkiliIfade>(
            std::move(sol), op, std::move(sag));
    }

    return sol;
}
```

**Sorular — cevaplamadan geçme:**

1. `toplama()` içindeki `auto sol = carpma();` satırı, `carpma()`'nın neden bir alt katman olarak çağrıldığını açıklar. Toplama ile çarpma arasındaki öncelik hangi çağrı sırasından gelir? Bu öncelik, dilbilgisi yorumundaki kuralla nasıl eşleşir?
2. `while` döngüsünün içinde `sol = std::make_unique<IkiliIfade>(...)` atamasının yaptığı işi, ağaç şekli üzerinden açıkla. `1 - 2 - 3` ifadesi için döngü her iterasyonda ağacın hangi düğümünü yeniden sarar?
3. `carpma()` ile `toplama()` arasındaki fark yalnızca işleç listesi midir? Bir işleç eklemek (örneğin `**`) için hangi fonksiyonu değiştirirsin ve neden yalnızca onu?
4. Bu tasarımın Pratt yöntemine göre bir avantajı ve bir dezavantajı nedir? (Bölüm 37.3'teki karşılaştırmayı kullan.)
5. `sag = carpma();` yerine `sag = toplama();` yazılsaydı ne olurdu? Bunu `2 + 3 + 4` ile düşün: ayrıştırıcı sonsuz özyinelemeye mi girer, yoksa farklı bir ağaç mı üretir?
6. (Mülakat) Bu ayrıştırıcının hata durumunda `tuket()` ve `senkronize()` ile nasıl davrandığını, sol özyineleme olmamasının bu davranışı nasıl kolaylaştırdığını açıkla.

## Bölüm Özeti

Bu bölümde derleyicinin içini, bir ön uçtan arka uca kadar, küçük bir dille birlikte gördük:

- **Spektrum**: derleyici, yorumlayıcı, bayt kodu VM ve JIT aynı problemin farklı zaman ve bellek dengeleridir. CPython'un `dis` dökümü, bayt kodunun yığın tabanlı yapısını gösterir.
- **Boru hattı**: ön uç dile özgüdür; orta katman ara gösterim üzerinde çalışır; arka uç hedefe özgüdür. Doruk ön uç ve bir yorumlayıcıdır.
- **Ayrıştırma**: özyinelemeli iniş, LL(1) için FIRST/FOLLOW kümeleri ve sol özyinelemenin kaldırılması; Pratt ile bağlama gücü; LR'nin kaydır-indirge sezgisi; panik modu ve senkronizasyon.
- **AST ve anlamsal analiz**: CST'den AST'ye geçiş, ziyaretçi kalıbı; sembol tablosu, kapsam yığını, gölgeleme ve tür denetimi.
- **Ara gösterim**: üç adresli kod, temel bloklar ve CFG (V(G) Bölüm 23'te), SSA ve φ düğümü; GCC'nin GIMPLE dökümü.
- **Optimizasyon**: sabit katlama, sabit yayılımı, erişilemez ve ölü kod eleme; geçişlerin sabit noktaya kadar tekrarı. gcc'nin `-O0`/`-O2` çıktısında bu geçişlerin izleri ve kuyruk özyinelemesinin döngüye dönüşümü görüldü.
- **Kod üretimi ve çalışma zamanı**: yığın makinesi, çerçeveler, argüman ve dönüş kuralları; çöp toplama türleri ve referans sayımının sınırları.
- **Bağlama**: sembol, yer değiştirme, statik ve dinamik bağlama; boyut farkı ölçümle.
- **Ölçüm**: Mini'de ağaç yorumcusu, naif VM ve hızlı VM'in süreleri; Python'da bayt kodu VM'in neden kazanmadığı, komut ve düğüm sayılarıyla açıklandı.
- **Doruk'ta doğrulanan bulgular**: eksik başlık, iki başarısız test, `INT64_MIN / -1` çökmesi, bayt tabanlı sütun sayımı ve dosya sonu hatasının konumu.

**Sonraki bölümde:** Kısım IX'un son bölümünü bitirdik. Bölüm 38'de **Git Derinlemesine** başlıyor ve bununla birlikte Kısım X — Yazılım Mühendisliği Pratiği açılıyor. Bu bölümde yaptığımız gibi bir projeyi versiyonlamanın, değişikliği izlemenin ve ekiple birlikte çalışmanın mühendislik yönünü ele alacağız. Git'in nesne modelini (blob, tree, commit) görünür kılacak, `git bisect` ile bir regresyonu nasıl bulduğumuzu göstereceğiz. Doruk gibi bir depoda hangi dalın hangi testi geçtiğini izlemek, bu bölümdeki bulguları düzenli bir iş akışına bağlamanın ilk adımı olacak.

::: mulakat
Klasik sorular; her birini birkaç dakika kâğıtta düşündükten sonra cevapla:

1. Bir ifadeyi ayrıştırırken `a - b - c` ile `a ^ b ^ c` farklı birleşme yönü almalı. Bunu hangi parametre belirler ve Pratt ayrıştırıcıda hangi satır bunu kodlar?
2. Sol özyinelemeli bir gramerde özyinelemeli iniş ayrıştırıcı neden sonsuz döngüye girer? Gramerin hangi biçimi bu sorunu çözer?
3. Bir LL(1) ayrıştırıcı ile bir LR(1) ayrıştırıcı arasındaki fark nedir? Hangi gramerler LR(1) ama LL(1) değildir ve bunun bir örneğini ver.
4. Yığın makinesi ile yazmaç makinesi bayt kodu arasındaki farkı, her biri için bir üretim (kod boyutu, hız, tahsis) açısından karşılaştır.
5. Bir optimizasyon geçişi neden kendi başına doğru sonuç verse bile, diğer geçişlerle birlikte sabit noktaya kadar çalıştırılması gerekebilir? Bir örnekle açıkla.
6. Bir değişkeni yazmaca koymak için graf boyama kullanılıyor. Girişim grafında k renk yetmiyorsa ne yapılır, ve hangi değişken seçilir?
7. Statik bağlama ile dinamik bağlamanın, bir gömülü sistemin bellek bütçesi ve güvenlik güncellemeleri açısından dengesi nedir?
8. Bir derleyici hata mesajında sütun numarası bayt sayıyorsa, Türkçe karakterli bir kaynak dosyada neden bir sorun olur? Bu sorunu hangi kodla düzeltirsin?
:::
